#include "tpssh_srv.h"
#include "tpssh_session.h"
// #include "tpp_env.h"

#include <algorithm>
#include <teleport_const.h>

#if 0
TP_SSH_CHANNEL_PAIR::TP_SSH_CHANNEL_PAIR() {
    type = TS_SSH_CHANNEL_TYPE_UNKNOWN;
    cli_channel = nullptr;
    srv_channel = nullptr;
    last_access_timestamp = (ex_u32) time(nullptr);

    state = TP_SESS_STAT_RUNNING;
    db_id = 0;
    channel_id = 0;

    win_width = 0;
    is_first_server_data = true;
    need_close = false;

    server_ready = false;
    maybe_cmd = false;
    process_srv = false;
    client_single_char = false;

    cmd_char_pos = cmd_char_list.begin();
}
#endif

SshServerSide::SshServerSide(SshSession *s, ssh_session sess_tp2cli, const std::string &thread_name) :
        ExThreadBase(thread_name.c_str()),
        m_owner(s),
        m_session(sess_tp2cli),
        m_conn_info(nullptr) {

    m_auth_error = TPE_FAILED;
    m_first_auth = true;
    m_allow_user_input_password = false;
    m_auth_fail_count = 0;

    m_auth_type = TP_AUTH_TYPE_PASSWORD;

    m_ssh_ver = 2;    // default to SSHv2

    m_is_logon = false;
    m_need_stop_poll = false;
    m_need_send_keepalive = false;

    m_recving_from_srv = false;
    m_recving_from_cli = false;

    memset(&m_srv_cb, 0, sizeof(m_srv_cb));
    ssh_callbacks_init(&m_srv_cb);
    m_srv_cb.userdata = this;

    memset(&m_channel_with_cli_cb, 0, sizeof(m_channel_with_cli_cb));
    ssh_callbacks_init(&m_channel_with_cli_cb);
    m_channel_with_cli_cb.userdata = this;

    m_srv_cb.auth_password_function = _on_auth_password_request;
    m_srv_cb.channel_open_request_session_function = _on_new_channel_request;

    m_channel_with_cli_cb.channel_data_function = _on_client_channel_data;
    // channel_eof_function
    m_channel_with_cli_cb.channel_close_function = _on_client_channel_close;
    // channel_signal_function
    // channel_exit_status_function
    // channel_exit_signal_function
    m_channel_with_cli_cb.channel_pty_request_function = _on_client_pty_request;
    m_channel_with_cli_cb.channel_shell_request_function = _on_client_shell_request;
    // channel_auth_agent_req_function
    // channel_x11_req_function
    m_channel_with_cli_cb.channel_pty_window_change_function = _on_client_pty_win_change;
    m_channel_with_cli_cb.channel_exec_request_function = _on_client_channel_exec_request;
    // channel_env_request_function
    m_channel_with_cli_cb.channel_subsystem_request_function = _on_client_channel_subsystem_request;

    ssh_set_server_callbacks(m_session, &m_srv_cb);
}

SshServerSide::~SshServerSide() {
    _on_stop();

    if (m_conn_info) {
#ifdef TEST_SSH_SESSION_000000
        delete m_conn_info;
#else
        g_ssh_env.free_connect_info(m_conn_info);
#endif
    }
    m_conn_info = nullptr;

    EXLOGD("[ssh] session tp<->client destroy: %s.\n", m_sid.c_str());
}

bool SshServerSide::init() {
    return true;
}

void SshServerSide::_on_stop() {
    // ExThreadBase::_on_stop();
}

void SshServerSide::_on_stopped() {
    _close_channels();

    if (nullptr != m_session) {
        ssh_disconnect(m_session);
        ssh_free(m_session);
        m_session = nullptr;
    }
    // m_proxy->session_finished(this);
    //m_owner->tp2cli_end(this);
}

#if 0
void SshServerSide::_session_error(int err_code) {
#ifndef TEST_SSH_SESSION_000000
    int db_id = 0;
    if (!g_ssh_env.session_begin(m_conn_info, &db_id) || db_id == 0) {
        EXLOGE("[ssh] can not write session error to database.\n");
        return;
    }

    g_ssh_env.session_end(m_sid.c_str(), db_id, err_code);
#endif
}
#endif


