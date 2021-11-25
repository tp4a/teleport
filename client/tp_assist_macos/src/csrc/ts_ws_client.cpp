#include <unistd.h>

#include <teleport_const.h>

#ifndef MAX_PATH
#    define MAX_PATH 1024
#endif

#include "../AppDelegate-C-Interface.h"

#include "ts_ws_client.h"
#include "ts_ver.h"
#include "ts_env.h"
#include "ts_cfg.h"
#include "ts_utils.h"

TsWsClient g_ws_client;
TsWsClient g_wss_client;

void* g_app = NULL;

// static
void TsWsClient::init_app(void* app)
{
    g_app = app;
}

void TsWsClient::stop_all_client()
{
    g_ws_client.stop();
    g_wss_client.stop();
}

// ============================================================================
// static
void TsWsClient::url_scheme_handler(const std::string& url)
{
    // url: teleport://register?param={"ws_url":"ws://127.0.0.1:7190/ws/assist/","assist_id":1234,"session_id":"tp_5678"}

    std::string protocol;
    std::string method;
    std::string param;

    std::string::size_type pos_protocol = url.find("://");
    if (pos_protocol == std::string::npos)
    {
        EXLOGE("[ws] invalid url: %s\n", url.c_str());
        return;
    }

    std::string::size_type pos_method = url.find('?');
    if (pos_method == std::string::npos)
    {
        EXLOGE("[ws] invalid url: %s\n", url.c_str());
        return;
    }

    protocol.assign(url, 0, pos_protocol);
    if (protocol != "teleport")
    {
        EXLOGE("[ws] invalid protocol: %s\n", protocol.c_str());
        return;
    }

    // now we support 'register' method only.
    method.assign(url, pos_protocol + 3, pos_method - pos_protocol - 3);
    if (method != "register")
    {
        EXLOGE("[ws] unknown method: %s\n", method.c_str());
        return;
    }

    param.assign(url, pos_method + 7);  // ?param=
    if (param.empty())
    {
        EXLOGE("[ws] invalid protocol: %s\n", protocol.c_str());
        return;
    }


    // decode param with url-decode.
    size_t len = param.length() * 2;
    ex_chars sztmp;
    sztmp.resize(len);
    memset(&sztmp[0], 0, len);
    if (-1 == ts_url_decode(param.c_str(), (int)param.length(), &sztmp[0], (int)len, 0))
    {
        EXLOGE("[ws] url-decode param failed: %s\n", param.c_str());
        return;
    }
    param = &sztmp[0];

    EXLOGV("[rpc] method=%s, json_param=%s\n", method.c_str(), param.c_str());

    Json::CharReaderBuilder jcrb;
    std::unique_ptr<Json::CharReader> const jreader(jcrb.newCharReader());
    const char* str_json_begin = param.c_str();

    Json::Value js_root;
    ex_astr err;
    if (!jreader->parse(str_json_begin, str_json_begin + param.length(), &js_root, &err))
    {
        EXLOGE("[ws] param not in json format: %s\n", param.c_str());
        return;
    }
    if (!js_root.isObject())
    {
        EXLOGE("[ws] invalid param, need json object: %s\n", param.c_str());
        return;
    }

    // now we support 'register' method only.
    _process_register(param, js_root);
}

