#include "stdafx.h"

#pragma warning(disable:4091)

#include <commdlg.h>
#include <ShlObj.h>
#include "ts_http_rpc.h"
#include "dlg_main.h"
#include "ts_ver.h"

/*
1.
SecureCRT支持设置标签页的标题，命令行参数 /N "tab name"就可以
Example:
To launch a new Telnet session, displaying the name "Houston, TX" on the tab, use the following:
/T /N "Houston, TX" /TELNET 192.168.0.6

2.
多次启动的SecureCRT放到一个窗口的不同标签页中，使用参数：  /T
  SecureCRT.exe /T /N "TP#ssh://192.168.1.3" /SSH2 /L root /PASSWORD 1234 120.26.109.25

3.
telnet客户端的启动：
  putty.exe telnet://administrator@127.0.0.1:52389
如果是SecureCRT，则需要
  SecureCRT.exe /T /N "TP#telnet://192.168.1.3" /SCRIPT X:\path\to\startup.vbs /TELNET 127.0.0.1 52389
其中，startup.vbs的内容为：
---------文件开始---------
#$language = "VBScript"
#$interface = "1.0"
Sub main
  crt.Screen.Synchronous = True
  crt.Screen.WaitForString "ogin: "
  crt.Screen.Send "SESSION-ID" & VbCr
  crt.Screen.Synchronous = False
End Sub
---------文件结束---------

4. 为了让putty的窗口标签显示正常的IP，可以尝试在连接成功后，主动向服务端发送下列命令：
	PS1="\[\e]0;${debian_chroot:+($debian_chroot)}\u@192.168.1.2: \w\a\]$PS1"
手工测试了，ubuntu服务器可以，不知道是否能够支持所有的Linux。SecureCRT对此表示忽略。
*/


#if 0
std::string rdp_content = "\
connect to console:i:%d\n\
screen mode id:i:%d\n\
desktopwidth:i:%d\n\
desktopheight:i:%d\n\
winposstr:s:0,1,%d,%d,%d,%d\n\
full address:s:%s:%d\n\
username:s:%s\n\
prompt for credentials:i:0\n\
use multimon:i:0\n\
authentication level:i:3\n\
session bpp:i:16\n\
compression:i:1\n\
keyboardhook:i:2\n\
audiocapturemode:i:0\n\
negotiate security layer:i:1\n\
videoplaybackmode:i:1\n\
connection type:i:2\n\
prompt for credentials on client:i:1\r\n\
displayconnectionbar:i:1\n\
disable wallpaper:i:1\n\
allow font smoothing:i:0\n\
allow desktop composition:i:0\n\
disable full window drag:i:1\n\
disable menu anims:i:1\n\
disable themes:i:0\n\
disable cursor setting:i:0\n\
bitmapcachepersistenable:i:1\n\
audiomode:i:0\n\
redirectprinters:i:1\n\
redirectcomports:i:0\n\
redirectsmartcards:i:1\n\
redirectclipboard:i:1\n\
redirectposdevices:i:0\n\
redirectdirectx:i:1\n\
autoreconnection enabled:i:1\n\
autoreconnection enabled:i:1\n\
drivestoredirect:s:*\n\
password 51:b:01000000D08C9DDF0115D1118C7A00C04FC297EB0100000052A9E191EA75A948B359790578C9371A0000000008000000700073007700000003660000A8000000100000000A1DCCD2E50775CA25EC3857164B34DC0000000004800000A000000010000000FCE1A645B9B61AA450946BB6F955058108020000D83591CA47562D6DDAA689F050AE145039EBE22E00D1D3AEAA98373C7B63C3E8E7149072DF989EA43EFCE20513AD3D27B11BE7F17066A688E1DCE828AF85460AAC327B38E90776DB962888E4393D19637578984B19A187AAD95F6D2726ADE7DD315FF56C15FF5B3031014EDDCC3C24D1B81779AFDB006EE575F5BEFB8D2D2138D9D9D642BBB251CC5ED7226968764856EC660A646BACE748A13D6002A9A537AA70710615650B9387EED66DE28BD57B304BBDD7B581B943DA628EB0289E30A8BA784B76F7885BECCAB4FEF7820E97EE3C6E036EEAF6EAA669288DF2FCACC9BEC045C907EBBDE87AFB8CC6B07A600BD63AC891B61D95C2265DD9FD5E635D61BFBF5EDC28311375066611C610FB533D64515B643C82F57D9B183B05C156D91BC0974D38E546022B139E82452E6F1EDF76E52F732C3904E5E433F8F3D488DB0698427DBB0791A9F207F8CB6654CB8410BAF4A59C4F9E821E589ABC1E6E6E1D432181B690408F6884FE1007895A4D26D4A5A2C7458EE747DA35D44AC9FB08AB5477EA3E7CCDB3E37EE20FAFD0D0CF9584E420598B7003B347943AC28048F45E0FD21AD08148FFADCE0E7877219259A7BE722FFAE845A429BA2CF0A71F2D19EA7495530FABDB5106E8D404A38A7E6394C38457640EA7398C5D55F0C4D342CC6A39C77E10A2A5145AEA40B14F5C7C3760334D83C9BE748383FADE231248537353817D51F7B44F61B406ABC61400000071C354139F458B02D978015F785B97F7F6B307380\n\
";

//password\n\
//51:b:01000000";

#endif


TsHttpRpc g_http_interface;

void http_rpc_main_loop(void)
{
	if (!g_http_interface.init(TS_HTTP_RPC_HOST, TS_HTTP_RPC_PORT))
	{
		EXLOGE("[ERROR] can not start HTTP-RPC listener, maybe port %d is already in use.\n", TS_HTTP_RPC_PORT);
		return;
	}

	EXLOGW("======================================================\n");
	EXLOGW("[rpc] TeleportAssist-HTTP-RPC ready on %s:%d\n", TS_HTTP_RPC_HOST, TS_HTTP_RPC_PORT);

	g_http_interface.run();

	EXLOGW("[rpc] main loop end.\n");
}

