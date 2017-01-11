#include "ssh_proxy.h"
#include "tpp_env.h"

SshProxy g_ssh_proxy;

SshProxy::SshProxy() :
	ExThreadBase("ssh-proxy-thread"),
	m_bind(NULL)
{
}

SshProxy::~SshProxy()
{
	if (NULL != m_bind)
		ssh_bind_free(m_bind);

	ssh_finalize();

	ts_sftp_sessions::iterator it = m_sftp_sessions.begin();
	for (; it != m_sftp_sessions.end(); ++it)
	{
		delete it->second;
	}
	m_sftp_sessions.clear();
}

bool SshProxy::init(void)
{
	m_host_ip = g_ssh_env.bind_ip;
	m_host_port = g_ssh_env.bind_port;


	m_bind = ssh_bind_new();
	if (NULL == m_bind)
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
		EXLOGE("[ssh] listening to socket: %s\n", ssh_get_error(m_bind));
		return false;
	}

	return true;
}

void SshProxy::_thread_loop(void)
{
	EXLOGV("[ssh] TeleportServer-SSH ready on %s:%d\n", m_host_ip.c_str(), m_host_port);
	_run();
	EXLOGV("[ssh] main-loop end.\n");
}

void SshProxy::_set_stop_flag(void)
{
	m_stop_flag = true;

	if (m_is_running)
	{
		// 用一个变通的方式来结束阻塞中的监听，就是连接一下它。
		ex_astr host_ip = m_host_ip;
		if (host_ip == "0.0.0.0")
			host_ip = "127.0.0.1";

		ssh_session _session = ssh_new();
		ssh_options_set(_session, SSH_OPTIONS_HOST, host_ip.c_str());
		ssh_options_set(_session, SSH_OPTIONS_PORT, &m_host_port);

		int _timeout_us = 100000;
		ssh_options_set(_session, SSH_OPTIONS_TIMEOUT_USEC, &_timeout_us);
		ssh_connect(_session);
		ssh_free(_session);
	}

	m_thread_mgr.stop_all();
}

void SshProxy::_run(void)
{
	for (;;)
	{
		// 注意，ssh_new()出来的指针，如果遇到停止标志，本函数内部就释放了，否则这个指针交给了SshSession类实例管理，其析构时会释放。
		ssh_session sess_to_client = ssh_new();

		struct sockaddr_storage sock_client;
		char ip[32] = { 0 };
		int len = sizeof(ip);

		if (ssh_bind_accept(m_bind, sess_to_client) != SSH_OK)
		{
			EXLOGE("[ssh] accepting a connection failed: %s.\n", ssh_get_error(m_bind));
			continue;
		}
		EXLOGD("[ssh] ssh_bind_accept() returned...\n");

		if (m_stop_flag)
		{
			ssh_free(sess_to_client);
			break;
		}

		SshSession* sess = new SshSession(this, sess_to_client);

#ifdef EX_OS_WIN32
		getpeername(ssh_get_fd(sess_to_client), (struct sockaddr*)&sock_client, &len);
#else
		getpeername(ssh_get_fd(sess_to_client), (struct sockaddr*)&sock_client, (unsigned int*)&len);
#endif
		sockaddr_in* addrin = (sockaddr_in*)&sock_client;

		if (0 == ex_ip4_name(addrin, ip, sizeof(ip)))
		{
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
	m_thread_mgr.stop_all();
}

void SshProxy::_dump_sftp_sessions(void)
{
	ts_sftp_sessions::iterator it = m_sftp_sessions.begin();
	for (; it != m_sftp_sessions.end(); ++it)
	{
		EXLOGD("ssh-proxy session: sid: %s\n", it->first.c_str());
	}
}

void SshProxy::add_sftp_session_info(const ex_astr& sid, const ex_astr& host_ip, int host_port, const ex_astr& user_name, const ex_astr& user_auth, int auth_mode)
{
	ExThreadSmartLock locker(m_lock);
	EXLOGD("[ssh] add sftp session-id: %s\n", sid.c_str());
	ts_sftp_sessions::iterator it = m_sftp_sessions.find(sid);
	if (it != m_sftp_sessions.end())
	{
		EXLOGD("[ssh] sftp-session-id '%s' already exists.\n", sid.c_str());
		it->second->ref_count++;
		return;
	}

	TS_SFTP_SESSION_INFO* info = new TS_SFTP_SESSION_INFO;
	info->host_ip = host_ip;
	info->host_port = host_port;
	info->user_name = user_name;
	info->user_auth = user_auth;
	info->auth_mode = auth_mode;
	info->ref_count = 1;

	if (!m_sftp_sessions.insert(std::make_pair(sid, info)).second)
	{
		EXLOGE("[ssh] ssh-proxy can not insert a sftp-session-id.\n");
	}

	_dump_sftp_sessions();
}

bool SshProxy::get_sftp_session_info(const ex_astr& sid, TS_SFTP_SESSION_INFO& info)
{
	ExThreadSmartLock locker(m_lock);
	EXLOGD("[ssh] try to get info by sftp session-id: %s\n", sid.c_str());

	_dump_sftp_sessions();

	ts_sftp_sessions::iterator it = m_sftp_sessions.find(sid);
	if (it == m_sftp_sessions.end())
	{
		EXLOGD("sftp-session '%s' not exists.\n", sid.c_str());
		return false;
	}

	info.host_ip = it->second->host_ip;
	info.host_port = it->second->host_port;
	info.user_name = it->second->user_name;
	info.user_auth = it->second->user_auth;
	info.auth_mode = it->second->auth_mode;
	info.ref_count = it->second->ref_count;

	return true;
}

void SshProxy::remove_sftp_sid(const ex_astr& sid)
{
	EXLOGD("[ssh] try to remove sftp session-id: %s\n", sid.c_str());

	ExThreadSmartLock locker(m_lock);
	ts_sftp_sessions::iterator it = m_sftp_sessions.find(sid);
	if (it == m_sftp_sessions.end())
	{
		EXLOGE("[ssh] ssh-proxy when remove sftp sid, it not in charge.\n");
		return;
	}

	it->second->ref_count--;
	if (it->second->ref_count <= 0)
	{
		delete it->second;
		m_sftp_sessions.erase(it);
		EXLOGD("[ssh] sftp session-id '%s' removed.\n", sid.c_str());
	}
}

void SshProxy::session_finished(SshSession* sess)
{
	ExThreadSmartLock locker(m_lock);
	ts_ssh_sessions::iterator it = m_sessions.find(sess);
	if (it != m_sessions.end())
	{
		m_sessions.erase(it);
		EXLOGV("[ssh] client %s:%d session removed.\n", sess->client_ip(), sess->client_port());
	}
	else
	{
		EXLOGW("[ssh] when session %s:%d end, it not in charge.\n", sess->client_ip(), sess->client_port());
	}

	delete sess;
}
