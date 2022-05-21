#include <unistd.h>

#include <teleport_const.h>

#ifndef MAX_PATH
#	define MAX_PATH 1024
#endif

#include "../AppDelegate-C-Interface.h"

#include "ts_http_rpc.h"
#include "ts_ver.h"
#include "ts_env.h"
#include "ts_cfg.h"

TsHttpRpc g_http_interface;

TsHttpRpc::TsHttpRpc() : ExThreadBase("http-rpc-thread")
{
	mg_mgr_init(&m_mg_mgr, NULL);
}

TsHttpRpc::~TsHttpRpc()
{
	mg_mgr_free(&m_mg_mgr);
}

bool TsHttpRpc::init() {
    struct mg_connection* nc = NULL;

    for(int port = TS_HTTP_RPC_PORT_MIN; port < TS_HTTP_RPC_PORT_MAX; ++port) {
        char addr[128] = { 0 };
        ex_strformat(addr, 128, "tcp://127.0.0.1:%d", port);

        nc = mg_bind(&m_mg_mgr, addr, _mg_event_handler);
        if (!nc) {
            EXLOGW("[WRN] can not start HTTP-RPC listener, maybe port %d is already in use.\n", port);
            continue;
        }

        m_port = port;
        break;
    }
    
    if(m_port == 0) {
        EXLOGE("[rpc] can not listen on port %d~%d\n", TS_HTTP_RPC_PORT_MIN, TS_HTTP_RPC_PORT_MAX);
        return false;
    }

    nc->user_data = this;

    mg_set_protocol_http_websocket(nc);

    return _on_init();
}

bool TsHttpRpc::_on_init() {
    m_content_type_map[".js"] = "application/javascript";
    m_content_type_map[".png"] = "image/png";
    m_content_type_map[".jpeg"] = "image/jpeg";
    m_content_type_map[".jpg"] = "image/jpeg";
    m_content_type_map[".gif"] = "image/gif";
    m_content_type_map[".ico"] = "image/x-icon";
    m_content_type_map[".json"] = "image/json";
    m_content_type_map[".html"] = "text/html";
    m_content_type_map[".css"] = "text/css";
    m_content_type_map[".tif"] = "image/tiff";
    m_content_type_map[".tiff"] = "image/tiff";
    m_content_type_map[".svg"] = "text/html";

    return true;
}

void TsHttpRpc::_thread_loop(void)
{
	while (!m_need_stop)
	{
		mg_mgr_poll(&m_mg_mgr, 500);
	}

	EXLOGV("[core] rpc main loop end.\n");
}

