#include "ssh_session.h"
#include "ssh_proxy.h"
#include "tpp_env.h"

#include <algorithm>
#include <teleport_const.h>

SshSession::SshSession(SshProxy* proxy, ssh_session rs_tp2cli, uint32_t dbg_id, const char* client_ip, uint16_t client_port) :
        ExThreadBase("ssh-session-thread"),
        m_proxy(proxy),
        m_state(SSH_SESSION_STATE_STARTING),
        m_rs_tp2cli(rs_tp2cli),
        m_rs_tp2srv(nullptr),
        m_dbg_id(dbg_id),
        m_conn_info(nullptr),
        m_conn_port(0),
        m_flags(0),
        m_auth_type(TP_AUTH_TYPE_NONE),
        m_client_ip(client_ip),
        m_client_port(client_port)
// , m_allow_user_input_password(false)
{
    ex_strformat(m_dbg_name, 128, "ssh-%d", dbg_id);
    ex_strformat(m_dbg_client, 128, "%s:%d", client_ip, client_port);

    m_first_auth = true;
    m_auth_passed = false;
    m_fault = false;
    m_need_send_keepalive = false;

    m_pair_id = 0;

    memset(&m_srv_cb, 0, sizeof(m_srv_cb));
    ssh_callbacks_init(&m_srv_cb)
    m_srv_cb.userdata = this;

    memset(&m_cli_channel_cb, 0, sizeof(m_cli_channel_cb));
    ssh_callbacks_init(&m_cli_channel_cb)
    m_cli_channel_cb.userdata = this;

    memset(&m_srv_channel_cb, 0, sizeof(m_srv_channel_cb));
    ssh_callbacks_init(&m_srv_channel_cb)
    m_srv_channel_cb.userdata = this;
}

SshSession::~SshSession()
{
    if (m_conn_info)
    {
#ifdef TEST_SSH_SESSION_000000
        delete m_conn_info;
#else
        g_ssh_env.free_connect_info(m_conn_info);
#endif
    }
    m_conn_info = nullptr;

    EXLOGD("[%s] session %s destroy.\n", m_dbg_name.c_str(), m_sid.c_str());
}

void SshSession::_on_stop()
{
    ExThreadBase::_on_stop();

    _close_channels();

    if (m_rs_tp2cli)
    {
        ssh_disconnect(m_rs_tp2cli);
        ssh_free(m_rs_tp2cli);
        m_rs_tp2cli = nullptr;
    }
    if (m_rs_tp2srv)
    {
        ssh_disconnect(m_rs_tp2srv);
        ssh_free(m_rs_tp2srv);
        m_rs_tp2srv = nullptr;
    }

    if (m_conn_info)
    {
        g_ssh_env.free_connect_info(m_conn_info);
        m_conn_info = nullptr;
    }
}

void SshSession::_on_stopped()
{
}

void SshSession::_set_last_error(int err_code)
{
    if (!m_auth_passed)
        return;
#ifndef TEST_SSH_SESSION_000000
    int db_id = 0;
    if (!g_ssh_env.session_begin(m_conn_info, &db_id) || db_id == 0)
    {
        EXLOGE("[%s] can not write session error to database.\n", m_dbg_name.c_str());
        return;
    }

    g_ssh_env.session_end(m_sid.c_str(), db_id, err_code);
#endif
}


void SshSession::_close_channels()
{
    ExThreadSmartLock locker(m_lock);

    for (auto& pair: m_pairs)
    {
        pair->need_close = true;
    }
}

void SshSession::check_channels()
{
    if (!(m_state == SSH_SESSION_STATE_CLOSING || m_state == SSH_SESSION_STATE_RUNNING))
        return;

    ExThreadSmartLock locker(m_lock);

    for (auto it = m_pairs.begin(); it != m_pairs.end();)
    {
        ssh_channel ch_tp2cli = (*it)->rsc_tp2cli;
        ssh_channel ch_tp2srv = (*it)->rsc_tp2srv;

        // 判断是否需要关闭通道：
        // 如果通道一侧打开过，但现在已经关闭了，则需要关闭另外一侧。
        bool need_close = (*it)->need_close;
        if (!need_close)
        {
            if (ch_tp2cli != nullptr && ssh_channel_is_closed(ch_tp2cli))
                need_close = true;
            if (ch_tp2srv != nullptr && ssh_channel_is_closed(ch_tp2srv))
                need_close = true;
        }

        if (need_close)
        {
            if (ch_tp2cli != nullptr)
            {
                if (!ssh_channel_is_closed(ch_tp2cli))
                {
                    ssh_channel_close(ch_tp2cli);
                }
                else
                {
                    auto it_map = m_channel_map.find(ch_tp2cli);
                    if (it_map != m_channel_map.end())
                        m_channel_map.erase(it_map);
                    ch_tp2cli = nullptr;
                }
            }

            if (ch_tp2srv != nullptr)
            {
                if (!ssh_channel_is_closed(ch_tp2srv))
                {
                    ssh_channel_close(ch_tp2srv);
                }
                else
                {
                    auto it_map = m_channel_map.find(ch_tp2srv);
                    if (it_map != m_channel_map.end())
                        m_channel_map.erase(it_map);
                    ch_tp2srv = nullptr;
                }
            }
        }

        if (ch_tp2cli == nullptr && ch_tp2srv == nullptr)
        {
            (*it)->record_end();
            delete (*it);
            m_pairs.erase(it++);
        }
        else
        {
            ++it;
        }
    }

    if (m_pairs.empty())
    {
        EXLOGV("[%s] all channels closed, should close and destroy this session.\n", m_dbg_name.c_str());
        // m_fault = true;
        m_state = SSH_SESSION_STATE_NO_CHANNEL;
    }
}