void http_rpc_stop(void)
{
	g_http_interface.stop();
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

TsHttpRpc::TsHttpRpc()
{
	m_stop = false;
	mg_mgr_init(&m_mg_mgr, NULL);
}

TsHttpRpc::~TsHttpRpc()
{
	mg_mgr_free(&m_mg_mgr);
}

bool TsHttpRpc::init(const char* ip, int port)
{
	char file_name[MAX_PATH] = { 0 };
	if (!GetModuleFileNameA(NULL, file_name, MAX_PATH))
		return false;

	int len = strlen(file_name);

	if (file_name[len] == '\\')
	{
		file_name[len] = '\0';
	}
	char* match = strrchr(file_name, '\\');
	if (match != NULL)
	{
		*match = '\0';
	}

	struct mg_connection* nc = NULL;

	char addr[128] = { 0 };
	if (0 == strcmp(ip, "127.0.0.1") || 0 == strcmp(ip, "localhost"))
		sprintf_s(addr, 128, ":%d", port);
	else
		sprintf_s(addr, 128, "%s:%d", ip, port);

	nc = mg_bind(&m_mg_mgr, addr, _mg_event_handler);
	if (nc == NULL)
	{
		EXLOGE("[rpc] TsHttpRpc::init %s:%d\n", ip, port);
		return false;
	}
	nc->user_data = this;

	mg_set_protocol_http_websocket(nc);

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

void TsHttpRpc::run(void)
{
	while(!m_stop)
	{
		mg_mgr_poll(&m_mg_mgr, 500);
	}
}

void TsHttpRpc::stop(void)
{
	m_stop = true;
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
		char* dbg_method = NULL;
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
			ex_wstr page = L"<html lang=\"zh_CN\"><head><meta charset=\"utf-8\"/><meta http-equiv=\"Content-Type\" content=\"text/html; charset=utf-8\"/><title>Teleport助手</title>\n<style type=\"text/css\">\n.box{padding:20px;margin:40px;border:1px solid #78b17c;background-color:#e4ffe5;}\n</style>\n</head><body><div class=\"box\">Teleport助手工作正常！</div></body></html>";
			ex_wstr2astr(page, ret_buf, EX_CODEPAGE_UTF8);

			mg_printf(nc, "HTTP/1.0 200 OK\r\nAccess-Control-Allow-Origin: *\r\nContent-Length: %d\r\nContent-Type: text/html\r\n\r\n%s", ret_buf.size() - 1, &ret_buf[0]);
			nc->flags |= MG_F_SEND_AND_CLOSE;
			return;
		}
		else if (uri == "/config")
		{
			uri = "/index.html";
			b_is_index = true;
		}

		{
			while (true)
			{
				int offset = uri.find("/");
				if (offset < 0)
				{
					break;
				}
				uri = uri.replace(offset, 1, "\\");
			}
			ex_astr file_suffix;
			int offset = uri.rfind(".");
			if (offset > 0)
			{
				file_suffix = uri.substr(offset, uri.length());
			}

			ex_astr temp;
			ex_wstr2astr(g_env.m_site_path, temp);
			ex_astr index_path = temp + uri;
			FILE* file = NULL;
			//fopen(index_path.c_str(), "rb");
			fopen_s(&file, index_path.c_str(), "rb");
			unsigned long file_size = 0;
			char* buf = 0;
			int ret = 0;
			if (file)
			{
				fseek(file, 0, SEEK_END);
				file_size = ftell(file);
				buf = new char[file_size];
				memset(buf, 0, file_size);
				fseek(file, 0, SEEK_SET);
				ret = fread(buf, 1, file_size, file);
				fclose(file);

				ex_astr content_type = _this->get_content_type(file_suffix);

				mg_printf(nc, "HTTP/1.0 200 OK\r\nAccess-Control-Allow-Origin: *\r\nContent-Length: %d\r\nContent-Type: %s\r\n\r\n", file_size, content_type.c_str());
				mg_send(nc, buf, file_size);
				delete []buf;
				nc->flags |= MG_F_SEND_AND_CLOSE;
				return;
			}
			else if (b_is_index)
			{
				ex_wstr page = L"<html lang=\"zh_CN\"><html><head><title>404 Not Found</title></head><body bgcolor=\"white\"><center><h1>404 Not Found</h1></center><hr><center><p>未能找到TELEPORT助手配置页面文件！</p></center></body></html>";
				ex_wstr2astr(page, ret_buf, EX_CODEPAGE_UTF8);

				mg_printf(nc, "HTTP/1.0 404 File Not Found\r\nAccess-Control-Allow-Origin: *\r\nContent-Length: %d\r\nContent-Type: text/html\r\n\r\n%s", ret_buf.size() - 1, &ret_buf[0]);
				nc->flags |= MG_F_SEND_AND_CLOSE;
				return;
			}
		}

		ex_astr method;
		ex_astr json_param;
		unsigned int rv = _this->_parse_request(hm, method, json_param);
		if (0 != rv)
		{
			EXLOGE("[ERROR] http-rpc got invalid request.\n");
			_this->_create_json_ret(ret_buf, rv);
		}
		else
		{
			_this->_process_js_request(method, json_param, ret_buf);
		}

		mg_printf(nc, "HTTP/1.0 200 OK\r\nAccess-Control-Allow-Origin: *\r\nContent-Length: %d\r\nContent-Type: application/json\r\n\r\n%s", ret_buf.size() - 1, &ret_buf[0]);
		nc->flags |= MG_F_SEND_AND_CLOSE;
	}
	break;
	default:
		break;
	}
}

unsigned int TsHttpRpc::_parse_request(struct http_message* req, ex_astr& func_cmd, ex_astr& func_args)
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

	if (0 == strs.size())
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

	if (func_args.length() > 0)
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

	EXLOGV("[rpc] method=%s, json_param=%s\n", func_cmd.c_str(), func_args.c_str());

	return TSR_OK;
}

