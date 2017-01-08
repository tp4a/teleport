#include "ts_http_rpc.h"
#include "ts_env.h"
#include "ts_session.h"
#include "ts_crypto.h"
#include "ts_db.h"

#include <sqlite3.h>


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
	EXLOGV("[core-rpc] TeleportServer-HTTP-RPC ready on %s:%d\n", m_host_ip.c_str(), m_host_port);

	for (;;)
	{
		if (m_stop_flag)
			break;
		mg_mgr_poll(&m_mg_mgr, 500);
	}

	EXLOGV("[core-rpc] main loop end.\n");
}

void TsHttpRpc::_set_stop_flag(void)
{
	m_stop_flag = true;
}


bool TsHttpRpc::init(void)
{
	struct mg_connection* nc = NULL;

	m_host_ip = g_env.rpc_bind_ip;
	m_host_port = g_env.rpc_bind_port;

	char addr[128] = { 0 };
	if (0 == strcmp(m_host_ip.c_str(), "127.0.0.1") || 0 == strcmp(m_host_ip.c_str(), "localhost"))
		ex_strformat(addr, 128, ":%d", m_host_port);
	else
		ex_strformat(addr, 128, "%s:%d", m_host_ip.c_str(), m_host_port);

	mg_mgr_init(&m_mg_mgr, NULL);
	nc = mg_bind(&m_mg_mgr, addr, _mg_event_handler);
	if (NULL == nc)
	{
		EXLOGE("[core-rpc] listener failed to bind at %s.\n", addr);
		return false;
	}

	nc->user_data = this;

	mg_set_protocol_http_websocket(nc);
	mg_enable_multithreading(nc);

	return true;
}

void TsHttpRpc::_mg_event_handler(struct mg_connection *nc, int ev, void *ev_data)
{
	struct http_message *hm = (struct http_message*)ev_data;

	TsHttpRpc* _this = (TsHttpRpc*)nc->user_data;
	if (NULL == _this)
	{
		EXLOGE("[core-rpc] invalid http request.\n");
		return;
	}

	switch (ev)
	{
	case MG_EV_HTTP_REQUEST:
	{
#ifdef EX_DEBUG
		const char* dbg_method = NULL;
		if (hm->method.len == 3 && 0 == memcmp(hm->method.p, "GET", hm->method.len))
			dbg_method = "GET";
		else if (hm->method.len == 4 && 0 == memcmp(hm->method.p, "POST", hm->method.len))
			dbg_method = "POST";
		else
			dbg_method = "UNSUPPORTED-HTTP-METHOD";

		ex_chars dbg_uri;
		dbg_uri.resize(hm->uri.len + 1);
		memset(&dbg_uri[0], 0, hm->uri.len + 1);
		memcpy(&dbg_uri[0], hm->uri.p, hm->uri.len);
		EXLOGV("[core-rpc] got %s request: %s\n", dbg_method, &dbg_uri[0]);
#endif
		ex_astr ret_buf;

		ex_astr method;
		ex_astr json_param;
		ex_rv rv = _this->_parse_request(hm, method, json_param);
		if (TSR_OK != rv)
		{
			EXLOGE("[core-rpc] got invalid request.\n");
			_this->_create_json_ret(ret_buf, rv);
		}
		else
		{
			_this->_process_js_request(method, json_param, ret_buf);
		}

		mg_printf(nc, "HTTP/1.0 200 OK\r\nAccess-Control-Allow-Origin: *\r\nContent-Length: %d\r\nContent-Type: application/json\r\n\r\n%s", (int)ret_buf.size() - 1, &ret_buf[0]);
		nc->flags |= MG_F_SEND_AND_CLOSE;
	}
		break;
	default:
		break;
	}
}

