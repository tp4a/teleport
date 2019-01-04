#include "ssh_session.h"
#include "ssh_proxy.h"
#include "tpp_env.h"

#include <algorithm>
#include <teleport_const.h>

TP_SSH_CHANNEL_PAIR::TP_SSH_CHANNEL_PAIR() {
    type = TS_SSH_CHANNEL_TYPE_UNKNOWN;
    cli_channel = NULL;
    srv_channel = NULL;
    last_access_timestamp = (ex_u32) time(NULL);

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

SshSession::SshSession(SshProxy *proxy, ssh_session sess_client) :
        ExThreadBase("ssh-session-thread"),
        m_proxy(proxy),
        m_cli_session(sess_client),
        m_srv_session(NULL),
        m_conn_info(NULL) {
    m_auth_type = TP_AUTH_TYPE_PASSWORD;

    m_ssh_ver = 2;    // default to SSHv2

    m_is_logon = false;
    m_have_error = false;
    m_recving_from_srv = false;
    m_recving_from_cli = false;

    memset(&m_srv_cb, 0, sizeof(m_srv_cb));
    ssh_callbacks_init(&m_srv_cb);
    m_srv_cb.userdata = this;

    memset(&m_cli_channel_cb, 0, sizeof(m_cli_channel_cb));
    ssh_callbacks_init(&m_cli_channel_cb);
    m_cli_channel_cb.userdata = this;

    memset(&m_srv_channel_cb, 0, sizeof(m_srv_channel_cb));
    ssh_callbacks_init(&m_srv_channel_cb);
    m_srv_channel_cb.userdata = this;

    // 	m_command_flag = 0;
    // 	m_cmd_char_pos = m_cmd_char_list.begin();
}

SshSession::~SshSession() {

    //_on_stop();

    if (NULL != m_conn_info) {
        g_ssh_env.free_connect_info(m_conn_info);
    }

    EXLOGD("[ssh] session destroy: %s.\n", m_sid.c_str());
}

void SshSession::_thread_loop(void) {
    _run();
}

void SshSession::_on_stop(void) {
    ExThreadBase::_on_stop();

    _close_channels();

    if (NULL != m_cli_session) {
        ssh_disconnect(m_cli_session);
        ssh_free(m_cli_session);
        m_cli_session = NULL;
    }
    if (NULL != m_srv_session) {
        ssh_disconnect(m_srv_session);
        ssh_free(m_srv_session);
        m_srv_session = NULL;
    }
}

void SshSession::_on_stopped() {
    m_proxy->session_finished(this);
}

void SshSession::_session_error(int err_code) {
    int db_id = 0;
    if (!g_ssh_env.session_begin(m_conn_info, &db_id) || db_id == 0) {
        EXLOGE("[ssh] can not write session error to database.\n");
        return;
    }

    g_ssh_env.session_end(m_sid.c_str(), db_id, err_code);
}

bool SshSession::_record_begin(TP_SSH_CHANNEL_PAIR *cp) {
    if (!g_ssh_env.session_begin(m_conn_info, &(cp->db_id))) {
        EXLOGE("[ssh] can not save to database, channel begin failed.\n");
        return false;
    } else {
        cp->channel_id = cp->db_id;
        //EXLOGD("[ssh] [channel:%d] channel begin\n", cp->channel_id);
    }


    if (!g_ssh_env.session_update(cp->db_id, m_conn_info->protocol_sub_type, TP_SESS_STAT_STARTED)) {
        EXLOGE("[ssh] [channel:%d] can not update state, cannel begin failed.\n", cp->channel_id);
        return false;
    }


    cp->rec.begin(g_ssh_env.replay_path.c_str(), L"tp-ssh", cp->db_id, m_conn_info);

    return true;
}

void SshSession::_record_end(TP_SSH_CHANNEL_PAIR *cp) {
    if (cp->db_id > 0) {
        //EXLOGD("[ssh] [channel:%d] channel end with code: %d\n", cp->channel_id, cp->state);

        // 如果会话过程中没有发生错误，则将其状态改为结束，否则记录下错误值
        if (cp->state == TP_SESS_STAT_RUNNING || cp->state == TP_SESS_STAT_STARTED)
            cp->state = TP_SESS_STAT_END;

        g_ssh_env.session_end(m_sid.c_str(), cp->db_id, cp->state);

        cp->db_id = 0;
    } else {
        //EXLOGD("[ssh] [channel:%d] when channel end, no db-id.\n", cp->channel_id);
    }
}

void SshSession::_close_channels(void) {
    ExThreadSmartLock locker(m_lock);

    tp_channels::iterator it = m_channels.begin();
    for (; it != m_channels.end(); ++it) {
// 		ssh_channel ch = (*it)->srv_channel;
// 		if (ch != NULL) {
// 			if (!ssh_channel_is_closed(ch)) {
// 				ssh_channel_close(ch);
// 			}
// 			ssh_channel_free(ch);
// 		}
// 
// 		ch = (*it)->cli_channel;
// 		if (ch != NULL) {
// 			if (!ssh_channel_is_closed(ch)) {
// 				ssh_channel_close(ch);
// 			}
// 			ssh_channel_free(ch);
// 		}
// 
// 		//EXLOGD("[ssh] [channel:%d]  --- end by close all channel\n", (*it)->channel_id);
// 		_record_end(*it);
//
//		delete (*it);

        (*it)->need_close = true;
        m_have_error = true;
    }

// 	m_channels.clear();
}

void SshSession::_check_channels() {
    ExThreadSmartLock locker(m_lock);

    tp_channels::iterator it = m_channels.begin();
    for (; it != m_channels.end();) {
        ssh_channel cli = (*it)->cli_channel;
        ssh_channel srv = (*it)->srv_channel;

        // of both cli-channel and srv-channel closed, free and erase.
        if (
                (cli != NULL && ssh_channel_is_closed(cli) && srv != NULL && ssh_channel_is_closed(srv))
                || (cli == NULL && srv == NULL)
                || (cli == NULL && srv != NULL && ssh_channel_is_closed(srv))
                || (srv == NULL && cli != NULL && ssh_channel_is_closed(cli))
                ) {
            if (cli) {
                ssh_channel_free(cli);
                cli = NULL;
            }
            if (srv) {
                ssh_channel_free(srv);
                srv = NULL;
            }
            _record_end((*it));

            delete (*it);
            m_channels.erase(it++);

            continue;
        }

        // check if channel need close
        bool need_close = (*it)->need_close;
        if (!need_close) {
            if (cli != NULL && ssh_channel_is_closed(cli)) {
                need_close = true;
            }
            if (srv != NULL && ssh_channel_is_closed(srv)) {
                need_close = true;
            }
        }

        if (need_close) {
            if (cli != NULL && !ssh_channel_is_closed(cli)) {
                ssh_channel_close(cli);
            }

            if (srv != NULL && !ssh_channel_is_closed(srv)) {
                ssh_channel_close(srv);
            }
        }

        ++it;
    }
}

void SshSession::_run(void) {
    m_srv_cb.auth_password_function = _on_auth_password_request;
    m_srv_cb.channel_open_request_session_function = _on_new_channel_request;

    m_srv_channel_cb.channel_data_function = _on_server_channel_data;
    m_srv_channel_cb.channel_close_function = _on_server_channel_close;

    m_cli_channel_cb.channel_data_function = _on_client_channel_data;
    // channel_eof_function
    m_cli_channel_cb.channel_close_function = _on_client_channel_close;
    // channel_signal_function
    // channel_exit_status_function
    // channel_exit_signal_function
    m_cli_channel_cb.channel_pty_request_function = _on_client_pty_request;
    m_cli_channel_cb.channel_shell_request_function = _on_client_shell_request;
    // channel_auth_agent_req_function
    // channel_x11_req_function
    m_cli_channel_cb.channel_pty_window_change_function = _on_client_pty_win_change;
    m_cli_channel_cb.channel_exec_request_function = _on_client_channel_exec_request;
    // channel_env_request_function
    m_cli_channel_cb.channel_subsystem_request_function = _on_client_channel_subsystem_request;


    ssh_set_server_callbacks(m_cli_session, &m_srv_cb);

    int err = SSH_OK;

    // 安全连接（密钥交换）
    err = ssh_handle_key_exchange(m_cli_session);
    if (err != SSH_OK) {
        EXLOGE("[ssh] key exchange with client failed: %s\n", ssh_get_error(m_cli_session));
        return;
    }

    ssh_event event_loop = ssh_event_new();
    if (NULL == event_loop) {
        EXLOGE("[ssh] can not create event loop.\n");
        return;
    }
    err = ssh_event_add_session(event_loop, m_cli_session);
    if (err != SSH_OK) {
        EXLOGE("[ssh] can not add client-session into event loop.\n");
        return;
    }

    // 认证，并打开一个通道
    while (!(m_is_logon && !m_channels.empty())) {
        if (m_have_error)
            break;
        err = ssh_event_dopoll(event_loop, -1);
        if (err != SSH_OK) {
            EXLOGE("[ssh] error when event poll: %s\n", ssh_get_error(m_cli_session));
            m_have_error = true;
            break;
        }
    }

    if (m_have_error) {
        ssh_event_remove_session(event_loop, m_cli_session);
        ssh_event_free(event_loop);
        EXLOGE("[ssh] Error, exiting loop.\n");
        return;
    }

    EXLOGW("[ssh] authenticated and got a channel.\n");

    // 现在双方的连接已经建立好了，开始转发
    ssh_event_add_session(event_loop, m_srv_session);
    do {
        //err = ssh_event_dopoll(event_loop, 5000);
        err = ssh_event_dopoll(event_loop, 1000);
        if (err == SSH_ERROR) {
            if (0 != ssh_get_error_code(m_cli_session)) {
                EXLOGE("[ssh] ssh_event_dopoll() [cli] %s\n", ssh_get_error(m_cli_session));
            } else if (0 != ssh_get_error_code(m_srv_session)) {
                EXLOGE("[ssh] ssh_event_dopoll() [srv] %s\n", ssh_get_error(m_srv_session));
            }

            //_close_channels();
            m_have_error = true;
        }

        if (m_ssh_ver == 1) {
            tp_channels::iterator it = m_channels.begin();
            if ((*it)->type == TS_SSH_CHANNEL_TYPE_SHELL || (*it)->type == TS_SSH_CHANNEL_TYPE_SFTP)
                break;
        }

        if (m_have_error || err == SSH_AGAIN) {
            m_have_error = false;
            // timeout.
            _check_channels();
        }
    } while (!m_channels.empty());

    if (m_channels.empty())
        EXLOGV("[ssh] [%s:%d] all channel in this session are closed.\n", m_client_ip.c_str(), m_client_port);

    ssh_event_remove_session(event_loop, m_cli_session);
    ssh_event_remove_session(event_loop, m_srv_session);
    ssh_event_free(event_loop);


    // 如果一边是走SSHv1，另一边是SSHv2，放在同一个event_loop时，SSHv1会收不到数据，放到循环中时，SSHv2得不到数据
    // 所以，当SSHv1的远程主机连接后，到建立好shell环境之后，就进入另一种读取数据的循环，不再使用ssh_event_dopoll()了。

    if (m_ssh_ver == 1) {
        tp_channels::iterator it = m_channels.begin(); // SSHv1只能打开一个channel
        ssh_channel cli = (*it)->cli_channel;
        ssh_channel srv = (*it)->srv_channel;

        bool ok = true;
        do {
            ex_u8 buf[4096] = {0};
            int len = 0;

            if (ok) {
                len = ssh_channel_read_nonblocking(cli, buf, 4096, 0);
                if (len < 0)
                    ok = false;
                else if (len > 0)
                    _on_client_channel_data(m_cli_session, cli, buf, len, 0, this);

                len = ssh_channel_read_nonblocking(cli, buf, 4096, 1);
                if (len < 0)
                    ok = false;
                else if (len > 0)
                    _on_client_channel_data(m_cli_session, cli, buf, len, 1, this);

                len = ssh_channel_read_nonblocking(srv, buf, 4096, 0);
                if (len < 0)
                    ok = false;
                else if (len > 0)
                    _on_server_channel_data(m_srv_session, srv, buf, len, 0, this);

                len = ssh_channel_read_nonblocking(srv, buf, 4096, 1);
                if (len < 0)
                    ok = false;
                else if (len > 0)
                    _on_server_channel_data(m_srv_session, srv, buf, len, 1, this);

                if (!ok) {
                    _close_channels();
                }
            }

            if (!ok) {
                _check_channels();
                ex_sleep_ms(1000);
                continue;
            }

            ex_sleep_ms(30);
        } while (m_channels.size() > 0);

        EXLOGV("[ssh] [%s:%d] all channel in this session are closed.\n", m_client_ip.c_str(), m_client_port);
    }
}

void SshSession::save_record() {
    ExThreadSmartLock locker(m_lock);

    tp_channels::iterator it = m_channels.begin();
    for (; it != m_channels.end(); ++it) {
        (*it)->rec.save_record();
    }
}

void SshSession::check_noop_timeout(ex_u32 t_now, ex_u32 timeout) {
    ExThreadSmartLock locker(m_lock);
    tp_channels::iterator it = m_channels.begin();
    for (; it != m_channels.end(); ++it) {
        if ((*it)->need_close)
            continue;
        if (t_now == 0)
            EXLOGW("[ssh] try close channel by kill.\n");
        else if (t_now - (*it)->last_access_timestamp > timeout)
            EXLOGW("[ssh] try close channel by timeout.\n");
        if (t_now == 0 || t_now - (*it)->last_access_timestamp > timeout) {
            (*it)->need_close = true;
            m_have_error = true;
        }
    }
}

int SshSession::_on_auth_password_request(ssh_session session, const char *user, const char *password, void *userdata) {
    // here, `user` is the session-id we need.
    SshSession *_this = (SshSession *) userdata;
    _this->m_sid = user;
    EXLOGV("[ssh] authenticating, session-id: %s\n", _this->m_sid.c_str());

    _this->m_conn_info = g_ssh_env.get_connect_info(_this->m_sid.c_str());

    if (NULL == _this->m_conn_info) {
        EXLOGE("[ssh] no such session: %s\n", _this->m_sid.c_str());
        _this->m_have_error = true;
        _this->_session_error(TP_SESS_STAT_ERR_SESSION);
        return SSH_AUTH_DENIED;
    } else {
        _this->m_conn_ip = _this->m_conn_info->conn_ip;
        _this->m_conn_port = _this->m_conn_info->conn_port;
        _this->m_auth_type = _this->m_conn_info->auth_type;
        _this->m_acc_name = _this->m_conn_info->acc_username;
        _this->m_acc_secret = _this->m_conn_info->acc_secret;
        _this->m_flags = _this->m_conn_info->protocol_flag;
        if (_this->m_conn_info->protocol_type != TP_PROTOCOL_TYPE_SSH) {
            EXLOGE("[ssh] session '%s' is not for SSH.\n", _this->m_sid.c_str());
            _this->m_have_error = true;
            _this->_session_error(TP_SESS_STAT_ERR_INTERNAL);
            return SSH_AUTH_DENIED;
        }
    }

    // config and try to connect to real SSH host.
    EXLOGV("[ssh] try to connect to real SSH server %s:%d\n", _this->m_conn_ip.c_str(), _this->m_conn_port);
    _this->m_srv_session = ssh_new();

    ssh_set_blocking(_this->m_srv_session, 1);

    ssh_options_set(_this->m_srv_session, SSH_OPTIONS_HOST, _this->m_conn_ip.c_str());
    int port = (int) _this->m_conn_port;
    ssh_options_set(_this->m_srv_session, SSH_OPTIONS_PORT, &port);
    int val = 0;
    ssh_options_set(_this->m_srv_session, SSH_OPTIONS_STRICTHOSTKEYCHECK, &val);

//#ifdef EX_DEBUG
//    int flag = SSH_LOG_FUNCTIONS;
//    ssh_options_set(_this->m_srv_session, SSH_OPTIONS_LOG_VERBOSITY, &flag);
//#endif


    if (_this->m_auth_type != TP_AUTH_TYPE_NONE)
        ssh_options_set(_this->m_srv_session, SSH_OPTIONS_USER, _this->m_acc_name.c_str());

    // default timeout is 10 seconds, it is too short for connect progress, so set it to 60 sec.
    int _timeout = 60; // 60 sec.
    ssh_options_set(_this->m_srv_session, SSH_OPTIONS_TIMEOUT, &_timeout);

    int rc = 0;
    rc = ssh_connect(_this->m_srv_session);
    if (rc != SSH_OK) {
        EXLOGE("[ssh] can not connect to real SSH server %s:%d. [%d] %s\n", _this->m_conn_ip.c_str(), _this->m_conn_port, rc, ssh_get_error(_this->m_srv_session));
        _this->m_have_error = true;
        _this->_session_error(TP_SESS_STAT_ERR_CONNECT);
        return SSH_AUTH_ERROR;
    }

    // once the server are connected, change the timeout back to default.
    _timeout = 30; // in seconds.
    ssh_options_set(_this->m_srv_session, SSH_OPTIONS_TIMEOUT, &_timeout);

    // get ssh version of host, v1 or v2
    // TODO: libssh-0.8.5 does not support sshv1 anymore.
    _this->m_ssh_ver = ssh_get_version(_this->m_srv_session);
    EXLOGW("[ssh] real host is SSHv%d\n", _this->m_ssh_ver);

#if 0
    // check supported auth type by host
    ssh_userauth_none(_this->m_srv_session, _this->m_acc_name.c_str());
    rc = ssh_userauth_none(_this->m_srv_session, NULL);
    if (rc == SSH_AUTH_ERROR) {
            EXLOGE("[ssh] can not got auth type supported by real SSH server %s:%d.\n", _this->m_conn_ip.c_str(), _this->m_conn_port);
            _this->m_have_error = true;
            _this->_session_error(TP_SESS_STAT_ERR_SESSION);
            return SSH_AUTH_ERROR;
    }

    int auth_methods = ssh_userauth_list(_this->m_srv_session, _this->m_acc_name.c_str());

    const char* banner = ssh_get_issue_banner(_this->m_srv_session);
    if (NULL != banner) {
        EXLOGE("[ssh] issue banner: %s\n", banner);
    }
#endif

    int auth_methods = 0;
    if (SSH_AUTH_ERROR != ssh_userauth_none(_this->m_srv_session, NULL)) {
        auth_methods = ssh_userauth_list(_this->m_srv_session, NULL);
        EXLOGV("[ssh] allowed auth method: 0x%08x\n", auth_methods);
    } else {
        EXLOGW("[ssh] can not get allowed auth method, try each method we can.\n");
    }

    // some host does not give me the auth methods list, so we need try each one.
    if(auth_methods == 0)
        auth_methods = SSH_AUTH_METHOD_INTERACTIVE | SSH_AUTH_METHOD_PASSWORD | SSH_AUTH_METHOD_PUBLICKEY;

    if (_this->m_auth_type == TP_AUTH_TYPE_PASSWORD) {
        if (!(((auth_methods & SSH_AUTH_METHOD_INTERACTIVE) == SSH_AUTH_METHOD_INTERACTIVE) || ((auth_methods & SSH_AUTH_METHOD_PASSWORD) == SSH_AUTH_METHOD_PASSWORD))) {
            _this->_session_error(TP_SESS_STAT_ERR_AUTH_TYPE);
            return SSH_AUTH_ERROR;
        }

        int retry_count = 0;

        // first try interactive login mode if server allow.
        if ((auth_methods & SSH_AUTH_METHOD_INTERACTIVE) == SSH_AUTH_METHOD_INTERACTIVE) {
            retry_count = 0;
            rc = ssh_userauth_kbdint(_this->m_srv_session, NULL, NULL);
            for (;;) {
                if (rc == SSH_AUTH_AGAIN) {
                    retry_count += 1;
                    if (retry_count >= 5)
                        break;
                    ex_sleep_ms(500);
                    rc = ssh_userauth_kbdint(_this->m_srv_session, NULL, NULL);
                    continue;
                }

                if (rc != SSH_AUTH_INFO)
                    break;

                int nprompts = ssh_userauth_kbdint_getnprompts(_this->m_srv_session);
                if (0 == nprompts) {
                    rc = ssh_userauth_kbdint(_this->m_srv_session, NULL, NULL);
                    continue;
                }

                for (int iprompt = 0; iprompt < nprompts; ++iprompt) {
                    char echo = 0;
                    const char *prompt = ssh_userauth_kbdint_getprompt(_this->m_srv_session, iprompt, &echo);
                    EXLOGV("[ssh] interactive login prompt: %s\n", prompt);

                    rc = ssh_userauth_kbdint_setanswer(_this->m_srv_session, iprompt, _this->m_acc_secret.c_str());
                    if (rc < 0) {
                        EXLOGE("[ssh] invalid password for interactive mode to login to real SSH server %s:%d.\n", _this->m_conn_ip.c_str(), _this->m_conn_port);
                        _this->m_have_error = true;
                        _this->_session_error(TP_SESS_STAT_ERR_AUTH_DENIED);
                        return SSH_AUTH_ERROR;
                    }
                }

                rc = ssh_userauth_kbdint(_this->m_srv_session, NULL, NULL);
            }
        }

        // and then try password login mode if server allow.
        if ((auth_methods & SSH_AUTH_METHOD_PASSWORD) == SSH_AUTH_METHOD_PASSWORD) {
            retry_count = 0;
            rc = ssh_userauth_password(_this->m_srv_session, NULL, _this->m_acc_secret.c_str());
            for (;;) {
                if (rc == SSH_AUTH_AGAIN) {
                    retry_count += 1;
                    if (retry_count >= 3)
                        break;
                    ex_sleep_ms(100);
                    rc = ssh_userauth_password(_this->m_srv_session, NULL, _this->m_acc_secret.c_str());
                    continue;
                }
                if (rc == SSH_AUTH_SUCCESS) {
                    EXLOGW("[ssh] logon with password mode.\n");
                    _this->m_is_logon = true;
                    return SSH_AUTH_SUCCESS;
                } else {
                    EXLOGE("[ssh] failed to login with password mode, got %d.\n", rc);
                    break;
                }
            }
        }

        EXLOGE("[ssh] can not use password mode or interactive mode to login to real SSH server %s:%d.\n", _this->m_conn_ip.c_str(), _this->m_conn_port);
        _this->m_have_error = true;
        _this->_session_error(TP_SESS_STAT_ERR_AUTH_DENIED);
        return SSH_AUTH_ERROR;
    } else if (_this->m_auth_type == TP_AUTH_TYPE_PRIVATE_KEY) {
        if ((auth_methods & SSH_AUTH_METHOD_PUBLICKEY) != SSH_AUTH_METHOD_PUBLICKEY) {
            _this->m_have_error = true;
            _this->_session_error(TP_SESS_STAT_ERR_AUTH_TYPE);
            return SSH_AUTH_ERROR;
        }

        ssh_key key = NULL;
        if (SSH_OK != ssh_pki_import_privkey_base64(_this->m_acc_secret.c_str(), NULL, NULL, NULL, &key)) {
            EXLOGE("[ssh] can not import private-key for auth.\n");
            _this->m_have_error = true;
            _this->_session_error(TP_SESS_STAT_ERR_BAD_SSH_KEY);
            return SSH_AUTH_ERROR;
        }

        rc = ssh_userauth_publickey(_this->m_srv_session, NULL, key);
        ssh_key_free(key);

        if (rc == SSH_AUTH_SUCCESS) {
            EXLOGW("[ssh] logon with public-key mode.\n");
            _this->m_is_logon = true;
            return SSH_AUTH_SUCCESS;
        }

        EXLOGE("[ssh] failed to use private-key to login to real SSH server %s:%d.\n", _this->m_conn_ip.c_str(), _this->m_conn_port);
        _this->m_have_error = true;
        _this->_session_error(TP_SESS_STAT_ERR_AUTH_DENIED);
        return SSH_AUTH_ERROR;
    } else if (_this->m_auth_type == TP_AUTH_TYPE_NONE) {
        _this->_session_error(TP_SESS_STAT_ERR_AUTH_DENIED);
        return SSH_AUTH_ERROR;
    } else {
        EXLOGE("[ssh] invalid auth mode.\n");
        _this->m_have_error = true;
        _this->_session_error(TP_SESS_STAT_ERR_AUTH_DENIED);
        return SSH_AUTH_ERROR;
    }
}

ssh_channel SshSession::_on_new_channel_request(ssh_session session, void *userdata) {
    // 客户端尝试打开一个通道（然后才能通过这个通道发控制命令或者收发数据）
    EXLOGV("[ssh] client open channel\n");

    SshSession *_this = (SshSession *) userdata;

    // TODO: 客户端与TP连接使用的总是SSHv2协议，因为最开始连接时还不知道真正的远程主机是不是SSHv1。
    // 因此此处行为与客户端直连远程主机有些不一样。直连时，SecureCRT的克隆会话功能会因为以为连接的是SSHv1而自动重新连接，而不是打开新通道。
    if (_this->m_ssh_ver == 1 && _this->m_channels.size() != 0) {
        EXLOGE("[ssh] SSH1 supports only one execution channel. One has already been opened.\n");
        return NULL;
    }

    ssh_channel cli_channel = ssh_channel_new(session);
    if (cli_channel == NULL) {
        EXLOGE("[ssh] can not create channel for client.\n");
        return NULL;
    }
    ssh_set_channel_callbacks(cli_channel, &_this->m_cli_channel_cb);

    // 我们也要向真正的服务器申请打开一个通道，来进行转发
    ssh_channel srv_channel = ssh_channel_new(_this->m_srv_session);
    if (srv_channel == NULL) {
        EXLOGE("[ssh] can not create channel for server.\n");
        return NULL;
    }
    if (SSH_OK != ssh_channel_open_session(srv_channel)) {
        EXLOGE("[ssh] error opening channel to real server: %s\n", ssh_get_error(_this->m_srv_session));
        ssh_channel_free(cli_channel);
        ssh_channel_free(srv_channel);
        return NULL;
    }
    ssh_set_channel_callbacks(srv_channel, &_this->m_srv_channel_cb);

    TP_SSH_CHANNEL_PAIR *cp = new TP_SSH_CHANNEL_PAIR;
    cp->type = TS_SSH_CHANNEL_TYPE_UNKNOWN;
    cp->cli_channel = cli_channel;
    cp->srv_channel = srv_channel;
    cp->last_access_timestamp = (ex_u32) time(NULL);

    if (!_this->_record_begin(cp)) {
        ssh_channel_close(cli_channel);
        ssh_channel_free(cli_channel);
        ssh_channel_close(srv_channel);
        ssh_channel_free(srv_channel);
        delete cp;
        return NULL;
    }

    // 将客户端和服务端的通道关联起来
    {
        ExThreadSmartLock locker(_this->m_lock);
        _this->m_channels.push_back(cp);
    }

    EXLOGD("[ssh] channel for client and server created.\n");
    return cli_channel;
}

TP_SSH_CHANNEL_PAIR *SshSession::_get_channel_pair(int channel_side, ssh_channel channel) {
    ExThreadSmartLock locker(m_lock);

    tp_channels::iterator it = m_channels.begin();
    for (; it != m_channels.end(); ++it) {
        if (channel_side == TP_SSH_CLIENT_SIDE) {
            if ((*it)->cli_channel == channel)
                return (*it);
        } else {
            if ((*it)->srv_channel == channel)
                return (*it);
        }
    }

    return NULL;
}

int SshSession::_on_client_pty_request(ssh_session session, ssh_channel channel, const char *term, int x, int y, int px, int py, void *userdata) {
    SshSession *_this = (SshSession *) userdata;

    EXLOGD("[ssh] client request pty: %s, (%d, %d) / (%d, %d)\n", term, x, y, px, py);

    TP_SSH_CHANNEL_PAIR *cp = _this->_get_channel_pair(TP_SSH_CLIENT_SIDE, channel);
    if (NULL == cp) {
        EXLOGE("[ssh] when client request pty, not found channel pair.\n");
        return SSH_ERROR;
    }

    cp->win_width = x;
    cp->rec.record_win_size_startup(x, y);
    cp->last_access_timestamp = (ex_u32) time(NULL);

    int err = ssh_channel_request_pty_size(cp->srv_channel, term, x, y);
    if (err != SSH_OK)
        EXLOGE("[ssh] pty request from server got %d\n", err);
    return err;
}

int SshSession::_on_client_shell_request(ssh_session session, ssh_channel channel, void *userdata) {
    SshSession *_this = (SshSession *) userdata;

    EXLOGD("[ssh] client request shell\n");
    if ((_this->m_flags & TP_FLAG_SSH_SHELL) != TP_FLAG_SSH_SHELL) {
        EXLOGE("[ssh] ssh-shell disabled by ops-policy.\n");
        return SSH_ERROR;
    }

    TP_SSH_CHANNEL_PAIR *cp = _this->_get_channel_pair(TP_SSH_CLIENT_SIDE, channel);
    if (NULL == cp) {
        EXLOGE("[ssh] when client request shell, not found channel pair.\n");
        return SSH_ERROR;
    }

    cp->type = TS_SSH_CHANNEL_TYPE_SHELL;
    if (_this->m_ssh_ver == 1)
        cp->server_ready = true;
    g_ssh_env.session_update(cp->db_id, TP_PROTOCOL_TYPE_SSH_SHELL, TP_SESS_STAT_STARTED);
    cp->last_access_timestamp = (ex_u32) time(NULL);

    // sometimes it will block here. the following function will never return.
    // Fixed at 20190104:
    // at libssh ssh_handle_packets_termination(), set timeout always to SSH_TIMEOUT_USER.
    // and at ssh_handle_packets(), when call ssh_poll_add_events() should use POLLIN|POLLOUT.
    int err = ssh_channel_request_shell(cp->srv_channel);
    if (err != SSH_OK) {
        EXLOGE("[ssh] shell request from server got %d\n", err);
    }
    return err;
}

void SshSession::_on_client_channel_close(ssh_session session, ssh_channel channel, void *userdata) {
    EXLOGV("[ssh]  ---client channel closed.\n");
    SshSession *_this = (SshSession *) userdata;

    TP_SSH_CHANNEL_PAIR *cp = _this->_get_channel_pair(TP_SSH_CLIENT_SIDE, channel);
    if (NULL == cp) {
        EXLOGE("[ssh] when client channel close, not found channel pair.\n");
        return;
    }

    _this->m_have_error = true;

    //EXLOGD("[ssh] [channel:%d]   -- end by client channel close\n", cp->channel_id);
    //_this->_record_end(cp);

    if (cp->srv_channel == NULL) {
        EXLOGW("[ssh] when client channel close, server-channel not exists.\n");
    } else {
        if (!ssh_channel_is_closed(cp->srv_channel)) {
            // ssh_channel_close(cp->srv_channel);
            //cp->need_close = true;
            //_this->m_have_error = true;
        }
    }
}

int SshSession::_on_client_channel_data(ssh_session session, ssh_channel channel, void *data, unsigned int len, int is_stderr, void *userdata) {
    //EXLOG_BIN((ex_u8 *) data, len, " ---> on_client_channel_data [is_stderr=%d]:", is_stderr);
    //EXLOGD(" ---> recv from client %d B\n", len);

    SshSession *_this = (SshSession *) userdata;

    // 当前线程正在接收服务端返回的数据，因此我们直接返回，这样紧跟着会重新再发送此数据的
    if (_this->m_recving_from_srv) {
        // EXLOGD("recving from srv...try again later...\n");
        return 0;
    }
    if (_this->m_recving_from_cli) {
        // EXLOGD("recving from cli...try again later...\n");
        return 0;
    }

    TP_SSH_CHANNEL_PAIR *cp = _this->_get_channel_pair(TP_SSH_CLIENT_SIDE, channel);
    if (NULL == cp) {
        EXLOGE("[ssh] when receive client channel data, not found channel pair.\n");
        return SSH_ERROR;
    }
    cp->last_access_timestamp = (ex_u32) time(NULL);

    _this->m_recving_from_cli = true;

    int _len = len;
    if (cp->type == TS_SSH_CHANNEL_TYPE_SHELL) {
        // 在收取服务端数据直到显示命令行提示符之前，不允许发送客户端数据到服务端，避免日志记录混乱。
        if (!cp->server_ready) {
            _this->m_recving_from_cli = false;
            return 0;
        }

        // 不可以拆分！！否则执行 rz 命令会出错！
        // xxxx 如果用户复制粘贴多行文本，我们将其拆分为每一行发送一次数据包
//         for (unsigned int i = 0; i < len; ++i) {
//             if (((ex_u8 *) data)[i] == 0x0d) {
//                 _len = i + 1;
//                 break;
//             }
//         }

        _this->_process_ssh_command(cp, TP_SSH_CLIENT_SIDE, (ex_u8 *) data, _len);
    } else {
        _this->_process_sftp_command(cp, (ex_u8 *) data, _len);
    }

    int ret = 0;
    if (is_stderr)
        ret = ssh_channel_write_stderr(cp->srv_channel, data, _len);
    else
        ret = ssh_channel_write(cp->srv_channel, data, _len);

    if (ret == SSH_ERROR) {
        EXLOGE("[ssh] send data(%dB) to server failed. [%d][cli:%s][srv:%s]\n", _len, ret, ssh_get_error(_this->m_cli_session), ssh_get_error(_this->m_srv_session));

        //ssh_channel_close(channel);
        cp->need_close = true;
        _this->m_have_error = true;
    }

    _this->m_recving_from_cli = false;

    return ret;
}

int SshSession::_on_client_pty_win_change(ssh_session session, ssh_channel channel, int width, int height, int pxwidth, int pwheight, void *userdata) {
    EXLOGD("[ssh] client pty win size change to: (%d, %d)\n", width, height);
    SshSession *_this = (SshSession *) userdata;

    TP_SSH_CHANNEL_PAIR *cp = _this->_get_channel_pair(TP_SSH_CLIENT_SIDE, channel);
    if (NULL == cp) {
        EXLOGE("[ssh] when client pty win change, not found channel pair.\n");
        return SSH_ERROR;
    }

    cp->win_width = width;
    cp->rec.record_win_size_change(width, height);
    cp->last_access_timestamp = (ex_u32) time(NULL);

    return ssh_channel_change_pty_size(cp->srv_channel, width, height);
}

int SshSession::_on_client_channel_subsystem_request(ssh_session session, ssh_channel channel, const char *subsystem, void *userdata) {
    EXLOGD("[ssh] on_client_channel_subsystem_request(): %s\n", subsystem);
    SshSession *_this = (SshSession *) userdata;

    if (_this->m_ssh_ver == 1) {
        // SSHv1 not support subsystem, so some client like WinSCP will use shell-mode instead.
        EXLOGE("[ssh] real host running on SSHv1, does not support subsystem `%s`.\n", subsystem);
        return SSH_ERROR;
    }

    TP_SSH_CHANNEL_PAIR *cp = _this->_get_channel_pair(TP_SSH_CLIENT_SIDE, channel);
    if (NULL == cp) {
        EXLOGE("[ssh] when request channel subsystem, not found channel pair.\n");
        return SSH_ERROR;
    }
    cp->last_access_timestamp = (ex_u32) time(NULL);


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


    cp->type = TS_SSH_CHANNEL_TYPE_SFTP;
    g_ssh_env.session_update(cp->db_id, TP_PROTOCOL_TYPE_SSH_SFTP, TP_SESS_STAT_STARTED);

    //EXLOGD("[ssh]   ---> request channel subsystem from server\n");
    int err = ssh_channel_request_subsystem(cp->srv_channel, subsystem);
    //EXLOGD("[ssh]   <--- request channel subsystem from server\n");
    if (err != SSH_OK)
        EXLOGE("[ssh] request channel subsystem from server got %d\n", err);
    return err;
}

int SshSession::_on_client_channel_exec_request(ssh_session session, ssh_channel channel, const char *command, void *userdata) {
    EXLOGW("[ssh] not-impl: client_channel_exec_request(): %s\n", command);
    return SSH_ERROR;
}

int SshSession::_on_server_channel_data(ssh_session session, ssh_channel channel, void *data, unsigned int len, int is_stderr, void *userdata) {
    //EXLOG_BIN((ex_u8 *) data, len, " <--- on_server_channel_data [is_stderr=%d]:", is_stderr);
    //EXLOGD(" <--- send to server %d B\n", len);

    SshSession *_this = (SshSession *) userdata;

    // return 0 means data not processed, so this function will be called with this data again.
    if (_this->m_recving_from_cli) {
        // EXLOGD("recving from cli...try again later...\n");
        return 0;
    }
    if (_this->m_recving_from_srv) {
        // EXLOGD("recving from srv...try again later...\n");
        return 0;
    }

    TP_SSH_CHANNEL_PAIR *cp = _this->_get_channel_pair(TP_SSH_SERVER_SIDE, channel);
    if (NULL == cp) {
        EXLOGE("[ssh] when receive server channel data, not found channel pair.\n");
        return SSH_ERROR;
    }
    cp->last_access_timestamp = (ex_u32) time(NULL);

    _this->m_recving_from_srv = true;

    if (cp->type == TS_SSH_CHANNEL_TYPE_SHELL && !is_stderr) {
        if (!cp->server_ready) {
            if (len >= 2 && (((ex_u8 *) data)[len - 2] != 0x0d && ((ex_u8 *) data)[len - 1] != 0x0a)) {
                cp->server_ready = true;
            }
        }

        _this->_process_ssh_command(cp, TP_SSH_SERVER_SIDE, (ex_u8 *) data, len);
        // 		ex_astr str(cp->cmd_char_list.begin(), cp->cmd_char_list.end());
        // 		ex_replace_all(str, "\r", "");
        // 		ex_replace_all(str, "\n", "");
        // 		EXLOGD("[ssh]   -- [%s]\n", str.c_str());

        cp->rec.record(TS_RECORD_TYPE_SSH_DATA, (unsigned char *) data, len);
    }

    int ret = 0;

    // 收到第一包服务端返回的数据时，在输出数据之前显示一些自定义的信息
#if 1
    if (!is_stderr && cp->is_first_server_data) {
        cp->is_first_server_data = false;

        if (cp->type != TS_SSH_CHANNEL_TYPE_SFTP) {
            char buf[512] = {0};

            const char *auth_mode = NULL;
            if (_this->m_auth_type == TP_AUTH_TYPE_PASSWORD)
                auth_mode = "password";
            else if (_this->m_auth_type == TP_AUTH_TYPE_PRIVATE_KEY)
                auth_mode = "private-key";
            else
                auth_mode = "unknown";

#ifdef EX_OS_WIN32
            int w = min(cp->win_width, 128);
#else
            int w = std::min(cp->win_width, 128);
#endif
            ex_astr line(w, '=');

            snprintf(buf, sizeof(buf),
                     "\r\n"\
                "%s\r\n"\
                "Teleport SSH Bastion Server...\r\n"\
                "  - teleport to %s:%d\r\n"\
                "  - authroized by %s\r\n"\
                "%s\r\n"\
                "\r\n\r\n",
                     line.c_str(),
                     _this->m_conn_ip.c_str(),
                     _this->m_conn_port, auth_mode,
                     line.c_str()
            );

            int buf_len = strlen(buf);
            ex_bin _data;
            _data.resize(buf_len + len);
            memcpy(&_data[0], buf, buf_len);
            memcpy(&_data[buf_len], data, len);

            ret = ssh_channel_write(cp->cli_channel, &_data[0], _data.size());

            _this->m_recving_from_srv = false;
            return len;
        }
    }
#endif

#if 1
    // 直接转发数据到客户端
    if (is_stderr)
        ret = ssh_channel_write_stderr(cp->cli_channel, data, len);
    else
        ret = ssh_channel_write(cp->cli_channel, data, len);
#else
    // 分析收到的服务端数据包，如果包含类似  \033]0;AABB\007  这样的数据，客户端会根据此改变窗口标题
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

    if (ret == SSH_ERROR) {
        EXLOGE("[ssh] send data(%dB) to client failed. [%d][cli:%s][srv:%s]\n", len, ret, ssh_get_error(_this->m_cli_session), ssh_get_error(_this->m_srv_session));
        cp->need_close = true;
        _this->m_have_error = true;
    } else if (ret != len) {
        EXLOGW("[ssh] received server data, got %dB, processed %dB.\n", len, ret);
    }

    _this->m_recving_from_srv = false;
    return ret;
}

void SshSession::_on_server_channel_close(ssh_session session, ssh_channel channel, void *userdata) {
    EXLOGV("[ssh]  ---server channel closed.\n");
    SshSession *_this = (SshSession *) userdata;
    TP_SSH_CHANNEL_PAIR *cp = _this->_get_channel_pair(TP_SSH_SERVER_SIDE, channel);
    if (NULL == cp) {
        EXLOGE("[ssh] when server channel close, not found channel pair.\n");
        return;
    }
    //cp->last_access_timestamp = (ex_u32)time(NULL);
    //cp->need_close = true;
    _this->m_have_error = true;

    //EXLOGD("[ssh] [channel:%d]  --- end by server channel close\n", cp->channel_id);
    //_this->_record_end(cp);

    // will the server-channel exist, the client-channel must exist too.
    if (cp->cli_channel == NULL) {
        EXLOGE("[ssh] when server channel close, client-channel not exists.\n");
    } else {
        if (!ssh_channel_is_closed(cp->cli_channel)) {
            //ssh_channel_close(cp->cli_channel);
            //cp->need_close = true;
            //_this->m_have_error = true;
        }
    }
}

void SshSession::_process_ssh_command(TP_SSH_CHANNEL_PAIR *cp, int from, const ex_u8 *data, int len) {
    if (len == 0)
        return;

    if (TP_SSH_CLIENT_SIDE == from) {
        if (len >= 2) {
            if (((ex_u8 *) data)[len - 1] == 0x0d) {
                // 疑似复制粘贴多行命令一次性执行，将其记录到日志文件中
                ex_astr str((const char *) data, len - 1);
                cp->rec.record_command(1, str);

                cp->process_srv = false;
                return;
            }
        }

        // 客户端输入回车时，可能时执行了一条命令，需要根据服务端返回的数据进行进一步判断
        cp->maybe_cmd = (data[len - 1] == 0x0d);
        // 		if (cp->maybe_cmd)
        // 			EXLOGD("[ssh]   maybe cmd.\n");

        // 有时在执行类似top命令的情况下，输入一个字母'q'就退出程序，没有输入回车，可能会导致后续记录命令时将返回的命令行提示符作为命令
        // 记录下来了，要避免这种情况，排除的方式是：客户端单个字母，后续服务端如果收到的是控制序列 1b 5b xx xx，就不计做命令。
        cp->client_single_char = (len == 1 && isprint(data[0]));

        cp->process_srv = true;
    } else if (TP_SSH_SERVER_SIDE == from) {
        if (!cp->process_srv)
            return;

        int offset = 0;
        bool esc_mode = false;
        int esc_arg = 0;
        for (; offset < len;) {
            ex_u8 ch = data[offset];

            if (esc_mode) {
                switch (ch) {
                    case '0':
                    case '1':
                    case '2':
                    case '3':
                    case '4':
                    case '5':
                    case '6':
                    case '7':
                    case '8':
                    case '9':
                        esc_arg = esc_arg * 10 + (ch - '0');
                        break;

                    case 0x3f:
                    case ';':
                    case '>':
                        cp->cmd_char_list.clear();
                        cp->cmd_char_pos = cp->cmd_char_list.begin();
                        return;
                        break;

                    case 0x4b: {    // 'K'
                        if (0 == esc_arg) {
                            // 删除光标到行尾的字符串
                            cp->cmd_char_list.erase(cp->cmd_char_pos, cp->cmd_char_list.end());
                            cp->cmd_char_pos = cp->cmd_char_list.end();
                        } else if (1 == esc_arg) {
                            // 删除从开始到光标处的字符串
                            cp->cmd_char_list.erase(cp->cmd_char_list.begin(), cp->cmd_char_pos);
                            cp->cmd_char_pos = cp->cmd_char_list.end();
                        } else if (2 == esc_arg) {
                            // 删除整行
                            cp->cmd_char_list.clear();
                            cp->cmd_char_pos = cp->cmd_char_list.begin();
                        }

                        esc_mode = false;
                        break;
                    }
                    case 0x43: {// ^[C
                        // 光标右移
                        if (esc_arg == 0)
                            esc_arg = 1;
                        for (int j = 0; j < esc_arg; ++j) {
                            if (cp->cmd_char_pos != cp->cmd_char_list.end())
                                cp->cmd_char_pos++;
                        }
                        esc_mode = false;
                        break;
                    }
                    case 0x44: { // ^[D
                        // 光标左移
                        if (esc_arg == 0)
                            esc_arg = 1;
                        for (int j = 0; j < esc_arg; ++j) {

                            if (cp->cmd_char_pos != cp->cmd_char_list.begin())
                                cp->cmd_char_pos--;
                        }
                        esc_mode = false;
                        break;
                    }

                    case 0x50: {// 'P' 删除指定数量的字符

                        if (esc_arg == 0)
                            esc_arg = 1;
                        for (int j = 0; j < esc_arg; ++j) {
                            if (cp->cmd_char_pos != cp->cmd_char_list.end())
                                cp->cmd_char_pos = cp->cmd_char_list.erase(cp->cmd_char_pos);
                        }
                        esc_mode = false;
                        break;
                    }

                    case 0x40: {    // '@' 插入指定数量的空白字符
                        if (esc_arg == 0)
                            esc_arg = 1;
                        for (int j = 0; j < esc_arg; ++j)
                            cp->cmd_char_pos = cp->cmd_char_list.insert(cp->cmd_char_pos, ' ');
                        esc_mode = false;
                        break;
                    }

                    default:
                        esc_mode = false;
                        break;
                }

                //d += 1;
                //l -= 1;
                offset++;
                continue;
            }

            switch (ch) {
                case 0x07:
                    // 响铃
                    break;
                case 0x08: {
                    // 光标左移
                    if (cp->cmd_char_pos != cp->cmd_char_list.begin())
                        cp->cmd_char_pos--;
                    break;
                }
                case 0x1b: {
                    if (offset + 1 < len) {
                        if (data[offset + 1] == 0x5b || data[offset + 1] == 0x5d) {
                            if (offset == 0 && cp->client_single_char) {
                                cp->cmd_char_list.clear();
                                cp->cmd_char_pos = cp->cmd_char_list.begin();
                                cp->maybe_cmd = false;
                                cp->process_srv = false;
                                cp->client_single_char = false;
                                return;
                            }
                        }

                        if (data[offset + 1] == 0x5b) {
                            esc_mode = true;
                            esc_arg = 0;

                            offset += 1;
                        }
                    }

                    break;
                }
                case 0x0d: {
                    if (offset + 1 < len && data[offset + 1] == 0x0a) {
                        // 					if (cp->maybe_cmd)
                        // 						EXLOGD("[ssh]   maybe cmd.\n");
                        if (cp->maybe_cmd) {
                            if (cp->cmd_char_list.size() > 0) {
                                ex_astr str(cp->cmd_char_list.begin(), cp->cmd_char_list.end());
                                // 							EXLOGD("[ssh]   --==--==-- save cmd: [%s]\n", str.c_str());
                                cp->rec.record_command(0, str);
                            }

                            cp->cmd_char_list.clear();
                            cp->cmd_char_pos = cp->cmd_char_list.begin();
                            cp->maybe_cmd = false;
                        }
                    } else {
                        cp->cmd_char_list.clear();
                        cp->cmd_char_pos = cp->cmd_char_list.begin();
                    }
                    cp->process_srv = false;
                    return;
                    break;
                }
                default:
                    if (cp->cmd_char_pos != cp->cmd_char_list.end()) {
                        cp->cmd_char_pos = cp->cmd_char_list.erase(cp->cmd_char_pos);
                        cp->cmd_char_pos = cp->cmd_char_list.insert(cp->cmd_char_pos, ch);
                        cp->cmd_char_pos++;
                    } else {
                        cp->cmd_char_list.push_back(ch);
                        cp->cmd_char_pos = cp->cmd_char_list.end();
                    }
            }

            offset++;
        }
    }

    return;
}

void SshSession::_process_sftp_command(TP_SSH_CHANNEL_PAIR *cp, const ex_u8 *data, int len) {
    // SFTP protocol: https://tools.ietf.org/html/draft-ietf-secsh-filexfer-13
    //EXLOG_BIN(data, len, "[sftp] client channel data");

    // TODO: 根据客户端的请求和服务端的返回，可以进一步判断用户是如何操作文件的，比如读、写等等，以及操作的结果是成功还是失败。
    // 记录格式：  time-offset,flag,action,result,file-path,[file-path]
    //   其中，flag目前总是为0，可以忽略（为保证与ssh-cmd格式一致），time-offset/action/result 都是数字
    //        file-path是被操作的对象，规格为 长度:实际内容，例如，  13:/root/abc.txt


    if (len < 9)
        return;

    int pkg_len = (int) ((data[0] << 24) | (data[1] << 16) | (data[2] << 8) | data[3]);
    if (pkg_len + 4 != len)
        return;

    ex_u8 sftp_cmd = data[4];

    if (sftp_cmd == 0x01) {
        // 0x01 = 1 = SSH_FXP_INIT
        cp->rec.record_command(0, "SFTP INITIALIZE\r\n");
        return;
    }

    // 需要的数据至少14字节
    // uint32 + byte + uint32 + (uint32 + char + ...)
    // pkg_len + cmd + req_id + string( length + content...)
    if (len < 14)
        return;

    ex_u8 *str1_ptr = (ex_u8 *) data + 9;
    int str1_len = (int) ((str1_ptr[0] << 24) | (str1_ptr[1] << 16) | (str1_ptr[2] << 8) | str1_ptr[3]);
    // 	if (str1_len + 9 != pkg_len)
    // 		return;
    ex_u8 *str2_ptr = NULL;// (ex_u8*)data + 13;
    int str2_len = 0;// (int)((data[9] << 24) | (data[10] << 16) | (data[11] << 8) | data[12]);


    switch (sftp_cmd) {
        case 0x03:
            // 0x03 = 3 = SSH_FXP_OPEN
            break;
            // 	case 0x0b:
            // 		// 0x0b = 11 = SSH_FXP_OPENDIR
            // 		act = "open dir";
            // 		break;
        case 0x0d:
            // 0x0d = 13 = SSH_FXP_REMOVE
            break;
        case 0x0e:
            // 0x0e = 14 = SSH_FXP_MKDIR
            break;
        case 0x0f:
            // 0x0f = 15 = SSH_FXP_RMDIR
            break;
        case 0x12:
            // 0x12 = 18 = SSH_FXP_RENAME
            // rename操作数据中包含两个字符串
            str2_ptr = str1_ptr + str1_len + 4;
            str2_len = (int) ((str2_ptr[0] << 24) | (str2_ptr[1] << 16) | (str2_ptr[2] << 8) | str2_ptr[3]);
            break;
        case 0x15:
            // 0x15 = 21 = SSH_FXP_LINK
            // link操作数据中包含两个字符串，前者是新的链接文件名，后者是现有被链接的文件名
            str2_ptr = str1_ptr + str1_len + 4;
            str2_len = (int) ((str2_ptr[0] << 24) | (str2_ptr[1] << 16) | (str2_ptr[2] << 8) | str2_ptr[3]);
            break;
        default:
            return;
    }

    int total_len = 5 + str1_len + 4;
    if (str2_len > 0)
        total_len += str2_len + 4;
    if (total_len > pkg_len)
        return;

    char msg[2048] = {0};
    if (str2_len == 0) {
        ex_astr str1((char *) ((ex_u8 *) data + 13), str1_len);
        ex_strformat(msg, 2048, "%d,%d,%s", sftp_cmd, 0, str1.c_str());
    } else {
        ex_astr str1((char *) (str1_ptr + 4), str1_len);
        ex_astr str2((char *) (str2_ptr + 4), str2_len);
        ex_strformat(msg, 2048, "%d,%d,%s:%s", sftp_cmd, 0, str1.c_str(), str2.c_str());
    }

    cp->rec.record_command(0, msg);
}