void TsHttpRpc::_process_js_request(const ex_astr& func_cmd, const ex_astr& func_args, ex_astr& buf)
{
	if (func_cmd == "ts_get_version")
	{
		_rpc_func_get_version(func_args, buf);
	}
	else if (func_cmd == "ts_op")
	{
		_rpc_func_create_ts_client(func_args, buf);
	}
	else if (func_cmd == "ts_check")
	{
		_rpc_func_ts_check(func_args, buf);
	}
	else if (func_cmd == "ts_rdp_play")
	{
		_rpc_func_ts_rdp_play(func_args, buf);
	}
	else if (func_cmd == "ts_get_config")
	{
		_rpc_func_get_config(func_args, buf);
	}
	else if (func_cmd == "ts_set_config")
	{
		_rpc_func_set_config(func_args, buf);
	}
	else if (func_cmd == "ts_file_action")
	{
		_rpc_func_file_action(func_args, buf);
	}
	else
	{
		EXLOGE("[rpc] got unknown command: %s\n", func_cmd.c_str());
		_create_json_ret(buf, TSR_NO_SUCH_METHOD);
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

void TsHttpRpc::_rpc_func_create_ts_client(const ex_astr& func_args, ex_astr& buf)
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
		_create_json_ret(buf, TSR_INVALID_JSON_FORMAT);
		return;
	}
	if (jsRoot.isArray())
	{
		_create_json_ret(buf, TSR_INVALID_JSON_PARAM);
		return;
	}

	// 判断参数是否正确
	if (!jsRoot["server_ip"].isString() || !jsRoot["size"].isNumeric()
		|| !jsRoot["server_port"].isNumeric() || !jsRoot["host_ip"].isString()
		|| !jsRoot["session_id"].isString() || !jsRoot["pro_type"].isNumeric()
		)
	{
		_create_json_ret(buf, TSR_INVALID_JSON_PARAM);
		return;
	}

	int pro_sub = 1;
	if (!jsRoot["pro_sub"].isNull()) {
		if (jsRoot["pro_sub"].isNumeric()) {
			pro_sub = jsRoot["pro_sub"].asInt();
		}
	}

	std::string teleport_ip = jsRoot["server_ip"].asCString();
	int teleport_port = jsRoot["server_port"].asUInt();

	int windows_size = 2;
	if (jsRoot["size"].isNull())
		windows_size = 2;
	else
		windows_size = jsRoot["size"].asUInt();

	int console = 0;
	if (jsRoot["console"].isNull())
		console = 0;
	else
		console = jsRoot["console"].asUInt();

	std::string real_host_ip = jsRoot["host_ip"].asCString();
	std::string sid = jsRoot["session_id"].asCString();

	int pro_type = jsRoot["pro_type"].asUInt();

	ex_wstr w_exe_path;
	WCHAR w_szCommandLine[MAX_PATH] = { 0 };


	ex_wstr w_sid;
	ex_astr2wstr(sid, w_sid);
	ex_wstr w_teleport_ip;
	ex_astr2wstr(teleport_ip, w_teleport_ip);
	ex_wstr w_real_host_ip;
	ex_astr2wstr(real_host_ip, w_real_host_ip);
	WCHAR w_port[32] = { 0 };
	swprintf_s(w_port, _T("%d"), teleport_port);


	if (pro_type == 1)
	{
		//==============================================
		// RDP
		//==============================================
#if 1

#if 0
		int split_pos = session_id.length() - 2;
		std::string real_s_id = session_id.substr(0, split_pos);
		std::string str_pwd_len = session_id.substr(split_pos, session_id.length());
		int n_pwd_len = strtol(str_pwd_len.c_str(), NULL, 16);
		n_pwd_len -= real_s_id.length();
		WCHAR w_szPwd[256] = { 0 };
		for (int i = 0; i < n_pwd_len; i++)
		{
			w_szPwd[i] = '*';
		}

		w_exe_path = g_env.m_tools_path + _T("\\tprdp\\tp_rdp.exe");
		ex_wstr w_s_id;
		ex_astr2str(real_s_id, w_s_id);
		ex_wstr w_server_ip;
		ex_astr2str(server_ip, w_server_ip);

		ex_wstr w_host_ip;
		ex_astr2str(host_ip, w_host_ip);

		swprintf_s(w_szCommandLine, _T(" -h%s -u%s -p%s -x%d -d%s -r%d"), w_server_ip.c_str(), w_s_id.c_str(), w_szPwd, host_port, w_host_ip.c_str(), windows_size);

		// 		sprintf_s(sz_file_name, ("%s\\%s.rdp"), temp_path, temp_host_ip.c_str());
		// 		FILE* f = fopen(sz_file_name, ("wt"));
		// 		if (f == NULL)
		// 		{
		// 			printf("fopen failed (%d).\n", GetLastError());
		// 			_create_json_ret(buf, TSR_OPENFILE_ERROR);
		// 			return;
		// 		}
		// 		// Write a string into the file.
		// 		fwrite(sz_rdp_file_content, strlen(sz_rdp_file_content), 1, f);
		// 		fclose(f);
		// 		ex_wstr w_sz_file_name;
		// 		ex_astr2str(sz_file_name, w_sz_file_name);
		//		swprintf_s(w_szCommandLine, _T("mstsc %s"), w_sz_file_name.c_str());

		w_exe_path += w_szCommandLine;
		//BOOL bRet = DeleteFile(w_sz_file_name.c_str());
#else
		wchar_t* w_screen = NULL;

		switch (windows_size)
		{
		case 0: //全屏
			w_screen = _T("/f");
			break;
		case 2:
			w_screen = _T("/size:1024x768");
			break;
		case 3:
			w_screen = _T("/size:1280x1024");
			break;
		case 1:
		default:
			w_screen = _T("/size:800x600");
			break;
		}

		int split_pos = sid.length() - 2;
		std::string real_sid = sid.substr(0, split_pos);
		std::string str_pwd_len = sid.substr(split_pos, sid.length());
		int n_pwd_len = strtol(str_pwd_len.c_str(), NULL, 16);
		n_pwd_len -= real_sid.length();
		WCHAR w_szPwd[256] = { 0 };
		for (int i = 0; i < n_pwd_len; i++)
		{
			w_szPwd[i] = '*';
		}

		ex_astr2wstr(real_sid, w_sid);


		w_exe_path = _T("\"");
		w_exe_path += g_env.m_tools_path + _T("\\tprdp\\tprdp-client.exe\"");

		// use /gdi:sw otherwise the display will be yellow.
		if (console != 0)
		{
			swprintf_s(w_szCommandLine, _T(" %s /v:{host_ip}:{host_port} /admin /u:{user_name} /p:%s +clipboard /drives /gdi:sw /t:\"TP#{real_ip}\""),
				w_screen, w_szPwd
				);
		}
		else
		{
			swprintf_s(w_szCommandLine, _T(" %s /v:{host_ip}:{host_port} /u:{user_name} /p:%s +clipboard /drives /gdi:sw /t:\"TP#{real_ip}\""),
				w_screen, w_szPwd
				);
		}

		w_exe_path += w_szCommandLine;

#endif

#else
		int width = 800;
		int higth = 600;
		int cx = 0;
		int cy = 0;

		int display = 1;
		int iWidth = GetSystemMetrics(SM_CXSCREEN);
		int iHeight = GetSystemMetrics(SM_CYSCREEN);
		switch (windows_size)
		{
		case 0:
			//全屏
			width = iWidth;
			higth = iHeight;
			display = 2;
			break;
		case 1:
		{
			width = 800;
			higth = 600;
			display = 1;
			break;
		}
		case 2:
		{
			width = 1024;
			higth = 768;
			display = 1;
			break;
		}
		case 3:
		{
			width = 1280;
			higth = 1024;
			display = 1;
			break;
		}
		default:
			//int iWidth = GetSystemMetrics(SM_CXSCREEN);
			//int iHeight = GetSystemMetrics(SM_CYSCREEN);
			//width = iWidth;
			//width = iHeight - 50;
			width = 800;
			higth = 600;
			break;
		}

		cx = (iWidth - width) / 2;
		cy = (iHeight - higth) / 2;
		if (cx < 0)
		{
			cx = 0;
		}
		if (cy < 0)
		{
			cy = 0;
		}

		int split_pos = sid.length() - 2;
		std::string real_sid = sid.substr(0, split_pos);

		char sz_rdp_file_content[4096] = { 0 };
		sprintf_s(sz_rdp_file_content, rdp_content.c_str(),
			console, display, width, higth
			, cx, cy, cx + width + 20, cy + higth + 40
			, teleport_ip.c_str(), teleport_port
			, real_sid.c_str()
			);

		char sz_file_name[MAX_PATH] = { 0 };
		char temp_path[MAX_PATH] = { 0 };
		DWORD ret = GetTempPathA(MAX_PATH, temp_path);
		if (ret <= 0)
		{
			printf("fopen failed (%d).\n", GetLastError());
			_create_json_ret(buf, TSR_GETTEMPPATH_ERROR);
			return;
		}
		ex_wstr w_s_id;
		ex_astr2str(real_sid, w_s_id);

		ex_astr temp_host_ip = replace_all_distinct(real_host_ip, ("."), "-");

		sprintf_s(sz_file_name, ("%s\\%s.rdp"), temp_path, temp_host_ip.c_str());
		FILE* f = fopen(sz_file_name, ("wt"));
		if (f == NULL)
		{
			printf("fopen failed (%d).\n", GetLastError());
			_create_json_ret(buf, TSR_OPENFILE_ERROR);
			return;
		}
		// Write a string into the file.
		fwrite(sz_rdp_file_content, strlen(sz_rdp_file_content), 1, f);
		fclose(f);
		ex_wstr w_sz_file_name;
		ex_astr2str(sz_file_name, w_sz_file_name);

		swprintf_s(w_szCommandLine, _T("mstsc %s"), w_sz_file_name.c_str());
		w_exe_path = w_szCommandLine;
		//BOOL bRet = DeleteFile(w_sz_file_name.c_str());
#endif
	}
	else if (pro_type == 2)
	{
		//==============================================
		// SSH
		//==============================================

		if (pro_sub == 1)
		{
			clientsetmap::iterator it = g_cfgSSH.m_clientsetmap.find(g_cfgSSH.m_current_client);
			if (it == g_cfgSSH.m_clientsetmap.end())
			{
				w_exe_path = _T("\"");
				w_exe_path += g_env.m_tools_path;
				w_exe_path += _T("\\putty\\putty.exe\"");
				w_exe_path += _T(" -ssh -pw **** -P {host_port} -l {user_name} {host_ip}");
			}
			else
			{
				w_exe_path = _T("\"");
				w_exe_path += it->second.path + _T("\" ");
				w_exe_path += it->second.commandline;
			}
		}
		else
		{
			clientsetmap::iterator it = g_cfgScp.m_clientsetmap.find(g_cfgScp.m_current_client);
			if (it == g_cfgScp.m_clientsetmap.end())
			{
				w_exe_path = _T("\"");
				w_exe_path += g_env.m_tools_path;
				w_exe_path += _T("\\winscp\\winscp.exe\"");
				w_exe_path += _T(" /sessionname=\"TP#{real_ip}\" {user_name}:****@{host_ip}:{host_port}");
			}
			else {
				w_exe_path = it->second.path + _T(" ");
				w_exe_path += it->second.commandline;
			}
		}
	}
	else if (pro_type == 3)
	{
		//==============================================
		// TELNET
		//==============================================

		clientsetmap::iterator it = g_cfgTelnet.m_clientsetmap.find(g_cfgTelnet.m_current_client);
		if (it == g_cfgTelnet.m_clientsetmap.end())
		{
			w_exe_path = _T("\"");
			w_exe_path += g_env.m_tools_path;
			w_exe_path += _T("\\putty\\putty.exe\"");
			w_exe_path += _T(" telnet://{user_name}@{host_ip}:{host_port}");
		}
		else
		{
			w_exe_path = _T("\"");
			w_exe_path += it->second.path + _T("\" ");
			w_exe_path += it->second.commandline;
		}
	}

	ex_replace_all(w_exe_path, _T("{host_port}"), w_port);
	ex_replace_all(w_exe_path, _T("{host_ip}"), w_teleport_ip.c_str());
	ex_replace_all(w_exe_path, _T("{user_name}"), w_sid.c_str());
	ex_replace_all(w_exe_path, _T("{real_ip}"), w_real_host_ip.c_str());
	ex_replace_all(w_exe_path, _T("{assist_tools_path}"), g_env.m_tools_path.c_str());

	
	STARTUPINFO si;
	PROCESS_INFORMATION pi;

	ZeroMemory(&si, sizeof(si));
	si.cb = sizeof(si);
	ZeroMemory(&pi, sizeof(pi));

	Json::Value root_ret;
	ex_astr utf8_path;
	ex_wstr2astr(w_exe_path, utf8_path, EX_CODEPAGE_UTF8);
	root_ret["path"] = utf8_path;

	if (!CreateProcess(NULL, (wchar_t *)w_exe_path.c_str(), NULL, NULL, FALSE, 0, NULL, NULL, &si, &pi))
	{
		EXLOGE(_T("CreateProcess() failed. Error=0x%08X.\n  %s\n"), GetLastError(), w_exe_path.c_str());
		root_ret["code"] = TSR_CREATE_PROCESS_ERROR;
		_create_json_ret(buf, root_ret);
		return;
	}

	root_ret["code"] = TSR_OK;
	_create_json_ret(buf, root_ret);
}

