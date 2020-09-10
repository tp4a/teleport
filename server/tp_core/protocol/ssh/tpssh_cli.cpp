#include "tpssh_cli.h"
#include "tpssh_session.h"
#include <teleport_const.h>

SshClientSide::SshClientSide(
        SshSession *owner,
        const std::string &host_ip,
        uint16_t host_port,
        const std::string &acc_name,
        const std::string &thread_name
) :
        ExThreadBase(thread_name.c_str()),
        m_owner(owner),
        m_host_ip(host_ip),
        m_host_port(host_port),
        m_acc_name(acc_name) {

    ex_strformat(m_dbg_name, 128, "S%s:%d", host_ip.c_str(), host_port);

    memset(&m_channel_cb, 0, sizeof(m_channel_cb));
    ssh_callbacks_init(&m_channel_cb);
    m_channel_cb.userdata = this;

    m_channel_cb.channel_data_function = _on_server_channel_data;
    m_channel_cb.channel_close_function = _on_server_channel_close;
}

SshClientSide::~SshClientSide() {
    _on_stop();
    EXLOGD("[ssh] session tp<->server destroy.\n");
}

void SshClientSide::channel_closed(ssh_channel ch) {
    ExThreadSmartLock locker(m_lock);
    auto it = m_channels.begin();
    for(; it != m_channels.end(); ++it) {
        if ((*it) == ch) {
            m_channels.erase(it);
            break;
        }
    }
}

void SshClientSide::_thread_loop() {
    int err = 0;

    ssh_event event_loop = ssh_event_new();
    if (nullptr == event_loop) {
        EXLOGE("[ssh] can not create event loop.\n");
        return;
    }

    err = ssh_event_add_session(event_loop, m_session);
    if (err != SSH_OK) {
        EXLOGE("[ssh] can not add tp2srv session into event loop.\n");
        return;
    }

//    int timer_for_keepalive = 0;
    do {
        err = ssh_event_dopoll(event_loop, 1000);
//        EXLOGV("-- tp2srv dopool return %d.\n", err);
//        if (m_need_stop_poll) {
//            EXLOGE("[ssh] exit loop because need stop pool flag set.\n");
//            break;
//        }
        if (err == SSH_OK)
            continue;

        if (err == SSH_AGAIN) {
            // _check_channels();

//            if (m_need_send_keepalive) {
//                timer_for_keepalive++;
//                if (timer_for_keepalive >= 60) {
//                    timer_for_keepalive = 0;
//                    EXLOGD("[ssh] send keep-alive.\n");
//                    ssh_send_ignore(m_session, "keepalive@openssh.com");
//                }
//            }
        }
        else if (err == SSH_ERROR) {
            EXLOGE("[ssh] poll event failed, %s\n", ssh_get_error(m_session));
            m_need_stop_poll = true;
            break;
        }
    } while (!m_channels.empty());

    EXLOGV("[ssh] session tp<->server [%s:%d] are closed.\n", m_host_ip.c_str(), m_host_port);
    if (!m_channels.empty()) {
        EXLOGW("[ssh] [%s:%d] not all tp<->client channels in this session are closed, close them later.\n", m_host_ip.c_str(), m_host_port);
    }

    ssh_event_remove_session(event_loop, m_session);
    ssh_event_free(event_loop);
}

void SshClientSide::_on_stop() {}

void SshClientSide::_on_stopped() {
    // _close_channels();
    {
        ExThreadSmartLock locker(m_lock);

        if (m_channels.empty())
            return;

        EXLOGV("[ssh] close all channels.\n");

        auto it = m_channels.begin();
        for (; it != m_channels.end(); ++it) {
//            // 先从通道管理器中摘掉这个通道（因为马上就要关闭它了）
//            m_owner->remove_channel(*it);
//            if (!ssh_channel_is_closed(*it))
//                ssh_channel_close(*it);
//            ssh_channel_free(*it);
//            *it = nullptr;

            if (!ssh_channel_is_closed(*it))
                ssh_channel_close(*it);
        }

        m_channels.clear();
    }

    if (nullptr != m_session) {
        ssh_disconnect(m_session);
        ssh_free(m_session);
        m_session = nullptr;
    }
    // m_proxy->session_finished(this);
    //m_owner->tp2srv_end(this);
}