void SshSession::_thread_loop()
{
    m_srv_cb.auth_password_function = _on_auth_password_request;
    m_srv_cb.channel_open_request_session_function = _on_new_channel_request;

    m_srv_channel_cb.channel_data_function = _on_server_channel_data;
    m_srv_channel_cb.channel_close_function = _on_server_channel_close;

    m_cli_channel_cb.channel_data_function = _on_client_channel_data;
    m_cli_channel_cb.channel_close_function = _on_client_channel_close;
    m_cli_channel_cb.channel_pty_request_function = _on_client_pty_request;
    m_cli_channel_cb.channel_shell_request_function = _on_client_shell_request;
    m_cli_channel_cb.channel_pty_window_change_function = _on_client_pty_win_change;
    m_cli_channel_cb.channel_exec_request_function = _on_client_channel_exec_request;
    m_cli_channel_cb.channel_subsystem_request_function = _on_client_channel_subsystem_request;
    // there are some other channel callbacks not implemented yet:
    // channel_eof_function
    // channel_signal_function
    // channel_exit_status_function
    // channel_exit_signal_function
    // channel_auth_agent_req_function
    // channel_x11_req_function
    // channel_env_request_function

    ssh_set_server_callbacks(m_rs_tp2cli, &m_srv_cb);

    int err = SSH_OK;

    // 安全连接（密钥交换）
    err = ssh_handle_key_exchange(m_rs_tp2cli);
    if (err != SSH_OK)
    {
        EXLOGE("[%s] key exchange with client failed: %s\n", m_dbg_name.c_str(), ssh_get_error(m_rs_tp2cli));
        return;
    }

    // ==============================================
    // 重要：
    //   安全连接之后需要设置为非阻塞方式，否则后续在回调中
    //   转发数据等操作会导致死锁。
    // ==============================================
    ssh_set_blocking(m_rs_tp2cli, 0);

    ssh_event event_loop = ssh_event_new();
    if (!event_loop)
    {
        EXLOGE("[%s] can not create event loop.\n", m_dbg_name.c_str());
        return;
    }
    err = ssh_event_add_session(event_loop, m_rs_tp2cli);
    if (err != SSH_OK)
    {
        EXLOGE("[%s] can not add client-session into event loop.\n", m_dbg_name.c_str());
        return;
    }

    m_state = SSH_SESSION_STATE_AUTHING;

    // 认证，并打开一个通道
    do
    {
        err = ssh_event_dopoll(event_loop, 500);
        if (err == SSH_AGAIN)
        {
            continue;
        }
        else if (err != SSH_OK)
        {
            EXLOGE("[%s] error when event poll: %s\n", m_dbg_name.c_str(), ssh_get_error(m_rs_tp2cli));
            m_fault = true;
        }

        if (m_fault)
        {
            EXLOGE("[%s] error when event poll, fault.\n", m_dbg_name.c_str());
            break;
        }
    } while (!(m_state == SSH_SESSION_STATE_AUTH_END && !m_pairs.empty()));

    if (m_fault)
    {
        ssh_event_remove_session(event_loop, m_rs_tp2cli);
        ssh_event_free(event_loop);
        EXLOGE("[%s] Error, exiting loop.\n", m_dbg_name.c_str());
        return;
    }

    EXLOGW("[%s] authenticated and got a channel.\n", m_dbg_name.c_str());
    m_state = SSH_SESSION_STATE_RUNNING;

    // 现在双方的连接已经建立好了，开始转发
    if (m_rs_tp2srv)
        ssh_event_add_session(event_loop, m_rs_tp2srv);

    auto t_last_send_keepalive = static_cast<uint32_t>(time(nullptr));

    do
    {
        err = ssh_event_dopoll(event_loop, 1000);
        if (m_fault)
            break;

        if (err == SSH_OK || err == SSH_AGAIN)
        {
            auto t_now = static_cast<uint32_t>(time(nullptr));
            if (t_now - t_last_send_keepalive >= 60)
            {
                t_last_send_keepalive = t_now;
                // EXLOGD("[%s] send keepalive.\n", m_dbg_name.c_str());
                ssh_send_ignore(m_rs_tp2cli, "keepalive@openssh.com");
                ssh_send_ignore(m_rs_tp2srv, "keepalive@openssh.com");
            }

            continue;
        }

        if (err == SSH_ERROR)
        {
            if (m_rs_tp2srv)
                EXLOGW("[%s] event poll failed. [client: %s] [server: %s]\n", m_dbg_name.c_str(), ssh_get_error(m_rs_tp2cli), ssh_get_error(m_rs_tp2srv));
            else
                EXLOGW("[%s] event poll failed. [client: %s] [server: NONE]\n", m_dbg_name.c_str(), ssh_get_error(m_rs_tp2cli));
            m_fault = true;
        }
    } while (!m_pairs.empty());

    if (m_pairs.empty())
        EXLOGV("[%s] all channel in this session are closed.\n", m_dbg_name.c_str());

    ssh_event_remove_session(event_loop, m_rs_tp2cli);
    if (m_rs_tp2srv)
        ssh_event_remove_session(event_loop, m_rs_tp2srv);
    ssh_event_free(event_loop);

    // m_state = SSH_SESSION_STATE_CLOSED;

    EXLOGV("[%s] session event loop end.\n", m_dbg_name.c_str());
}

void SshSession::save_record()
{
    ExThreadSmartLock locker(m_lock);

    for (auto& pair: m_pairs)
    {
        pair->rec.save_record();
    }
}

void SshSession::check_noop_timeout(ex_u32 t_now, ex_u32 timeout)
{
    ExThreadSmartLock locker(m_lock);

    for (auto& pair: m_pairs)
    {
        if (pair->need_close)
            continue;

        bool need_close = false;

        if (t_now == 0)
        {
            EXLOGW("[%s] try close channel by kill.\n", m_dbg_name.c_str());
            need_close = true;
        }
        if (t_now - pair->last_access_timestamp > timeout)
        {
            EXLOGW("[%s] try close channel by timeout.\n", m_dbg_name.c_str());
            need_close = true;
        }

        pair->need_close = need_close;
    }
}

bool SshSession::make_channel_pair(ssh_channel ch_tp2cli, ssh_channel ch_tp2srv)
{
    if (!ch_tp2cli)
    {
        EXLOGE("[%s] can not make channel pair with null channel.\n", m_dbg_name.c_str());
        return false;
    }

    ExThreadSmartLock locker(m_lock);

    auto it = m_channel_map.find(ch_tp2cli);
    if (it != m_channel_map.end())
    {
        EXLOGE("[%s] can not make channel pair, channel to client already exists.\n", m_dbg_name.c_str());
        return false;
    }

    if (ch_tp2srv)
    {
        it = m_channel_map.find(ch_tp2srv);
        if (it != m_channel_map.end())
        {
            EXLOGE("[%s] can not make channel pair, channel to server already exists.\n", m_dbg_name.c_str());
            return false;
        }
    }

    uint32_t dbg_id = m_pair_id++;
    auto _pair = new SshChannelPair(this, dbg_id, ch_tp2cli, ch_tp2srv);

    if (ch_tp2srv)
    {
        if (!_pair->record_begin(m_conn_info))
        {
            delete _pair;
            return false;
        }
    }

    m_pairs.push_back(_pair);

    m_channel_map.insert(std::make_pair(ch_tp2cli, _pair));
    if (ch_tp2srv)
        m_channel_map.insert(std::make_pair(ch_tp2srv, _pair));

    m_channels.push_back(ch_tp2cli);
    if (ch_tp2srv)
        m_channels.push_back(ch_tp2srv);

    return true;
}

SshChannelPair* SshSession::get_channel_pair(ssh_channel ch)
{
    ExThreadSmartLock locker(m_lock);

    auto it = m_channel_map.find(ch);
    if (it == m_channel_map.end())
        return nullptr;

    it->second->last_access_timestamp = static_cast<uint32_t>(time(nullptr));
    return it->second;
}

// void SshSession::set_channel_tp2srv_callbacks(ssh_channel ch_tp2srv)
// {
//     ssh_set_channel_callbacks(ch_tp2srv, &m_srv_channel_cb);
// }

void SshSession::keep_alive()
{
    m_need_send_keepalive = true;
    //     EXLOGD("[ssh] keep-alive.\n");
    //     if(m_srv_session)
    //         ssh_send_keepalive(m_srv_session);
    //     if (m_cli_session)
    //         ssh_send_keepalive(m_cli_session);
}

