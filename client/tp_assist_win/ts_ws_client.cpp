#include "stdafx.h"

#pragma warning(disable:4091)

#include <commdlg.h>
#include <ShlObj.h>
#include <WinCrypt.h>

#pragma comment(lib, "Crypt32.lib")

#include <teleport_const.h>

//#ifndef MAX_PATH
//#    define MAX_PATH 1024
//#endif

// #include "../AppDelegate-C-Interface.h"

#include "ts_ws_client.h"
#include "ts_ver.h"
#include "ts_env.h"
#include "ts_cfg.h"
#include "ts_utils.h"

//#ifdef RDP_CLIENT_SYSTEM_BUILTIN

//connect to console:i:%d
//compression:i:1
//bitmapcachepersistenable:i:1

std::string rdp_content = "\
administrative session:i:%d\n\
screen mode id:i:%d\n\
use multimon:i:0\n\
desktopwidth:i:%d\n\
desktopheight:i:%d\n\
session bpp:i:16\n\
winposstr:s:0,1,%d,%d,%d,%d\n\
bitmapcachepersistenable:i:1\n\
bitmapcachesize:i:32000\n\
compression:i:1\n\
keyboardhook:i:2\n\
audiocapturemode:i:0\n\
videoplaybackmode:i:1\n\
connection type:i:7\n\
networkautodetect:i:1\n\
bandwidthautodetect:i:1\n\
disableclipboardredirection:i:0\n\
displayconnectionbar:i:1\n\
enableworkspacereconnect:i:0\n\
disable wallpaper:i:1\n\
allow font smoothing:i:0\n\
allow desktop composition:i:0\n\
disable full window drag:i:1\n\
disable menu anims:i:1\n\
disable themes:i:1\n\
disable cursor setting:i:1\n\
full address:s:%s:%d\n\
audiomode:i:0\n\
redirectprinters:i:0\n\
redirectcomports:i:0\n\
redirectsmartcards:i:0\n\
redirectclipboard:i:%d\n\
redirectposdevices:i:0\n\
autoreconnection enabled:i:0\n\
authentication level:i:2\n\
prompt for credentials:i:0\n\
negotiate security layer:i:1\n\
remoteapplicationmode:i:0\n\
alternate shell:s:\n\
shell working directory:s:\n\
gatewayhostname:s:\n\
gatewayusagemethod:i:4\n\
gatewaycredentialssource:i:4\n\
gatewayprofileusagemethod:i:0\n\
promptcredentialonce:i:0\n\
gatewaybrokeringtype:i:0\n\
use redirection server name:i:0\n\
rdgiskdcproxy:i:0\n\
kdcproxyname:s:\n\
drivestoredirect:s:%s\n\
username:s:%s\n\
password 51:b:%s\n\
";

// https://www.donkz.nl/overview-rdp-file-settings/
//
// authentication level:i:2\n
//   
//
// negotiate security layer:i:1\n
//   0 = negotiation is not enabled and the session is started by using Secure Sockets Layer (SSL).
//   1 = negotiation is enabled and the session is started by using x.224 encryption.



//redirectdirectx:i:0\n\
//prompt for credentials on client:i:0\n\

//#endif

TsWsClient g_ws_client;

void* g_app = NULL;

bool calc_psw51b(const char* password, std::string& ret) {
	DATA_BLOB DataIn;
	DATA_BLOB DataOut;

	ex_wstr w_pswd;
	ex_astr2wstr(password, w_pswd, EX_CODEPAGE_ACP);

	DataIn.cbData = w_pswd.length() * sizeof(wchar_t);
	DataIn.pbData = (BYTE*)w_pswd.c_str();


	if (!CryptProtectData(&DataIn, L"psw", nullptr, nullptr, nullptr, 0, &DataOut))
		return false;

	char szRet[5] = { 0 };
	for (DWORD i = 0; i < DataOut.cbData; ++i) {
		sprintf_s(szRet, 5, "%02X", DataOut.pbData[i]);
		ret += szRet;
	}

	LocalFree(DataOut.pbData);
	return true;
}

// static
void TsWsClient::init_app(void* app)
{
	g_app = app;
}

void TsWsClient::stop_all_client()
{
	g_ws_client.stop();
}

