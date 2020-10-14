#include "ssh_proxy.h"
#include "tpp_env.h"

SshProxy g_ssh_proxy;

SshProxy::SshProxy() noexcept:
    ExThreadBase("ssh-proxy-thread"),
    m_bind(nullptr),
    m_host_port(0)
{
    m_timer_counter_check_noop = 0;
    m_timer_counter_keep_alive = 0;
    m_noop_timeout_sec         = 0;//900; // default to 15 minutes.
    m_listener_running         = false;
    m_dbg_id                   = 0;
}

SshProxy::~SshProxy()
{
    if (m_bind)
    {
        ssh_bind_free(m_bind);
        m_bind = nullptr;
    }
}

bool SshProxy::init()
{
    m_host_ip   = g_ssh_env.bind_ip;
    m_host_port = g_ssh_env.bind_port;

    m_bind = ssh_bind_new();
    if (!m_bind)
    {
        EXLOGE("[ssh] can not create bind.\n");
        return false;
    }

    if (SSH_OK != ssh_bind_options_set(m_bind, SSH_BIND_OPTIONS_BINDADDR, m_host_ip.c_str()))
    {
        EXLOGE("[ssh] can not set bind option: SSH_BIND_OPTIONS_BINDADDR.\n");
        return false;
    }

    if (SSH_OK != ssh_bind_options_set(m_bind, SSH_BIND_OPTIONS_BINDPORT, &m_host_port))
    {
        EXLOGE("[ssh] can not set bind option: SSH_BIND_OPTIONS_BINDPORT.\n");
        return false;
    }

    ex_wstr _key_file = g_ssh_env.etc_path;
    ex_path_join(_key_file, false, L"tp_ssh_server.key", NULL);
    ex_astr key_file;
    ex_wstr2astr(_key_file, key_file);

    EXLOGV("[ssh] try to load ssh-server-key: %s\n", key_file.c_str());
    if (SSH_OK != ssh_bind_options_set(m_bind, SSH_BIND_OPTIONS_RSAKEY, key_file.c_str()))
    {
        EXLOGE("[ssh] can not set bind option: SSH_BIND_OPTIONS_RSAKEY.\n");
        return false;
    }

    if (ssh_bind_listen(m_bind) < 0)
    {
        EXLOGE("[ssh] can not listen on port %d: %s\n", m_host_port, ssh_get_error(m_bind));
        return false;
    }

    return true;
}

void SshProxy::timer()
{
    // timer() will be called per one second by tp_core main thread.
    m_timer_counter_check_noop++;

    // clean closed session every one second.
    {
        ExThreadSmartLock locker(m_lock);

        for (auto it = m_sessions.begin(); it != m_sessions.end();)
        {
            // 检查通道是否已经关闭
            it->first->check_channels();
            // 检查会话是否已经关闭，如果会话已经完全关闭，则销毁之
            if (it->first->closed())
            {
                delete it->first;
                m_sessions.erase(it++);
            }
            else
            {
                ++it;
            }
        }

        if (m_need_stop)
            return;
    }

    // check no-op per 5 seconds.
    if (m_timer_counter_check_noop >= 5)
    {
        auto t_now = (ex_u32) time(nullptr);
        m_timer_counter_check_noop = 0;

        ExThreadSmartLock locker(m_lock);

        for (auto &session : m_sessions)
        {
            session.first->save_record();
            if (0 != m_noop_timeout_sec)
                session.first->check_noop_timeout(t_now, m_noop_timeout_sec);
        }
    }
}

void SshProxy::set_cfg(ex_u32 noop_timeout)
{
    m_noop_timeout_sec = noop_timeout;
}

void SshProxy::kill_sessions(const ex_astrs &sessions)
{
    ExThreadSmartLock locker(m_lock);

    for (auto &session : m_sessions)
    {
        for (const auto &sid : sessions)
        {
            if (session.first->sid() == sid)
            {
                EXLOGW("[ssh] kill session %s\n", sid.c_str());
                session.first->check_noop_timeout(0, 0); // 立即结束
                break;
            }
        }
    }
}

void SshProxy::_thread_loop()
{
    EXLOGI("[ssh] TeleportServer-SSH ready on %s:%d\n", m_host_ip.c_str(), m_host_port);

    m_listener_running = true;

    for (;;)
    {
        ssh_session rs_tp2cli = ssh_new();

// #ifdef EX_DEBUG
//        int flag = SSH_LOG_FUNCTIONS;
//        ssh_options_set(rs_tp2cli, SSH_OPTIONS_LOG_VERBOSITY, &flag);
// #endif

        if (ssh_bind_accept(m_bind, rs_tp2cli) != SSH_OK)
        {
            EXLOGE("[ssh] accepting a connection failed: %s.\n", ssh_get_error(m_bind));
            continue;
        }
        EXLOGD("[ssh] ssh_bind_accept() returned...\n");

        if (m_need_stop)
        {
            ssh_free(rs_tp2cli);
            break;
        }

        struct sockaddr_storage sock_client{};

        char ip[32] = { 0 };
        int  len    = sizeof(ip);


#ifdef EX_OS_WIN32
        getpeername(ssh_get_fd(rs_tp2cli), (struct sockaddr *) &sock_client, &len);
#else
        getpeername(ssh_get_fd(rs_tp2cli), (struct sockaddr *) &sock_client, (unsigned int *) &len);
#endif
        auto addr = (sockaddr_in *) &sock_client;

        if (0 != ex_ip4_name(addr, ip, sizeof(ip)))
        {
            EXLOGW("[ssh] can not parse client address into IP and port.\n");
        }

        uint32_t dbg_id  = m_dbg_id++;
        auto     session = new SshSession(this, rs_tp2cli, dbg_id, ip, addr->sin_port);
        EXLOGW("[ssh] ------ NEW SSH SESSION [%s from %s:%d] ------\n", session->dbg_name().c_str(), ip, addr->sin_port);

        {
            ExThreadSmartLock locker(m_lock);
            m_sessions.insert(std::make_pair(session, 0));
        }

        session->start();
    }

    // 通知所有session都立即结束
    {
        ExThreadSmartLock locker(m_lock);


        for (auto &session : m_sessions)
        {
            session.first->check_noop_timeout(0, 0);
        }
    }

    // 等待所有session完成关闭清理操作，工作线程退出
    for (;;)
    {
        // tp_core退出时会先停止timer线程，所以这里需要自己调用timer()来进行session状态检查
        timer();

        {
            ExThreadSmartLock locker(m_lock);
            if (m_sessions.empty())
                break;
            ex_sleep_ms(100);
        }
    }

    m_listener_running = false;
    EXLOGV("[ssh] main-loop end.\n");
}

void SshProxy::_on_stop()
{
    ExThreadBase::_on_stop();

    if (m_is_running)
    {
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

    while (m_listener_running)
    {
        ex_sleep_ms(1000);
    }
}