int SshSession::_on_auth_password_request(ssh_session /*session*/, const char* user, const char* password, void* userdata)
{
    auto* _this = (SshSession*)userdata;

    int ret = _this->_do_auth(user, password);
    _this->m_first_auth = false;
    return ret;
}

int SshSession::_do_auth(const char* user, const char* secret)
{
    EXLOGD("[%s] authenticating, user: %s\n", m_dbg_name.c_str(), user);
    // EXLOGD("[%s] authenticating, user: %s, secret: %s\n", m_dbg_name.c_str(), user, secret);

    // v3.6.0
    // 场景
    //  1. 标准方式：在web界面上登记远程账号的用户名和密码，远程连接时由TP负责填写；
    //  2. 手动输入密码：web界面上仅登记远程账号的用户名，不填写密码，每次远程连接时由操作者输入密码；
    //  3. 脱离web和助手进行远程连接：用户在客户端软件中配置远程主机，地址为tp核心服务地址+端口，用户名为 tp用户名--授权码，
    //                            密码为 tp登录密码--远程账号密码，可以不用登录tp就直接在客户端软件中进行远程连接。
    // 用户名的格式：
    //    SID_OR_TOKEN     6个字符的是SID，12个字符的是TOKEN
    // 范例：
    //    03ad57           // 6个字符的是临时会话ID，即SID，核心服务从会话的连接信息中取得远程用户名。
    //    tp7769b2e3Dw     // 12字节，为授权码，可以脱离web页面和助手使用
    //
    // 密码的格式：
    //    ****                    如果管理员已经这个远程账号设置了密码，则密码可以随便填写。
    //    tp账号密码--远程账号密码    用两个减号分隔第一部分和第二部分。第一部分为用户登录TP的密码，第二部分为远程账号的密码
    //
    // 使用授权码方式时，需要使用传入的密码进行额外验证。有三种情况：
    //  1. 8字符token，使用tp用户账号对应的密码
    //  2. 12字符token，使用tp_ops_token表中的对应的临时密码
    //  3. 如果管理员未对远程账号设置密码，则需要在上述密码后面加上  --远程账号密码
    //
    //
    // 如果是SID，则从连接信息中获取远程用户名，如果此时连接信息中的远程用户名是大写的 INTERACTIVE_USER，则报错。
    // 如果是TOKEN，这可能是脱离web使用，核心服务需要通过web接口获取相应的连接信息，并临时生成一个会话ID来使用。
    // 授权码具有有效期，在此有效期期间可以进行任意数量的连接，可用于如下场景：
    //   1. 操作者将 授权码 和对应的密码添加到ssh客户端如SecureCRT或者xShell中，以后可以脱离web使用；
    //   2. 邀请第三方运维人员临时参与某项运维工作，可以生成一个相对短有效期的授权码发给第三方运维人员。
    // 授权码到期时，已经连接的会话会被强行中断。
    // 授权码可以绑定到主机，也可绑定到具体远程用户。前者需要操作者自己填写真实的远程用户名，后者则无需填写，可以直接登录。
    // 为增加安全性，内部人员使用时可以配合动态密码使用，而对于临时的授权码，可以生成一个配套的临时密码来进行认证。
    // 此外，还可以利用QQ机器人或微信小程序，操作者向QQ机器人发送特定指令，QQ机器人则发送一个新的临时密码。
    //
    // Linux系统中，用户名通常长度不超过8个字符，并且由大小写字母和/或数字组成。登录名中不能有冒号(，因为冒号在这里是分隔符。为了兼容
    // 起见，登录名中最好不要包含点字符(.)，并且不使用连字符(-)和加号(+)打头。

    if (m_first_auth)
    {
        // std::string _name;
        // std::string _sid;
        // std::string tmp(user);
        //
        // std::string::size_type tmp_pos = tmp.rfind("--");
        // if (tmp_pos == std::string::npos)
        // {
        //     // 向下兼容
        //     _name = "TP";
        //     m_sid = tmp;
        // }
        // else
        // {
        //     _name.assign(tmp, 0, tmp_pos);
        //     m_sid.assign(tmp, tmp_pos + 2, tmp.length() - tmp_pos - 2);
        // }
        //
        // if (_name != "TP")
        //     m_acc_name = _name;

        EXLOGD("[%s] first auth, user: %s\n", m_dbg_name.c_str(), user);

#ifdef TEST_SSH_SESSION_000000
        m_conn_info = new TPP_CONNECT_INFO;

        m_conn_info->sid = "000000";
        m_conn_info->user_id = 1;
        m_conn_info->host_id = 1;
        m_conn_info->acc_id = 1;
        m_conn_info->user_username = "apex.liu";      // 申请本次连接的用户名
        m_conn_info->client_ip = "127.0.0.1";
        m_conn_info->username_prompt = "";    // for telnet
        m_conn_info->password_prompt = "";    // for telnet
        m_conn_info->protocol_type = TP_PROTOCOL_TYPE_SSH;
        m_conn_info->protocol_sub_type = TP_PROTOCOL_TYPE_SSH_SHELL;
        m_conn_info->protocol_flag = TP_FLAG_ALL;
        m_conn_info->record_flag = TP_FLAG_ALL;
        m_conn_info->auth_type = TP_AUTH_TYPE_PASSWORD;

        if (m_sid == "000000") {
            m_conn_info->host_ip = "39.97.125.170";
            m_conn_info->conn_ip = "39.97.125.170";
            m_conn_info->conn_port = 22;
            m_conn_info->acc_username = "root";
            m_conn_info->acc_secret = "*******";
            // m_conn_info->acc_username = "INTERACTIVE_USER";
            // m_conn_info->acc_secret = "";
        }
        else {
            m_conn_info->host_ip = "127.0.0.1";
            m_conn_info->conn_ip = "127.0.0.1";
            m_conn_info->conn_port = 22;
            m_conn_info->acc_username = "apex";
            m_conn_info->acc_secret = "********";
        }
#else
        std::string tp_password;
        std::string remote_password;

        m_sid = user;
        if (m_sid.length() == 6)
        {
            m_conn_info = g_ssh_env.get_connect_info(m_sid.c_str(), nullptr, nullptr);
            remote_password = secret;
        }
        else if (m_sid.length() == 12)
        {
            std::string tmp(secret);

            std::string::size_type tmp_pos = tmp.find("--");
            if (tmp_pos == std::string::npos)
            {
                tp_password = secret;
            }
            else
            {
                tp_password.assign(tmp, 0, tmp_pos);
                remote_password.assign(tmp, tmp_pos + 2, tmp.length() - tmp_pos - 2);
            }

            m_conn_info = g_ssh_env.get_connect_info(m_sid.c_str(), tp_password.c_str(), m_client_ip.c_str());
            if (m_conn_info) {
                // m_conn_info->client_ip = m_client_ip;
                m_sid = m_conn_info->sid;
            }
        }

#endif

        if (!m_conn_info)
        {
            _set_last_error(TP_SESS_STAT_ERR_SESSION);
            m_auth_err_msg = "invalid session id: '";
            m_auth_err_msg += m_sid;
            m_auth_err_msg += "'.";
            EXLOGE("[%s] %s\n", m_dbg_name.c_str(), m_auth_err_msg.c_str());
            // return SSH_AUTH_SUCCESS;
            return SSH_AUTH_DENIED;
        }

        m_conn_ip = m_conn_info->conn_ip;
        m_conn_port = m_conn_info->conn_port;
        m_auth_type = m_conn_info->auth_type;
        m_acc_name = m_conn_info->acc_username;
        m_acc_secret = m_conn_info->acc_secret;
        m_flags = m_conn_info->protocol_flag;

        // if (!remote_password.empty())
        //     m_acc_secret = remote_password;

        if (m_conn_info->protocol_type != TP_PROTOCOL_TYPE_SSH)
        {
            _set_last_error(TP_SESS_STAT_ERR_INTERNAL);
            m_auth_err_msg = "session ";
            m_auth_err_msg += m_sid;
            m_auth_err_msg += " is not for SSH.";
            EXLOGE("[%s] %s\n", m_dbg_name.c_str(), m_auth_err_msg.c_str());
            return SSH_AUTH_SUCCESS;
        }

        // _name = m_conn_info->acc_username;
        // if ((m_acc_name.empty() && _name == "INTERACTIVE_USER")
        //     || (!m_acc_name.empty() && _name != "INTERACTIVE_USER"))
        // {
        //     _set_last_error(TP_SESS_STAT_ERR_SESSION);
        //     m_auth_err_msg = "account name of remote host should not be 'INTERACTIVE_USER'.";
        //     EXLOGE("[%s] %s\n", m_dbg_name.c_str(), m_auth_err_msg.c_str());
        //
        //     return SSH_AUTH_SUCCESS;
        // }
        // if (m_acc_name.empty())
        //     m_acc_name = _name;
        if (m_acc_name.empty())
        {
            _set_last_error(TP_SESS_STAT_ERR_SESSION);
            m_auth_err_msg = "account name of remote host not set.";
            EXLOGE("[%s] %s\n", m_dbg_name.c_str(), m_auth_err_msg.c_str());
            return SSH_AUTH_SUCCESS;
        }

        if (m_acc_secret.empty())
        {
            // 如果TP中未设置远程账号密码，表示允许用户自行输入密码
            // m_allow_user_input_password = true;
            m_acc_secret = remote_password;
        }
    }
    else
    {
        // 如果第一次认证时没有确定目标远程主机IP和端口（例如session-id无效），则不再继续后面的操作
        if (m_conn_ip.empty() || m_conn_port == 0)
        {
            EXLOGE("[%s] second auth, user: %s, no remote host info, can not connect.\n", m_dbg_name.c_str(), user);
            return SSH_AUTH_DENIED;
        }

        // 允许用户自行输入密码的情况下，第二次认证，参数secret就是用户自己输入的密码了。
        m_acc_secret = secret;
    }

    // config and try to connect to real SSH host.
    ex_strformat(m_dbg_server, 128, "%s:%d", m_conn_ip.c_str(), m_conn_port);
    EXLOGV("[%s] try to connect to real SSH server %s\n", m_dbg_name.c_str(), m_dbg_server.c_str());

    if (m_rs_tp2srv)
    {
        ssh_free(m_rs_tp2srv);
        m_rs_tp2srv = nullptr;
    }

    m_rs_tp2srv = ssh_new();

    ssh_options_set(m_rs_tp2srv, SSH_OPTIONS_HOST, m_conn_ip.c_str());
    int port = (int)m_conn_port;
    ssh_options_set(m_rs_tp2srv, SSH_OPTIONS_PORT, &port);
    int val = 0;
    ssh_options_set(m_rs_tp2srv, SSH_OPTIONS_STRICTHOSTKEYCHECK, &val);

    //#ifdef EX_DEBUG
    //    int flag = SSH_LOG_FUNCTIONS;
    //    ssh_options_set(_this->m_srv_session, SSH_OPTIONS_LOG_VERBOSITY, &flag);
    //#endif

    if (m_auth_type != TP_AUTH_TYPE_NONE)
        ssh_options_set(m_rs_tp2srv, SSH_OPTIONS_USER, m_acc_name.c_str());

    // default timeout is 10 seconds, it is too short for connect progress, so set it to 120 sec.
    // usually when sshd config to UseDNS.
    int _timeout = 120; // 120 sec.
    ssh_options_set(m_rs_tp2srv, SSH_OPTIONS_TIMEOUT, &_timeout);

    int rc = ssh_connect(m_rs_tp2srv);
    if (rc != SSH_OK)
    {
        _set_last_error(TP_SESS_STAT_ERR_CONNECT);
        m_auth_err_msg = "can not connect to remote host ";
        m_auth_err_msg += m_dbg_server;
        m_auth_err_msg += ", ";
        m_auth_err_msg += ssh_get_error(m_rs_tp2srv);
        m_auth_err_msg += ".";
        EXLOGE("[%s] %s\n", m_dbg_name.c_str(), m_auth_err_msg.c_str());
        return SSH_AUTH_SUCCESS;
    }

    ssh_set_blocking(m_rs_tp2srv, 0);

    // once the server are connected, change the timeout back to default.
    _timeout = 10; // in seconds.
    ssh_options_set(m_rs_tp2srv, SSH_OPTIONS_TIMEOUT, &_timeout);

    // get ssh version of host, v1 or v2
    // TODO: libssh-0.8.5 does not support ssh-v1 anymore.
    // _this->m_ssh_ver = ssh_get_version(_this->m_rs_tp2srv);
    // EXLOGW("[ssh] real host is SSHv%d\n", _this->m_ssh_ver);

    const char* banner = ssh_get_issue_banner(m_rs_tp2srv);
    if (banner)
    {
        EXLOGI("[%s] remote host issue banner: %s\n", m_dbg_name.c_str(), banner);
    }

    int auth_methods = 0;

    rc = ssh_userauth_none(m_rs_tp2srv, nullptr);
    while (rc == SSH_AUTH_AGAIN)
    {
        ex_sleep_ms(20);
        rc = ssh_userauth_none(m_rs_tp2srv, nullptr);
    }

    if (SSH_AUTH_ERROR != rc)
    {
        auth_methods = ssh_userauth_list(m_rs_tp2srv, nullptr);
        EXLOGV("[%s] allowed auth method: 0x%08x\n", m_dbg_name.c_str(), auth_methods);
    }

    // some host does not give us the auth methods list, so we need try each one.
    if (auth_methods == 0)
    {
        auth_methods = SSH_AUTH_METHOD_INTERACTIVE | SSH_AUTH_METHOD_PASSWORD | SSH_AUTH_METHOD_PUBLICKEY;
        EXLOGW("[%s] can not get allowed auth method, try each method we can.\n", m_dbg_name.c_str());
    }

    if (m_auth_type == TP_AUTH_TYPE_PASSWORD)
    {
        if (!(((auth_methods & SSH_AUTH_METHOD_INTERACTIVE) == SSH_AUTH_METHOD_INTERACTIVE) || ((auth_methods & SSH_AUTH_METHOD_PASSWORD) == SSH_AUTH_METHOD_PASSWORD)))
        {
            _set_last_error(TP_SESS_STAT_ERR_AUTH_TYPE);
            m_auth_err_msg = "both password and interactive authorize methods are not allowed by remote host ";
            m_auth_err_msg += m_dbg_server;
            m_auth_err_msg += ".";
            EXLOGE("[%s] %s\n", m_dbg_name.c_str(), m_auth_err_msg.c_str());
            return SSH_AUTH_SUCCESS;
        }

        int retry_count = 0;

        // first try interactive login mode if server allow.
        if ((auth_methods & SSH_AUTH_METHOD_INTERACTIVE) == SSH_AUTH_METHOD_INTERACTIVE)
        {
            rc = ssh_userauth_kbdint(m_rs_tp2srv, nullptr, nullptr);
            for (;;)
            {
                if (rc == SSH_AUTH_SUCCESS)
                {
                    EXLOGW("[%s] login with interactive mode succeeded.\n", m_dbg_name.c_str());
                    m_auth_passed = true;
                    return SSH_AUTH_SUCCESS;
                }

                if (rc == SSH_AUTH_AGAIN)
                {
                    retry_count += 1;
                    if (retry_count >= 5)
                        break;
                    ex_sleep_ms(500);
                    rc = ssh_userauth_kbdint(m_rs_tp2srv, nullptr, nullptr);
                    continue;
                }

                if (rc != SSH_AUTH_INFO)
                {
                    if (!m_auth_err_msg.empty())
                        m_auth_err_msg += "\r\n";
                    m_auth_err_msg += "login remote host ";
                    m_auth_err_msg += m_dbg_server;
                    m_auth_err_msg += " with interactive authorize method failed, ";
                    m_auth_err_msg += ssh_get_error(m_rs_tp2srv);
                    EXLOGE("[%s] %s\n", m_dbg_name.c_str(), m_auth_err_msg.c_str());
                    break;
                }

                int prompts = ssh_userauth_kbdint_getnprompts(m_rs_tp2srv);
                if (0 == prompts)
                {
                    rc = ssh_userauth_kbdint(m_rs_tp2srv, nullptr, nullptr);
                    continue;
                }

                for (int i = 0; i < prompts; ++i)
                {
                    char echo = 0;
                    const char* prompt = ssh_userauth_kbdint_getprompt(m_rs_tp2srv, i, &echo);

                    // about 'echo':
                    // This is an optional variable. You can obtain a boolean if the user input should be echoed or
                    // hidden. For password it is usually hidden.

                    EXLOGV("[%s] interactive login prompt(%s): %s\n", m_dbg_name.c_str(), echo ? "hidden" : "not hidden", prompt);
                    if (echo)
                        continue;

                    rc = ssh_userauth_kbdint_setanswer(m_rs_tp2srv, i, m_acc_secret.c_str());
                    if (rc < 0)
                    {
                        _set_last_error(TP_SESS_STAT_ERR_AUTH_DENIED);

                        if (!m_auth_err_msg.empty())
                            m_auth_err_msg += "\r\n";
                        m_auth_err_msg += "login remote host ";
                        m_auth_err_msg += m_dbg_server;
                        m_auth_err_msg += " with interactive authorize method failed, ";
                        m_auth_err_msg += ssh_get_error(m_rs_tp2srv);

                        EXLOGE("[%s] %s\n", m_dbg_name.c_str(), m_auth_err_msg.c_str());
                        return SSH_AUTH_SUCCESS;
                    }

                    break;
                }

                rc = ssh_userauth_kbdint(m_rs_tp2srv, nullptr, nullptr);
            }
        }

        // and then try password login mode if server allow.
        retry_count = 0;
        if ((auth_methods & SSH_AUTH_METHOD_PASSWORD) == SSH_AUTH_METHOD_PASSWORD)
        {
            rc = ssh_userauth_password(m_rs_tp2srv, nullptr, m_acc_secret.c_str());
            for (;;)
            {
                if (rc == SSH_AUTH_SUCCESS)
                {
                    EXLOGW("[%s] login with password mode succeeded.\n", m_dbg_name.c_str());
                    m_auth_passed = true;
                    return SSH_AUTH_SUCCESS;
                }
                else if (rc == SSH_AUTH_AGAIN)
                {
                    retry_count += 1;
                    if (retry_count >= 5)
                        break;
                    ex_sleep_ms(100);
                    rc = ssh_userauth_password(m_rs_tp2srv, nullptr, m_acc_secret.c_str());
                    continue;
                }

                EXLOGE("[%s] failed to login with password mode, got %d.\n", m_dbg_name.c_str(), rc);
                break;
            }
        }

        _set_last_error(TP_SESS_STAT_ERR_AUTH_DENIED);

        m_auth_err_msg += "failed to login remote host ";
        m_auth_err_msg += m_dbg_server;
        m_auth_err_msg += " with interactive and password authorize methods, access denied.";
        EXLOGE("[%s] %s\n", m_dbg_name.c_str(), m_auth_err_msg.c_str());
        return SSH_AUTH_SUCCESS;
    }
    else if (m_auth_type == TP_AUTH_TYPE_PRIVATE_KEY)
    {
        if ((auth_methods & SSH_AUTH_METHOD_PUBLICKEY) != SSH_AUTH_METHOD_PUBLICKEY)
        {
            _set_last_error(TP_SESS_STAT_ERR_AUTH_TYPE);
            m_auth_err_msg = "public-key-authorize method is not allowed by remote host ";
            m_auth_err_msg += m_dbg_server;
            m_auth_err_msg += ".";
            EXLOGE("[%s] %s\n", m_dbg_name.c_str(), m_auth_err_msg.c_str());
            return SSH_AUTH_SUCCESS;
        }

        ssh_key key = nullptr;
        if (SSH_OK != ssh_pki_import_privkey_base64(m_acc_secret.c_str(), nullptr, nullptr, nullptr, &key))
        {
            _set_last_error(TP_SESS_STAT_ERR_BAD_SSH_KEY);
            m_auth_err_msg = "can not load private key for login remote host ";
            m_auth_err_msg += m_dbg_server;
            m_auth_err_msg += ", ";
            EXLOGE("[%s] %s\n", m_dbg_name.c_str(), m_auth_err_msg.c_str());
            return SSH_AUTH_SUCCESS;
        }

        int retry_count = 0;
        rc = ssh_userauth_publickey(m_rs_tp2srv, nullptr, key);
        for (;;)
        {
            if (rc == SSH_AUTH_SUCCESS)
            {
                EXLOGW("[%s] login with public-key mode succeeded.\n", m_dbg_name.c_str());
                m_auth_passed = true;
                ssh_key_free(key);
                return SSH_AUTH_SUCCESS;
            }
            else if (rc == SSH_AUTH_AGAIN)
            {
                retry_count += 1;
                if (retry_count >= 5)
                    break;
                ex_sleep_ms(100);
                rc = ssh_userauth_publickey(m_rs_tp2srv, nullptr, key);
                continue;
            }

            EXLOGE("[%s] failed to login with password mode, got %d.\n", m_dbg_name.c_str(), rc);

            break;
        }

        ssh_key_free(key);

        _set_last_error(TP_SESS_STAT_ERR_AUTH_DENIED);

        if (!m_auth_err_msg.empty())
            m_auth_err_msg += "\r\n";
        m_auth_err_msg += "login remote host ";
        m_auth_err_msg += m_dbg_server;
        m_auth_err_msg += " with public-key authorize method failed. ";
        m_auth_err_msg += ssh_get_error(m_rs_tp2srv);
        EXLOGE("[%s] %s\n", m_dbg_name.c_str(), m_auth_err_msg.c_str());

        return SSH_AUTH_SUCCESS;
    }
    else if (m_auth_type == TP_AUTH_TYPE_NONE)
    {
        _set_last_error(TP_SESS_STAT_ERR_AUTH_DENIED);
        m_auth_err_msg = "no authorize method for login remote host ";
        m_auth_err_msg += m_dbg_server;
        m_auth_err_msg += ".";
        EXLOGE("[%s] %s\n", m_dbg_name.c_str(), m_auth_err_msg.c_str());
        return SSH_AUTH_SUCCESS;
    }
    else
    {
        _set_last_error(TP_SESS_STAT_ERR_AUTH_DENIED);
        m_auth_err_msg = "unknown authorize method for login remote host ";
        m_auth_err_msg += m_dbg_server;
        m_auth_err_msg += ".";
        EXLOGE("[%s] %s\n", m_dbg_name.c_str(), m_auth_err_msg.c_str());
        return SSH_AUTH_SUCCESS;
    }
}

