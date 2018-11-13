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

// #define RDP_CLIENT_SYSTEM_BUILTIN
// #define RDP_CLIENT_SYSTEM_ACTIVE_CONTROL
#define RDP_CLIENT_FREERDP

TsHttpRpc g_http_interface;
TsHttpRpc g_https_interface;

void* g_app = NULL;

int http_rpc_start(void* app) {
	g_app = app;

    EXLOGW("======================================================\n");

    if (!g_http_interface.init_http())
	{
		EXLOGE("[ERROR] can not start HTTP-RPC listener, maybe port %d is already in use.\n", TS_HTTP_RPC_PORT);
		return -1;
	}
	
	EXLOGW("[rpc] TeleportAssist-HTTP-RPC ready on localhost:%d\n", TS_HTTP_RPC_PORT);
	
	if(!g_http_interface.start())
		return -2;

    if (!g_https_interface.init_https())
    {
        EXLOGE("[ERROR] can not start HTTPS-RPC listener, maybe port %d is already in use.\n", TS_HTTPS_RPC_PORT);
        return -1;
    }
    
    EXLOGW("[rpc] TeleportAssist-HTTPS-RPC ready on localhost:%d\n", TS_HTTPS_RPC_PORT);
    
    if(!g_https_interface.start())
        return -2;

    return 0;
}

void http_rpc_stop(void)
{
    g_http_interface.stop();
    g_https_interface.stop();
}

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

bool TsHttpRpc::init_http()
{
    
    char addr[128] = { 0 };
    ex_strformat(addr, 128, "tcp://localhost:%d", TS_HTTP_RPC_PORT);
    
    struct mg_connection* nc = NULL;
    nc = mg_bind(&m_mg_mgr, addr, _mg_event_handler);
    if (nc == NULL) {
        EXLOGE("[rpc] TsHttpRpc::init_http() localhost:%d\n", TS_HTTP_RPC_PORT);
        return false;
    }
    nc->user_data = this;
    
    mg_set_protocol_http_websocket(nc);
    
    return _on_init();
}

