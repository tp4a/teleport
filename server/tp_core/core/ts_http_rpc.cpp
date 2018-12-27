#include "ts_http_rpc.h"
#include "ts_ver.h"
#include "ts_env.h"
#include "ts_session.h"
#include "ts_crypto.h"
#include "ts_web_rpc.h"
#include "tp_tpp_mgr.h"

extern TppManager g_tpp_mgr;

#include <teleport_const.h>


#define HEXTOI(x) (isdigit(x) ? x - '0' : x - 'W')
int ts_url_decode(const char *src, int src_len, char *dst, int dst_len, int is_form_url_encoded)
{
	int i, j, a, b;

	for (i = j = 0; i < src_len && j < dst_len - 1; i++, j++)
	{
		if (src[i] == '%')
		{
			if (i < src_len - 2 && isxdigit(*(const unsigned char *)(src + i + 1)) &&
				isxdigit(*(const unsigned char *)(src + i + 2))) {
				a = tolower(*(const unsigned char *)(src + i + 1));
				b = tolower(*(const unsigned char *)(src + i + 2));
				dst[j] = (char)((HEXTOI(a) << 4) | HEXTOI(b));
				i += 2;
			}
			else
			{
				return -1;
			}
		}
		else if (is_form_url_encoded && src[i] == '+')
		{
			dst[j] = ' ';
		}
		else
		{
			dst[j] = src[i];
		}
	}

	dst[j] = '\0'; /* Null-terminate the destination */

	return i >= src_len ? j : -1;
}

TsHttpRpc::TsHttpRpc() :
	ExThreadBase("http-rpc-thread")
{
	mg_mgr_init(&m_mg_mgr, NULL);
}

TsHttpRpc::~TsHttpRpc()
{
	mg_mgr_free(&m_mg_mgr);
}

void TsHttpRpc::_thread_loop(void)
{
	EXLOGI("[core] TeleportServer-RPC ready on %s:%d\n", m_host_ip.c_str(), m_host_port);

	while (!m_need_stop)
	{
		mg_mgr_poll(&m_mg_mgr, 500);
	}

	EXLOGV("[core] rpc main loop end.\n");
}


bool TsHttpRpc::init(void)
{
	struct mg_connection* nc = NULL;

	m_host_ip = g_env.rpc_bind_ip;
	m_host_port = g_env.rpc_bind_port;

	char addr[128] = { 0 };
	// 	if (0 == strcmp(m_host_ip.c_str(), "127.0.0.1") || 0 == strcmp(m_host_ip.c_str(), "localhost"))
	// 		ex_strformat(addr, 128, ":%d", m_host_port);
	// 	else
	// 		ex_strformat(addr, 128, "%s:%d", m_host_ip.c_str(), m_host_port);
	if (0 == strcmp(m_host_ip.c_str(), "0.0.0.0"))
		ex_strformat(addr, 128, ":%d", m_host_port);
	else
		ex_strformat(addr, 128, "%s:%d", m_host_ip.c_str(), m_host_port);

	nc = mg_bind(&m_mg_mgr, addr, _mg_event_handler);
	if (NULL == nc)
	{
		EXLOGE("[core] rpc listener failed to bind at %s.\n", addr);
		return false;
	}

	nc->user_data = this;

	mg_set_protocol_http_websocket(nc);

	// 导致内存泄露的地方（每次请求约消耗1KB内存）
	// DO NOT USE MULTITHREADING OF MG.
	// cpq (one of the authors of MG) commented on 3 Feb: Multithreading support has been removed.
	// https://github.com/cesanta/mongoose/commit/707b9ed2d6f177b3ad8787cb16a1bff90ddad992
	//mg_enable_multithreading(nc);

	return true;
}