void SshServerSide::_close_channels() {
    ExThreadSmartLock locker(m_lock);

    if (m_channels.empty())
        return;

    EXLOGV("[ssh] close all channels.\n");

    auto it = m_channels.begin();
    for (; it != m_channels.end(); ++it) {
//        // 先从通道管理器中摘掉这个通道（因为马上就要关闭它了）
//        m_owner->remove_channel(*it);
//        if (!ssh_channel_is_closed(*it))
//            ssh_channel_close(*it);
//        ssh_channel_free(*it);
//        *it = nullptr;

        if (!ssh_channel_is_closed(*it)) {
            ssh_channel_close(*it);
            ssh_channel_free(*it);
        }
    }

    m_channels.clear();
}
#if 0
void SshServerSide::_check_channels() {
    ExThreadSmartLock locker(m_lock);

    auto it = m_channel_mgr.begin();
    for (; it != m_channel_mgr.end();) {
        ssh_channel cli = (*it)->cli_channel;
        ssh_channel srv = (*it)->srv_channel;

        // of both cli-channel and srv-channel closed, free and erase.
        if (
                (cli != nullptr && ssh_channel_is_closed(cli) && srv != nullptr && ssh_channel_is_closed(srv))
                || (cli == nullptr && srv == nullptr)
                || (cli == nullptr && srv != nullptr && ssh_channel_is_closed(srv))
                || (srv == nullptr && cli != nullptr && ssh_channel_is_closed(cli))
                ) {
            if (cli) {
                ssh_channel_free(cli);
                cli = nullptr;
            }
            if (srv) {
                ssh_channel_free(srv);
                srv = nullptr;
            }
            _record_end((*it));

            delete (*it);
            m_channel_mgr.erase(it++);

            continue;
        }

        // check if channel need close
        bool need_close = (*it)->need_close;
        if (!need_close) {
            if (cli != nullptr && ssh_channel_is_closed(cli)) {
                need_close = true;
            }
            if (srv != nullptr && ssh_channel_is_closed(srv)) {
                need_close = true;
            }
        }

        if (need_close) {
            if (cli != nullptr && !ssh_channel_is_closed(cli)) {
                ssh_channel_close(cli);
            }

            if (srv != nullptr && !ssh_channel_is_closed(srv)) {
                ssh_channel_close(srv);
            }
        }

        ++it;
    }
}
#endif

void SshServerSide::channel_closed(ssh_channel ch) {
    ExThreadSmartLock locker(m_lock);
    auto it = m_channels.begin();
    for(; it != m_channels.end(); ++it) {
        if ((*it) == ch) {
            m_channels.erase(it);
            break;
        }
    }
}