bool TsHttpRpc::init_https()
{
    ex_wstr file_ssl_cert = g_env.m_res_path;
    ex_path_join(file_ssl_cert, false, L"localhost.pem", NULL);
    ex_wstr file_ssl_key = g_env.m_res_path;
    ex_path_join(file_ssl_key, false, L"localhost.key", NULL);
    ex_astr _ssl_cert;
    ex_wstr2astr(file_ssl_cert, _ssl_cert);
    ex_astr _ssl_key;
    ex_wstr2astr(file_ssl_key, _ssl_key);
    
    const char *err = NULL;
    struct mg_bind_opts bind_opts;
    memset(&bind_opts, 0, sizeof(bind_opts));
    bind_opts.ssl_cert = _ssl_cert.c_str();
    bind_opts.ssl_key = _ssl_key.c_str();
    bind_opts.error_string = &err;
    
    char addr[128] = { 0 };
    ex_strformat(addr, 128, "tcp://localhost:%d", TS_HTTPS_RPC_PORT);

    struct mg_connection* nc = NULL;
    nc = mg_bind_opt(&m_mg_mgr, addr, _mg_event_handler, bind_opts);
    if (nc == NULL) {
        EXLOGE("[rpc] TsHttpRpc::init_https() localhost:%d\n", TS_HTTPS_RPC_PORT);
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

//void TsHttpRpc::_set_stop_flag(void)
//{
//    m_stop_flag = true;
//}

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
		bool b_is_index = false;

		if (uri == "/")
		{
			ex_wstr page = L"<html lang=\"zh_CN\"><head><meta charset=\"utf-8\"/><meta http-equiv=\"Content-Type\" content=\"text/html; charset=utf-8\"/><title>Teleport Assistor</title>\n<style type=\"text/css\">\n.box{padding:20px;margin:40px;border:1px solid #78b17c;background-color:#e4ffe5;}\n</style>\n</head><body><div class=\"box\">Teleport Assistor works fine.</div></body></html>";
			ex_wstr2astr(page, ret_buf, EX_CODEPAGE_UTF8);

			mg_printf(nc, "HTTP/1.0 200 OK\r\nAccess-Control-Allow-Origin: *\r\nContent-Length: %ld\r\nContent-Type: text/html\r\n\r\n%s", ret_buf.size() - 1, &ret_buf[0]);
			nc->flags |= MG_F_SEND_AND_CLOSE;
			return;
		}

		if (uri == "/config")
		{
			uri = "/index.html";
			b_is_index = true;
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
				
				mg_printf(nc, "HTTP/1.0 200 OK\r\nAccess-Control-Allow-Origin: *\r\nContent-Length: %ld\r\nContent-Type: application/json\r\n\r\n%s", ret_buf.size() - 1, &ret_buf[0]);
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
		}
		else if (b_is_index)
		{
			ex_wstr page = L"<html lang=\"zh_CN\"><html><head><title>404 Not Found</title></head><body bgcolor=\"white\"><center><h1>404 Not Found</h1></center><hr><center><p>Teleport Assistor configuration page not found.</p></center></body></html>";
			ex_wstr2astr(page, ret_buf, EX_CODEPAGE_UTF8);
			
			mg_printf(nc, "HTTP/1.0 404 File Not Found\r\nAccess-Control-Allow-Origin: *\r\nContent-Length: %ld\r\nContent-Type: text/html\r\n\r\n%s", ret_buf.size() - 1, &ret_buf[0]);
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
		// 将参数进行 url-decode 解码
		size_t len = func_args.length() * 2;
		ex_chars sztmp;
		sztmp.resize(len);
		memset(&sztmp[0], 0, len);
		if (-1 == ts_url_decode(func_args.c_str(), (int)func_args.length(), &sztmp[0], (int)len, 0))
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
	else if (func_cmd == "run")
	{
		_rpc_func_run_client(func_args, buf);
	}
	else if (func_cmd == "rdp_play")
	{
		_rpc_func_rdp_play(func_args, buf);
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
	// 返回： {"code":123}

	Json::FastWriter jr_writer;
	Json::Value jr_root;

	jr_root["code"] = errcode;
	buf = jr_writer.write(jr_root);
}

void TsHttpRpc::_create_json_ret(ex_astr& buf, Json::Value& jr_root)
{
	Json::FastWriter jr_writer;
	buf = jr_writer.write(jr_root);
}

void TsHttpRpc::_rpc_func_run_client(const ex_astr& func_args, ex_astr& buf)
{
	// 入参：{"ip":"192.168.5.11","port":22,"uname":"root","uauth":"abcdefg","authmode":1,"protocol":2}
	//   authmode: 1=password, 2=private-key
	//   protocol: 1=rdp, 2=ssh
	// SSH返回： {"code":0, "data":{"sid":"0123abcde"}}
	// RDP返回： {"code":0, "data":{"sid":"0123abcde0A"}}

	Json::Reader jreader;
	Json::Value jsRoot;

	if (!jreader.parse(func_args.c_str(), jsRoot))
	{
		_create_json_ret(buf, TPE_JSON_FORMAT);
		return;
	}
	if (!jsRoot.isObject())
	{
		_create_json_ret(buf, TPE_PARAM);
		return;
	}

	// 判断参数是否正确
	if (!jsRoot["teleport_ip"].isString()
		|| !jsRoot["teleport_port"].isNumeric() || !jsRoot["remote_host_ip"].isString()
		|| !jsRoot["session_id"].isString() || !jsRoot["protocol_type"].isNumeric() || !jsRoot["protocol_sub_type"].isNumeric()
		|| !jsRoot["protocol_flag"].isNumeric()
		)
	{
		_create_json_ret(buf, TPE_PARAM);
		return;
	}

	int pro_type = jsRoot["protocol_type"].asUInt();
	int pro_sub = jsRoot["protocol_sub_type"].asInt();
	ex_u32 protocol_flag = jsRoot["protocol_flag"].asUInt();

	ex_astr teleport_ip = jsRoot["teleport_ip"].asCString();
	int teleport_port = jsRoot["teleport_port"].asUInt();
    char _port[64] = {0};
    ex_strformat(_port, 64, "%d", teleport_port);
    ex_astr str_teleport_port = _port;

	ex_astr real_host_ip = jsRoot["remote_host_ip"].asCString();
	ex_astr sid = jsRoot["session_id"].asCString();

	ex_astr s_exec;
    ex_astr s_arg;
	ex_astrs s_argv;
	
	
	if (pro_type == TP_PROTOCOL_TYPE_RDP)
	{
		//==============================================
		// RDP
		//==============================================

		if(g_cfg.rdp.application.length() == 0) {
			_create_json_ret(buf, TPE_NOT_EXISTS);
			return;
		}
		
		bool flag_clipboard = (protocol_flag & TP_FLAG_RDP_CLIPBOARD);
		bool flag_disk = (protocol_flag & TP_FLAG_RDP_DISK);
		bool flag_console = (protocol_flag & TP_FLAG_RDP_CONSOLE);

		int rdp_w = 800;
		int rdp_h = 640;
		bool rdp_console = false;

		if (!jsRoot["rdp_width"].isNull()) {
			if (jsRoot["rdp_width"].isNumeric()) {
				rdp_w = jsRoot["rdp_width"].asUInt();
			}
			else {
				_create_json_ret(buf, TPE_PARAM);
				return;
			}
		}

		if (!jsRoot["rdp_height"].isNull()) {
			if (jsRoot["rdp_height"].isNumeric()) {
				rdp_h = jsRoot["rdp_height"].asUInt();
			}
			else {
				_create_json_ret(buf, TPE_PARAM);
				return;
			}
		}

		if (!jsRoot["rdp_console"].isNull()) {
			if (jsRoot["rdp_console"].isBool()) {
				rdp_console = jsRoot["rdp_console"].asBool();
			}
			else {
				_create_json_ret(buf, TPE_PARAM);
				return;
			}
		}

		if (!flag_console)
			rdp_console = false;


		size_t split_pos = sid.length() - 2;
		ex_astr real_sid = sid.substr(0, split_pos);
		ex_astr str_pwd_len = sid.substr(split_pos, sid.length());
		size_t n_pwd_len = strtol(str_pwd_len.c_str(), NULL, 16);
		n_pwd_len -= real_sid.length();
		n_pwd_len -= 2;
		char szPwd[256] = { 0 };
		for (int i = 0; i < n_pwd_len; i++)
		{
			szPwd[i] = '*';
		}
		
		//ex_astr2wstr(real_sid, w_sid);
		
		//w_exe_path = _T("\"");
		//w_exe_path += g_cfg.rdp_app + _T("\" ");
		//w_exe_path += g_cfg.rdp_cmdline;
		//w_exe_path = _T("xfreerdp -u {user_name} {size} {console} {clipboard} {drives} ");
		//w_exe_path = _T("/usr/local/Cellar/freerdp/1.0.2_1/bin/xfreerdp -u {user_name} {size} {console} ");
		//w_exe_path = _T("xfreerdp -u {user_name} {size} {console} ");
		//s_exec = "/usr/local/Cellar/freerdp/1.0.2_1/bin/xfreerdp";
		s_exec = g_cfg.rdp.application;
		s_argv.push_back(s_exec.c_str());

		{
			ex_astr username = "02" + real_sid;
			
			s_argv.push_back("-u");
			s_argv.push_back(username.c_str());
			
			if (rdp_w == 0 || rdp_h == 0) {
				s_argv.push_back("-f");
			}
			else {
				char sz_size[64] = {0};
				ex_strformat(sz_size, 63, "%dx%d", rdp_w, rdp_h);
				s_argv.push_back("-g");
				s_argv.push_back(sz_size);
			}
			
			if (flag_console && rdp_console)
				s_argv.push_back("/admin");

//			if(flag_clipboard)
//				s_argv.push_back("+clipboard");
//			else
//				s_argv.push_back("-clipboard");

//			if(flag_disk)
//				s_argv.push_back("+drives");
//			else
//				s_argv.push_back("-drives");
			
			{
				char sz_temp[128] = {0};
				ex_strformat(sz_temp, 127, "%s:%d", teleport_ip.c_str(), teleport_port);
				s_argv.push_back(sz_temp);
			}
		}

	}
	else if (pro_type == TP_PROTOCOL_TYPE_SSH)
	{
		//==============================================
		// SSH
		//==============================================

		if (pro_sub == TP_PROTOCOL_TYPE_SSH_SHELL)
		{
            if(g_cfg.ssh.name == "terminal" || g_cfg.ssh.name == "iterm2") {
                char szCmd[1024] = {0};
                ex_strformat(szCmd, 1023, "ssh %s@%s -p %d", sid.c_str(), teleport_ip.c_str(), teleport_port);
                
                char szTitle[128] = {0};
                ex_strformat(szTitle, 127, "TP#%s", real_host_ip.c_str());
                
                int ret = AppDelegate_start_ssh_client(g_app, szCmd, g_cfg.ssh.name.c_str(), g_cfg.ssh.cmdline.c_str(), szTitle);
                if(ret == 0)
                    _create_json_ret(buf, TPE_OK);
                else
                    _create_json_ret(buf, TPE_FAILED);
                return;
            }
            
            if(g_cfg.ssh.application.length() == 0) {
                _create_json_ret(buf, TPE_NOT_EXISTS);
                return;
            }
            
            s_exec = g_cfg.ssh.application;
            s_argv.push_back(s_exec.c_str());
            
            s_arg = g_cfg.ssh.cmdline;
		}
		else
		{
            
			// sorry, SFTP not supported yet for macOS.
//            _create_json_ret(buf, TPE_NOT_IMPLEMENT);
//            return;

            if(g_cfg.sftp.application.length() == 0) {
                _create_json_ret(buf, TPE_NOT_EXISTS);
                return;
            }
            
            s_exec = g_cfg.sftp.application;
            s_argv.push_back(s_exec.c_str());
            
            s_arg = g_cfg.sftp.cmdline;

        }
	}
	else if (pro_type == TP_PROTOCOL_TYPE_TELNET)
	{
		//==============================================
		// TELNET
		//==============================================

		// sorry, TELNET not supported yet for macOS.
        _create_json_ret(buf, TPE_NOT_IMPLEMENT);
        return;

//        if(g_cfg.telnet.name == "terminal" || g_cfg.telnet.name == "iterm2") {
//            char szCmd[1024] = {0};
//            ex_strformat(szCmd, 1023, "telnet -l %s %s %d", sid.c_str(), teleport_ip.c_str(), teleport_port);
//
//            char szTitle[128] = {0};
//            ex_strformat(szTitle, 127, "TP#%s", real_host_ip.c_str());
//
//            int ret = AppDelegate_start_ssh_client(g_app, szCmd, g_cfg.telnet.name.c_str(), g_cfg.telnet.cmdline.c_str(), szTitle);
//            if(ret == 0)
//                _create_json_ret(buf, TPE_OK);
//            else
//                _create_json_ret(buf, TPE_FAILED);
//            return;
//        }
//
//        if(g_cfg.telnet.application.length() == 0) {
//            _create_json_ret(buf, TPE_NOT_EXISTS);
//            return;
//        }
//
//        s_exec = g_cfg.telnet.application;
//        s_argv.push_back(s_exec.c_str());
//
//        s_arg = g_cfg.telnet.cmdline;
    }

    
    //---- split s_arg and push to s_argv ---
    ex_astr::size_type p1 = 0;
    ex_astr::size_type p2 = 0;
    ex_astr tmp = s_arg;
    for(;;) {
        ex_remove_white_space(tmp, EX_RSC_BEGIN);
        if(tmp.empty()) {
            break;
        }

        if(tmp[0] == '"') {
            p1 = 1;
            p2 = tmp.find('"', p1);

            if(p2 == ex_astr::npos) {
                _create_json_ret(buf, TPE_PARAM);
                return;
            }

            ex_astr _t;
            _t.assign(tmp, p1, p2 - p1);
            tmp.erase(0, p2 + 2);
            
            s_argv.push_back(_t);
        } else {
            p1 = 0;
            p2 = tmp.find(' ', p1);

            if(p2 == ex_astr::npos) {
                s_argv.push_back(tmp);
                tmp.clear();
                break;
            }

            ex_astr _t;
            _t.assign(tmp, p1, p2 - p1);
            tmp.erase(0, p2 + 1);
            
            s_argv.push_back(_t);
        }
    }
    
    
	Json::Value root_ret;
	ex_astr utf8_path = s_exec;

	ex_astrs::iterator it = s_argv.begin();
	for(; it != s_argv.end(); ++it) {
        ex_replace_all((*it), "{host_port}", str_teleport_port);
        ex_replace_all((*it), "{host_ip}", teleport_ip);
        ex_replace_all((*it), "{user_name}", sid);
        ex_replace_all((*it), "{real_ip}", real_host_ip);
        //ex_replace_all(utf8_path, _T("{assist_tools_path}"), g_env.m_tools_path.c_str());

        utf8_path += " ";
        utf8_path += (*it);
    }
    
	root_ret["path"] = utf8_path;

	// for macOS, Create Process should be fork()/exec()...
	pid_t processId;
	if ((processId = fork()) == 0) {
		
		int i = 0;
		char** _argv = (char**)calloc(s_argv.size()+1, sizeof(char*));
		if (!_argv)
			return;
		
		for (i = 0; i < s_argv.size(); ++i)
		{
			_argv[i] = ex_strdup(s_argv[i].c_str());
		}
		_argv[i] = NULL;

        execv(s_exec.c_str(), _argv);

		for(i = 0; i < s_argv.size(); ++i) {
			if(_argv[i] != NULL) {
				free(_argv[i]);
			}
		}
		free(_argv);
		
	} else if (processId < 0) {
		root_ret["code"] = TPE_FAILED;
	} else {
		root_ret["code"] = TPE_OK;
	}
	

//	root_ret["code"] = TPE_OK;
	_create_json_ret(buf, root_ret);
}



void TsHttpRpc::_rpc_func_rdp_play(const ex_astr& func_args, ex_astr& buf)
{
	_create_json_ret(buf, TPE_NOT_IMPLEMENT);
}

void TsHttpRpc::_rpc_func_get_config(const ex_astr& func_args, ex_astr& buf)
{
	Json::Value jr_root;
	jr_root["code"] = 0;
	jr_root["data"] = g_cfg.get_root();
	_create_json_ret(buf, jr_root);
}

void TsHttpRpc::_rpc_func_set_config(const ex_astr& func_args, ex_astr& buf)
{
	Json::Reader jreader;
	Json::Value jsRoot;
	if (!jreader.parse(func_args.c_str(), jsRoot))
	{
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

void TsHttpRpc::_rpc_func_get_version(const ex_astr& func_args, ex_astr& buf)
{
	Json::Value root_ret;
	ex_wstr w_version = TP_ASSIST_VER;
	ex_astr version;
	ex_wstr2astr(w_version, version, EX_CODEPAGE_UTF8);
	root_ret["version"] = version;
	root_ret["code"] = TPE_OK;
	_create_json_ret(buf, root_ret);
	return;
}