ex_rv TsHttpRpc::_parse_request(struct http_message* req, ex_astr& func_cmd, ex_astr& func_args)
{
	if (NULL == req)
		return TSR_INVALID_REQUEST;

	bool is_get = true;
	if (req->method.len == 3 && 0 == memcmp(req->method.p, "GET", req->method.len))
		is_get = true;
	else if (req->method.len == 4 && 0 == memcmp(req->method.p, "POST", req->method.len))
		is_get = false;
	else
		return TSR_INVALID_REQUEST;

	std::vector<ex_astr> strs;

	size_t pos_start = 1;	// 跳过第一个字节，一定是 '/'

	size_t i = 0;
	for (i = pos_start; i < req->uri.len; ++i)
	{
		if (req->uri.p[i] == '/')
		{
			if (i - pos_start > 0)
			{
				ex_astr tmp_uri;
				tmp_uri.assign(req->uri.p + pos_start, i - pos_start);
				strs.push_back(tmp_uri);
			}
			pos_start = i + 1;	// 跳过当前找到的分隔符
		}
	}
	if (pos_start < req->uri.len)
	{
		ex_astr tmp_uri;
		tmp_uri.assign(req->uri.p + pos_start, req->uri.len - pos_start);
		strs.push_back(tmp_uri);
	}

	if(0 == strs.size())
		return TSR_INVALID_REQUEST;

	if (is_get)
	{
		if (1 == strs.size())
		{
			func_cmd = strs[0];
		}
		else if (2 == strs.size())
		{
			func_cmd = strs[0];
			func_args = strs[1];
		}
		else
		{
			return TSR_INVALID_REQUEST;
		}
	}
	else
	{
		if (1 == strs.size())
		{
			func_cmd = strs[0];
		}
		else
		{
			return TSR_INVALID_REQUEST;
		}

		if (req->body.len > 0)
		{
			func_args.assign(req->body.p, req->body.len);
		}
	}

	if (func_args.length()>0)
	{
		// 将参数进行 url-decode 解码
		int len = func_args.length() * 2;
		ex_chars sztmp;
		sztmp.resize(len);
		memset(&sztmp[0], 0, len);
		if (-1 == ts_url_decode(func_args.c_str(), func_args.length(), &sztmp[0], len, 0))
			return TSR_INVALID_URL_ENCODE;

		func_args = &sztmp[0];
	}

	//EXLOGV("[rpc] method=%s, json_param=%s\n", func_cmd.c_str(), func_args.c_str());

	return TSR_OK;
}

void TsHttpRpc::_create_json_ret(ex_astr& buf, Json::Value& jr_root)
{
	Json::FastWriter jr_writer;
	buf = jr_writer.write(jr_root);
}

void TsHttpRpc::_create_json_ret(ex_astr& buf, int errcode)
{
	// 返回： {"code":123}

	Json::FastWriter jr_writer;
	Json::Value jr_root;

	jr_root["code"] = errcode;
	buf = jr_writer.write(jr_root);
}

void TsHttpRpc::_process_js_request(const ex_astr& func_cmd, const ex_astr& func_args, ex_astr& buf)
{
	if (func_cmd == "request_session")
	{
		_rpc_func_request_session(func_args, buf);
	}
	else if (func_cmd == "enc")
	{
		_rpc_func_enc(func_args, buf);
	}
// 	else if (func_cmd == "get_auth_id")
// 	{
// 		_rpc_func_get_auth_id(func_args, buf);
// 	}
// 	else if (func_cmd == "get_auth_info")
// 	{
// 		_rpc_func_get_auth_info(func_args, buf);
// 	}
	else if (func_cmd == "exit")
	{
		_rpc_func_exit(func_args, buf);
	}
	else
	{
		EXLOGE("[core-rpc] got unknown command: %s\n", func_cmd.c_str());
		_create_json_ret(buf, TSR_NO_SUCH_METHOD);
	}
}

extern bool g_exit_flag;	// 要求整个TS退出的标志（用于停止各个工作线程）
void TsHttpRpc::_rpc_func_exit(const ex_astr& func_args, ex_astr& buf)
{
	// 设置一个全局退出标志
	g_exit_flag = true;
	_create_json_ret(buf, TSR_OK);
	return;
}