void SshServerSide::_thread_loop() {
    // 安全连接（密钥交换）
    int err = ssh_handle_key_exchange(m_session);
    if (err != SSH_OK) {
        EXLOGE("[ssh] key exchange with client failed: %s\n", ssh_get_error(m_session));
        return;
    }

    ssh_event event_loop = ssh_event_new();
    if (nullptr == event_loop) {
        EXLOGE("[ssh] can not create event loop.\n");
        return;
    }
    err = ssh_event_add_session(event_loop, m_session);
    if (err != SSH_OK) {
        EXLOGE("[ssh] can not add tp2client session into event loop.\n");
        return;
    }

    //int timer_for_auth = 0;

    // 认证，并打开一个通道
    while (!(m_is_logon && !m_channels.empty())) {
        if (m_need_stop_poll) {
            EXLOGE("[ssh] error when connect and auth.\n");
            break;
        }
        err = ssh_event_dopoll(event_loop, 1000);
        if (err == SSH_AGAIN) {
            //timer_for_auth++;
            //if (timer_for_auth >= 60) {
            //    EXLOGE("[ssh] can not auth and open channel in 60 seconds, session end.\n");
            //    m_need_stop_poll = true;
            //    break;
            //}
        }
        else if (err != SSH_OK) {
            EXLOGE("[ssh] error when event poll: %s\n", ssh_get_error(m_session));
            m_need_stop_poll = true;
            break;
        }
    }

    if (m_need_stop_poll) {
        ssh_event_remove_session(event_loop, m_session);
        ssh_event_free(event_loop);
        return;
    }

    EXLOGW("[ssh] authenticated and got a channel.\n");

    // 更新会话的最后访问时间（变为非0，开始接受通道和会话状态检查，必要时会被关闭、清理掉）
    m_owner->update_last_access_time();

    int timer_for_keepalive = 0;
    do {
        err = ssh_event_dopoll(event_loop, 1000);
//        EXLOGV("-- tp2cli dopool return %d.\n", err);

        if (m_need_stop_poll)
            break;
        if (err == SSH_OK)
            continue;

        if (err == SSH_AGAIN) {
            // _check_channels();

            if (m_need_send_keepalive) {
                timer_for_keepalive++;
                if (timer_for_keepalive >= 60) {
                    timer_for_keepalive = 0;
                    EXLOGD("[ssh] send keep-alive.\n");
                    ssh_send_ignore(m_session, "keepalive@openssh.com");
                }
            }
        }
        else if (err == SSH_ERROR) {
            if (0 != ssh_get_error_code(m_session)) {
                EXLOGW("[ssh] %s\n", ssh_get_error(m_session));
            }
            m_need_stop_poll = true;
            break;
        }
    } while (!m_channels.empty());

    EXLOGV("[ssh] session of [%s:%d] are closed.\n", m_client_ip.c_str(), m_client_port);
    if (!m_channels.empty()) {
        EXLOGW("[ssh] [%s:%d] not all tp<->client channels in this session are closed, close them later.\n", m_client_ip.c_str(), m_client_port);
    }

    ssh_event_remove_session(event_loop, m_session);
    ssh_event_free(event_loop);
}