bool isIPAddress(const char *s)
{
	const char *pChar;
	bool rv = true;
	int tmp1, tmp2, tmp3, tmp4, i;
	while (1)
	{
		i = sscanf_s(s, "%d.%d.%d.%d", &tmp1, &tmp2, &tmp3, &tmp4);
		if (i != 4)
		{
			rv = false;
			break;
		}

		if ((tmp1 > 255) || (tmp2 > 255) || (tmp3 > 255) || (tmp4 > 255))
		{
			rv = false;
			break;
		}

		for (pChar = s; *pChar != 0; pChar++)
		{
			if ((*pChar != '.')
				&& ((*pChar < '0') || (*pChar > '9')))
			{
				rv = false;
				break;
			}
		}
		break;
	}

	return rv;
}

void TsHttpRpc::_rpc_func_ts_check(const ex_astr& func_args, ex_astr& buf)
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
		_create_json_ret(buf, TSR_INVALID_JSON_FORMAT);
		return;
	}
	if (jsRoot.isArray())
	{
		_create_json_ret(buf, TSR_INVALID_JSON_PARAM);
		return;
	}
	int windows_size = 2;



	// 判断参数是否正确
	if (!jsRoot["server_ip"].isString() || !jsRoot["ssh_port"].isNumeric()
		|| !jsRoot["rdp_port"].isNumeric()
		)
	{
		_create_json_ret(buf, TSR_INVALID_JSON_PARAM);
		return;
	}

	std::string host = jsRoot["server_ip"].asCString();
	int rdp_port = jsRoot["rdp_port"].asUInt();
	int ssh_port = jsRoot["rdp_port"].asUInt();
	std::string server_ip;
	if (isIPAddress(host.c_str()))
	{
		server_ip = host;
	}
	else
	{
		char *ptr, **pptr;
		struct hostent *hptr;
		char IP[128] = { 0 };
		/* 取得命令后第一个参数，即要解析的域名或主机名 */
		ptr = (char*)host.c_str();
		/* 调用gethostbyname()。调用结果都存在hptr中 */
		if ((hptr = gethostbyname(ptr)) == NULL)
		{
			//printf("gethostbyname error for host:%s/n", ptr);
			_create_json_ret(buf, TSR_INVALID_JSON_PARAM);
			return; /* 如果调用gethostbyname发生错误，返回1 */
		}
		/* 将主机的规范名打出来 */
		//printf("official hostname:%s/n", hptr->h_name);
		// 主机可能有多个别名，将所有别名分别打出来
		//for (pptr = hptr->h_aliases; *pptr != NULL; pptr++)
		//	printf(" alias:%s/n", *pptr);
		/* 根据地址类型，将地址打出来 */
		char szbuf[1204] = { 0 };
		switch (hptr->h_addrtype)
		{
		case AF_INET:
		case AF_INET6:
			pptr = hptr->h_addr_list;
			/* 将刚才得到的所有地址都打出来。其中调用了inet_ntop()函数 */

			for (; *pptr != NULL; pptr++)
				inet_ntop(hptr->h_addrtype, *pptr, IP, sizeof(IP));
			server_ip = IP;
			//printf(" address:%s/n", inet_ntop(hptr->h_addrtype, *pptr, str, sizeof(str)));
			break;
		default:
			printf("unknown address type/n");
			break;
		}
	}
	if (!isIPAddress(server_ip.c_str()))
	{
		_create_json_ret(buf, TSR_INVALID_JSON_PARAM);
		return;
	}
	if (TestTCPPort(server_ip, rdp_port) && TestTCPPort(server_ip, ssh_port))
	{
		_create_json_ret(buf, TSR_OK);
		return;
	}
	ICMPheaderRet temp = { 0 };
	int b_ok = ICMPSendTo(&temp, (char*)server_ip.c_str(), 16, 8);
	if (b_ok == 0)
	{
		_create_json_ret(buf, TSR_PING_OK);
		return;
	}
	else
	{
		_create_json_ret(buf, TSR_PING_ERROR);
	}

	return;
}