// ============================================================================
// static
void TsWsClient::url_scheme_handler(const std::string& url)
{
	// from command line:
	//   teleport://register?param={"ws_url":"ws://127.0.0.1:7190/ws/assist/","assist_id":1234,"session_id":"tp_5678"}
	// from system-url-protocol handler. why Windows add extra '/' for me??? 
	//   teleport://register/?param={"ws_url":"ws://127.0.0.1:7190/ws/assist/","assist_id":1234,"session_id":"tp_5678"}

	std::string protocol;
	std::string method;
	std::string param;

	std::string::size_type pos_protocol = url.find("://");
	if (pos_protocol == std::string::npos)
	{
		EXLOGE("[url-schema] invalid url: %s\n", url.c_str());
		return;
	}

	std::string::size_type pos_method = url.find('?');
	if (pos_method == std::string::npos)
	{
		EXLOGE("[url-schema] invalid url: %s\n", url.c_str());
		return;
	}

	protocol.assign(url, 0, pos_protocol);
	if (protocol != "teleport")
	{
		EXLOGE("[url-schema] invalid protocol: %s\n", protocol.c_str());
		return;
	}

	method.assign(url, pos_protocol + 3, pos_method - pos_protocol - 3);
	if (method.empty())
	{
		EXLOGE("[ws] no method, what should I do now?\n");
		return;
	}
	if (method[method.length() - 1] == '/')
		method.erase(method.length() - 1, 1);

	param.assign(url, pos_method + 7);  // ?param=
	if (param.empty())
	{
		EXLOGE("[url-schema] invalid protocol: %s\n", protocol.c_str());
		return;
	}


	// decode param with url-decode.
	size_t len = param.length() * 2;
	ex_chars sztmp;
	sztmp.resize(len);
	memset(&sztmp[0], 0, len);
	if (-1 == ts_url_decode(param.c_str(), (int)param.length(), &sztmp[0], (int)len, 0))
	{
		EXLOGE("[url-schema] url-decode param failed: %s\n", param.c_str());
		return;
	}
	param = &sztmp[0];

	EXLOGV("[url-schema] method=%s, json_param=%s\n", method.c_str(), param.c_str());

	Json::CharReaderBuilder jcrb;
	std::unique_ptr<Json::CharReader> const jreader(jcrb.newCharReader());
	const char* str_json_begin = param.c_str();

	Json::Value js_root;
	ex_astr err;
	if (!jreader->parse(str_json_begin, str_json_begin + param.length(), &js_root, &err))
	{
		EXLOGE("[url-schema] param not in json format: %s\n", param.c_str());
		return;
	}
	if (!js_root.isObject())
	{
		EXLOGE("[url-schema] invalid param, need json object: %s\n", param.c_str());
		return;
	}

	if (method == "register")
	{
		_process_register(param, js_root);
	}
	else if (method == "run")
	{
		_process_run(param, js_root);
	}
	else if (method == "replay_rdp")
	{
		_process_replay_rdp(param, js_root);
	}
	else
	{
		EXLOGE("[ws] unknown method: %s\n", method.c_str());
		return;
	}
}

// static
void TsWsClient::_process_register(const std::string& param, Json::Value& js_root)
{
	// {"ws_url":"ws://127.0.0.1:7190/ws/assist/","assist_id":1234,"session_id":"tp_5678"}

	// check param
	if (!js_root["ws_url"].isString() || !js_root["assist_id"].isNumeric() || !js_root["session_id"].isString())
	{
		EXLOGE("[url-schema] invalid param: %s\n", param.c_str());
		return;
	}

	std::string ws_url = js_root["ws_url"].asCString();
	uint32_t assist_id = js_root["assist_id"].asUInt();
	std::string session_id = js_root["session_id"].asCString();

	std::string protocol;
	protocol.assign(ws_url, 0, 5);
	if (protocol == "ws://")
	{
		g_ws_client._register(false, ws_url, assist_id, session_id);
	}
	else if (protocol == "wss:/")
	{
		g_ws_client._register(true, ws_url, assist_id, session_id);
	}
	else
	{
		EXLOGE("[url-schema] invalid ws_url: %s\n", ws_url.c_str());
		return;
	}
}

void TsWsClient::_process_run(const std::string& param, Json::Value& js_root)
{
	// wrapper for _rpc_func_run_client().

	Json::Value js_param;
	js_param["method"] = "run";
	js_param["param"] = js_root;

	AssistMessage msg_req;
	std::string buf;
	_rpc_func_run_client(buf, msg_req, js_param);
}

void TsWsClient::_process_replay_rdp(const std::string& param, Json::Value& js_root)
{
	// wrapper for _rpc_func_replay_rdp().

	Json::Value js_param;
	js_param["method"] = "replay_rdp";
	js_param["param"] = js_root;

	AssistMessage msg_req;
	std::string buf;
	_rpc_func_replay_rdp(buf, msg_req, js_param);
}