int SshServerSide::_auth(const char *user, const char *password) {
    // v3.6.0
    // 场景
    //  1. 标准方式：在web界面上登记远程账号的用户名和密码，远程连接时由TP负责填写；
    //  2. 手动输入密码：web界面上仅登记远程账号的用户名，不填写密码，每次远程连接时由操作者输入密码；
    //  3. 手动输入用户名和密码：web界面上选择连接时输入用户名密码，每次远程时，web界面上先提示操作者输入远程用户名，然后开始连接，
    //                       在连接过程中要求输入密码；
    //        注意，这种方式，在数据库中的远程账号用户名字段，填写的是"INTERACTIVE_USER"。
    //  4. 脱离web进行远程连接：这种方式类似于手动输入用户名和密码，需要配合授权码使用，操作者需要使用 远程用户名--授权码  组合形式
    //                       作为ssh连接的用户名来连接到TP的SSH核心服务。
    // 用户名的格式：
    //    username--CODE   用两个减号分隔第一部分和第二部分。第一部分为用户名，第二部分为会话ID或者授权码
    // 范例：
    //    TP--03ad57            // 最简单的形式，省略了远程用户名(用大写TP代替)，核心服务从会话的连接信息中取得远程用户名。
    //    apex.liu--25c308      // 总是从最后两个减号开始分解，这是操作者手动输入用户名的情况
    //    apex-liu--7769b2e3    // 8字节为授权码，可以脱离web页面和助手使用
    //
    // 如果第一部分为大写 TP，则从连接信息中获取远程用户名，如果此时连接信息中的远程用户名是大写的 INTERACTIVE_USER，则报错。
    // 如果第二部分是授权码，这可能是脱离web使用，核心服务需要通过web接口获取响应的连接信息，并临时生成一个会话ID来使用。
    // 授权码具有有效期，在此有效期期间可以进行任意数量的连接，可用于如下场景：
    //   1. 操作者将 远程用户名--授权码 和对应的密码添加到ssh客户端如SecureCRT或者xShell中，以后可以脱离web使用；
    //   2. 邀请第三方运维人员临时参与某个运维工作，可以生成一个相对短有效期的授权码发给第三方运维人员。
    // 授权码到期时，已经连接的会话会被强行中断。
    // 授权码可以绑定到主机，也可绑定到具体远程用户。前者需要操作者自己填写真实的远程用户名，后者则无需填写，可以直接登录。
    // 为增加安全性，内部人员使用时可以配合动态密码使用，而对于临时的授权码，可以生成一个配套的临时密码来进行认证。
    // 此外，还可以利用QQ机器人或微信小程序，操作者向QQ机器人发送特定指令，QQ机器人则发送一个新的临时密码。
    //
    // Linux系统中，用户名通常长度不超过8个字符，并且由大小写字母和/或数字组成。登录名中不能有冒号(，因为冒号在这里是分隔符。为了兼容
    // 起见，登录名中最好不要包含点字符(.)，并且不使用连字符(-)和加号(+)打头。

    if (m_first_auth) {
        std::string tmp(user);
        std::string::size_type tmp_pos = tmp.rfind("--");
        if (tmp_pos == std::string::npos) {
            m_need_stop_poll = true;
            m_owner->on_error(TP_SESS_STAT_ERR_SESSION);
            return SSH_AUTH_SUCCESS;
        }

        std::string _name;
        std::string _sid;
        _name.assign(tmp, 0, tmp_pos);
        m_sid.assign(tmp, tmp_pos + 2, tmp.length() - tmp_pos - 2);

        if (_name != "TP")
            m_acc_name = _name;

        //EXLOGV("[ssh] authenticating, session-id: %s\n", _this->m_sid.c_str());
        EXLOGD("[ssh] first auth, user: %s, password: %s\n", user, password);

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

        m_conn_info->host_ip = "39.97.125.170";
        m_conn_info->conn_ip = "39.97.125.170";
        m_conn_info->conn_port = 22;
//        m_conn_info->acc_username = "root";
        m_conn_info->acc_secret = "Mc7b5We8";
        m_conn_info->acc_username = "INTERACTIVE_USER";
//        m_conn_info->acc_secret = "";
#else
        _this->m_conn_info = g_ssh_env.get_connect_info(_this->m_sid.c_str());
#endif

        if (!m_conn_info) {
            EXLOGE("[ssh] no such session: %s\n", m_sid.c_str());
            m_need_stop_poll = true;
            m_owner->on_error(TP_SESS_STAT_ERR_SESSION);
            return SSH_AUTH_SUCCESS;
        }

        m_conn_ip = m_conn_info->conn_ip;
        m_conn_port = m_conn_info->conn_port;
        m_auth_type = m_conn_info->auth_type;
        // m_acc_name = m_conn_info->acc_username;
        m_acc_secret = m_conn_info->acc_secret;
        m_flags = m_conn_info->protocol_flag;
        if (m_conn_info->protocol_type != TP_PROTOCOL_TYPE_SSH) {
            EXLOGE("[ssh] session '%s' is not for SSH.\n", m_sid.c_str());
            m_need_stop_poll = true;
            m_owner->on_error(TP_SESS_STAT_ERR_INTERNAL);
            return SSH_AUTH_SUCCESS;
        }

        _name = m_conn_info->acc_username;
        if ((m_acc_name.empty() && _name == "INTERACTIVE_USER")
            || (!m_acc_name.empty() && _name != "INTERACTIVE_USER")
            ) {
            EXLOGE("[ssh] conflict account info.\n");
            m_need_stop_poll = true;
            m_owner->on_error(TP_SESS_STAT_ERR_SESSION);
            return SSH_AUTH_SUCCESS;
        }
        if (m_acc_name.empty())
            m_acc_name = _name;

        if (m_acc_secret.empty()) {
            // 如果TP中未设置远程账号密码，表示允许用户自行输入密码
            m_allow_user_input_password = true;

            // 如果传入的password为特定值，应该是由助手调用客户端，填写的密码
            // 直接返回认证失败，这样客户端会让用户输入密码
            if (0 == strcmp(password, "INTERACTIVE_USER"))
                return SSH_AUTH_DENIED;

            // 用户脱离TP-WEB，直接使用客户端输入的密码
            m_acc_secret = password;
        }
    }
    else {
        // 允许用户自行输入密码的情况下，第二次认证，参数password就是用户自己输入的密码了。
        m_acc_secret = password;
    }

    // 连接到远程主机并进行认证
    uint32_t rv = TP_SESS_STAT_RUNNING;
    auto tp2srv = m_owner->connect_to_host(m_conn_ip, m_conn_port, m_acc_name, rv);
    if (!tp2srv || rv != TP_SESS_STAT_RUNNING) {
        m_need_stop_poll = true;
        m_owner->on_error(rv);
        return SSH_AUTH_SUCCESS;
    }

    EXLOGV("[ssh] connected, now auth, type=%d, secret=%s\n", m_auth_type, m_acc_secret.c_str());
    rv = tp2srv->auth(m_auth_type, m_acc_secret);
    if (rv == TP_SESS_STAT_RUNNING) {
        // 操作成功！！
        //m_need_stop_poll = false;
        m_auth_error = TPE_OK;
        m_is_logon = true;
        return SSH_AUTH_SUCCESS;
    }
    else if (rv == TP_SESS_STAT_ERR_AUTH_DENIED) {
        // 连接成功，但是认证失败
        if (m_auth_type == TP_AUTH_TYPE_PRIVATE_KEY || !m_allow_user_input_password || m_auth_fail_count >= 3) {
            m_need_stop_poll = true;
            m_owner->on_error(TP_SESS_STAT_ERR_AUTH_DENIED);
            return SSH_AUTH_SUCCESS;
        }

        m_auth_fail_count++;
        return SSH_AUTH_DENIED;
    }
    else {
        m_need_stop_poll = true;
        m_owner->on_error(rv);
        return SSH_AUTH_SUCCESS;
    }
}