ssh_channel SshSession::_on_new_channel_request(ssh_session session, void* userdata)
{
    // 客户端尝试打开一个通道（然后才能通过这个通道发控制命令或者收发数据）
    auto _this = (SshSession*)userdata;
    EXLOGV("[%s] client open channel.\n", _this->m_dbg_name.c_str());

    if (_this->m_state == SSH_SESSION_STATE_AUTHING)
        _this->m_state = SSH_SESSION_STATE_AUTH_END;

    // 如果认证过程中已经发生了不可继续的错误，打开一个单边通道（客户端<->TP，没有 TP<->服务端）
    // 这样在后面合适的时候给客户端输出一个合适的错误提示，避免客户端反复重连

    ssh_channel rc_tp2cli = ssh_channel_new(session);
    if (!rc_tp2cli)
    {
        EXLOGE("[%s] can not create channel for client.\n", _this->m_dbg_name.c_str());
        _this->_set_last_error(TP_SESS_STAT_ERR_CREATE_CHANNEL);
        return nullptr;
    }
    ssh_set_channel_callbacks(rc_tp2cli, &_this->m_cli_channel_cb);
    EXLOGD("[%s] channel to client created.\n", _this->m_dbg_name.c_str());

    if (!_this->m_auth_passed)
    {
        if (!_this->make_channel_pair(rc_tp2cli, nullptr))
        {
            EXLOGE("[%s] can not make channel pair.\n", _this->m_dbg_name.c_str());
            _this->_set_last_error(TP_SESS_STAT_ERR_INTERNAL);
            ssh_channel_close(rc_tp2cli);
            return nullptr;
        }

        return rc_tp2cli;
    }

    // 我们也要向真正的服务器申请打开一个通道，来进行转发
    ssh_channel rc_tp2srv = ssh_channel_new(_this->m_rs_tp2srv);
    if (!rc_tp2srv)
    {
        EXLOGE("[%s] can not create channel for server.\n", _this->m_dbg_name.c_str());
        _this->_set_last_error(TP_SESS_STAT_ERR_CREATE_CHANNEL);
        return nullptr;
    }

    int rc = ssh_channel_open_session(rc_tp2srv);
    while (rc == SSH_AGAIN)
    {
        ex_sleep_ms(20);
        rc = ssh_channel_open_session(rc_tp2srv);
    }

    if (SSH_OK != rc)
    {
        EXLOGE("[%s] error opening channel to real server: %s\n", _this->m_dbg_name.c_str(), ssh_get_error(_this->m_rs_tp2srv));
        ssh_channel_free(rc_tp2cli);
        _this->_set_last_error(TP_SESS_STAT_ERR_CREATE_CHANNEL);
        return nullptr;
    }
    EXLOGD("[%s] channel to real server opened.\n", _this->m_dbg_name.c_str());

    ssh_set_channel_callbacks(rc_tp2srv, &_this->m_srv_channel_cb);

    if (!_this->make_channel_pair(rc_tp2cli, rc_tp2srv))
    {
        EXLOGE("[%s] can not make channel pair.\n", _this->m_dbg_name.c_str());
        _this->_set_last_error(TP_SESS_STAT_ERR_INTERNAL);
        ssh_channel_close(rc_tp2cli);
        ssh_channel_close(rc_tp2srv);
        return nullptr;
    }

    return rc_tp2cli;
}