void TsHttpRpc::_rpc_func_ts_rdp_play(const ex_astr& func_args, ex_astr& buf)
{
	Json::Reader jreader;
	Json::Value jsRoot;

	if (!jreader.parse(func_args.c_str(), jsRoot))
	{
		_create_json_ret(buf, TSR_INVALID_JSON_FORMAT);
		return;
	}

	// 判断参数是否正确
	if (!jsRoot["host"].isString())
	{
		_create_json_ret(buf, TSR_INVALID_JSON_PARAM);
		return;
	}
	if (!jsRoot["port"].isInt())
	{
		_create_json_ret(buf, TSR_INVALID_JSON_PARAM);
		return;
	}
	if (!jsRoot["tail"].isString())
	{
		_create_json_ret(buf, TSR_INVALID_JSON_PARAM);
		return;
	}
	ex_astr a_host = jsRoot["host"].asCString();
	int port = jsRoot["port"].asInt();
	ex_astr a_tail = jsRoot["tail"].asCString();
	ex_astr server_ip;
	if (isIPAddress(a_host.c_str()))
	{
		server_ip = a_host;
	}
	else
	{
		char *ptr, **pptr;
		struct hostent *hptr;
		char IP[128] = { 0 };
		/* 取得命令后第一个参数，即要解析的域名或主机名 */
		ptr = (char*)a_host.c_str();
		/* 调用gethostbyname()。调用结果都存在hptr中 */
		if ((hptr = gethostbyname(ptr)) == NULL)
		{
			//printf("gethostbyname error for host:%s/n", ptr);
			_create_json_ret(buf, TSR_INVALID_JSON_PARAM);
			return;
		}
		/* 将主机的规范名打出来 */
		//printf("official hostname:%s/n", hptr->h_name);
		///* 主机可能有多个别名，将所有别名分别打出来 */
		//for (pptr = hptr->h_aliases; *pptr != NULL; pptr++)
		//	printf(" alias:%s/n", *pptr);
		/* 根据地址类型，将地址打出来 */
		char szbuf[1204] = { 0 };
		switch (hptr->h_addrtype)
		{
		case AF_INET:
		case AF_INET6:
			pptr = hptr->h_addr_list;
			/* 将刚才得到的所有地址都打出来。其中调用了inet_ntop()函数 */

			for (; *pptr != NULL; pptr++)
				inet_ntop(hptr->h_addrtype, *pptr, IP, sizeof(IP));
			server_ip = IP;
			break;
		default:
			printf("unknown address type/n");
			break;
		}
	}
	char szURL[256] = { 0 };
	sprintf_s(szURL, 256, "http://%s:%d/%s", server_ip.c_str(), port, a_tail.c_str());
	ex_astr a_url = szURL;
	ex_wstr w_url;
	ex_astr2wstr(a_url, w_url);

	char szHost[256] = { 0 };
	sprintf_s(szHost, 256, "%s:%d", a_host.c_str(), port);

	a_host = szHost;
	ex_wstr w_host;
	ex_astr2wstr(a_host, w_host);
	
	ex_wstr w_exe_path;
	w_exe_path = _T("\"");
	w_exe_path += g_env.m_tools_path + _T("\\tprdp\\tprdp-replay.exe\"");
	//swprintf_s(w_szCommandLine, _T(" -ssh -pw **** -P %d -l %s %s"), teleport_port, w_s_id.c_str(), w_teleport_ip.c_str());
	w_exe_path += _T(" ");
	w_exe_path += w_url;

	w_exe_path += _T(" ");
	w_exe_path += w_host;

	Json::Value root_ret;
	ex_astr utf8_path;
	ex_wstr2astr(w_exe_path, utf8_path, EX_CODEPAGE_UTF8);
	root_ret["path"] = utf8_path;

	STARTUPINFO si;
	PROCESS_INFORMATION pi;

	ZeroMemory(&si, sizeof(si));
	si.cb = sizeof(si);
	ZeroMemory(&pi, sizeof(pi));
	if (!CreateProcess(NULL, (wchar_t *)w_exe_path.c_str(), NULL, NULL, FALSE, 0, NULL, NULL, &si, &pi))
	{
		EXLOGE(_T("CreateProcess() failed. Error=0x%08X.\n  %s\n"), GetLastError(), w_exe_path.c_str());
		root_ret["code"] = TSR_CREATE_PROCESS_ERROR;
		_create_json_ret(buf, root_ret);
		return;
	}

	root_ret["code"] = TSR_OK;
	_create_json_ret(buf, root_ret);
	return;
}