uint32_t SshClientSide::connect() {
    // config and try to connect to real SSH host.
    EXLOGV("[ssh-%s] try to connect to real SSH server %s:%d\n", m_dbg_name.c_str(), m_host_ip.c_str(), m_host_port);
    EXLOGD("[ssh-%s] account=%s\n", m_dbg_name.c_str(), m_acc_name.c_str());
    m_session = ssh_new();
    // ssh_set_blocking(m_session, 0);

    ssh_options_set(m_session, SSH_OPTIONS_HOST, m_host_ip.c_str());
    int port = (int) m_host_port;
    ssh_options_set(m_session, SSH_OPTIONS_PORT, &port);
    int val = 0;
    ssh_options_set(m_session, SSH_OPTIONS_STRICTHOSTKEYCHECK, &val);

//#ifdef EX_DEBUG
//    int flag = SSH_LOG_FUNCTIONS;
//    ssh_options_set(m_session, SSH_OPTIONS_LOG_VERBOSITY, &flag);
//#endif

//    int _timeout_cli = 120; // 120 sec.
//    ssh_options_set(_this->m_cli_session, SSH_OPTIONS_TIMEOUT, &_timeout_cli);


//    if (auth_type != TP_AUTH_TYPE_NONE)
//        ssh_options_set(m_session, SSH_OPTIONS_USER, acc_name.c_str());

    if (!m_acc_name.empty())
        ssh_options_set(m_session, SSH_OPTIONS_USER, m_acc_name.c_str());

    // default timeout is 10 seconds, it is too short for connect progress, so set it to 120 sec.
    // usually when sshd config to UseDNS.
    int _timeout = 120; // 120 sec.
    ssh_options_set(m_session, SSH_OPTIONS_TIMEOUT, &_timeout);

    int rc = 0;
    rc = ssh_connect(m_session);
    if (rc != SSH_OK) {
        EXLOGE("[ssh-%s] can not connect to real SSH server. [%d] %s\n", m_dbg_name.c_str(), rc, ssh_get_error(m_session));
        //_this->m_need_stop_poll = true;
        //_this->_session_error(TP_SESS_STAT_ERR_CONNECT);
        //return SSH_AUTH_ERROR;
        return TP_SESS_STAT_ERR_CONNECT;
    }

//    if (ssh_is_blocking(_this->m_cli_session))
//        EXLOGD("[ssh] client session is blocking.\n");
//    if (ssh_is_blocking(m_session))
//        EXLOGD("[ssh] server session is blocking.\n");

    // once the server are connected, change the timeout back to default.
    _timeout = 10; // in seconds.
    ssh_options_set(m_session, SSH_OPTIONS_TIMEOUT, &_timeout);

    // get ssh version of host, v1 or v2
    // TODO: from v0.8.5, libssh does not support SSHv1 anymore.
    //m_ssh_ver = ssh_get_version(m_session);
    //EXLOGW("[ssh] real host is SSHv%d\n", _this->m_ssh_ver);

#if 0
    const char* banner = ssh_get_issue_banner(m_session);
    if (NULL != banner) {
        EXLOGE("[ssh] issue banner: %s\n", banner);
    }
#endif

    return TP_SESS_STAT_RUNNING;
}