int SshSession::_on_client_pty_request(ssh_session /*session*/, ssh_channel channel, const char* term, int x, int y, int px, int py, void* userdata)
{
    auto _this = (SshSession*)userdata;
    EXLOGD("[%s] client request pty: %s, (%d, %d) / (%d, %d)\n", _this->m_dbg_name.c_str(), term, x, y, px, py);

    auto cp = _this->get_channel_pair(channel);
    if (!cp)
    {
        EXLOGE("[%s] when client request pty, channel pair not found.\n", _this->m_dbg_name.c_str());
        return SSH_ERROR;
    }

    cp->win_width = x;
    if (!_this->m_auth_passed)
    {
        return SSH_OK;
    }


    cp->rec.record_win_size_startup(x, y);

    int rc = ssh_channel_request_pty_size(cp->rsc_tp2srv, term, x, y);
    while (rc == SSH_AGAIN)
    {
        ex_sleep_ms(20);
        rc = ssh_channel_request_pty_size(cp->rsc_tp2srv, term, x, y);
    }

    if (rc != SSH_OK)
    {
        EXLOGE("[%s] request pty from server failed, %s\n", _this->m_dbg_name.c_str(), ssh_get_error(_this->m_rs_tp2srv));
    }
    return rc;
}

int SshSession::_on_client_shell_request(ssh_session /*session*/, ssh_channel channel, void* userdata)
{
    auto _this = (SshSession*)userdata;
    EXLOGD("[%s] client request shell\n", _this->m_dbg_name.c_str());

    auto cp = _this->get_channel_pair(channel);
    if (!cp)
    {
        EXLOGE("[%s] when client request shell, channel pair not found.\n", _this->m_dbg_name.c_str());
        return SSH_ERROR;
    }

    if (!_this->m_auth_passed)
    {
        std::string msg = "ERROR: ";
        msg += _this->m_auth_err_msg;
        msg += "\r\n\r\n";
        _this->_send(cp->rsc_tp2cli, 0, (void*)msg.c_str(), msg.length());

        cp->need_close = true;

        // 不能直接返回SSH_ERROR来断开连接，否则会导致上面发送的错误信息客户端来不及接收。
        return SSH_OK;
    }

    // 收到第一包服务端返回的数据时，在输出数据之前显示一些自定义的信息
    {
        char buf[512] = {0};

        const char* auth_mode;
        if (_this->m_auth_type == TP_AUTH_TYPE_PASSWORD)
            auth_mode = "password";
        else if (_this->m_auth_type == TP_AUTH_TYPE_PRIVATE_KEY)
            auth_mode = "private-key";
        else
            auth_mode = "unknown";

        int w = MIN(cp->win_width, 64);
        ex_astr line(w, '=');

        snprintf(
                buf, sizeof(buf), "\r\n"\
                "%s\r\n"\
                "Teleport SSH Bastion Server...\r\n"\
                "  - teleport to %s:%d\r\n"\
                "  - authorized by %s\r\n"\
                "%s\r\n"\
                "\r\n\r\n", line.c_str(), _this->m_conn_ip.c_str(), _this->m_conn_port, auth_mode, line.c_str()
        );

        _this->_send(cp->rsc_tp2cli, 0, buf, strlen(buf));
    }

    if ((_this->m_flags & TP_FLAG_SSH_SHELL) != TP_FLAG_SSH_SHELL)
    {
        EXLOGE("[%s] ssh-shell disabled by ops-policy.\n", _this->m_dbg_name.c_str());
        //return SSH_ERROR;
        std::string msg = "ERROR: ssh-shell disabled by ops-policy.\r\n\r\n";
        _this->_send(cp->rsc_tp2cli, 0, (void*)msg.c_str(), msg.length());

        cp->need_close = true;

        // 不能直接返回SSH_ERROR来断开连接，否则会导致上面发送的错误信息客户端来不及接收。
        return SSH_OK;
    }

    cp->type = TS_SSH_CHANNEL_TYPE_SHELL;

    g_ssh_env.session_update(cp->db_id, TP_PROTOCOL_TYPE_SSH_SHELL, TP_SESS_STAT_STARTED);

    int rc = ssh_channel_request_shell(cp->rsc_tp2srv);
    while (rc == SSH_AGAIN)
    {
        ex_sleep_ms(20);
        rc = ssh_channel_request_shell(cp->rsc_tp2srv);
    }

    if (rc != SSH_OK)
    {
        EXLOGE("[%s] request shell from server failed, %s\n", _this->m_dbg_name.c_str(), ssh_get_error(_this->m_rs_tp2srv));

        std::string msg = "ERROR: request shell from remote host ";
        msg += _this->m_dbg_server;
        msg += " failed.\r\n\r\n";
        _this->_send(cp->rsc_tp2cli, 0, (void*)msg.c_str(), msg.length());

        cp->need_close = true;

        // 不能直接返回SSH_ERROR来断开连接，否则会导致上面发送的错误信息客户端来不及接收。
        return SSH_OK;
    }

    return rc;
}