void TsHttpRpc::_mg_event_handler(struct mg_connection *nc, int ev, void *ev_data)
{
	struct http_message *hm = (struct http_message*)ev_data;

	TsHttpRpc* _this = (TsHttpRpc*)nc->user_data;
	if (NULL == _this)
	{
		EXLOGE("[ERROR] invalid http request.\n");
		return;
	}

	switch (ev)
	{
	case MG_EV_HTTP_REQUEST:
	{
		ex_astr uri;
		ex_chars _uri;
		_uri.resize(hm->uri.len + 1);
		memset(&_uri[0], 0, hm->uri.len + 1);
		memcpy(&_uri[0], hm->uri.p, hm->uri.len);
		uri = &_uri[0];

#ifdef EX_DEBUG
		const char* dbg_method = NULL;
		if (hm->method.len == 3 && 0 == memcmp(hm->method.p, "GET", hm->method.len))
			dbg_method = "GET";
		else if (hm->method.len == 4 && 0 == memcmp(hm->method.p, "POST", hm->method.len))
			dbg_method = "POST";
		else
			dbg_method = "UNSUPPORTED-HTTP-METHOD";

		EXLOGV("[rpc] got %s request: %s\n", dbg_method, uri.c_str());
#endif
		ex_astr ret_buf;
        bool b_is_html = false;

        if (uri == "/") {
            uri = "/status.html";
            b_is_html = true;
        }
        else if (uri == "/config") {
            uri = "/index.html";
            b_is_html = true;
        }

		ex_astr temp;
		size_t offset = uri.find("/", 1);
		if (offset > 0)
		{
			temp = uri.substr(1, offset-1);

			if(temp == "api") {
				ex_astr method;
				ex_astr json_param;
				int rv = _this->_parse_request(hm, method, json_param);
				if (0 != rv)
				{
					EXLOGE("[ERROR] http-rpc got invalid request.\n");
					_this->_create_json_ret(ret_buf, rv);
				}
				else
				{
					_this->_process_js_request(method, json_param, ret_buf);
				}

				mg_printf(nc, "HTTP/1.0 200 OK\r\nAccess-Control-Allow-Origin: *\r\nContent-Length: %ld\r\nContent-Type: application/json\r\n\r\n%s", ret_buf.length(), ret_buf.c_str());
				nc->flags |= MG_F_SEND_AND_CLOSE;
				return;
			}
		}


		ex_astr file_suffix;
		offset = uri.rfind(".");
		if (offset > 0)
		{
			file_suffix = uri.substr(offset, uri.length());
		}

		ex_wstr2astr(g_env.m_site_path, temp);
		ex_astr index_path = temp + uri;


		FILE* file = ex_fopen(index_path.c_str(), "rb");
		if (file)
		{
			unsigned long file_size = 0;
			char* buf = 0;
			size_t ret = 0;

			fseek(file, 0, SEEK_END);
			file_size = ftell(file);
			buf = new char[file_size];
			memset(buf, 0, file_size);
			fseek(file, 0, SEEK_SET);
			ret = fread(buf, 1, file_size, file);
			fclose(file);

			ex_astr content_type = _this->get_content_type(file_suffix);

			mg_printf(nc, "HTTP/1.0 200 OK\r\nAccess-Control-Allow-Origin: *\r\nContent-Length: %ld\r\nContent-Type: %s\r\n\r\n", file_size, content_type.c_str());
			mg_send(nc, buf, (int)file_size);
			delete []buf;
			nc->flags |= MG_F_SEND_AND_CLOSE;
			return;
        } else if (b_is_html) {
			ex_wstr page = L"<html lang=\"zh_CN\"><html><head><title>404 Not Found</title></head><body bgcolor=\"white\"><center><h1>404 Not Found</h1></center><hr><center><p>Teleport Assistor configuration page not found.</p></center></body></html>";
			ex_wstr2astr(page, ret_buf, EX_CODEPAGE_UTF8);

			mg_printf(nc, "HTTP/1.0 404 File Not Found\r\nAccess-Control-Allow-Origin: *\r\nContent-Length: %ld\r\nContent-Type: text/html\r\n\r\n%s", ret_buf.length(), ret_buf.c_str());
			nc->flags |= MG_F_SEND_AND_CLOSE;
			return;
		}

	}
	break;
	default:
		break;
	}
}

int TsHttpRpc::_parse_request(struct http_message* req, ex_astr& func_cmd, ex_astr& func_args)
{
	if (NULL == req)
		return TPE_FAILED;

	bool is_get = true;
	if (req->method.len == 3 && 0 == memcmp(req->method.p, "GET", req->method.len))
		is_get = true;
	else if (req->method.len == 4 && 0 == memcmp(req->method.p, "POST", req->method.len))
		is_get = false;
	else
		return TPE_HTTP_METHOD;

	ex_astrs strs;

	size_t pos_start = 1;	// skip first charactor, it must be '/'

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
			pos_start = i + 1;	// skip current split chactor.
		}
	}
	if (pos_start < req->uri.len)
	{
		ex_astr tmp_uri;
		tmp_uri.assign(req->uri.p + pos_start, req->uri.len - pos_start);
		strs.push_back(tmp_uri);
	}

	if (0 == strs.size() || strs[0] != "api")
		return TPE_PARAM;

	if (is_get)
	{
		if (2 == strs.size())
		{
			func_cmd = strs[1];
		}
		else if (3 == strs.size())
		{
			func_cmd = strs[1];
			func_args = strs[2];
		}
		else
		{
			return TPE_PARAM;
		}
	}
	else
	{
		if (2 == strs.size())
		{
			func_cmd = strs[1];
		}
		else
		{
			return TPE_PARAM;
		}

		if (req->body.len > 0)
		{
			func_args.assign(req->body.p, req->body.len);
		}
	}

	if (func_args.length() > 0)
	{
		// decode param with url-decode.
		size_t len = func_args.length() * 2;
		ex_chars sztmp;
		sztmp.resize(len);
		memset(&sztmp[0], 0, len);
		if (-1 == ex_url_decode(func_args.c_str(), (int)func_args.length(), &sztmp[0], (int)len, 0))
			return TPE_HTTP_URL_ENCODE;

		func_args = &sztmp[0];
	}

	EXLOGV("[rpc] method=%s, json_param=%s\n", func_cmd.c_str(), func_args.c_str());

	return TPE_OK;
}