// ============================================================================

TsWsClient::TsWsClient() :
	ExThreadBase("ws-client-thread"),
	m_nc(NULL),
	m_assist_id(0)
{
	mg_mgr_init(&m_mg_mgr, NULL);
}

TsWsClient::~TsWsClient()
{
	mg_mgr_free(&m_mg_mgr);
}

void TsWsClient::_thread_loop(void)
{
	while (!m_need_stop)
	{
		mg_mgr_poll(&m_mg_mgr, 500);
	}

	EXLOGV("[ws] main loop end.\n");
}

void TsWsClient::_register(bool is_ssl, const std::string& ws_url, uint32_t assist_id, const std::string& session_id)
{
	if (m_assist_id == 0)
		m_assist_id = assist_id;

	ex_wstr w_ver(TP_ASSIST_VER);
	ex_astr a_ver;
	ex_wstr2astr(w_ver, a_ver);

	//
	char msg[256] = { 0 };
	ex_strformat(
		msg, 256, "{\"type\":0,\"method\":\"register\",\"param\":{\"client\":\"assist\",\"sid\":\"%s\",\"request_assist_id\":%u,\"assist_id\":%u,\"assist_ver\":\"%s\"}}",
		session_id.c_str(), assist_id, m_assist_id, a_ver.c_str());

	if (!m_is_running)
	{
		// not start yet.
		std::string url = ws_url;
		url += msg;

		EXLOGD("mg_connect_ws: %s\n", url.c_str());

		if (is_ssl)
		{
			struct mg_connect_opts opts;
			memset(&opts, 0, sizeof(opts));
			opts.ssl_ca_cert = "*";
			opts.ssl_server_name = "*";
			m_nc = mg_connect_ws_opt(&m_mg_mgr, _mg_event_handler, opts, url.c_str(), "wss", NULL);
		}
		else
		{
			m_nc = mg_connect_ws(&m_mg_mgr, _mg_event_handler, url.c_str(), NULL, NULL);
		}

		// m_nc = mg_connect_ws(&m_mg_mgr, _mg_event_handler, url.c_str(), NULL, NULL);
		if (!m_nc)
		{
			EXLOGE("[ws] TsWsClient::init failed: %s\n", url.c_str());
			return;
		}
		m_nc->user_data = this;

		start();
		return;
	}


	EXLOGV("[ws] send: %s\n", msg);
	mg_send_websocket_frame(m_nc, WEBSOCKET_OP_TEXT, msg, strlen(msg));
}

// static
void TsWsClient::_mg_event_handler(struct mg_connection* nc, int ev, void* ev_data)
{
	auto* _this = (TsWsClient*)nc->user_data;
	if (NULL == _this)
	{
		EXLOGE("[ERROR] invalid request.\n");
		return;
	}

	switch (ev)
	{
	case MG_EV_CONNECT:
	{
		int status = *((int*)ev_data);
		if (status != 0)
		{
			EXLOGE("[ERROR] -- connect to ws server failed: %d\n", status);
		}

		break;
	}

	case MG_EV_WEBSOCKET_HANDSHAKE_DONE:
	{
		auto* hm = (struct http_message*)ev_data;
		if (hm->resp_code == 101)
		{
			EXLOGV("-- ws server connected\n");
		}
		else
		{
			EXLOGE("[ERROR] -- connect to ws server failed, HTTP code: %d\n", hm->resp_code);
		}
		break;
	}


	case MG_EV_WEBSOCKET_FRAME:
	{
		// on_message().
		auto* wm = (struct websocket_message*)ev_data;
		// EXLOGV("%d: %s\n", wm->size, wm->data);
		std::string message;
		message.assign((const char*)wm->data, wm->size);
		std::string buf;
		_this->_on_message(message, buf);

		if (!buf.empty())
		{
			mg_send_websocket_frame(nc, WEBSOCKET_OP_TEXT, buf.c_str(), buf.length());
		}

		break;
	}


	case MG_EV_CLOSE:
	{
		EXLOGV("-- ws server disconnected\n");
		_this->m_need_stop = true;
		break;
	}
	}
}

void TsWsClient::_create_response(ex_astr& buf, const AssistMessage& msg_ret, int err_code)
{
	Json::Value js_data(Json::objectValue);
	_create_response(buf, msg_ret, err_code, L"", js_data);
}

void TsWsClient::_create_response(ex_astr& buf, const AssistMessage& msg_ret, int err_code, const ex_wstr& message)
{
	Json::Value js_data(Json::objectValue);
	_create_response(buf, msg_ret, err_code, message, js_data);
}