void TsHttpRpc::_rpc_func_get_config(const ex_astr& func_args, ex_astr& buf)
{
	Json::Reader jreader;
	Json::Value jsRoot;

	if (!jreader.parse(func_args.c_str(), jsRoot))
	{
		_create_json_ret(buf, TSR_INVALID_JSON_FORMAT);
		return;
	}
	// 判断参数是否正确
	if (!jsRoot["type"].isNumeric())
	{
		_create_json_ret(buf, TSR_INVALID_JSON_PARAM);
		return;
	}
	int type = jsRoot["type"].asUInt();
	if (type == 1)
	{
		Json::Value jr_root;
		Json::Value config_list;

		jr_root["code"] = 0;

		clientsetmap::iterator it;
		for (it = g_cfgSSH.m_clientsetmap.begin(); it != g_cfgSSH.m_clientsetmap.end(); it++)
		{

			Json::Value config;
			ex_astr temp;
			ex_wstr2astr(it->first, temp, EX_CODEPAGE_UTF8);
			config["name"] = temp;

			ex_wstr2astr(it->second.path, temp, EX_CODEPAGE_UTF8);
			config["path"] = temp;

			ex_wstr2astr(it->second.commandline, temp, EX_CODEPAGE_UTF8);
			config["commandline"] = temp;

			ex_wstr2astr(it->second.alias_name, temp, EX_CODEPAGE_UTF8);
			config["alias_name"] = temp;

			ex_wstr2astr(it->second.desc, temp, EX_CODEPAGE_UTF8);
			config["desc"] = temp;

			config["build_in"] = it->second.is_default ? 1 : 0;
			if (it->first == g_cfgSSH.m_current_client)
			{
				config["current"] = 1;
			}
			else {
				config["current"] = 0;
			}


			config_list.append(config);
		}

		jr_root["config_list"] = config_list;
		_create_json_ret(buf, jr_root);

		return;
	}
	else if (type == 2)
	{
		Json::Value jr_root;
		Json::Value config_list;

		jr_root["code"] = 0;

		clientsetmap::iterator it;
		for (it = g_cfgScp.m_clientsetmap.begin(); it != g_cfgScp.m_clientsetmap.end(); it++)
		{

			Json::Value config;
			ex_astr temp;
			ex_wstr2astr(it->first, temp, EX_CODEPAGE_UTF8);
			config["name"] = temp;

			ex_wstr2astr(it->second.path, temp, EX_CODEPAGE_UTF8);
			config["path"] = temp;

			ex_wstr2astr(it->second.commandline, temp, EX_CODEPAGE_UTF8);
			config["commandline"] = temp;

			ex_wstr2astr(it->second.desc, temp, EX_CODEPAGE_UTF8);
			config["desc"] = temp;

			ex_wstr2astr(it->second.alias_name, temp, EX_CODEPAGE_UTF8);
			config["alias_name"] = temp;

			config["build_in"] = it->second.is_default ? 1 : 0;

			if (it->first == g_cfgScp.m_current_client)
				config["current"] = 1;
			else
				config["current"] = 0;

			config_list.append(config);
		}

		jr_root["config_list"] = config_list;
		_create_json_ret(buf, jr_root);
		return;
	}
	else if (type == 3)
	{
		Json::Value jr_root;
		Json::Value config_list;

		jr_root["code"] = 0;

		clientsetmap::iterator it;
		for (it = g_cfgTelnet.m_clientsetmap.begin(); it != g_cfgTelnet.m_clientsetmap.end(); it++)
		{
			Json::Value config;
			ex_astr temp;
			ex_wstr2astr(it->first, temp, EX_CODEPAGE_UTF8);
			config["name"] = temp;

			ex_wstr2astr(it->second.path, temp, EX_CODEPAGE_UTF8);
			config["path"] = temp;

			ex_wstr2astr(it->second.commandline, temp, EX_CODEPAGE_UTF8);
			config["commandline"] = temp;

			ex_wstr2astr(it->second.desc, temp, EX_CODEPAGE_UTF8);
			config["desc"] = temp;

			ex_wstr2astr(it->second.alias_name, temp, EX_CODEPAGE_UTF8);
			config["alias_name"] = temp;

			config["build_in"] = it->second.is_default ? 1 : 0;

			if (it->first == g_cfgTelnet.m_current_client)
				config["current"] = 1;
			else
				config["current"] = 0;

			config_list.append(config);
		}

		jr_root["config_list"] = config_list;
		_create_json_ret(buf, jr_root);
		return;
	}
	else
	{
		_create_json_ret(buf, TSR_INVALID_JSON_PARAM);
		return;
	}
}

