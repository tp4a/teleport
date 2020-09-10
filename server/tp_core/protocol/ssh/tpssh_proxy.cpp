#include "tpssh_proxy.h"
#include "tpp_env.h"

SshProxy g_ssh_proxy;

SshProxy::SshProxy() :
        ExThreadBase("ssh-proxy-thread"),
        m_bind(nullptr) {
    // m_session_dbg_base_id = 0;
    m_timer_counter_check_noop = 0;
    m_timer_counter_keep_alive = 0;
    m_cfg_noop_timeout_sec = 900; // default to 15 minutes.
    m_listener_running = false;
}

SshProxy::~SshProxy() {
    if (!m_bind) {
        ssh_bind_free(m_bind);
        m_bind = nullptr;
    }

    //ssh_finalize();
}

bool SshProxy::init() {
    m_host_ip = g_ssh_env.bind_ip;
    m_host_port = g_ssh_env.bind_port;

    m_bind = ssh_bind_new();
    if (!m_bind) {
        EXLOGE("[ssh] can not create bind.\n");
        return false;
    }

    if (SSH_OK != ssh_bind_options_set(m_bind, SSH_BIND_OPTIONS_BINDADDR, m_host_ip.c_str())) {
        EXLOGE("[ssh] can not set bind option: SSH_BIND_OPTIONS_BINDADDR.\n");
        return false;
    }
    if (SSH_OK != ssh_bind_options_set(m_bind, SSH_BIND_OPTIONS_BINDPORT, &m_host_port)) {
        EXLOGE("[ssh] can not set bind option: SSH_BIND_OPTIONS_BINDPORT.\n");
        return false;
    }

    ex_wstr _key_file = g_ssh_env.etc_path;
    ex_path_join(_key_file, false, L"tp_ssh_server.key", NULL);
    ex_astr key_file;
    ex_wstr2astr(_key_file, key_file);

    EXLOGV("[ssh] try to load ssh-server-key: %s\n", key_file.c_str());
    if (SSH_OK != ssh_bind_options_set(m_bind, SSH_BIND_OPTIONS_RSAKEY, key_file.c_str())) {
        EXLOGE("[ssh] can not set bind option: SSH_BIND_OPTIONS_RSAKEY.\n");
        return false;
    }

    if (ssh_bind_listen(m_bind) < 0) {
        EXLOGE("[ssh] listening to socket: %s\n", ssh_get_error(m_bind));
        return false;
    }

    m_listener_running = true;

    return true;
}

void SshProxy::timer() {
    // timer() will be called per one second
    m_timer_counter_check_noop++;
    m_timer_counter_keep_alive++;

    // clean closed session.
    _clean_closed_session();

    // check no-op per 5 seconds.
    // save record per 5 seconds.
    if (m_timer_counter_check_noop >= 5) {
        m_timer_counter_check_noop = 0;

        ExThreadSmartLock locker(m_lock);
        auto t_now = (uint32_t) time(nullptr);

        auto it = m_sessions.begin();
        for (; it != m_sessions.end(); ++it) {
            (*it)->save_record();
            if (0 != m_cfg_noop_timeout_sec)
                (*it)->check_noop_timeout(t_now, m_cfg_noop_timeout_sec);
        }
    }

//    // send keep-alive every 60 seconds
//    if (m_timer_counter_keep_alive >= 60) {
//        m_timer_counter_keep_alive = 0;
//        ExThreadSmartLock locker(m_lock);
//        auto it = m_sessions.begin();
//        for (; it != m_sessions.end(); ++it) {
//            (*it)->keep_alive();
//        }
//    }

    {
        ExThreadSmartLock locker(m_lock);

        auto it = m_sessions.begin();
        for (; it != m_sessions.end(); ++it) {
            (*it)->check_channels();
        }
    }
}

void SshProxy::set_cfg(ex_u32 noop_timeout) {
    m_cfg_noop_timeout_sec = noop_timeout;
}

void SshProxy::kill_sessions(const ex_astrs &sessions) {
    ExThreadSmartLock locker(m_lock);
    auto it = m_sessions.begin();
    for (; it != m_sessions.end(); ++it) {
        //for (size_t i = 0; i < sessions.size(); ++i) {
        for (const auto &session : sessions) {
            if ((*it)->sid() == session) {
                EXLOGW("[ssh] try to kill %s\n", session.c_str());
                (*it)->check_noop_timeout(0, 0); // 立即结束
            }
        }
    }
}