void TsHttpRpc::_rpc_func_request_session(const ex_astr& func_args, ex_astr& buf)
{
	// 申请一个会话ID
	// 入参: 两种模式
	// MODE A: 已知目标服务器信息及认证信息
	// 示例: {"ip":"192.168.5.11","port":22,"uname":"root","uauth":"abcdefg","authmode":1,"protocol":2,"enc":0}
	//   ip: 目标服务器IP地址
	//   port: 目标服务器端口
	//   uname: 目标服务器认证所用的用户名
	//   uauth: 目标服务器认证所用的密码或私钥
	//   authmode: 1=password, 2=private-key
	//   protocol: 1=rdp, 2=ssh
	//   enc: 1=uauth中的内容是加密的，0=uauth中的内容是明文（仅用于开发测试阶段）
	// MODE B: 认证ID，需要根据这个ID到数据库中取得目标服务器信息及认证信息
	// 示例: {"authid":123456}
	// 返回：
	//   SSH返回： {"code":0, "data":{"sid":"0123abcde"}}
	//   RDP返回： {"code":0, "data":{"sid":"0123abcde0A"}}
	//   错误返回： {"code":1234}

	Json::Reader jreader;
	Json::Value jsRoot;

	if (!jreader.parse(func_args.c_str(), jsRoot))
	{
		_create_json_ret(buf, TSR_INVALID_JSON_FORMAT);
		return;
	}
	if (jsRoot.isArray())
	{
		_create_json_ret(buf, TSR_INVALID_JSON_PARAM);
		return;
	}

	ex_astr host_ip;
	int host_port = 0;
	int sys_type = 0;
	ex_astr user_name;
	ex_astr user_auth;
	ex_astr user_param;
	
	ex_astr account_name;
	int auth_mode = 0;
	int protocol = 0;
	int is_enc = 1;
	int auth_id = 0;
	// 入参模式
	if (!jsRoot["auth_id"].isNull())
	{
		// 使用认证ID的方式申请SID
		if (!jsRoot["auth_id"].isNumeric())
		{
			_create_json_ret(buf, TSR_INVALID_JSON_PARAM);
			return;
		}
		auth_id = jsRoot["auth_id"].asUInt();
		TS_DB_AUTH_INFO ts_auth_info;
		if (!g_db.get_auth_info(auth_id, ts_auth_info))
		{
			_create_json_ret(buf, TSR_GETAUTH_INFO_ERROR);
			return;
		}
		if (ts_auth_info.host_lock !=0 )
		{
			_create_json_ret(buf, TSR_HOST_LOCK_ERROR);
			return;
		}
		if (ts_auth_info.account_lock != 0)
		{
			_create_json_ret(buf, TSR_ACCOUNT_LOCK_ERROR);
			return;
		}
		host_ip = ts_auth_info.host_ip;
		host_port = ts_auth_info.host_port;
		sys_type = ts_auth_info.sys_type;
		user_name = ts_auth_info.user_name;
		user_auth = ts_auth_info.user_auth;
		user_param = ts_auth_info.user_param;
		auth_mode = ts_auth_info.auth_mode;
		protocol = ts_auth_info.protocol;
		is_enc = ts_auth_info.is_encrypt;
		account_name = ts_auth_info.account_name;
	}
	else
	{
		// 判断参数是否正确
		if (jsRoot["ip"].isNull() || !jsRoot["ip"].isString()
			|| jsRoot["port"].isNull() || !jsRoot["port"].isNumeric()
			|| jsRoot["systype"].isNull() || !jsRoot["systype"].isNumeric()
			|| jsRoot["account"].isNull() || !jsRoot["account"].isString()
			|| jsRoot["uname"].isNull() || !jsRoot["uname"].isString()
			|| jsRoot["uauth"].isNull() || !jsRoot["uauth"].isString()
			|| jsRoot["authmode"].isNull() || !jsRoot["authmode"].isNumeric()
			|| jsRoot["protocol"].isNull() || !jsRoot["protocol"].isNumeric()
			|| jsRoot["enc"].isNull() || !jsRoot["enc"].isNumeric()
			)
		{
			_create_json_ret(buf, TSR_INVALID_JSON_PARAM);
			return;
		}

		host_ip = jsRoot["ip"].asCString();
		host_port = jsRoot["port"].asUInt();
		sys_type = jsRoot["systype"].asUInt();
		account_name = jsRoot["account"].asCString();
		user_name = jsRoot["uname"].asCString();
		user_auth = jsRoot["uauth"].asCString();
		if (jsRoot["uparam"].isNull())
		{
			user_param = "";
		}
		else 
		{
			user_param = jsRoot["uparam"].asCString();
		}
		
		auth_mode = jsRoot["authmode"].asUInt();
		protocol = jsRoot["protocol"].asUInt();
		is_enc = jsRoot["enc"].asUInt();
	}

	// 进一步判断参数是否合法
	if (host_ip.length() == 0 || host_port >= 65535 || account_name.length() == 0 
		|| !(auth_mode == TS_AUTH_MODE_NONE || auth_mode == TS_AUTH_MODE_PASSWORD || auth_mode == TS_AUTH_MODE_PRIVATE_KEY)
		|| !(protocol == TS_PROXY_PROTOCOL_RDP || protocol == TS_PROXY_PROTOCOL_SSH || protocol == TS_PROXY_PROTOCOL_TELNET)
		|| !(is_enc == 0 || is_enc == 1)
		)
	{
		_create_json_ret(buf, TSR_INVALID_JSON_PARAM);
		return;
	}

	if(is_enc)
	{
		if (user_auth.length() > 0)
		{
			ex_astr _auth;
			if (!ts_db_field_decrypt(user_auth, _auth))
			{
				_create_json_ret(buf, TSR_FAILED);
				return;
			}

			user_auth = _auth;
		}
	}

	// 生成一个session-id（内部会避免重复）
	ex_astr sid;
	ex_rv rv = g_session_mgr.request_session(sid, account_name, auth_id, 
		host_ip, host_port, sys_type, protocol, 
		user_name, user_auth, user_param, auth_mode);
	if (rv != TSR_OK)
	{
		_create_json_ret(buf, rv);
		return;
	}

	EXLOGD("[core-rpc] new session-id: %s\n", sid.c_str());

	Json::Value jr_root;
	jr_root["code"] = TSR_OK;
	jr_root["data"]["sid"] = sid;

	_create_json_ret(buf, jr_root);
}