void TsHttpRpc::_rpc_func_set_config(const ex_astr& func_args, ex_astr& buf)
{
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

	// 判断参数是否正确
	if (!jsRoot["name"].isString() || !jsRoot["path"].isString() ||
		!jsRoot["commandline"].isString() ||
		!jsRoot["type"].isNumeric())
	{
		_create_json_ret(buf, TSR_INVALID_JSON_PARAM);
		return;
	}
	int type = jsRoot["type"].asUInt();
	ex_astr name = jsRoot["name"].asCString();
	ex_astr path = jsRoot["path"].asCString();
	ex_astr commandline = jsRoot["commandline"].asCString();

	ex_wstr w_path;
	ex_astr2wstr(path, w_path, EX_CODEPAGE_UTF8);
	ex_wstr w_name;
	ex_astr2wstr(name, w_name, EX_CODEPAGE_UTF8);

	ex_wstr w_commandline;
	ex_astr2wstr(commandline, w_commandline, EX_CODEPAGE_UTF8);

	if (type == 1)
	{

		clientsetmap::iterator it = g_cfgSSH.m_clientsetmap.find(w_name);
		if (it == g_cfgSSH.m_clientsetmap.end()) {
			_create_json_ret(buf, TSR_INVALID_JSON_PARAM);
			return;
		}
		if (it->second.is_default)
		{
			g_cfgSSH.set(_T("common"), _T("current_client"), w_name);
			g_cfgSSH.save();
			g_cfgSSH.init();
			_create_json_ret(buf, TSR_OK);
			return;
		}
		g_cfgSSH.set(w_name, _T("path"), w_path);
		g_cfgSSH.set(w_name, _T("command_line"), w_commandline);
		g_cfgSSH.set(_T("common"), _T("current_client"), w_name);

		g_cfgSSH.save();
		g_cfgSSH.init();
		_create_json_ret(buf, TSR_OK);
		return;

	}
	else if (type == 2)
	{
		clientsetmap::iterator it = g_cfgScp.m_clientsetmap.find(w_name);
		if (it == g_cfgScp.m_clientsetmap.end()) {
			_create_json_ret(buf, TSR_INVALID_JSON_PARAM);
			return;
		}
		if (it->second.is_default)
		{
			g_cfgScp.set(_T("common"), _T("current_client"), w_name);
			g_cfgScp.save();
			g_cfgScp.init();
			_create_json_ret(buf, TSR_OK);
			return;
		}
		g_cfgScp.set(w_name, _T("path"), w_path);
		g_cfgScp.set(w_name, _T("command_line"), w_commandline);
		g_cfgScp.set(_T("common"), _T("current_client"), w_name);

		g_cfgScp.save();
		g_cfgScp.init();
		_create_json_ret(buf, TSR_OK);
		return;
	}
	else if (type == 3)
	{
		clientsetmap::iterator it = g_cfgTelnet.m_clientsetmap.find(w_name);
		if (it == g_cfgTelnet.m_clientsetmap.end()) {
			_create_json_ret(buf, TSR_INVALID_JSON_PARAM);
			return;
		}
		if (it->second.is_default)
		{
			g_cfgTelnet.set(_T("common"), _T("current_client"), w_name);
			g_cfgTelnet.save();
			g_cfgTelnet.init();
			_create_json_ret(buf, TSR_OK);
			return;
		}
		g_cfgTelnet.set(w_name, _T("path"), w_path);
		g_cfgTelnet.set(w_name, _T("command_line"), w_commandline);
		g_cfgTelnet.set(_T("common"), _T("current_client"), w_name);

		g_cfgTelnet.save();
		g_cfgTelnet.init();
		_create_json_ret(buf, TSR_OK);
		return;
	}
	else {
		_create_json_ret(buf, TSR_INVALID_JSON_PARAM);
		return;
	}
}