uint32_t SshClientSide::auth(int auth_type, const std::string &acc_secret) {
    EXLOGD("[ssh-%s] auth with type=%d.\n", m_dbg_name.c_str(), auth_type);
    m_auth_type = auth_type;

    int rc = 0;
    int auth_methods = 0;
    if (SSH_AUTH_ERROR != ssh_userauth_none(m_session, nullptr)) {
        auth_methods = ssh_userauth_list(m_session, nullptr);
        EXLOGV("[ssh-%s] allowed auth method: 0x%08x\n", m_dbg_name.c_str(), auth_methods);
    }

    // some host does not give me the auth methods list, so we need try each one.
    if (auth_methods == 0) {
        EXLOGW("[ssh] can not get allowed auth method, try each method we can.\n");
        auth_methods = SSH_AUTH_METHOD_INTERACTIVE | SSH_AUTH_METHOD_PASSWORD | SSH_AUTH_METHOD_PUBLICKEY;
    }

    if (auth_type == TP_AUTH_TYPE_PASSWORD) {
        if (!(((auth_methods & SSH_AUTH_METHOD_INTERACTIVE) == SSH_AUTH_METHOD_INTERACTIVE) || ((auth_methods & SSH_AUTH_METHOD_PASSWORD) == SSH_AUTH_METHOD_PASSWORD))) {
//            _this->m_need_stop_poll = true;
//            _this->_session_error(TP_SESS_STAT_ERR_AUTH_TYPE);
//            return SSH_AUTH_ERROR;
            return TP_SESS_STAT_ERR_AUTH_TYPE;
        }

        int retry_count = 0;

        // first try interactive login mode if server allow.
        if ((auth_methods & SSH_AUTH_METHOD_INTERACTIVE) == SSH_AUTH_METHOD_INTERACTIVE) {
            retry_count = 0;
            rc = ssh_userauth_kbdint(m_session, nullptr, nullptr);
            for (;;) {
                if (rc == SSH_AUTH_SUCCESS) {
                    EXLOGW("[ssh] login with interactive mode succeeded.\n");
                    return TP_SESS_STAT_RUNNING;
                }

                if (rc == SSH_AUTH_AGAIN) {
                    retry_count += 1;
                    if (retry_count >= 5)
                        break;
                    ex_sleep_ms(500);
                    rc = ssh_userauth_kbdint(m_session, nullptr, nullptr);
                    continue;
                }

                if (rc != SSH_AUTH_INFO)
                    break;

                int nprompts = ssh_userauth_kbdint_getnprompts(m_session);
                if (nprompts < 0)
                    break;
                if (0 == nprompts) {
                    rc = ssh_userauth_kbdint(m_session, nullptr, nullptr);
                    continue;
                }

                for (unsigned int iprompt = 0; iprompt < nprompts; ++iprompt) {
                    char echo = 0;
                    const char *prompt = ssh_userauth_kbdint_getprompt(m_session, iprompt, &echo);
                    EXLOGV("[ssh] interactive login prompt: %s\n", prompt);

                    rc = ssh_userauth_kbdint_setanswer(m_session, iprompt, acc_secret.c_str());
                    if (rc < 0) {
                        EXLOGE("[ssh] can not set answer for prompt '%s' of '%s:%d', error: [%d] %s\n", prompt, m_host_ip.c_str(), m_host_port, rc, ssh_get_error(m_session));
//                        _this->m_need_stop_poll = true;
//                        _this->_session_error(TP_SESS_STAT_ERR_AUTH_DENIED);
//                        return SSH_AUTH_ERROR;
                        return TP_SESS_STAT_ERR_AUTH_DENIED;
                    }
                }

                rc = ssh_userauth_kbdint(m_session, nullptr, nullptr);
            }
        }

        // and then try password login mode if server allow.
        if ((auth_methods & SSH_AUTH_METHOD_PASSWORD) == SSH_AUTH_METHOD_PASSWORD) {
            retry_count = 0;
            rc = ssh_userauth_password(m_session, nullptr, acc_secret.c_str());
            for (;;) {
                if (rc == SSH_AUTH_AGAIN) {
                    retry_count += 1;
                    if (retry_count >= 3)
                        break;
                    ex_sleep_ms(100);
                    rc = ssh_userauth_password(m_session, nullptr, acc_secret.c_str());
                    continue;
                }
                if (rc == SSH_AUTH_SUCCESS) {
                    EXLOGW("[ssh] login with password mode succeeded.\n");
//                    _this->m_is_logon = true;
//                    return SSH_AUTH_SUCCESS;
                    return TP_SESS_STAT_RUNNING;
                }
                else {
                    EXLOGE("[ssh] failed to login with password mode, error: [%d] %s\n", rc, ssh_get_error(m_session));
                    break;
                }
            }
        }

        EXLOGE("[ssh] failed to login to real SSH server %s:%d with password/interactive mode.\n", m_host_ip.c_str(), m_host_port);
        return TP_SESS_STAT_ERR_AUTH_DENIED;
    }
    else if (auth_type == TP_AUTH_TYPE_PRIVATE_KEY) {
        if ((auth_methods & SSH_AUTH_METHOD_PUBLICKEY) != SSH_AUTH_METHOD_PUBLICKEY) {
//            _this->m_need_stop_poll = true;
//            _this->_session_error(TP_SESS_STAT_ERR_AUTH_TYPE);
//            return SSH_AUTH_ERROR;
            return TP_SESS_STAT_ERR_AUTH_TYPE;
        }

        ssh_key key = nullptr;
        if (SSH_OK != ssh_pki_import_privkey_base64(acc_secret.c_str(), nullptr, nullptr, nullptr, &key)) {
            EXLOGE("[ssh] can not import private-key for auth.\n");
//            _this->m_need_stop_poll = true;
//            _this->_session_error(TP_SESS_STAT_ERR_BAD_SSH_KEY);
//            return SSH_AUTH_ERROR;
            return TP_SESS_STAT_ERR_BAD_SSH_KEY;
        }

        rc = ssh_userauth_publickey(m_session, nullptr, key);
        ssh_key_free(key);

        if (rc == SSH_AUTH_SUCCESS) {
            EXLOGW("[ssh] login with public-key mode succeeded.\n");
//            _this->m_is_logon = true;
//            return SSH_AUTH_SUCCESS;
            return TP_SESS_STAT_RUNNING;
        }

        EXLOGE("[ssh] failed to login to real SSH server %s:%d with private-key.\n", m_host_ip.c_str(), m_host_port);
//        _this->m_need_stop_poll = true;
//        _this->_session_error(TP_SESS_STAT_ERR_AUTH_DENIED);
//        return SSH_AUTH_ERROR;
        return TP_SESS_STAT_ERR_AUTH_DENIED;
    }
    else if (auth_type == TP_AUTH_TYPE_NONE) {
//        _this->_session_error(TP_SESS_STAT_ERR_AUTH_DENIED);
//        return SSH_AUTH_ERROR;
//        return TP_SESS_STAT_ERR_AUTH_DENIED;
        return TP_SESS_STAT_ERR_AUTH_TYPE;
    }
    else {
        EXLOGE("[ssh] invalid auth type: %d.\n", auth_type);
//        _this->m_need_stop_poll = true;
//        _this->_session_error(TP_SESS_STAT_ERR_AUTH_DENIED);
//        return SSH_AUTH_ERROR;
        return TP_SESS_STAT_ERR_AUTH_TYPE;
    }
}