void TsHttpRpc::_rpc_func_enc(const ex_astr& func_args, ex_astr& buf)
{
	// 加密一个字符串 [ p=plain-text, c=cipher-text ]
	// 入参: {"p":"need be encrypt"}
	// 示例: {"p":"this-is-a-password"}
	//   p: 被加密的字符串
	// 返回：
	//   data域中的"c"的内容是加密后密文的base64编码结果
	// 示例: {"code":0, "data":{"c":"Mxs340a9r3fs+3sdf=="}}
	//   错误返回： {"code":1234}

	Json::Reader jreader;
	Json::Value jsRoot;

	if (!jreader.parse(func_args.c_str(), jsRoot))
	{
		_create_json_ret(buf, TSR_INVALID_JSON_FORMAT);
		return;
	}
	if (jsRoot.isArray())
	{
		_create_json_ret(buf, TSR_INVALID_JSON_PARAM);
		return;
	}

	ex_astr plain_text;

	if (jsRoot["p"].isNull() || !jsRoot["p"].isString())
	{
		_create_json_ret(buf, TSR_INVALID_JSON_PARAM);
		return;
	}

	plain_text = jsRoot["p"].asCString();
	if (plain_text.length() == 0)
	{
		_create_json_ret(buf, TSR_DATA_LEN_ZERO);
		return;
	}
	ex_astr cipher_text;

	if (!ts_db_field_encrypt(plain_text, cipher_text))
	{
		_create_json_ret(buf, TSR_FAILED);
		return;
	}

	Json::Value jr_root;
	jr_root["code"] = TSR_OK;
	jr_root["data"]["c"] = cipher_text;

	_create_json_ret(buf, jr_root);
}

