#include "ssh_proxy.h"
#include "tpp_env.h"

SshProxy g_ssh_proxy;

SshProxy::SshProxy() :
        ExThreadBase("ssh-proxy-thread"),
        m_bind(NULL) {
    m_timer_counter = 0;

    m_noop_timeout_sec = 900; // default to 15 minutes.
}

SshProxy::~SshProxy() {
    if (NULL != m_bind)
        ssh_bind_free(m_bind);

    ssh_finalize();
}

bool SshProxy::init() {
    m_host_ip = g_ssh_env.bind_ip;
    m_host_port = g_ssh_env.bind_port;

    m_bind = ssh_bind_new();
    if (NULL == m_bind) {
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

    return true;
}

void SshProxy::timer() {
    // timer() will be called per one second, and I will do my job per 5 seconds.
    m_timer_counter++;
    if (m_timer_counter < 5)
        return;

    m_timer_counter = 0;

    ExThreadSmartLock locker(m_lock);
    ex_u32 t_now = (ex_u32) time(NULL);

    ts_ssh_sessions::iterator it;
    for (it = m_sessions.begin(); it != m_sessions.end(); ++it) {
        it->first->save_record();
        if (0 != m_noop_timeout_sec)
            it->first->check_noop_timeout(t_now, m_noop_timeout_sec);
    }
}

void SshProxy::set_cfg(ex_u32 noop_timeout) {
    m_noop_timeout_sec = noop_timeout;
}

void SshProxy::kill_sessions(const ex_astrs &sessions) {
    ExThreadSmartLock locker(m_lock);
    ts_ssh_sessions::iterator it = m_sessions.begin();
    for (; it != m_sessions.end(); ++it) {
        for (size_t i = 0; i < sessions.size(); ++i) {
            if (it->first->sid() == sessions[i]) {
                EXLOGW("[ssh] try to kill %s\n", sessions[i].c_str());
                it->first->check_noop_timeout(0, 0); // 立即结束
            }
        }
    }
}

void SshProxy::_thread_loop() {
    EXLOGI("[ssh] TeleportServer-SSH ready on %s:%d\n", m_host_ip.c_str(), m_host_port);

    for (;;) {
        // 注意，ssh_new()出来的指针，如果遇到停止标志，本函数内部就释放了，否则这个指针交给了SshSession类实例管理，其析构时会释放。
        ssh_session sess_to_client = ssh_new();

        // int flag = SSH_LOG_FUNCTIONS;
 		// ssh_options_set(sess_to_client, SSH_OPTIONS_LOG_VERBOSITY, &flag);

        ssh_set_blocking(sess_to_client, 1);

        struct sockaddr_storage sock_client;
        char ip[32] = {0};
        int len = sizeof(ip);

        if (ssh_bind_accept(m_bind, sess_to_client) != SSH_OK) {
            EXLOGE("[ssh] accepting a connection failed: %s.\n", ssh_get_error(m_bind));
            continue;
        }
        EXLOGD("[ssh] ssh_bind_accept() returned...\n");

        if (m_need_stop) {
            ssh_free(sess_to_client);
            break;
        }

        SshSession *sess = new SshSession(this, sess_to_client);

#ifdef EX_OS_WIN32
        getpeername(ssh_get_fd(sess_to_client), (struct sockaddr *) &sock_client, &len);
#else
        getpeername(ssh_get_fd(sess_to_client), (struct sockaddr*)&sock_client, (unsigned int*)&len);
#endif
        sockaddr_in *addrin = (sockaddr_in *) &sock_client;

        if (0 == ex_ip4_name(addrin, ip, sizeof(ip))) {
            sess->client_ip(ip);
            sess->client_port(addrin->sin_port);
        }


        EXLOGV("[ssh] ------ NEW SSH CLIENT [%s:%d] ------\n", sess->client_ip(), sess->client_port());


        {
            ExThreadSmartLock locker(m_lock);
            m_sessions.insert(std::make_pair(sess, 0));
        }

        sess->start();
    }

    // 等待所有工作线程退出
    //m_thread_mgr.stop_all();

    {
        ExThreadSmartLock locker(m_lock);
        ts_ssh_sessions::iterator it = m_sessions.begin();
        for (; it != m_sessions.end(); ++it) {
            it->first->check_noop_timeout(0, 0); // 立即结束
        }
    }

    for(;;)
    {
        {
            ExThreadSmartLock locker(m_lock);
            if (m_sessions.empty())
                break;
            ex_sleep_ms(100);
        }
    }

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
        ssh_free(_session);
    }

// 	m_thread_mgr.stop_all();
}

void SshProxy::session_finished(SshSession *sess) {
    // TODO: 向核心模块汇报此会话终止，以减少对应连接信息的引用计数

    ExThreadSmartLock locker(m_lock);
    ts_ssh_sessions::iterator it = m_sessions.find(sess);
    if (it != m_sessions.end()) {
        m_sessions.erase(it);
        EXLOGV("[ssh] client %s:%d session removed.\n", sess->client_ip(), sess->client_port());
    } else {
        EXLOGW("[ssh] when session %s:%d end, it not in charge.\n", sess->client_ip(), sess->client_port());
    }

    delete sess;
}