void TsWsClient::_create_response(ex_astr& buf, const AssistMessage& msg_ret, int err_code, const ex_wstr& message, Json::Value& data)
{
	ex_astr _message;
	// ex_wstr2astr(message, _message, EX_CODEPAGE_UTF8);
	ex_wstr2astr(message, _message);

	Json::Value js_ret;
	js_ret["type"] = MESSAGE_TYPE_RESPONSE;
	js_ret["command_id"] = msg_ret.command_id;
	js_ret["method"] = msg_ret.method;
	js_ret["code"] = err_code;
	js_ret["message"] = _message;
	js_ret["data"] = data;

	Json::StreamWriterBuilder jwb;
	// jwb["emitUTF8"] = true;
	jwb["indentation"] = "";  // 压缩格式，没有换行和不必要的空白字符
	std::unique_ptr<Json::StreamWriter> js_writer(jwb.newStreamWriter());
	ex_aoss os;
	js_writer->write(js_ret, &os);
	buf = os.str();
}

void TsWsClient::_on_message(const std::string& message, std::string& buf)
{
	// {
	//     "type":0,
	//     "method":"run",
	//     "param":{
	//         "teleport_ip":"127.0.0.1","teleport_port":52189,"remote_host_ip":"39.97.125.170",
	//         "remote_host_name":"tp4a.com","session_id":"9DE744","protocol_type":2,
	//         "protocol_sub_type":200,"protocol_flag":4294967295
	//     }
	// }

	AssistMessage msg_req;

	Json::CharReaderBuilder jrb;
	std::unique_ptr<Json::CharReader> const js_reader(jrb.newCharReader());
	const char* str_json_begin = message.c_str();

	Json::Value js_root;
	ex_astr err;
	if (!js_reader->parse(str_json_begin, str_json_begin + message.length(), &js_root, &err))
	{
		_create_response(buf, msg_req, TPE_JSON_FORMAT);
		return;
	}
	if (!js_root.isObject())
	{
		_create_response(buf, msg_req, TPE_PARAM);
		return;
	}

	if (js_root["type"].isNull() || !js_root["type"].isInt())
	{
		_create_response(buf, msg_req, TPE_PARAM);
		return;
	}

	int cmd_type = js_root["type"].asInt();
	if (!(cmd_type == MESSAGE_TYPE_REQUEST || cmd_type == MESSAGE_TYPE_RESPONSE))
	{
		_create_response(buf, msg_req, TPE_PARAM);
		return;
	}

	// 收到的信息已经是“返回值”了，说明已经是一条命令的结束了，不用继续处理
	// todo: 可能需要记录日志，或者展示结果。
	//if (cmd_type == MESSAGE_TYPE_RESPONSE)
	//{
	//	char msg[129] = { 0 };
	//	_snprintf_s(msg, 128, "%d  %d", cmd_type, MESSAGE_TYPE_RESPONSE);
	//	MessageBoxA(NULL, msg, "INFO", MB_OK);
	//	return;
	//}

	if (js_root["method"].isNull() || !js_root["method"].isString() || js_root["command_id"].isNull() || !js_root["command_id"].isInt())
	{
		_create_response(buf, msg_req, TPE_PARAM);
		return;
	}

	msg_req.command_id = js_root["command_id"].asInt();
	msg_req.method = js_root["method"].asString();

	if (msg_req.command_id == 0 || msg_req.method.empty())
	{
		_create_response(buf, msg_req, TPE_PARAM);
		return;
	}

	if (msg_req.method == "run")
	{
		_rpc_func_run_client(buf, msg_req, js_root);
	}
	else if (msg_req.method == "replay_rdp")
	{
		_rpc_func_replay_rdp(buf, msg_req, js_root);
	}
	else if (msg_req.method == "get_config")
	{
		_rpc_func_get_config(buf, msg_req, js_root);
	}
	else if (msg_req.method == "set_config")
	{
		_rpc_func_set_config(buf, msg_req, js_root);
	}
	else if (msg_req.method == "select_file")
	{
		_rpc_func_select_file(buf, msg_req, js_root);
	}
	else
	{
		EXLOGE("[ws] got unknown command: %s\n", msg_req.method.c_str());
		_create_response(buf, msg_req, TPE_UNKNOWN_CMD);
	}
}

void TsWsClient::_rpc_func_get_config(ex_astr& buf, AssistMessage& msg_req, Json::Value& js_root)
{
	Json::Value& ret = g_cfg.get_root();
	ret["os_type"] = "windows";

	_create_response(buf, msg_req, TPE_OK, L"", ret);
}