void SshSession::_on_client_channel_close(ssh_session /*session*/, ssh_channel /*channel*/, void* userdata)
{
    auto _this = (SshSession*)userdata;
    EXLOGV("[%s] client channel (from %s) closed.\n", _this->m_dbg_name.c_str(), _this->m_dbg_client.c_str());
}

int SshSession::_on_client_pty_win_change(ssh_session /*session*/, ssh_channel channel, int width, int height, int /*px_width*/, int /*pw_height*/, void* userdata)
{
    auto _this = (SshSession*)userdata;
    EXLOGD("[%s] client pty win size change to: (%d, %d)\n", _this->m_dbg_name.c_str(), width, height);

    auto cp = _this->get_channel_pair(channel);
    if (!cp)
    {
        EXLOGE("[%s] when client pty win change, channel pair not found.\n", _this->m_dbg_name.c_str());
        return SSH_ERROR;
    }

    if (!_this->m_auth_passed)
    {
        return SSH_OK;
    }

    cp->win_width = width;
    cp->rec.record_win_size_change(width, height);

    int rc = ssh_channel_change_pty_size(cp->rsc_tp2srv, width, height);
    while (rc == SSH_AGAIN)
    {
        ex_sleep_ms(20);
        rc = ssh_channel_change_pty_size(cp->rsc_tp2srv, width, height);
    }

    if (rc != SSH_OK)
    {
        EXLOGE("[%s] request shell from server failed, %s\n", _this->m_dbg_name.c_str(), ssh_get_error(_this->m_rs_tp2srv));
    }
    return rc;
}