// static
void TsWsClient::_process_register(const std::string& param, Json::Value& js_root)
{
    // {"ws_url":"ws://127.0.0.1:7190/ws/assist/","assist_id":1234,"session_id":"tp_5678"}

    // check param
    if (!js_root["ws_url"].isString() || !js_root["assist_id"].isNumeric() || !js_root["session_id"].isString())
    {
        EXLOGE("[ws] invalid param: %s\n", param.c_str());
        return;
    }

    std::string ws_url = js_root["ws_url"].asCString();
    uint32_t assist_id = js_root["assist_id"].asUInt();
    std::string session_id = js_root["session_id"].asCString();

    std::string protocol;
    protocol.assign(ws_url, 0, 3);
    if (protocol == "ws:")
    {
        g_ws_client._register(ws_url, assist_id, session_id);
    }
    else if (protocol == "wss")
    {
        g_wss_client._register(ws_url, assist_id, session_id);
    }
    else
    {
        EXLOGE("[ws] invalid ws_url: %s\n", ws_url.c_str());
        return;
    }
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

void TsWsClient::_register(const std::string& ws_url, uint32_t assist_id, const std::string& session_id)
{
    if (m_assist_id == 0)
        m_assist_id = assist_id;

    ex_wstr w_ver(TP_ASSIST_VER);
    ex_astr a_ver;
    ex_wstr2astr(w_ver, a_ver);

    //
    char msg[256] = {0};
    ex_strformat(
            msg, 256, "{\"type\":0,\"method\":\"register\",\"param\":{\"client\":\"assist\",\"sid\":\"%s\",\"request_assist_id\":%u,\"assist_id\":%u,\"assist_ver\":\"%s\"}}",
            session_id.c_str(), assist_id, m_assist_id, a_ver.c_str());

    if (!m_is_running)
    {
        // not start yet.
        std::string url = ws_url;
        url += msg;

        m_nc = mg_connect_ws(&m_mg_mgr, _mg_event_handler, url.c_str(), NULL, NULL);
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
        //            EXLOGV("%d: %s\n", wm->size, wm->data);
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
    _create_response(buf, msg_ret, err_code, "", js_data);
}

void TsWsClient::_create_response(ex_astr& buf, const AssistMessage& msg_ret, int err_code, const std::string& message)
{
    Json::Value js_data(Json::objectValue);
    _create_response(buf, msg_ret, err_code, message, js_data);
}

void TsWsClient::_create_response(ex_astr& buf, const AssistMessage& msg_ret, int err_code, const std::string& message, Json::Value& data)
{
    Json::Value js_ret;
    js_ret["type"] = MESSAGE_TYPE_RESPONSE;
    js_ret["command_id"] = msg_ret.command_id;
    js_ret["method"] = msg_ret.method;
    js_ret["code"] = err_code;
    js_ret["message"] = message;
    js_ret["data"] = data;

    Json::StreamWriterBuilder jwb;
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
    if (cmd_type == MESSAGE_TYPE_RESPONSE)
        return;

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
    else if(msg_req.method == "get_config")
    {
        _rpc_func_get_config(buf, msg_req, js_root);
    }
    else if(msg_req.method == "set_config")
    {
        _rpc_func_set_config(buf, msg_req, js_root);
    }
    else if(msg_req.method == "select_file")
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
    if(ret["os_type"].isNull())
        ret["os_type"] = "macos";

    _create_response(buf, msg_req, TPE_OK, "", ret);
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
    // AppDelegate_select_app(g_app);
    _create_response(buf, msg_req, TPE_FAILED, "尚不支持在macOS平台选择应用，请手动填写应用程序路径！");
}

void TsWsClient::_rpc_func_run_client(ex_astr& buf, AssistMessage& msg_req, Json::Value& js_root)
{
    // {
    //     "method":"run",
    //     "param":{
    //         "teleport_ip":"127.0.0.1","teleport_port":52189,"remote_host_ip":"39.97.125.170",
    //         "remote_host_name":"tp4a.com","session_id":"9DE744","protocol_type":2,
    //         "protocol_sub_type":200,"protocol_flag":4294967295
    //     }
    // }

    if (js_root["param"].isNull() || !js_root["param"].isObject())
    {
        _create_response(buf, msg_req, TPE_PARAM);
        return;
    }
    Json::Value& js_param = js_root["param"];

    // check param
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
    char _port[64] = {0};
    ex_strformat(_port, 64, "%d", teleport_port);
    ex_astr str_teleport_port = _port;

    ex_astr real_host_ip = js_param["remote_host_ip"].asCString();
    ex_astr real_host_name = js_param["remote_host_name"].asCString();
    ex_astr sid = js_param["session_id"].asCString();


    ex_astr s_exec;
    ex_astr s_arg;
    ex_astrs s_argv;


    if (pro_type == TP_PROTOCOL_TYPE_RDP)
    {
        //==============================================
        // RDP
        //==============================================

        if (g_cfg.rdp.application.length() == 0)
        {
            _create_response(buf, msg_req, TPE_NOT_EXISTS, "助手未配置本地RDP客户端，请检查您的助手设置。");
            return;
        }

        if (!ex_is_file_exists(g_cfg.rdp.application.c_str()))
        {
            _create_response(buf, msg_req, TPE_NOT_EXISTS, "无法定位助手配置的RDP客户端，请检查您的助手设置。");
            return;
        }

        bool flag_clipboard = ((protocol_flag & TP_FLAG_RDP_CLIPBOARD) == TP_FLAG_RDP_CLIPBOARD);
        bool flag_disk = ((protocol_flag & TP_FLAG_RDP_DISK) == TP_FLAG_RDP_DISK);
        bool flag_console = ((protocol_flag & TP_FLAG_RDP_CONSOLE) == TP_FLAG_RDP_CONSOLE);

        int rdp_w = 800;
        int rdp_h = 640;
        bool rdp_console = false;

        if (!js_param["rdp_width"].isNull())
        {
            if (js_param["rdp_width"].isNumeric())
            {
                rdp_w = js_param["rdp_width"].asUInt();
            }
            else
            {
                _create_response(buf, msg_req, TPE_PARAM);
                return;
            }
        }

        if (!js_param["rdp_height"].isNull())
        {
            if (js_param["rdp_height"].isNumeric())
            {
                rdp_h = js_param["rdp_height"].asUInt();
            }
            else
            {
                _create_response(buf, msg_req, TPE_PARAM);
                return;
            }
        }

        if (!js_param["rdp_console"].isNull())
        {
            if (js_param["rdp_console"].isBool())
            {
                rdp_console = js_param["rdp_console"].asBool();
            }
            else
            {
                _create_response(buf, msg_req, TPE_PARAM);
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
        char szPwd[256] = {0};
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
        s_arg = g_cfg.rdp.cmdline;

        sid = "02" + real_sid;
        //        s_argv.push_back("/f");

        s_argv.push_back("/sec:tls");
        s_argv.push_back("-wallpaper");
        s_argv.push_back("-themes");
        // Ignore certificate
        s_argv.push_back("/cert-ignore");
        // Automatically accept certificate on first connect
        s_argv.push_back("/cert-tofu");

        ex_astr _tmp_pass = "/p:PLACEHOLDER";
        //_tmp_pass += szPwd;
        s_argv.push_back(_tmp_pass);

        //#if 0
        //s_argv.push_back(s_exec.c_str());

        {
            //            ex_astr username = "02" + real_sid;
            //            s_argv.push_back("/u:");
            //            s_argv.push_back(username.c_str());


            if (rdp_w == 0 || rdp_h == 0)
            {
                s_argv.push_back("/f");
            }
            else
            {
                //                char sz_size[64] = {0};
                //                ex_strformat(sz_size, 63, "%dx%d", rdp_w, rdp_h);
                //                s_argv.push_back("-g");
                //                s_argv.push_back(sz_size);
                char sz_width[64] = {0};
                ex_strformat(sz_width, 63, "/w:%d", rdp_w);
                s_argv.push_back(sz_width);

                char sz_height[64] = {0};
                ex_strformat(sz_height, 63, "/h:%d", rdp_h);
                s_argv.push_back(sz_height);
            }

            if (flag_console && rdp_console)
                s_argv.push_back("/admin");

            //            if(flag_clipboard)
            //                s_argv.push_back("+clipboard");
            //            else
            //                s_argv.push_back("-clipboard");

            //            if(flag_disk)
            //                s_argv.push_back("+drives");
            //            else
            //                s_argv.push_back("-drives");
            //
            //            {
            //                char sz_temp[128] = {0};
            //                ex_strformat(sz_temp, 127, "%s:%d", teleport_ip.c_str(), teleport_port);
            //                s_argv.push_back(sz_temp);
            //            }
        }
        //#endif
    }
    else if (pro_type == TP_PROTOCOL_TYPE_SSH)
    {
        //==============================================
        // SSH
        //==============================================

        if (pro_sub == TP_PROTOCOL_TYPE_SSH_SHELL)
        {
            if (g_cfg.ssh.name == "terminal" || g_cfg.ssh.name == "iterm2")
            {
                char szCmd[1024] = {0};
                ex_strformat(szCmd, 1023, "ssh %s@%s -p %d -o \"StrictHostKeyChecking no\"", sid.c_str(), teleport_ip.c_str(), teleport_port);

                char szTitle[128] = {0};
                ex_strformat(szTitle, 127, "TP#%s", real_host_ip.c_str());

                int ret = AppDelegate_start_ssh_client(g_app, szCmd, g_cfg.ssh.name.c_str(), g_cfg.ssh.cmdline.c_str(), szTitle);
                if (ret == 0)
                    _create_response(buf, msg_req, TPE_OK);
                else
                    _create_response(buf, msg_req, TPE_FAILED);
                return;
            }

            if (g_cfg.ssh.application.length() == 0)
            {
                _create_response(buf, msg_req, TPE_NOT_EXISTS);
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

            if (g_cfg.sftp.application.length() == 0)
            {
                _create_response(buf, msg_req, TPE_NOT_EXISTS);
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
        //        _create_json_ret(buf, TPE_NOT_IMPLEMENT);
        //        return;

        g_cfg.telnet.name = "iterm2";

        if (g_cfg.telnet.name == "terminal" || g_cfg.telnet.name == "iterm2")
        {
            char szCmd[1024] = {0};
            ex_strformat(szCmd, 1023, "telnet -l %s %s %d", sid.c_str(), teleport_ip.c_str(), teleport_port);

            char szTitle[128] = {0};
            ex_strformat(szTitle, 127, "TP#%s", real_host_ip.c_str());

            int ret = AppDelegate_start_ssh_client(g_app, szCmd, g_cfg.telnet.name.c_str(), g_cfg.telnet.cmdline.c_str(), szTitle);
            if (ret == 0)
                _create_response(buf, msg_req, TPE_OK);
            else
                _create_response(buf, msg_req, TPE_FAILED);
            return;
        }

        if (g_cfg.telnet.application.length() == 0)
        {
            _create_response(buf, msg_req, TPE_NOT_EXISTS);
            return;
        }

        s_exec = g_cfg.telnet.application;
        s_argv.push_back(s_exec.c_str());

        s_arg = g_cfg.telnet.cmdline;
    }


    //---- split s_arg and push to s_argv ---
    ex_astr::size_type p1 = 0;
    ex_astr::size_type p2 = 0;
    ex_astr tmp = s_arg;
    for (;;)
    {
        ex_remove_white_space(tmp, EX_RSC_BEGIN);
        if (tmp.empty())
        {
            break;
        }

        if (tmp[0] == '"')
        {
            p1 = 1;
            p2 = tmp.find('"', p1);

            if (p2 == ex_astr::npos)
            {
                _create_response(buf, msg_req, TPE_PARAM);
                return;
            }

            ex_astr _t;
            _t.assign(tmp, p1, p2 - p1);
            tmp.erase(0, p2 + 2);

            s_argv.push_back(_t);
        }
        else
        {
            p1 = 0;
            p2 = tmp.find(' ', p1);

            if (p2 == ex_astr::npos)
            {
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


    Json::Value js_data;
    ex_astr utf8_path = s_exec;

    ex_astrs::iterator it = s_argv.begin();
    for (; it != s_argv.end(); ++it)
    {
        ex_replace_all((*it), "{host_port}", str_teleport_port);
        ex_replace_all((*it), "{host_ip}", teleport_ip);
        ex_replace_all((*it), "{user_name}", sid);
        ex_replace_all((*it), "{real_ip}", real_host_ip);
        ex_replace_all((*it), "{host_name}", real_host_name);
        //ex_replace_all(utf8_path, _T("{assist_tools_path}"), g_env.m_tools_path.c_str());

        utf8_path += " ";
        utf8_path += (*it);
    }

    js_data["path"] = utf8_path;

    // for macOS, Create Process should be fork()/exec()...
    pid_t processId;
    if ((processId = fork()) == 0)
    {

        int i = 0;
        char** _argv = (char**)calloc(s_argv.size() + 1, sizeof(char*));
        if (!_argv)
            return;

        for (i = 0; i < s_argv.size(); ++i)
        {
            _argv[i] = ex_strdup(s_argv[i].c_str());
        }
        _argv[i] = NULL;

        execv(s_exec.c_str(), _argv);

        for (i = 0; i < s_argv.size(); ++i)
        {
            if (_argv[i] != NULL)
            {
                free(_argv[i]);
            }
        }
        free(_argv);
    }
    else if (processId < 0)
    {
        _create_response(buf, msg_req, TPE_FAILED);
    }
    else
    {
        _create_response(buf, msg_req, TPE_OK, "", js_data);
    }
}