ssh_channel SshClientSide::request_new_channel() {
    EXLOGV("-- cp x1\n");
    ssh_channel ch = ssh_channel_new(m_session);
    if (ch == nullptr) {
        EXLOGE("[ssh] can not create channel for communicate with server.\n");
        return nullptr;
    }
    EXLOGV("-- cp x2\n");

    if (SSH_OK != ssh_channel_open_session(ch)) {
        EXLOGE("[ssh] error opening channel to real server: %s\n", ssh_get_error(m_session));
        ssh_channel_free(ch);
        return nullptr;
    }
    EXLOGV("-- cp x3\n");

    ssh_set_channel_callbacks(ch, &m_channel_cb);
    m_channels.push_back(ch);

    return ch;
}

//void SshClientSide::close_channel(ssh_channel ch) {
//    // 先判断一下这个通道是不是自己管理的
//
//    // 然后关闭此通道
//    if (!ssh_channel_is_closed(ch))
//        ssh_channel_close(ch);
//    ssh_channel_free(ch);
//}

int SshClientSide::_on_server_channel_data(ssh_session session, ssh_channel channel, void *data, unsigned int len, int is_stderr, void *userdata) {
    //EXLOG_BIN(static_cast<uint8_t *>(data), len, " <--- on_server_channel_data [is_stderr=%d]:", is_stderr);
    //EXLOGD(" <--- send to server %d B\n", len);

    auto *_this = (SshClientSide *) userdata;
    _this->m_owner->update_last_access_time();
    EXLOGD("[ssh] -- cp 1.\n");

//    // return 0 means data not processed, so this function will be called with this data again.
//    if (_this->m_recving_from_cli) {
//        // EXLOGD("recving from cli...try again later...\n");
//        return 0;
//    }
//    if (_this->m_recving_from_srv) {
//        // EXLOGD("recving from srv...try again later...\n");
//        return 0;
//    }

    auto cp = _this->m_owner->get_channel_pair(channel);
    if (nullptr == cp) {
        EXLOGE("[ssh] when receive server channel data, not found channel pair.\n");
        return SSH_ERROR;
    }

//    _this->m_recving_from_srv = true;

    if (cp->type == TS_SSH_CHANNEL_TYPE_SHELL && !is_stderr) {
        if (!cp->server_ready) {
            if (len >= 2 && (((ex_u8 *) data)[len - 2] != 0x0d && ((ex_u8 *) data)[len - 1] != 0x0a)) {
                cp->server_ready = true;
            }
        }

        //cp->process_ssh_command(channel, (ex_u8 *) data, len);
        // 		ex_astr str(cp->cmd_char_list.begin(), cp->cmd_char_list.end());
        // 		ex_replace_all(str, "\r", "");
        // 		ex_replace_all(str, "\n", "");
        // 		EXLOGD("[ssh]   -- [%s]\n", str.c_str());

        cp->rec.record(TS_RECORD_TYPE_SSH_DATA, (unsigned char *) data, len);
    }
    EXLOGD("[ssh] -- cp 2.\n");

    int ret = 0;
    ex_bin ext_data;
    const uint8_t *_send_data = static_cast<uint8_t *>(data);
    unsigned int _send_len = len;


    // 收到第一包服务端返回的数据时，在输出数据之前显示一些自定义的信息
#if 1
    if (cp->is_first_server_data && !is_stderr && cp->type == TS_SSH_CHANNEL_TYPE_SHELL) {
        cp->is_first_server_data = false;

        char buf[512] = {0};

        const char *auth_mode = nullptr;
        if (_this->m_auth_type == TP_AUTH_TYPE_PASSWORD)
            auth_mode = "password";
        else if (_this->m_auth_type == TP_AUTH_TYPE_PRIVATE_KEY)
            auth_mode = "private-key";
        else
            auth_mode = "unknown";

#ifdef EX_OS_WIN32
        int w = min(cp->win_width, 64);
#else
        int w = std::min(cp->win_width, 64);
#endif
        ex_astr line(w, '=');

        snprintf(buf, sizeof(buf),
                 "\r\n"\
                "%s\r\n"\
                "Teleport SSH Bastion Server...\r\n"\
                "  - teleport to %s:%d [%d]\r\n"\
                "  - authroized by %s\r\n"\
                "%s\r\n"\
                "\r\n\r\n",
                 line.c_str(),
                 _this->m_host_ip.c_str(),
                 _this->m_host_port,
                 cp->db_id,
                 auth_mode,
                 line.c_str()
        );

        auto buf_len = static_cast<unsigned int>(strlen(buf));
        _send_len = len + buf_len;
        ext_data.resize(_send_len);
        memset(&ext_data[0], 0, _send_len);
        memcpy(&ext_data[0], buf, buf_len);
        memcpy(&ext_data[buf_len], data, len);

        EXLOGV("[ssh] title:\n%s\n", &ext_data[0]);

        _send_data = &ext_data[0];

//        ret = ssh_channel_write(cp->channel_tp2cli, &_data[0], _data.size());
//
//        if (ret == SSH_ERROR) {
//            EXLOGE("[ssh] send data(%dB) to client failed. [%d] %s\n", len, ret, ssh_get_error(_this->m_owner->tp2cli()));
//            ssh_channel_close(channel);
//        }
//        else if (ret != len) {
//            EXLOGW("[ssh] received server data, got %dB, processed %dB.\n", len, ret);
//        }

//            _this->m_recving_from_srv = false;
//        return len;

    }
#endif

#if 1
    //static int idx = 0;

    // ssh_set_blocking(_this->m_session, 0);
    ssh_channel_set_blocking(cp->channel_tp2cli, 0);
    EXLOGD("[ssh] -- cp 3.\n");

    unsigned int sent_len = 0;
    do {
        // 直接转发数据到客户端
        if (is_stderr)
            ret = ssh_channel_write_stderr(cp->channel_tp2cli, _send_data + sent_len, _send_len - sent_len);
        else
            ret = ssh_channel_write(cp->channel_tp2cli, _send_data + sent_len, _send_len - sent_len);

        if (ret > 0) {
            sent_len += ret;
        }
        else if (ret == SSH_AGAIN) {
            EXLOGD("ssh_channel_write() need send again.\n");
            ex_sleep_ms(50);
            continue;
        }
        else {
            break;
        }
    }while(sent_len >= _send_len);

    // ssh_set_blocking(_this->m_session, 1);
    ssh_channel_set_blocking(cp->channel_tp2cli, 1);
    EXLOGD("[ssh] -- cp 4.\n");

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
            if (nullptr != _begin) {
                size_t len_before = _begin - (const ex_u8*)data;
                const ex_u8* _end = ex_memmem(_begin + 4, len - len_before, (const ex_u8*)"\007", 1);
                if (nullptr != _end)
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
        EXLOGE("[ssh] send data(%dB) to client failed. [%d] %s\n", _send_len, ret, ssh_get_error(_this->m_owner->tp2cli()));
        ssh_channel_close(channel);
        //cp->need_close = true;
        //_this->m_need_stop_poll = true;
    }
    else if (sent_len != _send_len) {
        EXLOGW("[ssh] received server data, got %dB, processed %dB.\n", _send_len, sent_len);
    }

//    _this->m_recving_from_srv = false;
    return sent_len > len ? len : sent_len;
}