void TsHttpRpc::_mg_event_handler(struct mg_connection *nc, int ev, void *ev_data)
{
	struct http_message *hm = (struct http_message*)ev_data;

	TsHttpRpc* _this = (TsHttpRpc*)nc->user_data;
	if (NULL == _this)
	{
		EXLOGE("[core] rpc invalid http request.\n");
		return;
	}

	switch (ev)
	{
	case MG_EV_HTTP_REQUEST:
	{
		ex_astr ret_buf;

		ex_astr uri;
		uri.assign(hm->uri.p, hm->uri.len);

		//EXLOGD("[core] rpc got request: %s\n", uri.c_str());

		if (uri == "/rpc")
		{
			ex_astr method;
			Json::Value json_param;

			ex_rv rv = _this->_parse_request(hm, method, json_param);
			if (TPE_OK != rv)
			{
				EXLOGE("[core] rpc got invalid request.\n");
				_this->_create_json_ret(ret_buf, rv);
			}
			else
			{
				EXLOGD("[core] rpc got request method `%s`\n", method.c_str());
				_this->_process_request(method, json_param, ret_buf);
			}
		}
		else
		{
			EXLOGE("[core] rpc got invalid request: not `rpc` uri.\n");
			_this->_create_json_ret(ret_buf, TPE_PARAM, "not a `rpc` request.");
		}

		mg_printf(nc, "HTTP/1.0 200 OK\r\nAccess-Control-Allow-Origin: *\r\nContent-Length: %d\r\nContent-Type: application/json\r\n\r\n%s", (int)ret_buf.size() - 1, &ret_buf[0]);
		nc->flags |= MG_F_SEND_AND_CLOSE;
	}
	break;
	default:
		break;
	}
}

ex_rv TsHttpRpc::_parse_request(struct http_message* req, ex_astr& func_cmd, Json::Value& json_param)
{
	if (NULL == req)
		return TPE_PARAM;

	bool is_get = true;
	if (req->method.len == 3 && 0 == memcmp(req->method.p, "GET", req->method.len))
		is_get = true;
	else if (req->method.len == 4 && 0 == memcmp(req->method.p, "POST", req->method.len))
		is_get = false;
	else
		return TPE_HTTP_METHOD;

	ex_astr json_str;
    bool need_decode = false;
    if (is_get) {
        json_str.assign(req->query_string.p, req->query_string.len);
        need_decode = true;
    }
    else {
        json_str.assign(req->body.p, req->body.len);
        if (json_str.length() > 0 && json_str[0] == '%')
            need_decode = true;
    }

    if (need_decode) {
        // 将参数进行 url-decode 解码
        int len = json_str.length() * 2;
        ex_chars sztmp;
        sztmp.resize(len);
        memset(&sztmp[0], 0, len);
        if (-1 == ts_url_decode(json_str.c_str(), json_str.length(), &sztmp[0], len, 0))
            return TPE_HTTP_URL_ENCODE;

        json_str = &sztmp[0];
    }

	if (0 == json_str.length())
		return TPE_PARAM;

    Json::Reader jreader;

	if (!jreader.parse(json_str.c_str(), json_param))
		return TPE_JSON_FORMAT;

	if (json_param.isArray())
		return TPE_PARAM;

	if (json_param["method"].isNull() || !json_param["method"].isString())
		return TPE_PARAM;

	func_cmd = json_param["method"].asCString();
	json_param = json_param["param"];

	return TPE_OK;
}

void TsHttpRpc::_create_json_ret(ex_astr& buf, int errcode, const Json::Value& jr_data)
{
	// 返回： {"code":errcode, "data":{jr_data}}

	Json::FastWriter jr_writer;
	Json::Value jr_root;

	jr_root["code"] = errcode;
	jr_root["data"] = jr_data;
	buf = jr_writer.write(jr_root);
}

void TsHttpRpc::_create_json_ret(ex_astr& buf, int errcode)
{
	// 返回： {"code":errcode}

	Json::FastWriter jr_writer;
	Json::Value jr_root;

	jr_root["code"] = errcode;
	buf = jr_writer.write(jr_root);
}

void TsHttpRpc::_create_json_ret(ex_astr& buf, int errcode, const char* message)
{
	// 返回： {"code":errcode, "message":message}

	Json::FastWriter jr_writer;
	Json::Value jr_root;

	jr_root["code"] = errcode;
	jr_root["message"] = message;
	buf = jr_writer.write(jr_root);
}

void TsHttpRpc::_process_request(const ex_astr& func_cmd, const Json::Value& json_param, ex_astr& buf)
{
	if (func_cmd == "request_session") {
		_rpc_func_request_session(json_param, buf);
	}
	else if (func_cmd == "kill_sessions") {
		_rpc_func_kill_sessions(json_param, buf);
	}
	else if (func_cmd == "get_config") {
		_rpc_func_get_config(json_param, buf);
	}
	else if (func_cmd == "set_config") {
		_rpc_func_set_config(json_param, buf);
	}
	else if (func_cmd == "enc") {
		_rpc_func_enc(json_param, buf);
	}
	else if (func_cmd == "exit") {
		_rpc_func_exit(json_param, buf);
	}
	else {
		EXLOGE("[core] rpc got unknown command: %s\n", func_cmd.c_str());
		_create_json_ret(buf, TPE_UNKNOWN_CMD);
	}
}