int SshSession::_on_client_channel_subsystem_request(ssh_session /*session*/, ssh_channel channel, const char* subsystem, void* userdata)
{
    auto _this = (SshSession*)userdata;
    EXLOGD("[%s] on_client_channel_subsystem_request(): %s\n", _this->m_dbg_name.c_str(), subsystem);

    auto cp = _this->get_channel_pair(channel);
    if (!cp)
    {
        EXLOGE("[%s] when request channel subsystem, channel pair not found.\n", _this->m_dbg_name.c_str());
        return SSH_ERROR;
    }

    if (!_this->m_auth_passed)
    {
        cp->need_close = true;
        return SSH_OK;
    }

    // 目前只支持SFTP子系统
    if (strcmp(subsystem, "sftp") != 0)
    {
        EXLOGE("[%s] support `sftp` subsystem only, but got `%s`.\n", _this->m_dbg_name.c_str(), subsystem);
        cp->state = TP_SESS_STAT_ERR_UNSUPPORT_PROTOCOL;
        return SSH_ERROR;
    }

    if ((_this->m_flags & TP_FLAG_SSH_SFTP) != TP_FLAG_SSH_SFTP)
    {
        EXLOGE("[%s] ssh-sftp disabled by ops-policy.\n", _this->m_dbg_name.c_str());
        return SSH_ERROR;
    }

    cp->type = TS_SSH_CHANNEL_TYPE_SFTP;

    g_ssh_env.session_update(cp->db_id, TP_PROTOCOL_TYPE_SSH_SFTP, TP_SESS_STAT_STARTED);

    int rc = ssh_channel_request_subsystem(cp->rsc_tp2srv, subsystem);
    while (rc == SSH_AGAIN)
    {
        ex_sleep_ms(20);
        rc = ssh_channel_request_subsystem(cp->rsc_tp2srv, subsystem);
    }

    if (rc != SSH_OK)
    {
        EXLOGE("[%s] request shell from server failed, %s\n", _this->m_dbg_name.c_str(), ssh_get_error(_this->m_rs_tp2srv));
    }
    return rc;
}

int SshSession::_on_client_channel_exec_request(ssh_session /*session*/, ssh_channel /*channel*/, const char* command, void* userdata)
{
    auto _this = (SshSession*)userdata;
    EXLOGW("[%s] ssh exec not supported. command: %s\n", _this->m_dbg_name.c_str(), command);
    return SSH_ERROR;
}

void SshSession::_on_server_channel_close(ssh_session /*session*/, ssh_channel /*channel*/, void* userdata)
{
    auto _this = (SshSession*)userdata;
    EXLOGV("[%s] server channel (to %s) closed.\n", _this->m_dbg_name.c_str(), _this->m_dbg_server.c_str());
}