void TsHttpRpc::_process_js_request(const ex_astr& func_cmd, const ex_astr& func_args, ex_astr& buf)
{
	if (func_cmd == "get_version")
	{
		_rpc_func_get_version(func_args, buf);
	}
	else if (func_cmd == "get_config")
	{
		_rpc_func_get_config(func_args, buf);
	}
	else if (func_cmd == "set_config")
	{
		_rpc_func_set_config(func_args, buf);
	}
	else if (func_cmd == "file_action")
	{
		_rpc_func_file_action(func_args, buf);
	}
	else
	{
		EXLOGE("[rpc] got unknown command: %s\n", func_cmd.c_str());
		_create_json_ret(buf, TPE_UNKNOWN_CMD);
	}
}

void TsHttpRpc::_create_json_ret(ex_astr& buf, int errcode)
{
	// return {"code":123}

	Json::Value jr_root;
	jr_root["code"] = errcode;
    Json::StreamWriterBuilder jwb;
    std::unique_ptr<Json::StreamWriter> jwriter(jwb.newStreamWriter());
    ex_aoss os;
    jwriter->write(jr_root, &os);
    buf = os.str();
}

void TsHttpRpc::_create_json_ret(ex_astr& buf, Json::Value& jr_root)
{
    Json::StreamWriterBuilder jwb;
    std::unique_ptr<Json::StreamWriter> jwriter(jwb.newStreamWriter());
    ex_aoss os;
    jwriter->write(jr_root, &os);
    buf = os.str();
}

void TsHttpRpc::_rpc_func_get_config(const ex_astr& func_args, ex_astr& buf) {
	Json::Value jr_root;
	jr_root["code"] = 0;
	jr_root["data"] = g_cfg.get_root();
	_create_json_ret(buf, jr_root);
}

void TsHttpRpc::_rpc_func_set_config(const ex_astr& func_args, ex_astr& buf) {
    Json::CharReaderBuilder jcrb;
    std::unique_ptr<Json::CharReader> const jreader(jcrb.newCharReader());
    const char *str_json_begin = func_args.c_str();
    Json::Value jsRoot;
    ex_astr err;
    if (!jreader->parse(str_json_begin, str_json_begin + func_args.length(), &jsRoot, &err)) {
        _create_json_ret(buf, TPE_JSON_FORMAT);
        return;
    }

	if(!g_cfg.save(func_args))
		_create_json_ret(buf, TPE_FAILED);
	else
		_create_json_ret(buf, TPE_OK);
}

void TsHttpRpc::_rpc_func_file_action(const ex_astr& func_args, ex_astr& buf) {
    _create_json_ret(buf, TPE_FAILED);
#if 0
    Json::Reader jreader;
    Json::Value jsRoot;

    if (!jreader.parse(func_args.c_str(), jsRoot)) {
        _create_json_ret(buf, TPE_JSON_FORMAT);
        return;
    }

//    if (!jsRoot["action"].isNumeric()) {
//        _create_json_ret(buf, TPE_PARAM);
//        return;
//    }
//    int action = jsRoot["action"].asUInt();

    AppDelegate_select_app(g_app);
    _create_json_ret(buf, TPE_FAILED);

//    if (ret) {
//        if (action == 1 || action == 2 || action == 3) {
//            ex_astr utf8_path;
//            ex_wstr2astr(wszReturnPath, utf8_path, EX_CODEPAGE_UTF8);
//            Json::Value root;
//            root["code"] = TPE_OK;
//            root["path"] = utf8_path;
//            _create_json_ret(buf, root);
//
//            return;
//        } else {
//            _create_json_ret(buf, TPE_OK);
//            return;
//        }
//    } else {
//        _create_json_ret(buf, TPE_DATA);
//        return;
//    }
#endif
}

void TsHttpRpc::_rpc_func_get_version(const ex_astr& func_args, ex_astr& buf) {
	Json::Value root_ret;
	ex_wstr w_version = TP_ASSIST_VER;
	ex_astr version;
	ex_wstr2astr(w_version, version, EX_CODEPAGE_UTF8);
	root_ret["version"] = version;
	root_ret["code"] = TPE_OK;
	_create_json_ret(buf, root_ret);
	return;
}