extern bool g_exit_flag;	// 要求整个TS退出的标志（用于停止各个工作线程）
void TsHttpRpc::_rpc_func_exit(const Json::Value& json_param, ex_astr& buf)
{
	// 设置一个全局退出标志
	g_exit_flag = true;
	_create_json_ret(buf, TPE_OK);
}

void TsHttpRpc::_rpc_func_get_config(const Json::Value& json_param, ex_astr& buf)
{
	Json::Value jr_data;

	ex_astr _replay_name;
	ex_wstr2astr(g_env.m_replay_path, _replay_name);
	jr_data["replay-path"] = _replay_name;

	jr_data["web-server-rpc"] = g_env.web_server_rpc;

	ex_astr _version;
	ex_wstr2astr(TP_SERVER_VER, _version);
	jr_data["version"] = _version;

	ExIniFile& ini = g_env.get_ini();
	ex_ini_sections& secs = ini.GetAllSections();
	ex_ini_sections::iterator it = secs.begin();
	for (; it != secs.end(); ++it)
	{
		if (it->first.length() > 9 && 0 == wcsncmp(it->first.c_str(), L"protocol-", 9))
		{
			ex_wstr name;
			name.assign(it->first, 9, it->first.length() - 9);
			ex_astr _name;
			ex_wstr2astr(name, _name);

			bool enabled = false;
			it->second->GetBool(L"enabled", enabled, false);

			ex_wstr ip;
			if (!it->second->GetStr(L"bind-ip", ip))
				continue;
			ex_astr _ip;
			ex_wstr2astr(ip, _ip);

			int port;
			it->second->GetInt(L"bind-port", port, 52189);

			jr_data[_name.c_str()]["enable"] = enabled;
			jr_data[_name.c_str()]["ip"] = _ip;
			jr_data[_name.c_str()]["port"] = port;
		}
	}

	_create_json_ret(buf, TPE_OK, jr_data);
}

void TsHttpRpc::_rpc_func_request_session(const Json::Value& json_param, ex_astr& buf)
{
	// https://github.com/tp4a/teleport/wiki/TELEPORT-CORE-JSON-RPC#request_session

	int conn_id = 0;
	ex_rv rv = TPE_OK;

	if (json_param["conn_id"].isNull())
	{
		_create_json_ret(buf, TPE_PARAM);
		return;
	}
	if (!json_param["conn_id"].isInt())
	{
		_create_json_ret(buf, TPE_PARAM);
		return;
	}

	conn_id = json_param["conn_id"].asInt();
	if (0 == conn_id)
	{
		_create_json_ret(buf, TPE_PARAM);
		return;
	}

	TS_CONNECT_INFO* info = new TS_CONNECT_INFO;
	if ((rv = ts_web_rpc_get_conn_info(conn_id, *info)) != TPE_OK)
	{
		_create_json_ret(buf, rv);
		return;
	}

// 	info->ref_count = 0;
// 	info->ticket_start = ex_get_tick_count();
// 
	// 生成一个session-id（内部会避免重复）
	ex_astr sid;
	if (!g_session_mgr.request_session(sid, info)) {
		_create_json_ret(buf, TPE_FAILED);
		return;
	}

	EXLOGD("[core] rpc new session-id: %s\n", sid.c_str());

	Json::Value jr_data;
	jr_data["sid"] = sid;

	_create_json_ret(buf, TPE_OK, jr_data);
}

void TsHttpRpc::_rpc_func_kill_sessions(const Json::Value& json_param, ex_astr& buf) {
	/*
	{
	"sessions": ["0123456", "ABCDEF", ...]
	}
	*/

	if (json_param.isArray()) {
		_create_json_ret(buf, TPE_PARAM);
		return;
	}

	if (json_param["sessions"].isNull() || !json_param["sessions"].isArray()) {
		_create_json_ret(buf, TPE_PARAM);
		return;
	}

	Json::Value s = json_param["sessions"];
	int cnt = s.size();
	for (int i = 0; i < cnt; ++i) {
		if (!s[i].isString()) {
			_create_json_ret(buf, TPE_PARAM);
			return;
		}
	}

	EXLOGV("[core] try to kill %d sessions.\n", cnt);
	ex_astr sp = s.toStyledString();
	g_tpp_mgr.kill_sessions(sp);

	_create_json_ret(buf, TPE_OK);
}