int SshServerSide::_on_auth_password_request(ssh_session session, const char *user, const char *password, void *userdata) {
    auto *_this = (SshServerSide *) userdata;
    int ret = _this->_auth(user, password);
    if (_this->m_first_auth)
        _this->m_first_auth = false;
    // _this->m_owner->update_last_access_time();
    return ret;
}

ssh_channel SshServerSide::_on_new_channel_request(ssh_session session, void *userdata) {
    // 客户端尝试打开一个通道（然后才能通过这个通道发控制命令或者收发数据）
    EXLOGV("[ssh] client open channel\n");

    auto _this = (SshServerSide *) userdata;
    auto tp2srv = _this->m_owner->tp2srv();
    // _this->m_owner->update_last_access_time();

    // 如果认证过程中已经发生了不可继续的错误，这里返回null，中断连接
    if (_this->m_auth_error != TPE_OK || !tp2srv) {
        _this->m_need_stop_poll = true;
        EXLOGE("[ssh] before request shell, already failed.\n");
        return nullptr;
    }

    EXLOGV("-- cp a\n");

    ssh_channel ch_tp2cli = ssh_channel_new(session);
    if (ch_tp2cli == nullptr) {
        EXLOGE("[ssh] can not create channel for communicate client.\n");
        return nullptr;
    }
    ssh_set_channel_callbacks(ch_tp2cli, &_this->m_channel_with_cli_cb);
    _this->m_channels.push_back(ch_tp2cli);

    EXLOGV("-- cp b\n");

    // 我们也要向真正的服务器申请打开一个通道，来进行转发
    ssh_channel ch_tp2srv = tp2srv->request_new_channel();
    if (ch_tp2srv == nullptr) {
        EXLOGE("[ssh] can not create channel for server.\n");
        return nullptr;
    }

    EXLOGV("-- cp c\n");

    // start the thread.
    tp2srv->start();

    if (!_this->m_owner->make_channel_pair(ch_tp2cli, ch_tp2srv)) {
        EXLOGE("[ssh] can not make channel pair.\n");
        return nullptr;
    }

#if 0
    if (SSH_OK != ssh_channel_open_session(srv_channel)) {
        EXLOGE("[ssh] error opening channel to real server: %s\n", ssh_get_error(_this->m_srv_session));
        ssh_channel_free(channel_to_cli);
        ssh_channel_free(srv_channel);
        return nullptr;
    }
    ssh_set_channel_callbacks(srv_channel, &_this->m_srv_channel_cb);

    TP_SSH_CHANNEL_PAIR *cp = new TP_SSH_CHANNEL_PAIR;
    cp->type = TS_SSH_CHANNEL_TYPE_UNKNOWN;
    cp->cli_channel = channel_to_cli;
    cp->srv_channel = srv_channel;
    cp->last_access_timestamp = (ex_u32) time(nullptr);

    if (!_this->_record_begin(cp)) {
        ssh_channel_close(channel_to_cli);
        ssh_channel_free(channel_to_cli);
        ssh_channel_close(srv_channel);
        ssh_channel_free(srv_channel);
        delete cp;
        return nullptr;
    }

    // 将客户端和服务端的通道关联起来
    {
        ExThreadSmartLock locker(_this->m_lock);
        _this->m_channel_mgr.push_back(cp);
    }
#endif // 0

    EXLOGV("-- cp d\n");

    EXLOGD("[ssh] channel for client and server created.\n");
    return ch_tp2cli;
}