void TsWsClient::_rpc_func_set_config(ex_astr& buf, AssistMessage& msg_req, Json::Value& js_root)
{
	if (js_root["param"].isNull() || !js_root["param"].isObject())
	{
		_create_response(buf, msg_req, TPE_PARAM);
		return;
	}
	Json::Value& js_param = js_root["param"];

	Json::StreamWriterBuilder jwb;
	std::unique_ptr<Json::StreamWriter> js_writer(jwb.newStreamWriter());
	ex_aoss os;
	js_writer->write(js_param, &os);

	if (!g_cfg.save(os.str()))
		_create_response(buf, msg_req, TPE_FAILED);
	else
		_create_response(buf, msg_req, TPE_OK);
}

void TsWsClient::_rpc_func_select_file(ex_astr& buf, AssistMessage& msg_req, Json::Value& js_root)
{
	// _create_response(buf, msg_req, TPE_FAILED, L"尚不支持在macOS平台选择应用，请手动填写应用程序路径！");
	// _create_response(buf, msg_req, TPE_FAILED, L"尚不支持选择应用，请手动填写应用程序路径！");

	if (js_root["param"].isNull() || !js_root["param"].isObject() || js_root["param"]["app_type"].isNull())
	{
		_create_response(buf, msg_req, TPE_PARAM);
		return;
	}
	// Json::Value& js_param = js_root["param"];

	HWND hParent = GetForegroundWindow();
	if (NULL == hParent)
		hParent = NULL;


	BOOL ret = FALSE;
	wchar_t wszReturnPath[MAX_PATH] = _T("");

	OPENFILENAME ofn;
	ex_wstr wsDefaultName;
	ex_wstr wsDefaultPath;
	StringCchCopy(wszReturnPath, MAX_PATH, wsDefaultName.c_str());

	ZeroMemory(&ofn, sizeof(ofn));

	ofn.lStructSize = sizeof(ofn);
	ofn.lpstrTitle = NULL;// L"Select application execute file";
	ofn.hwndOwner = hParent;
	ofn.lpstrFilter = L"Execute file (*.exe)\0*.exe\0";
	ofn.lpstrFile = wszReturnPath;
	ofn.nMaxFile = MAX_PATH;
	ofn.lpstrInitialDir = wsDefaultPath.c_str();
	ofn.Flags = OFN_EXPLORER | OFN_PATHMUSTEXIST;
	ofn.Flags |= OFN_FILEMUSTEXIST;

	ret = GetOpenFileNameW(&ofn);

	if (!ret)
	{
		_create_response(buf, msg_req, TPE_FAILED, L"用户取消了选择操作!");
		return;
	}

	ex_astr utf8_path;
	ex_wstr2astr(wszReturnPath, utf8_path, EX_CODEPAGE_UTF8);

	Json::Value js_ret;
	js_ret["app_type"] = js_root["param"]["app_type"];
	js_ret["app_path"] = utf8_path;

	_create_response(buf, msg_req, TPE_OK, L"", js_ret);
}