void TsHttpRpc::_rpc_func_enc(const Json::Value& json_param, ex_astr& buf)
{
	// https://github.com/tp4a/teleport/wiki/TELEPORT-CORE-JSON-RPC#enc
	// 加密一个字符串 [ p=plain-text, c=cipher-text ]
	// 入参: {"p":"need be encrypt"}
	// 示例: {"p":"this-is-a-password"}
	//   p: 被加密的字符串
	// 返回：
	//   data域中的"c"的内容是加密后密文的base64编码结果
	// 示例: {"code":0, "data":{"c":"Mxs340a9r3fs+3sdf=="}}
	//   错误返回： {"code":1234}

	if (json_param.isArray())
	{
		_create_json_ret(buf, TPE_PARAM);
		return;
	}

	ex_astr plain_text;

	if (json_param["p"].isNull() || !json_param["p"].isString())
	{
		_create_json_ret(buf, TPE_PARAM);
		return;
	}

	plain_text = json_param["p"].asCString();
	if (plain_text.length() == 0)
	{
		_create_json_ret(buf, TPE_PARAM);
		return;
	}
	ex_astr cipher_text;

	if (!ts_db_field_encrypt(plain_text, cipher_text))
	{
		_create_json_ret(buf, TPE_FAILED);
		return;
	}

	Json::Value jr_data;
	jr_data["c"] = cipher_text;
	_create_json_ret(buf, TPE_OK, jr_data);
}

void TsHttpRpc::_rpc_func_set_config(const Json::Value& json_param, ex_astr& buf)
{
	// https://github.com/tp4a/teleport/wiki/TELEPORT-CORE-JSON-RPC#set_config
	/*
	{
	  "noop-timeout": 15     # 按分钟计
	}
	*/

	if (json_param.isArray()) {
		_create_json_ret(buf, TPE_PARAM);
		return;
	}

	if (json_param["noop_timeout"].isNull() || !json_param["noop_timeout"].isUInt()) {
		_create_json_ret(buf, TPE_PARAM);
		return;
	}

	int noop_timeout = json_param["noop_timeout"].asUInt();
	EXLOGV("[core] set run-time config:\n");
	EXLOGV("[core]   noop_timeout = %dm\n", noop_timeout);

	ex_astr sp = json_param.toStyledString();
	g_tpp_mgr.set_runtime_config(sp);

	_create_json_ret(buf, TPE_OK);
}


/*
void TsHttpRpc::_rpc_func_enc(const Json::Value& json_param, ex_astr& buf)
{
	// https://github.com/tp4a/teleport/wiki/TELEPORT-CORE-JSON-RPC#enc
	// 加密多个个字符串 [ p=plain-text, c=cipher-text ]
	// 入参: {"p":["need be encrypt", "plain to cipher"]}
	// 示例: {"p":["password-for-A"]}
	//   p: 被加密的字符串
	// 返回：
	//   data域中的"c"的内容是加密后密文的base64编码结果
	// 示例: {"code":0, "data":{"c":["Mxs340a9r3fs+3sdf=="]}}
	//   错误返回： {"code":1234}

	if (json_param.isArray())
	{
		_create_json_ret(buf, TPE_PARAM);
		return;
	}

	ex_astr plain_text;

	if (json_param["p"].isNull() || !json_param["p"].isArray())
	{
		_create_json_ret(buf, TPE_PARAM);
		return;
	}

	Json::Value c;

	Json::Value p = json_param["p"];
	int cnt = p.size();
	for (int i = 0; i < cnt; ++i)
	{
		if (!p[i].isString()) {
			_create_json_ret(buf, TPE_PARAM);
			return;
		}

		ex_astr p_txt = p[i].asCString();
		if (p_txt.length() == 0) {
			c["c"].append("");
		}

		ex_astr c_txt;
		if (!ts_db_field_encrypt(p_txt, c_txt))
		{
			_create_json_ret(buf, TPE_FAILED);
			return;
		}

		c["c"].append(c_txt);
	}

	Json::Value jr_data;
	jr_data["c"] = c;
	_create_json_ret(buf, TPE_OK, jr_data);
}
*/