void TsHttpRpc::_rpc_func_file_action(const ex_astr& func_args, ex_astr& buf) {

	Json::Reader jreader;
	Json::Value jsRoot;

	if (!jreader.parse(func_args.c_str(), jsRoot))
	{
		_create_json_ret(buf, TSR_INVALID_JSON_FORMAT);
		return;
	}
	// 判断参数是否正确
	if (!jsRoot["action"].isNumeric())
	{
		_create_json_ret(buf, TSR_INVALID_JSON_PARAM);
		return;
	}
	int action = jsRoot["action"].asUInt();

	HWND hParent = GetForegroundWindow();
	if (NULL == hParent)
		hParent = g_hDlgMain;

	BOOL ret = FALSE;
	wchar_t wszReturnPath[MAX_PATH] = _T("");

	if (action == 1 || action == 2)
	{
		OPENFILENAME ofn;
		ex_wstr wsDefaultName;
		ex_wstr wsDefaultPath;
		StringCchCopy(wszReturnPath, MAX_PATH, wsDefaultName.c_str());

		ZeroMemory(&ofn, sizeof(ofn));

		ofn.lStructSize = sizeof(ofn);
		ofn.lpstrTitle = _T("选择文件");
		ofn.hwndOwner = hParent;
		ofn.lpstrFilter = _T("可执行程序 (*.exe)\0*.exe\0");
		ofn.lpstrFile = wszReturnPath;
		ofn.nMaxFile = MAX_PATH;
		ofn.lpstrInitialDir = wsDefaultPath.c_str();
		ofn.Flags = OFN_EXPLORER | OFN_PATHMUSTEXIST;

		if (action == 1)
		{
			ofn.Flags |= OFN_FILEMUSTEXIST;
			ret = GetOpenFileName(&ofn);
		}
		else
		{
			ofn.Flags |= OFN_OVERWRITEPROMPT;
			ret = GetSaveFileName(&ofn);
		}
	}
	else if (action == 3)
	{
		BROWSEINFO bi;
		ZeroMemory(&bi, sizeof(BROWSEINFO));
		bi.hwndOwner = NULL;
		bi.pidlRoot = NULL;
		bi.pszDisplayName = wszReturnPath; //此参数如为NULL则不能显示对话框
		bi.lpszTitle = _T("选择目录");
		bi.ulFlags = BIF_RETURNONLYFSDIRS;
		bi.lpfn = NULL;
		bi.iImage = 0;   //初始化入口参数bi结束
		LPITEMIDLIST pIDList = SHBrowseForFolder(&bi);//调用显示选择对话框
		if (pIDList)
		{
			ret = true;
			SHGetPathFromIDList(pIDList, wszReturnPath);
		}
		else
		{
			ret = false;
		}
	}
	else if (action == 4)
	{
		ex_wstr wsDefaultName;
		ex_wstr wsDefaultPath;

		if (wsDefaultPath.length() == 0)
		{
			_create_json_ret(buf, TSR_INVALID_JSON_PARAM);
			return;
		}

		ex_wstr::size_type pos = 0;

		while (ex_wstr::npos != (pos = wsDefaultPath.find(L"/", pos)))
		{
			wsDefaultPath.replace(pos, 1, L"\\");
			pos += 1;
		}

		ex_wstr wArg = L"/select, \"";
		wArg += wsDefaultPath;
		wArg += L"\"";
		if ((int)ShellExecute(hParent, _T("open"), _T("explorer"), wArg.c_str(), NULL, SW_SHOW) > 32)
			ret = true;
		else
			ret = false;
	}

	if (ret)
	{
		if (action == 1 || action == 2 || action == 3)
		{
			ex_astr utf8_path;
			ex_wstr2astr(wszReturnPath, utf8_path, EX_CODEPAGE_UTF8);
			Json::Value root;
			root["path"] = utf8_path;
			_create_json_ret(buf, root);

			return;
		}
		else
		{
			_create_json_ret(buf, TSR_OK);
			return;
		}
	}
	else
	{
		_create_json_ret(buf, TSR_INVALID_DATA);
		return;
	}
}

void TsHttpRpc::_rpc_func_get_version(const ex_astr& func_args, ex_astr& buf)
{
	Json::Value root_ret;
	ex_wstr w_version = TP_ASSIST_VER;
	ex_astr version;
	ex_wstr2astr(w_version, version, EX_CODEPAGE_UTF8);
	root_ret["version"] = version;
	root_ret["code"] = TSR_OK;
	_create_json_ret(buf, root_ret);
	return;
}