#if 0
TP_SSH_CHANNEL_PAIR *SshServerSide::_get_channel_pair(int channel_side, ssh_channel channel) {
    ExThreadSmartLock locker(m_lock);

    auto it = m_channel_mgr.begin();
    for (; it != m_channel_mgr.end(); ++it) {
        if (channel_side == TP_SSH_CLIENT_SIDE) {
            if ((*it)->cli_channel == channel)
                return (*it);
        }
        else {
            if ((*it)->srv_channel == channel)
                return (*it);
        }
    }

    return nullptr;
}
#endif

int SshServerSide::_on_client_pty_request(ssh_session session, ssh_channel channel, const char *term, int x, int y, int px, int py, void *userdata) {
    EXLOGD("[ssh] client request pty: %s, (%d, %d) / (%d, %d)\n", term, x, y, px, py);

    auto _this = (SshServerSide *) userdata;
    _this->m_owner->update_last_access_time();

    auto cp = _this->m_owner->get_channel_pair(channel);
    if (nullptr == cp) {
        EXLOGE("[ssh] when client request pty, not found channel pair.\n");
        return SSH_ERROR;
    }

    cp->win_width = x;
    cp->rec.record_win_size_startup(x, y);

    int err = ssh_channel_request_pty_size(cp->channel_tp2srv, term, x, y);
    if (err != SSH_OK) {
        EXLOGE("[ssh] pty request from server got %d\n", err);
    }

    return err;
}

int SshServerSide::_on_client_shell_request(ssh_session session, ssh_channel channel, void *userdata) {
    EXLOGD("[ssh] client request shell\n");

    auto _this = (SshServerSide *) userdata;
    _this->m_owner->update_last_access_time();

    if ((_this->m_flags & TP_FLAG_SSH_SHELL) != TP_FLAG_SSH_SHELL) {
        EXLOGE("[ssh] ssh-shell disabled by ops-policy.\n");
        return SSH_ERROR;
    }
    EXLOGV("-- cp y1\n");

    auto cp = _this->m_owner->get_channel_pair(channel);
    if (!cp) {
        EXLOGE("[ssh] when client request shell, not found channel pair.\n");
        return SSH_ERROR;
    }

    cp->type = TS_SSH_CHANNEL_TYPE_SHELL;
    cp->update_session_state(TP_PROTOCOL_TYPE_SSH_SHELL, TP_SESS_STAT_STARTED);

    EXLOGV("-- cp y2\n");
//    std::string msg("Hello world.\r\n");
//    ssh_channel_write(cp->channel_tp2cli, msg.c_str(), msg.length());
    EXLOGV("-- cp y3\n");

    // sometimes it will block here. the following function will never return.
    // Fixed at 20190104:
    // at libssh ssh_handle_packets_termination(), set timeout always to SSH_TIMEOUT_USER.
    // and at ssh_handle_packets(), when call ssh_poll_add_events() should use POLLIN|POLLOUT.
    // 注意，此处有嵌套死锁的问题。
    // 在本回调函数中，向另一侧要求打开shell，另一侧会收到第一包数据（一般是 welcome 信息），需要转发给本侧，
    // 但是本侧尚在回调函数中，处于阻塞状态，因此发送会阻塞，从而形成死锁。
    int err = ssh_channel_request_shell(cp->channel_tp2srv);
    if (err != SSH_OK) {
        EXLOGE("[ssh] shell request from server got %d\n", err);
    }
    EXLOGV("-- cp y4\n");

    return err;
}