void SshProxy::_thread_loop() {
    EXLOGI("[ssh] TeleportServer-SSH ready on %s:%d\n", m_host_ip.c_str(), m_host_port);

    for (;;) {
        // 注意，ssh_new()出来的指针，如果遇到停止标志，本函数内部就释放了，否则这个指针交给了SshSession类实例管理，其析构时会释放。
        ssh_session sess_tp2cli = ssh_new();

// #ifdef EX_DEBUG
//        int flag = SSH_LOG_FUNCTIONS;
//        ssh_options_set(sess_tp2cli, SSH_OPTIONS_LOG_VERBOSITY, &flag);
// #endif

        // ssh_set_blocking(sess_tp2cli, 0);

        struct sockaddr_storage sock_client{};
        if (ssh_bind_accept(m_bind, sess_tp2cli) != SSH_OK) {
            EXLOGE("[ssh] accepting a connection failed: %s.\n", ssh_get_error(m_bind));
            continue;
        }
        EXLOGD("[ssh] ssh_bind_accept() returned...\n");

        if (m_need_stop) {
            ssh_free(sess_tp2cli);
            break;
        }

        char ip[32] = {0};
        int len = sizeof(ip);
#ifdef EX_OS_WIN32
        getpeername(ssh_get_fd(sess_to_client), (struct sockaddr *) &sock_client, &len);
#else
        getpeername(ssh_get_fd(sess_tp2cli), (struct sockaddr *) &sock_client, (unsigned int *) &len);
#endif
        auto *addrin = (sockaddr_in *) &sock_client;

        if (0 != ex_ip4_name(addrin, ip, sizeof(ip))) {
            ssh_free(sess_tp2cli);
            EXLOGE("[ssh] can not parse address of client.\n");
            continue;
        }

        // todo: add debug id for session and channel.
        auto s = new SshSession(this, ip, addrin->sin_port);
        EXLOGV("[ssh] ------ NEW SSH SESSION [%s] ------\n", s->dbg_name().c_str());

        {
            ExThreadSmartLock locker(m_lock);
            m_sessions.push_back(s);
        }

        if (!s->start(sess_tp2cli)) {
            EXLOGE("[ssh] can not start session [%s]\n", s->dbg_name().c_str());
            continue;
        }
    }

    // listen stoped, ask all sessions stop too.
    {
        ExThreadSmartLock locker(m_lock);
        auto it = m_sessions.begin();
        for (; it != m_sessions.end(); ++it) {
            (*it)->check_noop_timeout(0, 0); // 立即结束
        }
    }

    // and wait for all sessions stop.
    for (;;) {
        {
            ExThreadSmartLock locker(m_lock);
            timer();
            if (m_sessions.empty())
                break;
            ex_sleep_ms(500);
        }
    }

    m_listener_running = false;
    EXLOGV("[ssh] main-loop end.\n");
}

void SshProxy::_on_stop() {
    ExThreadBase::_on_stop();

    if (m_is_running) {
        // 用一个变通的方式来结束阻塞中的监听，就是连接一下它。
        ex_astr host_ip = m_host_ip;
        if (host_ip == "0.0.0.0")
            host_ip = "127.0.0.1";

        ssh_session _session = ssh_new();
        ssh_options_set(_session, SSH_OPTIONS_HOST, host_ip.c_str());
        ssh_options_set(_session, SSH_OPTIONS_PORT, &m_host_port);

        int _timeout_us = 10;
        ssh_options_set(_session, SSH_OPTIONS_TIMEOUT, &_timeout_us);
        ssh_connect(_session);
        ex_sleep_ms(500);

        ssh_disconnect(_session);
        ssh_free(_session);
        ex_sleep_ms(500);
    }

    while (m_listener_running) {
        ex_sleep_ms(1000);
    }

// 	m_thread_mgr.stop_all();
}

void SshProxy::_clean_closed_session() {
    ExThreadSmartLock locker(m_lock);
    auto it = m_sessions.begin();
    for (; it != m_sessions.end(); ) {
        if (!(*it)->is_running()) {
            EXLOGV("[ssh-%s] session removed.\n", (*it)->dbg_name().c_str());
            delete (*it);
            m_sessions.erase(it++);
        }
        else {
            ++it;
        }
    }
}