void SshClientSide::_on_server_channel_close(ssh_session session, ssh_channel channel, void *userdata) {
    // 注意，此回调会在通道已经被关闭之后调用
    // 无需做额外操作，关闭的通道会由 SshSession 实例定期清理（包括关闭对端通道）
    EXLOGV("[ssh] channel tp<->server closed.\n");

//    auto *_this = (SshClientSide *) userdata;
//
//    auto cp = _this->m_owner->get_channel_pair(channel);
//    if (nullptr == cp) {
//        EXLOGE("[ssh] when server channel close, not found channel pair.\n");
//        return;
//    }
//    //cp->last_access_timestamp = (ex_u32)time(nullptr);
//    //cp->need_close = true;
//    //_this->m_need_stop_poll = true;
//
//    //EXLOGD("[ssh] [channel:%d]  --- end by server channel close\n", cp->channel_id);
//    //_this->_record_end(cp);
//
//    // will the server-channel exist, the client-channel must exist too.
//    if (cp->cli_channel == nullptr) {
//        EXLOGE("[ssh] when server channel close, client-channel not exists.\n");
//    }
//    else {
//        if (!ssh_channel_is_closed(cp->cli_channel)) {
//            //ssh_channel_close(cp->cli_channel);
//            //cp->need_close = true;
//            //_this->m_need_stop_poll = true;
//        }
//    }
}