bool SshSession::_send(ssh_channel channel_to, int is_stderr, void* data, uint32_t len)
{
    uint32_t sent_len = 0;

    for (;;)
    {
        int ret;
        if (is_stderr)
            ret = ssh_channel_write_stderr(channel_to, data, len - sent_len);
        else
            ret = ssh_channel_write(channel_to, data, len - sent_len);

        if (ret < 0)
        {
            if (ret == SSH_AGAIN)
            {
                ex_sleep_ms(1);
                continue;
            }
            else
            {
                EXLOGE("[%s] send data failed: %d\n", m_dbg_name.c_str(), ret);
                return false;
            }
        }

        if (ret > 0)
        {
            sent_len += ret;
            if (sent_len >= len)
            {
                return true;
            }
        }
    }
}

int SshSession::_on_client_channel_data(ssh_session /*session*/, ssh_channel channel, void* data, unsigned int len, int is_stderr, void* userdata)
{
    // EXLOG_BIN((ex_u8 *) data, len, " ---> on_client_channel_data [is_stderr=%d]:", is_stderr);
    // EXLOGD(" ---> recv from client %d B\n", len);

    auto _this = (SshSession*)userdata;

    auto cp = _this->get_channel_pair(channel);
    if (!cp)
    {
        EXLOGE("[%s] when receive client channel data, channel pair not found.\n", _this->m_dbg_name.c_str());
        return SSH_ERROR;
    }

    if (!_this->m_auth_passed)
    {
        cp->need_close = true;
        return static_cast<int>(len);
    }

    if (!is_stderr)
    {
        if (cp->type == TS_SSH_CHANNEL_TYPE_SHELL)
        {
            cp->process_pty_data_from_client(static_cast<uint8_t*>(data), len);
        }
        else
        {
            cp->process_sftp_command(channel, (ex_u8*)data, len);
        }
    }

    if (!_this->_send(cp->rsc_tp2srv, is_stderr, data, len))
    {
        cp->need_close = true;
        return SSH_ERROR;
    }

    return static_cast<int>(len);
}

int SshSession::_on_server_channel_data(ssh_session /*session*/, ssh_channel channel, void* data, unsigned int len, int is_stderr, void* userdata)
{
    // EXLOG_BIN((ex_u8 *) data, len, " <--- on_server_channel_data [is_stderr=%d]:", is_stderr);
    // EXLOGD(" <--- recv from server %d B\n", len);

    auto _this = (SshSession*)userdata;

    auto cp = _this->get_channel_pair(channel);
    if (!cp)
    {
        EXLOGE("[%s] when receive server channel data, channel pair not found.\n", _this->m_dbg_name.c_str());
        return SSH_ERROR;
    }

    if (!is_stderr)
    {
        if (cp->type == TS_SSH_CHANNEL_TYPE_SHELL)
        {
            cp->process_pty_data_from_server(static_cast<uint8_t*>(data), len);
            cp->rec.record(TS_RECORD_TYPE_SSH_DATA, static_cast<uint8_t*>(data), len);
        }
        else
        {
            // cp->process_sftp_command(channel, (ex_u8*)data, len);
        }
    }

#if 0
    // 收到第一包服务端返回的数据时，在输出数据之前显示一些自定义的信息
    if (!is_stderr && cp->is_first_server_data)
    {
        cp->is_first_server_data = false;

        if (cp->type != TS_SSH_CHANNEL_TYPE_SFTP)
        {
            char buf[512] = {0};

            const char* auth_mode;
            if (_this->m_auth_type == TP_AUTH_TYPE_PASSWORD)
                auth_mode = "password";
            else if (_this->m_auth_type == TP_AUTH_TYPE_PRIVATE_KEY)
                auth_mode = "private-key";
            else
                auth_mode = "unknown";

            int w = MIN(cp->win_width, 64);
            ex_astr line(w, '=');

            snprintf(
                    buf, sizeof(buf), "\r\n"\
                "%s\r\n"\
                "Teleport SSH Bastion Server...\r\n"\
                "  - teleport to %s:%d\r\n"\
                "  - authorized by %s\r\n"\
                "%s\r\n"\
                "\r\n\r\n", line.c_str(), _this->m_conn_ip.c_str(), _this->m_conn_port, auth_mode, line.c_str()
            );

            if (!_this->_send(cp->rsc_tp2cli, 0, buf, strlen(buf)))
            {
                cp->need_close = true;
                return SSH_ERROR;
            }
        }
    }
#endif

    if (!_this->_send(cp->rsc_tp2cli, is_stderr, data, len))
    {
        cp->need_close = true;
        return SSH_ERROR;
    }

    return static_cast<int>(len);

#if 0
    // 1b 5d 30 3b "root@host: ~" 07   ===  \033]0;root@host: ~\007
    // 分析收到的服务端数据包，如果包含类似  \033]0;AABB\007  这样的数据，客户端可能会根据此改变窗口标题为AABB（例如putty）
    // 我们需要替换这部分数据，使之显示类似 \033]0;TP#ssh://remote-ip\007 这样的标题。
    // 但是这样会降低一些性能，因此目前不启用，保留此部分代码备用。
    if (is_stderr) {
        ret = ssh_channel_write_stderr(cp->cli_channel, data, len);
    }
    else if (cp->type != TS_SSH_CHANNEL_TYPE_SHELL) {
        ret = ssh_channel_write(cp->cli_channel, data, len);
    }
    else {
        if (len > 5 && len < 256) {
            const ex_u8* _begin = ex_memmem((const ex_u8*)data, len, (const ex_u8*)"\033]0;", 4);
            if (NULL != _begin) {
                size_t len_before = _begin - (const ex_u8*)data;
                const ex_u8* _end = ex_memmem(_begin + 4, len - len_before, (const ex_u8*)"\007", 1);
                if (NULL != _end)
                {
                    _end++;

                    // 这个包中含有改变标题的数据，将标题换为我们想要的
                    EXLOGD("-- found title\n");
                    size_t len_end = len - (_end - (const ex_u8*)data);
                    MemBuffer mbuf;

                    if (len_before > 0)
                        mbuf.append((ex_u8*)data, len_before);

                    mbuf.append((ex_u8*)"\033]0;TP#ssh://", 13);
                    mbuf.append((ex_u8*)_this->m_conn_ip.c_str(), _this->m_conn_ip.length());
                    mbuf.append((ex_u8*)"\007", 1);

                    if (len_end > 0)
                        mbuf.append((ex_u8*)_end, len_end);

                    if (mbuf.size() > 0)
                    {
                        for (;;) {
                            ret = ssh_channel_write(cp->cli_channel, mbuf.data(), mbuf.size());
                            if (ret == SSH_ERROR)
                                break;
                            if (ret == mbuf.size()) {
                                ret = len; // 表示我们已经处理了所有的数据了。
                                break;
                            }
                            else {
                                mbuf.pop(ret);
                                ex_sleep_ms(100);
                            }
                        }
                        // 						if (ret <= 0)
                        // 							EXLOGE("[ssh] send to client failed (1).\n");
                        // 						else
                        // 							ret = len;
                    }
                    else
                    {
                        ret = ssh_channel_write(cp->cli_channel, data, len);
                    }
                }
                else
                {
                    ret = ssh_channel_write(cp->cli_channel, data, len);
                }
            }
            else {
                ret = ssh_channel_write(cp->cli_channel, data, len);
            }
        }
        else {
            ret = ssh_channel_write(cp->cli_channel, data, len);
        }
    }
#endif
}