void SshServerSide::_on_client_channel_close(ssh_session session, ssh_channel channel, void *userdata) {
    // 注意，此回调会在通道已经被关闭之后调用
    // 无需做额外操作，关闭的通道会由 SshSession 实例定期清理（包括关闭对端通道）
    EXLOGV("[ssh] channel client<->tp closed.\n");


//    auto _this = (SshServerSide *) userdata;
//    auto tp2srv = _this->m_owner->tp2srv();
//    auto cp = _this->m_owner->get_channel_pair(channel);
//
//    if (nullptr == cp) {
//        EXLOGE("[ssh] when client channel close, not found channel pair.\n");
//        return;
//    }

//    _this->m_owner->remove_channel(channel);
////    if (!ssh_channel_is_closed(channel))
////        ssh_channel_close(channel);
//    ssh_channel_free(channel);
//
//    // 与客户端的通道关闭了，同时关闭与远程主机的对应通道
//    cp->channel_tp2cli = nullptr;
//    cp->need_close = true;
////    tp2srv->close_channel(cp->channel_tp2srv);
////    cp->close();
//


//    _this->m_need_stop_poll = true;

//    //EXLOGD("[ssh] [channel:%d]   -- end by client channel close\n", cp->channel_id);
//    //_this->_record_end(cp);
//
//    if (cp->srv_channel == nullptr) {
//        EXLOGW("[ssh] when client channel close, server-channel not exists.\n");
//    }
//    else {
//        if (!ssh_channel_is_closed(cp->srv_channel)) {
//            // ssh_channel_close(cp->srv_channel);
//            //cp->need_close = true;
//            //_this->m_need_stop_poll = true;
//        }
//    }
}

int SshServerSide::_on_client_pty_win_change(ssh_session session, ssh_channel channel, int width, int height, int pxwidth, int pwheight, void *userdata) {
    EXLOGD("[ssh] client pty win size change to: (%d, %d)\n", width, height);

    auto _this = (SshServerSide *) userdata;
    _this->m_owner->update_last_access_time();

    auto cp = _this->m_owner->get_channel_pair(channel);
    if (nullptr == cp) {
        EXLOGE("[ssh] when client pty win change, not found channel pair.\n");
        return SSH_ERROR;
    }

    cp->win_width = width;
    cp->rec.record_win_size_change(width, height);

    return ssh_channel_change_pty_size(cp->channel_tp2srv, width, height);
//    return _this->m_cli->change_pty_size(width, height);
}

int SshServerSide::_on_client_channel_subsystem_request(ssh_session session, ssh_channel channel, const char *subsystem, void *userdata) {
    EXLOGD("[ssh] on_client_channel_subsystem_request(): %s\n", subsystem);

    auto _this = (SshServerSide *) userdata;
    _this->m_owner->update_last_access_time();

//    if (_this->m_ssh_ver == 1) {
//        // SSHv1 not support subsystem, so some client like WinSCP will use shell-mode instead.
//        EXLOGE("[ssh] real host running on SSHv1, does not support subsystem `%s`.\n", subsystem);
//        return SSH_ERROR;
//    }

    auto cp = _this->m_owner->get_channel_pair(channel);
    if (nullptr == cp) {
        EXLOGE("[ssh] when request channel subsystem, not found channel pair.\n");
        return SSH_ERROR;
    }

    // 目前只支持SFTP子系统
    if (strcmp(subsystem, "sftp") != 0) {
        EXLOGE("[ssh] support `sftp` subsystem only, but got `%s`.\n", subsystem);
        cp->state = TP_SESS_STAT_ERR_UNSUPPORT_PROTOCOL;
        return SSH_ERROR;
    }

    if ((_this->m_flags & TP_FLAG_SSH_SFTP) != TP_FLAG_SSH_SFTP) {
        EXLOGE("[ssh] ssh-sftp disabled by ops-policy.\n");
        return SSH_ERROR;
    }

    //EXLOGD("[ssh]   ---> request channel subsystem from server\n");
    int err = ssh_channel_request_subsystem(cp->channel_tp2srv, subsystem);
    //EXLOGD("[ssh]   <--- request channel subsystem from server\n");
    if (err != SSH_OK) {
        EXLOGE("[ssh] request channel subsystem from server got %d\n", err);
        return err;
    }

    cp->type = TS_SSH_CHANNEL_TYPE_SFTP;
    cp->update_session_state(TP_PROTOCOL_TYPE_SSH_SFTP, TP_SESS_STAT_STARTED);

    return SSH_OK;

//    return _this->m_cli->request_subsystem(subsystem);
}