void TsWsClient::_rpc_func_replay_rdp(ex_astr& buf, AssistMessage& msg_req, Json::Value& js_root)
{
	// {
	//     "method":"replay_rdp",
	//     "param":{
	//         "rid":1234,
	//         "web":"http://127.0.0.1:7190",
	//         "sid":"tp_1622707094_1c8e4fd4006c6ad5"
	//     }
	// }

	if (js_root["param"].isNull() || !js_root["param"].isObject())
	{
		_create_response(buf, msg_req, TPE_PARAM);
		return;
	}
	Json::Value& js_param = js_root["param"];

	// check param
	if (!js_param["rid"].isNumeric()
		|| !js_param["web"].isString()
		|| !js_param["sid"].isString()
		)
	{
		_create_response(buf, msg_req, TPE_PARAM);
		return;
	}

	ex_astrs s_argv;

	ex_wstr w_exec_file = g_env.m_exec_path;
	ex_path_join(w_exec_file, false, L"tp-player.exe", nullptr);

	int rid = js_param["rid"].asInt();
	ex_astr a_url_base = js_param["web"].asCString();
	ex_astr a_sid = js_param["sid"].asCString();

	char cmd_args[1024] = { 0 };
	ex_strformat(cmd_args, 1023, "%s/%s/%d", a_url_base.c_str(), a_sid.c_str(), rid);

	ex_wstr w_cmd_args;
	ex_astr2wstr(cmd_args, w_cmd_args);

	// char total_cmd[1024] = { 0 };
	// ex_strformat(total_cmd, 1023, "%s %s", exec_file.c_str(), cmd_args);

	wchar_t cmd[1024] = { 0 };
	ex_wcsformat(cmd, 1023, L"%s %s", w_exec_file.c_str(), w_cmd_args.c_str());

	ex_astr total_cmd;
	ex_wstr2astr(cmd, total_cmd);

	Json::Value js_ret;

	ex_astr utf8_path;
	//ex_wstr2astr(total_cmd, utf8_path, EX_CODEPAGE_UTF8);
	js_ret["cmdline"] = total_cmd;

	// EXLOGD(utf8_path.c_str());

	STARTUPINFO si;
	PROCESS_INFORMATION pi;

	ZeroMemory(&si, sizeof(si));
	si.cb = sizeof(si);
	ZeroMemory(&pi, sizeof(pi));

	if (!CreateProcess(NULL, cmd, NULL, NULL, FALSE, 0, NULL, NULL, &si, &pi)) {
		EXLOGE(_T("CreateProcess() failed. Error=0x%08X.\n  %s\n"), GetLastError(), cmd);
		_create_response(buf, msg_req, TPE_START_CLIENT);
		return;
	}

	_create_response(buf, msg_req, TPE_OK, L"", js_ret);
}