#if 0
void TsHttpRpc::_rpc_func_get_auth_id(const ex_astr& func_args, ex_astr& buf)
{
	// 获取所有的或者指定主机的认证ID
	// 入参: {"host":"host-ip-address"} 或者 无
	// 示例: {"host":"123.45.67.89"}
	//   host: 要查询的主机的IP地址
	// 返回：
	//   data域为一个列表，其中每一个元素为一组键值对。
	//      
	//   错误返回： {"code":1234}

	Json::Reader jreader;
	Json::Value jsRoot;

	AuthInfo2Vec ret;

	if (0 == func_args.length())
	{
		if (!g_db.get_auth_id_list_by_all(ret))
		{
			_create_json_ret(buf, TSR_DATA_LEN_ZERO);
			return;
		}
	}
	else
	{
		if (!jreader.parse(func_args.c_str(), jsRoot))
		{
			_create_json_ret(buf, TSR_INVALID_JSON_FORMAT);
			return;
		}
		if (jsRoot.isArray())
		{
			_create_json_ret(buf, TSR_INVALID_JSON_PARAM);
			return;
		}

		ex_astr host_ip;

		if (jsRoot["host"].isNull() || !jsRoot["host"].isString())
		{
			_create_json_ret(buf, TSR_INVALID_JSON_PARAM);
			return;
		}

		host_ip = jsRoot["host"].asCString();
		if (host_ip.length() == 0)
		{
			_create_json_ret(buf, TSR_INVALID_JSON_PARAM);
			return;
		}

		if (!g_db.get_auth_id_list_by_ip(host_ip, ret))
		{
			_create_json_ret(buf, TSR_DATA_LEN_ZERO);
			return;
		}
	}

	if (ret.size() == 0)
	{
		_create_json_ret(buf, TSR_DATA_LEN_ZERO);
		return;
	}

	//EXLOGV("encrypt: [%s]=>[%s]\n", plain_text.c_str(), cipher_text.c_str());

	Json::Value jr_root;
	jr_root["code"] = TSR_OK;

	int i = 0;
	AuthInfo2Vec::iterator it = ret.begin();
	for (; it != ret.end(); ++it)
	{
		jr_root["data"][i]["auth_id"] = (*it).auth_id;
		jr_root["data"][i]["host_id"] = (*it).host_id;
		jr_root["data"][i]["host_ip"] = (*it).host_ip;
		jr_root["data"][i]["protocol"] = (*it).pro_type;
		jr_root["data"][i]["auth_mode"] = (*it).auth_mode;
		jr_root["data"][i]["host_status"] = (*it).host_lock;

		i++;
	}

	_create_json_ret(buf, jr_root);
}

void TsHttpRpc::_rpc_func_get_auth_info(const ex_astr& func_args, ex_astr& buf)
{
	// 获取所有的或者指定主机的认证INFO
	// 入参: {"host":"host-ip-address"} 或者 无
	// 示例: {"host":"123.45.67.89"}
	//   host: 要查询的主机的IP地址
	// 返回：
	//   data域为一个列表，其中每一个元素为一组键值对。
	//      
	//   错误返回： {"code":1234}

	Json::Reader jreader;
	Json::Value jsRoot;

	AuthInfo3Vec ret;

	if (0 == func_args.length())
	{
		if (!g_db.get_auth_info_list_by_all(ret))
		{
			_create_json_ret(buf, TSR_DATA_LEN_ZERO);
			return;
		}
	}
	else
	{
		if (!jreader.parse(func_args.c_str(), jsRoot))
		{
			_create_json_ret(buf, TSR_INVALID_JSON_FORMAT);
			return;
		}
		if (jsRoot.isArray())
		{
			_create_json_ret(buf, TSR_INVALID_JSON_PARAM);
			return;
		}

		ex_astr host_ip;

		if (jsRoot["host"].isNull() || !jsRoot["host"].isString())
		{
			_create_json_ret(buf, TSR_INVALID_JSON_PARAM);
			return;
		}

		host_ip = jsRoot["host"].asCString();
		if (host_ip.length() == 0)
		{
			_create_json_ret(buf, TSR_INVALID_JSON_PARAM);
			return;
		}

		if (!g_db.get_auth_info_list_by_ip(host_ip, ret))
		{
			_create_json_ret(buf, TSR_DATA_LEN_ZERO);
			return;
		}
	}

	if (ret.size() == 0)
	{
		_create_json_ret(buf, TSR_DATA_LEN_ZERO);
		return;
	}

	//EXLOGV("encrypt: [%s]=>[%s]\n", plain_text.c_str(), cipher_text.c_str());

	Json::Value jr_root;
	jr_root["code"] = TSR_OK;

	int i = 0;
	AuthInfo3Vec::iterator it = ret.begin();
	for (; it != ret.end(); ++it)
	{
		jr_root["data"][i]["host_id"] = (*it).host_id;
		jr_root["data"][i]["host_ip"] = (*it).host_ip;
		jr_root["data"][i]["username"] = (*it).host_user_name;
		jr_root["data"][i]["password"] = (*it).host_user_pwd;
		jr_root["data"][i]["auth_mode"] = (*it).auth_mode;
		jr_root["data"][i]["key_id"] = (*it).cert_id;
		jr_root["data"][i]["key_pri"] = (*it).cert_pri;
		jr_root["data"][i]["key_pub"] = (*it).cert_pub;

		i++;
	}

	_create_json_ret(buf, jr_root);
}
#endif