int SshServerSide::_on_client_channel_exec_request(ssh_session session, ssh_channel channel, const char *command, void *userdata) {
    EXLOGW("[ssh] not-impl: client_channel_exec_request(): %s\n", command);
    return SSH_ERROR;
}

int SshServerSide::_on_client_channel_data(ssh_session session, ssh_channel channel, void *data, unsigned int len, int is_stderr, void *userdata) {
    //EXLOG_BIN(static_cast<uint8_t *>(data), len, " ---> on_client_channel_data [is_stderr=%d]:", is_stderr);
    //EXLOGD(" ---> recv from client %d B\n", len);

    auto _this = (SshServerSide *) userdata;
    _this->m_owner->update_last_access_time();

//    // 当前线程正在接收服务端返回的数据，因此我们直接返回，这样紧跟着会重新再发送此数据的
//    if (_this->m_recving_from_srv) {
//        // EXLOGD("recving from srv...try again later...\n");
//        return 0;
//    }
//    if (_this->m_recving_from_cli) {
//        // EXLOGD("recving from cli...try again later...\n");
//        return 0;
//    }

    auto cp = _this->m_owner->get_channel_pair(channel);
    if (nullptr == cp) {
        EXLOGE("[ssh] when receive client channel data, not found channel pair.\n");
        return SSH_ERROR;
    }

//    _this->m_recving_from_cli = true;

    if (cp->type == TS_SSH_CHANNEL_TYPE_SHELL) {
        // 在收取服务端数据直到显示命令行提示符之前，不允许发送客户端数据到服务端，避免日志记录混乱。
//        if (!cp->server_ready) {
//            _this->m_recving_from_cli = false;
//            return 0;
//        }

        // 不可以拆分！！否则执行 rz 命令会出错！
        // xxxx 如果用户复制粘贴多行文本，我们将其拆分为每一行发送一次数据包
//         for (unsigned int i = 0; i < len; ++i) {
//             if (((ex_u8 *) data)[i] == 0x0d) {
//                 _len = i + 1;
//                 break;
//             }
//         }

        //cp->process_ssh_command(channel, (ex_u8 *) data, len);
        // _this->_process_ssh_command(cp, TP_SSH_CLIENT_SIDE, (ex_u8 *) data, _len);
    }
    else {
        cp->process_sftp_command(channel, (ex_u8 *) data, len);
        // _this->_process_sftp_command(cp, (ex_u8 *) data, _len);
    }

    int ret = 0;
//    if (is_stderr)
//        ret = ssh_channel_write_stderr(cp->channel_tp2srv, data, len);
//    else
//        ret = ssh_channel_write(cp->channel_tp2srv, data, len);


    ssh_set_blocking(_this->m_session, 0);
    EXLOGD("[ssh] -- cp a3.\n");

    int xx = 0;
    for (xx = 0; xx < 1000; ++xx) {

//        idx++;
//        EXLOGD(">>>>> %d . %d\n", cp->db_id, idx);

        // 直接转发数据到客户端
        if (is_stderr)
            ret = ssh_channel_write_stderr(cp->channel_tp2srv, data, len);
        else
            ret = ssh_channel_write(cp->channel_tp2srv, data, len);

//        EXLOGD("<<<<< %d . %d\n", cp->db_id, idx);

        if (ret == SSH_OK) {
//            EXLOGD("ssh_channel_write() ok.\n");
            break;
        }
        else if (ret == SSH_AGAIN) {
            EXLOGD("ssh_channel_write() need again, %d.\n", xx);
            ex_sleep_ms(50);
            continue;
        }
        else {
//            EXLOGD("ssh_channel_write() failed.\n");
            break;
        }
    }

    ssh_set_blocking(_this->m_session, 1);
    EXLOGD("[ssh] -- cp a4.\n");



    if (ret == SSH_ERROR) {
        EXLOGE("[ssh] send data(%dB) to server failed. [%d] %s\n", len, ret, ssh_get_error(_this->m_owner->tp2srv()));
        ssh_channel_close(channel);
        // cp->need_close = true;
    }

//    _this->m_recving_from_cli = false;

    return ret;
}