void TsWsClient::_rpc_func_run_client(ex_astr& buf, AssistMessage& msg_req, Json::Value& js_root) {
	// {
	//     "method":"run",
	//     "param":{
	//         "teleport_ip":"127.0.0.1","teleport_port":52189,"remote_host_ip":"39.97.125.170",
	//         "remote_host_name":"tp4a.com","session_id":"9DE744","protocol_type":2,
	//         "protocol_sub_type":200,"protocol_flag":4294967295
	//     }
	// }

	// 判断参数是否正确
	if (js_root["param"].isNull() || !js_root["param"].isObject())
	{
		_create_response(buf, msg_req, TPE_PARAM);
		return;
	}
	Json::Value& js_param = js_root["param"];

	if (!js_param["teleport_ip"].isString()
		|| !js_param["teleport_port"].isNumeric() || !js_param["remote_host_ip"].isString()
		|| !js_param["session_id"].isString() || !js_param["protocol_type"].isNumeric() || !js_param["protocol_sub_type"].isNumeric()
		|| !js_param["protocol_flag"].isNumeric()
		)
	{
		_create_response(buf, msg_req, TPE_PARAM);
		return;
	}

	int pro_type = js_param["protocol_type"].asUInt();
	int pro_sub = js_param["protocol_sub_type"].asInt();
	ex_u32 protocol_flag = js_param["protocol_flag"].asUInt();

	ex_astr teleport_ip = js_param["teleport_ip"].asCString();
	int teleport_port = js_param["teleport_port"].asUInt();

	ex_astr real_host_ip = js_param["remote_host_ip"].asCString();
	ex_astr remote_host_name = js_param["remote_host_name"].asCString();
	ex_astr sid = js_param["session_id"].asCString();

	ex_wstr w_exe_path;
	WCHAR w_szCommandLine[MAX_PATH] = { 0 };


	ex_wstr w_sid;
	ex_astr2wstr(sid, w_sid);
	ex_wstr w_teleport_ip;
	ex_astr2wstr(teleport_ip, w_teleport_ip);
	ex_wstr w_real_host_ip;
	ex_astr2wstr(real_host_ip, w_real_host_ip);
	ex_wstr w_remote_host_name;
	ex_astr2wstr(remote_host_name, w_remote_host_name);
	WCHAR w_port[32] = { 0 };
	swprintf_s(w_port, _T("%d"), teleport_port);

	ex_wstr tmp_rdp_file; // for .rdp file

	if (pro_type == TP_PROTOCOL_TYPE_RDP) {
		//==============================================
		// RDP
		//==============================================

		bool flag_clipboard = ((protocol_flag & TP_FLAG_RDP_CLIPBOARD) == TP_FLAG_RDP_CLIPBOARD);
		bool flag_disk = ((protocol_flag & TP_FLAG_RDP_DISK) == TP_FLAG_RDP_DISK);
		bool flag_console = ((protocol_flag & TP_FLAG_RDP_CONSOLE) == TP_FLAG_RDP_CONSOLE);

		int rdp_w = 800;
		int rdp_h = 640;
		bool rdp_console = false;

		if (!js_param["rdp_width"].isNull()) {
			if (js_param["rdp_width"].isNumeric()) {
				rdp_w = js_param["rdp_width"].asUInt();
			}
			else {
				_create_response(buf, msg_req, TPE_PARAM);
				return;
			}
		}

		if (!js_param["rdp_height"].isNull()) {
			if (js_param["rdp_height"].isNumeric()) {
				rdp_h = js_param["rdp_height"].asUInt();
			}
			else {
				_create_response(buf, msg_req, TPE_PARAM);
				return;
			}
		}

		if (!js_param["rdp_console"].isNull()) {
			if (js_param["rdp_console"].isBool()) {
				rdp_console = js_param["rdp_console"].asBool();
			}
			else {
				_create_response(buf, msg_req, TPE_PARAM);
				return;
			}
		}

		if (!flag_console)
			rdp_console = false;


		int split_pos = sid.length() - 2;
		ex_astr real_sid = sid.substr(0, split_pos);
		ex_astr str_pwd_len = sid.substr(split_pos, sid.length());
		int n_pwd_len = strtol(str_pwd_len.c_str(), nullptr, 16);
		n_pwd_len -= real_sid.length();
		n_pwd_len -= 2;
		char szPwd[256] = { 0 };
		for (int i = 0; i < n_pwd_len; i++) {
			szPwd[i] = '*';
		}

		ex_astr2wstr(real_sid, w_sid);

		w_exe_path = _T("\"");
		w_exe_path += g_cfg.rdp.application + _T("\" ");

		ex_wstr rdp_name = g_cfg.rdp.name;
		if (rdp_name == L"mstsc") {
			w_exe_path += g_cfg.rdp.cmdline;

			int width = 0;
			int higth = 0;
			int cx = 0;
			int cy = 0;

			int display = 1;
			int iWidth = GetSystemMetrics(SM_CXSCREEN);
			int iHeight = GetSystemMetrics(SM_CYSCREEN);

			if (rdp_w == 0 || rdp_h == 0) {
				//全屏
				width = iWidth;
				higth = iHeight;
				display = 2;
			}
			else {
				width = rdp_w;
				higth = rdp_h;
				display = 1;
			}

			cx = (iWidth - width) / 2;
			cy = (iHeight - higth) / 2;
			if (cx < 0) {
				cx = 0;
			}
			if (cy < 0) {
				cy = 0;
			}

			// 			int console_mode = 0;
			// 			if (rdp_console)
			// 				console_mode = 1;

			std::string psw51b;
			if (!calc_psw51b(szPwd, psw51b)) {
				EXLOGE("calc password failed.\n");
				_create_response(buf, msg_req, TPE_PARAM);
				return;
			}

			real_sid = "01" + real_sid;

			char sz_rdp_file_content[4096] = { 0 };
			sprintf_s(sz_rdp_file_content, 4096, rdp_content.c_str()
				, (flag_console && rdp_console) ? 1 : 0
				, display, width, higth
				, cx, cy, cx + width + 100, cy + higth + 100
				, teleport_ip.c_str(), teleport_port
				, flag_clipboard ? 1 : 0
				, flag_disk ? "*" : ""
				, real_sid.c_str()
				, psw51b.c_str()
			);

			char sz_file_name[MAX_PATH] = { 0 };
			char temp_path[MAX_PATH] = { 0 };
			DWORD ret = GetTempPathA(MAX_PATH, temp_path);
			if (ret <= 0) {
				EXLOGE("fopen failed (%d).\n", GetLastError());
				_create_response(buf, msg_req, TPE_FAILED);
				return;
			}

			ex_astr temp_host_ip = real_host_ip;
			ex_replace_all(temp_host_ip, ".", "-");

			sprintf_s(sz_file_name, MAX_PATH, ("%s%s.rdp"), temp_path, temp_host_ip.c_str());

			FILE* f = NULL;
			if (fopen_s(&f, sz_file_name, "wt") != 0) {
				EXLOGE("fopen failed (%d).\n", GetLastError());
				_create_response(buf, msg_req, TPE_OPENFILE);
				return;
			}
			// Write a string into the file.
			fwrite(sz_rdp_file_content, strlen(sz_rdp_file_content), 1, f);
			fclose(f);
			ex_astr2wstr(sz_file_name, tmp_rdp_file);

			// 变量替换
			ex_replace_all(w_exe_path, _T("{tmp_rdp_file}"), tmp_rdp_file);
		}
		else if (g_cfg.rdp.name == L"freerdp") {
			w_exe_path += L"{size} {console} {clipboard} {drives} ";
			w_exe_path += g_cfg.rdp.cmdline;

			ex_wstr w_screen;

			if (rdp_w == 0 || rdp_h == 0) {
				//全屏
				w_screen = _T("/f");
			}
			else {
				char sz_size[64] = { 0 };
				ex_strformat(sz_size, 63, "/size:%dx%d", rdp_w, rdp_h);
				ex_astr2wstr(sz_size, w_screen);
			}

			// 			wchar_t* w_console = NULL;
			// 
			// 			if (flag_console && rdp_console)
			// 			{
			// 				w_console = L"/admin";
			// 			}
			// 			else
			// 			{
			// 				w_console = L"";
			// 			}

			ex_wstr w_password;
			ex_astr2wstr(szPwd, w_password);
			w_exe_path += L" /p:";
			w_exe_path += w_password;

			w_sid = L"02" + w_sid;

			w_exe_path += L" /gdi:sw"; // 使用软件渲染，gdi:hw使用硬件加速，但是会出现很多黑块（录像回放时又是正常的！）
			w_exe_path += L" -grab-keyboard"; // [new style] 防止启动FreeRDP后，失去本地键盘响应，必须得先最小化一下FreeRDP窗口（不过貌似不起作用）

			// 变量替换
			ex_replace_all(w_exe_path, _T("{size}"), w_screen);

			if (flag_console && rdp_console)
				ex_replace_all(w_exe_path, _T("{console}"), L"/admin");
			else
				ex_replace_all(w_exe_path, _T("{console}"), L"");

			//ex_replace_all(w_exe_path, _T("{clipboard}"), L"+clipboard");

			if (flag_clipboard)
				ex_replace_all(w_exe_path, _T("{clipboard}"), L"/clipboard");
			else
				ex_replace_all(w_exe_path, _T("{clipboard}"), L"-clipboard");

			if (flag_disk)
				ex_replace_all(w_exe_path, _T("{drives}"), L"/drives");
			else
				ex_replace_all(w_exe_path, _T("{drives}"), L"-drives");
		}
		else {
			_create_response(buf, msg_req, TPE_FAILED);
			return;
		}
	}
	else if (pro_type == TP_PROTOCOL_TYPE_SSH) {
		//==============================================
		// SSH
		//==============================================

		if (pro_sub == TP_PROTOCOL_TYPE_SSH_SHELL) {
			w_exe_path = _T("\"");
			w_exe_path += g_cfg.ssh.application + _T("\" ");
			w_exe_path += g_cfg.ssh.cmdline;
		}
		else {
			w_exe_path = _T("\"");
			w_exe_path += g_cfg.sftp.application + _T("\" ");
			w_exe_path += g_cfg.sftp.cmdline;
		}
	}
	else if (pro_type == TP_PROTOCOL_TYPE_TELNET) {
		//==============================================
		// TELNET
		//==============================================
		w_exe_path = _T("\"");
		w_exe_path += g_cfg.telnet.application + _T("\" ");
		w_exe_path += g_cfg.telnet.cmdline;
	}

	ex_replace_all(w_exe_path, _T("{host_ip}"), w_teleport_ip.c_str());
	ex_replace_all(w_exe_path, _T("{host_port}"), w_port);
	ex_replace_all(w_exe_path, _T("{user_name}"), w_sid.c_str());
	ex_replace_all(w_exe_path, _T("{host_name}"), w_remote_host_name.c_str());
	ex_replace_all(w_exe_path, _T("{real_ip}"), w_real_host_ip.c_str());
	ex_replace_all(w_exe_path, _T("{assist_tools_path}"), g_env.m_tools_path.c_str());


	STARTUPINFO si;
	PROCESS_INFORMATION pi;

	ZeroMemory(&si, sizeof(si));
	si.cb = sizeof(si);
	ZeroMemory(&pi, sizeof(pi));

	Json::Value js_data;
	ex_astr utf8_path;
	ex_wstr2astr(w_exe_path, utf8_path, EX_CODEPAGE_UTF8);
	js_data["path"] = utf8_path;

	if (!CreateProcess(NULL, (wchar_t*)w_exe_path.c_str(), NULL, NULL, FALSE, 0, NULL, NULL, &si, &pi)) {
		EXLOGE(_T("CreateProcess() failed. Error=0x%08X.\n  %s\n"), GetLastError(), w_exe_path.c_str());
		_create_response(buf, msg_req, TPE_START_CLIENT);
		return;
	}

	_create_response(buf, msg_req, TPE_OK, L"", js_data);
}
