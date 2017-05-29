#include "ssh_session.h"
#include "ssh_proxy.h"
#include "tpp_env.h"

#include <algorithm>

SshSession::SshSession(SshProxy *proxy, ssh_session sess_client) :
	ExThreadBase("ssh-session-thread"),
	m_proxy(proxy),
	m_cli_session(sess_client),
	m_srv_session(NULL)
{
	m_retcode = SESS_STAT_RUNNING;
	m_db_id = 0;

	m_auth_mode = TS_AUTH_MODE_PASSWORD;

	m_is_first_server_data = true;
	m_is_sftp = false;

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

	m_command_flag = 0;
	m_cmd_char_pos = m_cmd_char_list.begin();
}

SshSession::~SshSession() {

	_set_stop_flag();

	if (m_is_sftp) {
		m_proxy->remove_sftp_sid(m_sid);
	}

	EXLOGD("[ssh] session destroy.\n");
}

void SshSession::_thread_loop(void) {
	_run();
	_on_session_end();
	m_proxy->session_finished(this);
}

void SshSession::_set_stop_flag(void) {
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

bool SshSession::_on_session_begin(const TPP_SESSION_INFO* info)
{
	if (!g_ssh_env.session_begin(info, &m_db_id))
	{
		EXLOGD("[ssh] session_begin error. %d\n", m_db_id);
		return false;
	}

	m_rec.begin(g_ssh_env.replay_path.c_str(), L"tp-ssh", m_db_id, info);

	return true;
}

bool SshSession::_on_session_end(void)
{
	if (m_db_id > 0)
	{
		EXLOGD("[ssh] session ret-code: %d\n", m_retcode);

		// 如果会话过程中没有发生错误，则将其状态改为结束，否则记录下错误值
		if (m_retcode == SESS_STAT_RUNNING)
			m_retcode = SESS_STAT_END;

		g_ssh_env.session_end(m_db_id, m_retcode);
	}

	return true;
}

void SshSession::_close_channels(void) {
	ExThreadSmartLock locker(m_lock);

	if (m_channel_cli_srv.size() > 0)
		EXLOGW("[ssh] when close all channels, %d client channel need close.\n", m_channel_cli_srv.size());
	if (m_channel_srv_cli.size() > 0)
		EXLOGW("[ssh] when close all channels, %d server channel need close.\n", m_channel_srv_cli.size());

	ts_ssh_channel_map::iterator it = m_channel_cli_srv.begin();
	for (; it != m_channel_cli_srv.end(); ++it) {
		if (!ssh_channel_is_eof(it->first))
			ssh_channel_send_eof(it->first);
		if (!ssh_channel_is_closed(it->first))
			ssh_channel_close(it->first);
		ssh_channel_free(it->first);

		if (NULL != it->second) {
			if (!ssh_channel_is_eof(it->second->channel))
				ssh_channel_send_eof(it->second->channel);
			if (!ssh_channel_is_closed(it->second->channel))
				ssh_channel_close(it->second->channel);
			ssh_channel_free(it->second->channel);

			delete it->second;
		}
	}

	it = m_channel_srv_cli.begin();
	for (; it != m_channel_srv_cli.end(); ++it) {
		if (NULL != it->second) {
			delete it->second;
		}
	}

	m_channel_cli_srv.clear();
	m_channel_srv_cli.clear();
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

	// 安全连接（密钥交换）
	if (ssh_handle_key_exchange(m_cli_session)) {
		EXLOGE("[ssh] key exchange with client failed: %s\n", ssh_get_error(m_cli_session));
		return;
	}

	ssh_event event_loop = ssh_event_new();
	ssh_event_add_session(event_loop, m_cli_session);

	// 认证，并打开一个通道
	int r = 0;
	while (!(m_is_logon && m_channel_cli_srv.size() > 0)) {
		if (m_have_error)
			break;
		r = ssh_event_dopoll(event_loop, -1);
		if (r == SSH_ERROR) {
			EXLOGE("[ssh] Error : %s\n", ssh_get_error(m_cli_session));
			ssh_disconnect(m_cli_session);
			return;
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
		r = ssh_event_dopoll(event_loop, -1);
		if (r == SSH_ERROR) {
			if (0 != ssh_get_error_code(m_cli_session))
			{
				EXLOGE("[ssh] ssh_event_dopoll() [cli] %s\n", ssh_get_error(m_cli_session));
			}
			else if (0 != ssh_get_error_code(m_srv_session))
			{
				EXLOGE("[ssh] ssh_event_dopoll() [srv] %s\n", ssh_get_error(m_srv_session));
			}

			_close_channels();
		}
	} while (m_channel_cli_srv.size() > 0);

	EXLOGV("[ssh] [%s:%d] all channel in this session are closed.\n", m_client_ip.c_str(), m_client_port);

	ssh_event_remove_session(event_loop, m_cli_session);
	ssh_event_remove_session(event_loop, m_srv_session);
	ssh_event_free(event_loop);
}


int SshSession::_on_auth_password_request(ssh_session session, const char *user, const char *password, void *userdata) {
	// 这里拿到的user就是我们要的session-id，password可以用ticket来填充，作为额外判断用户是否被允许访问的依据。
	SshSession *_this = (SshSession *)userdata;
	_this->m_sid = user;
	EXLOGV("[ssh] authenticating, session-id: %s\n", _this->m_sid.c_str());

	int protocol = 0;
	TPP_SESSION_INFO* sess_info = g_ssh_env.take_session(_this->m_sid.c_str());

	if (NULL == sess_info) {
		EXLOGW("[ssh] try to get login-info from ssh-sftp-session.\n");
		// 尝试从sftp连接记录中获取连接信息（一个ssh会话如果成为sftp会话，内部会将连接信息记录下来备用）
		TS_SFTP_SESSION_INFO sftp_info;
		if (!_this->m_proxy->get_sftp_session_info(_this->m_sid, sftp_info)) {
			EXLOGE("[ssh] no such session: %s\n", _this->m_sid.c_str());
			_this->m_have_error = true;
			_this->m_retcode = SESS_STAT_ERR_AUTH_DENIED;
			return SSH_AUTH_DENIED;
		}

		_this->m_server_ip = sftp_info.host_ip;
		_this->m_server_port = sftp_info.host_port;
		_this->m_auth_mode = sftp_info.auth_mode;
		_this->m_user_name = sftp_info.user_name;
		_this->m_user_auth = sftp_info.user_auth;
		protocol = TS_PROXY_PROTOCOL_SSH;

		// 因为是从sftp会话得来的登录数据，因此限制本会话只能用于sftp，不允许再使用shell了。
		_this->_enter_sftp_mode();
	} else {
		_this->m_server_ip = sess_info->host_ip;
		_this->m_server_port = sess_info->host_port;
		_this->m_auth_mode = sess_info->auth_mode;
		_this->m_user_name = sess_info->user_name;
		_this->m_user_auth = sess_info->user_auth;
		protocol = sess_info->protocol;
	}

	if (protocol != TS_PROXY_PROTOCOL_SSH) {
		g_ssh_env.free_session(sess_info);
		EXLOGE("[ssh] session '%s' is not for SSH.\n", _this->m_sid.c_str());
		_this->m_have_error = true;
		_this->m_retcode = SESS_STAT_ERR_AUTH_DENIED;
		return SSH_AUTH_DENIED;
	}

	if (!_this->_on_session_begin(sess_info))
	{
		g_ssh_env.free_session(sess_info);
		_this->m_have_error = true;
		_this->m_retcode = SESS_STAT_ERR_AUTH_DENIED;
		return SSH_AUTH_DENIED;
	}

	g_ssh_env.free_session(sess_info);
	sess_info = NULL;

	// 现在尝试根据session-id获取得到的信息，连接并登录真正的SSH服务器
	EXLOGV("[ssh] try to connect to real SSH server %s:%d\n", _this->m_server_ip.c_str(), _this->m_server_port);
	_this->m_srv_session = ssh_new();
	ssh_options_set(_this->m_srv_session, SSH_OPTIONS_HOST, _this->m_server_ip.c_str());
	int port = (int)_this->m_server_port;
	ssh_options_set(_this->m_srv_session, SSH_OPTIONS_PORT, &port);
#ifdef EX_DEBUG
// 	int flag = SSH_LOG_FUNCTIONS;
// 	ssh_options_set(_this->m_srv_session, SSH_OPTIONS_LOG_VERBOSITY, &flag);
#endif

	if (_this->m_auth_mode != TS_AUTH_MODE_NONE)
		ssh_options_set(_this->m_srv_session, SSH_OPTIONS_USER, _this->m_user_name.c_str());

#ifdef EX_DEBUG
// 	int _timeout_us = 500000000; // 5 sec.
// 	ssh_options_set(_this->m_srv_session, SSH_OPTIONS_TIMEOUT_USEC, &_timeout_us);
#else
	int _timeout_us = 10000000; // 10 sec.
	ssh_options_set(_this->m_srv_session, SSH_OPTIONS_TIMEOUT_USEC, &_timeout_us);
#endif

	int rc = 0;
	rc = ssh_connect(_this->m_srv_session);
	if (rc != SSH_OK) {
		EXLOGE("[ssh] can not connect to real SSH server %s:%d. [%d]%s\n", _this->m_server_ip.c_str(), _this->m_server_port, rc, ssh_get_error(_this->m_srv_session));
		_this->m_have_error = true;
		_this->m_retcode = SESS_STAT_ERR_CONNECT;
		return SSH_AUTH_ERROR;
	}

	// 检查服务端支持的认证协议
	ssh_userauth_none(_this->m_srv_session, NULL);
	int auth_methods = ssh_userauth_list(_this->m_srv_session, NULL);

	if (_this->m_auth_mode == TS_AUTH_MODE_PASSWORD) {
		if (auth_methods & SSH_AUTH_METHOD_PASSWORD) {
			rc = ssh_userauth_password(_this->m_srv_session, NULL, _this->m_user_auth.c_str());
			if (rc != SSH_AUTH_SUCCESS) {
				EXLOGE("[ssh] invalid password for password mode to login to real SSH server %s:%d.\n", _this->m_server_ip.c_str(), _this->m_server_port);
				_this->m_have_error = true;
				_this->m_retcode = SESS_STAT_ERR_AUTH_DENIED;
				return SSH_AUTH_DENIED;
			}
		}
		else if (auth_methods & SSH_AUTH_METHOD_INTERACTIVE) {
			bool is_login = false;
			for (;;) {
				rc = ssh_userauth_kbdint(_this->m_srv_session, NULL, NULL);
				if (rc != SSH_AUTH_INFO)
					break;

				if(ssh_userauth_kbdint_getnprompts(_this->m_srv_session) != 1)
					break;

				rc = ssh_userauth_kbdint_setanswer(_this->m_srv_session, 0, _this->m_user_auth.c_str());
				if (rc < 0)
					break;

				// 有时候服务端会再发一个空的提示来完成交互
				rc = ssh_userauth_kbdint(_this->m_srv_session, NULL, NULL);
				if (rc == SSH_AUTH_INFO) {
					if (ssh_userauth_kbdint_getnprompts(_this->m_srv_session) != 0)
						break;
					rc = ssh_userauth_kbdint(_this->m_srv_session, NULL, NULL);
					if (rc < 0)
						break;
				}

				if(rc == SSH_AUTH_SUCCESS)
					is_login = true;
				break;
			}

			if (!is_login) {
				EXLOGE("[ssh] invalid password for keyboard-interactive mode to login to real SSH server %s:%d.\n", _this->m_server_ip.c_str(), _this->m_server_port);
				_this->m_have_error = true;
				_this->m_retcode = SESS_STAT_ERR_AUTH_DENIED;
				return SSH_AUTH_DENIED;
			}
		}
		else {
			EXLOGE("[ssh] real SSH server [%s:%d] does not support password or keyboard-interactive login.\n", _this->m_server_ip.c_str(), _this->m_server_port);
			_this->m_have_error = true;
			_this->m_retcode = SESS_STAT_ERR_AUTH_DENIED;
			return SSH_AUTH_DENIED;
		}
	}
	else if (_this->m_auth_mode == TS_AUTH_MODE_PRIVATE_KEY) {
		if (auth_methods & SSH_AUTH_METHOD_PUBLICKEY) {
			ssh_key key = NULL;
			if (SSH_OK != ssh_pki_import_privkey_base64(_this->m_user_auth.c_str(), NULL, NULL, NULL, &key)) {
				EXLOGE("[ssh] can not import private-key for auth.\n");
				_this->m_have_error = true;
				_this->m_retcode = SESS_STAT_ERR_BAD_SSH_KEY;
				return SSH_AUTH_DENIED;
			}

			rc = ssh_userauth_publickey(_this->m_srv_session, NULL, key);
			if (rc != SSH_OK) {
				ssh_key_free(key);
				EXLOGE("[ssh] invalid private-key for login to real SSH server %s:%d.\n", _this->m_server_ip.c_str(), _this->m_server_port);
				_this->m_have_error = true;
				_this->m_retcode = SESS_STAT_ERR_AUTH_DENIED;
				return SSH_AUTH_DENIED;
			}

			ssh_key_free(key);
		}
		else {
			EXLOGE("[ssh] real SSH server [%s:%d] does not support public key login.\n", _this->m_server_ip.c_str(), _this->m_server_port);
			_this->m_have_error = true;
			_this->m_retcode = SESS_STAT_ERR_AUTH_DENIED;
			return SSH_AUTH_DENIED;
		}

	}
	else if (_this->m_auth_mode == TS_AUTH_MODE_NONE)
	{
		// do nothing.
		return SSH_AUTH_DENIED;
	}
	else {
		EXLOGE("[ssh] invalid auth mode.\n");
		_this->m_have_error = true;
		_this->m_retcode = SESS_STAT_ERR_AUTH_DENIED;
		return SSH_AUTH_DENIED;
	}

	_this->m_is_logon = true;
	return SSH_AUTH_SUCCESS;
}

ssh_channel SshSession::_on_new_channel_request(ssh_session session, void *userdata) {
	// 客户端尝试打开一个通道（然后才能通过这个通道发控制命令或者收发数据）
	EXLOGV("[ssh] allocated session channel\n");

	SshSession *_this = (SshSession *)userdata;

	ssh_channel cli_channel = ssh_channel_new(session);
	ssh_set_channel_callbacks(cli_channel, &_this->m_cli_channel_cb);

	// 我们也要向真正的服务器申请打开一个通道，来进行转发
	ssh_channel srv_channel = ssh_channel_new(_this->m_srv_session);
	if (ssh_channel_open_session(srv_channel)) {
		EXLOGE("[ssh] error opening channel to real server: %s\n", ssh_get_error(session));
		ssh_channel_free(cli_channel);
		return NULL;
	}
	ssh_set_channel_callbacks(srv_channel, &_this->m_srv_channel_cb);

	// 将客户端和服务端的通道关联起来
	{
		ExThreadSmartLock locker(_this->m_lock);

		TS_SSH_CHANNEL_INFO *srv_info = new TS_SSH_CHANNEL_INFO;
		srv_info->channel = srv_channel;
		srv_info->type = TS_SSH_CHANNEL_TYPE_UNKNOWN;
		_this->m_channel_cli_srv.insert(std::make_pair(cli_channel, srv_info));

		TS_SSH_CHANNEL_INFO *cli_info = new TS_SSH_CHANNEL_INFO;
		cli_info->channel = cli_channel;
		cli_info->type = TS_SSH_CHANNEL_TYPE_UNKNOWN;
		_this->m_channel_srv_cli.insert(std::make_pair(srv_channel, cli_info));
	}

	return cli_channel;
}

TS_SSH_CHANNEL_INFO *SshSession::_get_cli_channel(ssh_channel srv_channel) {
	ExThreadSmartLock locker(m_lock);
	ts_ssh_channel_map::iterator it = m_channel_srv_cli.find(srv_channel);
	if (it == m_channel_srv_cli.end())
		return NULL;
	else
		return it->second;
}

TS_SSH_CHANNEL_INFO *SshSession::_get_srv_channel(ssh_channel cli_channel) {
	ExThreadSmartLock locker(m_lock);
	ts_ssh_channel_map::iterator it = m_channel_cli_srv.find(cli_channel);
	if (it == m_channel_cli_srv.end())
		return NULL;
	else
		return it->second;
}

void SshSession::_process_ssh_command(int from, const ex_u8* data, int len)
{
	if (TS_SSH_DATA_FROM_CLIENT == from)
	{
		m_command_flag = 0;

		if (len == 3)
		{
			if ((data[0] == 0x1b && data[1] == 0x5b && data[2] == 0x41)			// key-up
				|| (data[0] == 0x1b && data[1] == 0x5b && data[2] == 0x42)		// key-down
				)
			{
				m_command_flag = 1;
				return;
			}
			else if (data[0] == 0x1b && data[1] == 0x5b && data[2] == 0x43)		// key-right
			{
				if (m_cmd_char_pos != m_cmd_char_list.end())
					m_cmd_char_pos++;
				return;
			}
			else if (data[0] == 0x1b && data[1] == 0x5b && data[2] == 0x44)		// key-left
			{
				if (m_cmd_char_pos != m_cmd_char_list.begin())
					m_cmd_char_pos--;
				return;
			}
			else if (
				(data[0] == 0x1b && data[1] == 0x4f && data[2] == 0x41)
				|| (data[0] == 0x1b && data[1] == 0x4f && data[2] == 0x42)
				|| (data[0] == 0x1b && data[1] == 0x4f && data[2] == 0x43)
				|| (data[0] == 0x1b && data[1] == 0x4f && data[2] == 0x44)
				)
			{
				// 编辑模式下的上下左右键
				return;
			}
		}
		else if (len == 1)
		{
			if (data[0] == 0x09)
			{
				m_command_flag = 1;
				return;
			}
			else if (data[0] == 0x7f)	// Backspace (回删一个字符)
			{
				if (m_cmd_char_pos != m_cmd_char_list.begin())
				{
					m_cmd_char_pos--;
					m_cmd_char_pos = m_cmd_char_list.erase(m_cmd_char_pos);
				}
				return;
			}
			else if (data[0] == 0x1b)
			{
				// 按下 Esc 键
				return;
			}

			if (data[0] != 0x0d && !isprint(data[0]))
				return;
		}
		else if (len > 3)
		{
			if (data[0] == 0x1b && data[1] == 0x5b)
			{
				// 不是命令行上的上下左右，也不是编辑模式下的上下左右，那么就忽略（应该是编辑模式下的其他输入）
				m_cmd_char_list.clear();
				m_cmd_char_pos = m_cmd_char_list.begin();
				return;
			}
		}

		int processed = 0;
		for (int i = 0; i < len; i++)
		{
			if (data[i] == 0x0d)
			{
				m_command_flag = 0;

				for (int j = processed; j < i; ++j)
				{
					m_cmd_char_pos = m_cmd_char_list.insert(m_cmd_char_pos, data[j]);
					m_cmd_char_pos++;
				}

				if (m_cmd_char_list.size() > 0)
				{
					ex_astr str(m_cmd_char_list.begin(), m_cmd_char_list.end());
					ex_replace_all(str, "\r", "");
					ex_replace_all(str, "\n", "");
					//EXLOGD("[ssh] save cmd: [%s]", str.c_str());
					str += "\r\n";
					m_rec.record_command(str);
				}
				m_cmd_char_list.clear();
				m_cmd_char_pos = m_cmd_char_list.begin();

				processed = i + 1;
			}
		}

		if (processed < len)
		{
			for (int j = processed; j < len; ++j)
			{
				m_cmd_char_pos = m_cmd_char_list.insert(m_cmd_char_pos, data[j]);
				m_cmd_char_pos++;
			}
		}
	}
	else if (TS_SSH_DATA_FROM_SERVER == from)
	{
		if (m_command_flag == 0)
			return;

		bool esc_mode = false;
		int esc_arg = 0;

		for (int i = 0; i < len; i++)
		{
			if (esc_mode)
			{
				switch (data[i])
				{
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
					esc_arg = esc_arg * 10 + (data[i] - '0');
					break;

				case 0x3f:
				case ';':
				case '>':
					m_cmd_char_list.clear();
					m_cmd_char_pos = m_cmd_char_list.begin();
					return;
					break;

				case 0x4b:	// 'K'
				{
					if (0 == esc_arg)
					{
						// 删除光标到行尾的字符串
						m_cmd_char_list.erase(m_cmd_char_pos, m_cmd_char_list.end());
						m_cmd_char_pos = m_cmd_char_list.end();
					}
					else if (1 == esc_arg)
					{
						// 删除从开始到光标处的字符串
						m_cmd_char_list.erase(m_cmd_char_list.begin(), m_cmd_char_pos);
						m_cmd_char_pos = m_cmd_char_list.end();
					}
					else if (2 == esc_arg)
					{
						// 删除整行
						m_cmd_char_list.clear();
						m_cmd_char_pos = m_cmd_char_list.begin();
					}

					esc_mode = false;
					break;
				}
				case 0x43:	// 'C'
				{
					// 光标右移
					if (esc_arg == 0)
						esc_arg = 1;
					for (int j = 0; j < esc_arg; ++j)
					{
						if (m_cmd_char_pos != m_cmd_char_list.end())
							m_cmd_char_pos++;
					}
					esc_mode = false;
					break;
				}

				case 0x50:	// 'P' 删除指定数量的字符
				{
					if (esc_arg == 0)
						esc_arg = 1;
					for (int j = 0; j < esc_arg; ++j)
					{
						if (m_cmd_char_pos != m_cmd_char_list.end())
							m_cmd_char_pos = m_cmd_char_list.erase(m_cmd_char_pos);
					}
					esc_mode = false;
					break;
				}

				case 0x40:	// '@' 插入指定数量的空白字符
				{
					if (esc_arg == 0)
						esc_arg = 1;
					for (int j = 0; j < esc_arg; ++j)
					{
						m_cmd_char_pos = m_cmd_char_list.insert(m_cmd_char_pos, ' ');
					}
					esc_mode = false;
					break;
				}

				default:
					esc_mode = false;
					break;
				}

				continue;
			}

			switch (data[i])
			{
			case 0x07:
			{
				// 响铃
				break;
			}
			case 0x08:
			{
				// 光标左移
				if (m_cmd_char_pos != m_cmd_char_list.begin())
					m_cmd_char_pos--;

				break;
			}
			case 0x1b:
			{
				if (i + 1 < len)
				{
					if (data[i + 1] == 0x5b)
					{
						esc_mode = true;
						esc_arg = 0;

						i += 1;
						break;
					}
				}

				break;
			}
			case 0x0d:
			{
				m_cmd_char_list.clear();
				m_cmd_char_pos = m_cmd_char_list.begin();

				break;
			}
			default:
				if (m_cmd_char_pos != m_cmd_char_list.end())
				{
					m_cmd_char_pos = m_cmd_char_list.erase(m_cmd_char_pos);
					m_cmd_char_pos = m_cmd_char_list.insert(m_cmd_char_pos, data[i]);
					m_cmd_char_pos++;
				}
				else
				{
					m_cmd_char_list.push_back(data[i]);
					m_cmd_char_pos = m_cmd_char_list.end();
				}
			}
		}
	}

	return;
}

void SshSession::_process_sftp_command(const ex_u8* data, int len) {
	// SFTP protocol: https://tools.ietf.org/html/draft-ietf-secsh-filexfer-13
	//EXLOG_BIN(data, len, "[sftp] client channel data");

	if (len < 9)
		return;

	int pkg_len = (int)((data[0] << 24) | (data[1] << 16) | (data[2] << 8) | data[3]);
	if (pkg_len + 4 != len)
		return;

	ex_u8 sftp_cmd = data[4];

	if (sftp_cmd == 0x01) {
		// 0x01 = 1 = SSH_FXP_INIT
		m_rec.record_command("SFTP INITIALIZE\r\n");
		return;
	}
	
	// 需要的数据至少14字节
	// uint32 + byte + uint32 + (uint32 + char + ...)
	// pkg_len + cmd + req_id + string( length + content...)
	if (len < 14)
		return;

	ex_u8* str1_ptr = (ex_u8*)data + 9;
	int str1_len = (int)((str1_ptr[0] << 24) | (str1_ptr[1] << 16) | (str1_ptr[2] << 8) | str1_ptr[3]);
// 	if (str1_len + 9 != pkg_len)
// 		return;
	ex_u8* str2_ptr = NULL;// (ex_u8*)data + 13;
	int str2_len = 0;// (int)((data[9] << 24) | (data[10] << 16) | (data[11] << 8) | data[12]);

	
	char* act = NULL;
	switch (sftp_cmd) {
	case 0x03:
		// 0x03 = 3 = SSH_FXP_OPEN
		act = "open file";
		break;
// 	case 0x0b:
// 		// 0x0b = 11 = SSH_FXP_OPENDIR
// 		act = "open dir";
// 		break;
	case 0x0d:
		// 0x0d = 13 = SSH_FXP_REMOVE
		act = "remove file";
		break;
	case 0x0e:
		// 0x0e = 14 = SSH_FXP_MKDIR
		act = "create dir";
		break;
	case 0x0f:
		// 0x0f = 15 = SSH_FXP_RMDIR
		act = "remove dir";
		break;
	case 0x12:
		// 0x12 = 18 = SSH_FXP_RENAME
		// rename操作数据中包含两个字符串
		act = "rename";
		str2_ptr = str1_ptr + str1_len + 4;
		str2_len = (int)((str2_ptr[0] << 24) | (str2_ptr[1] << 16) | (str2_ptr[2] << 8) | str2_ptr[3]);
		break;
	case 0x15:
		// 0x15 = 21 = SSH_FXP_LINK
		// link操作数据中包含两个字符串，前者是新的链接文件名，后者是现有被链接的文件名
		act = "create link";
		str2_ptr = str1_ptr + str1_len + 4;
		str2_len = (int)((str2_ptr[0] << 24) | (str2_ptr[1] << 16) | (str2_ptr[2] << 8) | str2_ptr[3]);
		break;
	default:
		return;
	}

	int total_len = 5 + str1_len + 4;
	if (str2_len > 0)
		total_len += str2_len + 4;
	if (total_len > pkg_len)
		return;

	char msg[2048] = { 0 };
	if (str2_len == 0) {
		ex_astr str1((char*)((ex_u8*)data + 13), str1_len);
		ex_strformat(msg, 2048, "%d:%s:%s:\r\n", sftp_cmd, act, str1.c_str());
	}
	else {
		ex_astr str1((char*)(str1_ptr + 4), str1_len);
		ex_astr str2((char*)(str2_ptr + 4), str2_len);
		ex_strformat(msg, 2048, "%d:%s:%s:%s\r\n", sftp_cmd, act, str1.c_str(), str2.c_str());
	}

	m_rec.record_command(msg);
}


int SshSession::_on_client_pty_request(ssh_session session, ssh_channel channel, const char *term, int x, int y, int px, int py, void *userdata) {
	SshSession *_this = (SshSession *)userdata;

	if (_this->m_is_sftp) {
		EXLOGE("[ssh] try to request pty on a sftp-session.\n");
		return SSH_ERROR;
	}

	EXLOGD("[ssh] client request terminal: %s, (%d, %d) / (%d, %d)\n", term, x, y, px, py);
	_this->m_rec.record_win_size_startup(x, y);
	TS_SSH_CHANNEL_INFO *info = _this->_get_srv_channel(channel);
	if (NULL == info || NULL == info->channel) {
		EXLOGE("[ssh] when client request pty, not found server channel.\n");
		return SSH_ERROR;
	}

	return ssh_channel_request_pty_size(info->channel, term, x, y);
}

int SshSession::_on_client_shell_request(ssh_session session, ssh_channel channel, void *userdata) {
	SshSession *_this = (SshSession *)userdata;

	if (_this->m_is_sftp) {
		EXLOGE("[ssh] try to request shell on a sftp-session.\n");
// 		char buf[2048] = { 0 };
// 		snprintf(buf, sizeof(buf),
// 			"\r\n\r\n"\
// 			"!! ERROR !!\r\n"\
// 			"Session-ID '%s' has been used for SFTP.\r\n"\
// 			"\r\n", _this->m_sid.c_str()
// 			);
// 		ssh_channel_write(channel, buf, strlen(buf));
// 
		return SSH_ERROR;
	}

	EXLOGD("[ssh] client request shell\n");

	TS_SSH_CHANNEL_INFO *srv_info = _this->_get_srv_channel(channel);
	if (NULL == srv_info || NULL == srv_info->channel) {
		EXLOGE("[ssh] when client request shell, not found server channel.\n");
		return SSH_ERROR;
	}
	srv_info->type = TS_SSH_CHANNEL_TYPE_SHELL;

	TS_SSH_CHANNEL_INFO *cli_info = _this->_get_cli_channel(srv_info->channel);
	if (NULL == cli_info || NULL == cli_info->channel) {
		EXLOGE("[ssh] when client request shell, not found client channel.\n");
		return SSH_ERROR;
	}
	cli_info->type = TS_SSH_CHANNEL_TYPE_SHELL;

	return ssh_channel_request_shell(srv_info->channel);
}

void SshSession::_on_client_channel_close(ssh_session session, ssh_channel channel, void *userdata) {
	EXLOGD("[ssh] on_client_channel_close().\n");

	SshSession *_this = (SshSession *)userdata;
	TS_SSH_CHANNEL_INFO *info = _this->_get_srv_channel(channel);
	if (NULL == info || NULL == info->channel) {
		EXLOGW("[ssh] when close client channel, not found server channel, maybe it already closed.\n");
		return;
	}
	if (!ssh_channel_is_eof(channel))
		ssh_channel_send_eof(channel);
	if (!ssh_channel_is_closed(channel))
		ssh_channel_close(channel);
	//ssh_channel_free(channel);

	if (!ssh_channel_is_eof(info->channel))
		ssh_channel_send_eof(info->channel);
	if (!ssh_channel_is_closed(info->channel))
		ssh_channel_close(info->channel);
	//ssh_channel_free(info->channel);

	{
		ExThreadSmartLock locker(_this->m_lock);

		ts_ssh_channel_map::iterator it = _this->m_channel_cli_srv.find(channel);
		if (it != _this->m_channel_cli_srv.end()) {
			delete it->second;
			_this->m_channel_cli_srv.erase(it);
		}
		else {
			EXLOGW("[ssh] when remove client channel, it not in charge.\n");
		}

		it = _this->m_channel_srv_cli.find(info->channel);
		if (it != _this->m_channel_srv_cli.end()) {
			delete it->second;
			_this->m_channel_srv_cli.erase(it);
		}
		else {
			EXLOGW("[ssh] when remove client channel, not found server channel.\n");
		}
	}
}

int SshSession::_on_client_channel_data(ssh_session session, ssh_channel channel, void *data, unsigned int len, int is_stderr, void *userdata)
{
	//EXLOG_BIN((ex_u8*)data, len, "on_client_channel_data [is_stderr=%d]:", is_stderr);

	SshSession *_this = (SshSession *)userdata;

	// 当前线程正在接收服务端返回的数据，因此我们直接返回，这样紧跟着会重新再发送此数据的
	if (_this->m_recving_from_srv)
		return 0;
	if (_this->m_recving_from_cli)
		return 0;

	TS_SSH_CHANNEL_INFO *info = _this->_get_srv_channel(channel);
	if (NULL == info || NULL == info->channel) {
		EXLOGE("[ssh] when receive client channel data, not found server channel.\n");
		return SSH_ERROR;
	}

	_this->m_recving_from_cli = true;

	if (info->type == TS_SSH_CHANNEL_TYPE_SHELL)
	{
		try
		{
			_this->_process_ssh_command(TS_SSH_DATA_FROM_CLIENT, (ex_u8*)data, len);
		}
		catch (...)
		{
		}
	}
	else
	{
		_this->_process_sftp_command((ex_u8*)data, len);
	}

	int ret = 0;
	if (is_stderr)
		ret = ssh_channel_write_stderr(info->channel, data, len);
	else
		ret = ssh_channel_write(info->channel, data, len);
	if (ret <= 0)
		EXLOGE("[ssh] send to server failed.\n");

	_this->m_recving_from_cli = false;

	return len;
}

int SshSession::_on_client_pty_win_change(ssh_session session, ssh_channel channel, int width, int height, int pxwidth, int pwheight, void *userdata) {
	EXLOGD("[ssh] client pty win size change to: (%d, %d)\n", width, height);
	SshSession *_this = (SshSession *)userdata;
	TS_SSH_CHANNEL_INFO *info = _this->_get_srv_channel(channel);
	if (NULL == info || NULL == info->channel) {
		EXLOGE("[ssh] when client pty win change, not found server channel.\n");
		return SSH_ERROR;
	}

	_this->m_rec.record_win_size_change(width, height);

	return ssh_channel_change_pty_size(info->channel, width, height);
}

int SshSession::_on_client_channel_subsystem_request(ssh_session session, ssh_channel channel, const char *subsystem, void *userdata) {
	EXLOGD("[ssh] on_client_channel_subsystem_request(): %s\n", subsystem);
	SshSession *_this = (SshSession *)userdata;

	// 目前只支持SFTP子系统
	if (strcmp(subsystem, "sftp") != 0) {
		EXLOGE("[ssh] support `sftp` subsystem only, but got `%s`.\n", subsystem);
		_this->m_retcode = SESS_STAT_ERR_UNSUPPORT_PROTOCOL;
		return SSH_ERROR;
	}

	TS_SSH_CHANNEL_INFO *srv_info = _this->_get_srv_channel(channel);
	if (NULL == srv_info || NULL == srv_info->channel) {
		EXLOGE("[ssh] when receive client channel subsystem request, not found server channel.\n");
		return SSH_ERROR;
	}
	srv_info->type = TS_SSH_CHANNEL_TYPE_SFTP;

	TS_SSH_CHANNEL_INFO *cli_info = _this->_get_cli_channel(srv_info->channel);
	if (NULL == cli_info || NULL == cli_info->channel) {
		EXLOGE("[ssh] when client request shell, not found client channel.\n");
		return SSH_ERROR;
	}
	cli_info->type = TS_SSH_CHANNEL_TYPE_SFTP;

	// 一个ssh会话打开了sftp通道，就将连接信息记录下来备用，随后这个session-id再次尝试连接时，我们允许其连接。
	_this->_enter_sftp_mode();

	return ssh_channel_request_subsystem(srv_info->channel, subsystem);
}

void SshSession::_enter_sftp_mode(void) {
	if (!m_is_sftp) {
		m_is_sftp = true;
		m_proxy->add_sftp_session_info(m_sid, m_server_ip, m_server_port, m_user_name, m_user_auth, m_auth_mode);
	}
}

int SshSession::_on_client_channel_exec_request(ssh_session session, ssh_channel channel, const char *command, void *userdata) {
	EXLOGD("[ssh] on_client_channel_exec_request(): %s\n", command);
	return 0;
}

typedef int (*_ssh_channel_write_func)(ssh_channel channel, const void *data, uint32_t len);
int SshSession::_on_server_channel_data(ssh_session session, ssh_channel channel, void *data, unsigned int len, int is_stderr, void *userdata)
{
	//EXLOG_BIN((ex_u8*)data, len, "on_server_channel_data [is_stderr=%d]:", is_stderr);
	SshSession *_this = (SshSession *)userdata;

	if (_this->m_recving_from_cli)
		return 0;
	if (_this->m_recving_from_srv)
		return 0;

	TS_SSH_CHANNEL_INFO *info = _this->_get_cli_channel(channel);
	if (NULL == info || NULL == info->channel) {
		EXLOGE("[ssh] when receive server channel data, not found client channel.\n");
		_this->m_retcode = SESS_STAT_ERR_INTERNAL;
		return SSH_ERROR;
	}

	// TODO: hard code not good... :(
	// 偶尔，某次操作会导致ssh_session->session_state为SSH_SESSION_STATE_ERROR
	// 但是将其强制改为SSH_SESSION_STATE_AUTHENTICATED，后续操作仍然能成功（主要在向客户端发送第一包数据时）
	ex_u8* _t = (ex_u8*)(ssh_channel_get_session(info->channel));
	if (_t[1116] == 9) // SSH_SESSION_STATE_AUTHENTICATED = 8, SSH_SESSION_STATE_ERROR = 9
	{
		EXLOGW(" --- [ssh] hard code to fix client connect session error state.\n");
		_t[1116] = 8;
	}


	_ssh_channel_write_func _write = NULL;
	if (is_stderr)
		_write = ssh_channel_write_stderr;
	else
		_write = ssh_channel_write;

	_this->m_recving_from_srv = true;

	if (info->type == TS_SSH_CHANNEL_TYPE_SHELL && !is_stderr)
	{
		try
		{
			_this->_process_ssh_command(TS_SSH_DATA_FROM_SERVER, (ex_u8*)data, len);
			_this->m_rec.record(TS_RECORD_TYPE_SSH_DATA, (unsigned char *)data, len);
		}
		catch (...)
		{
			EXLOGE("[ssh] process ssh command got exception.\n");
		}
	}

	int ret = 0;

	// 收到第一包服务端返回的数据时，在输出数据之前显示一些自定义的信息
#if 1
	if (!is_stderr && _this->m_is_first_server_data)
	{
		_this->m_is_first_server_data = false;

		if (info->type != TS_SSH_CHANNEL_TYPE_SFTP)
		{
			char buf[256] = { 0 };

			const char *auth_mode = NULL;
			if (_this->m_auth_mode == TS_AUTH_MODE_PASSWORD)
				auth_mode = "password";
			else if (_this->m_auth_mode == TS_AUTH_MODE_PRIVATE_KEY)
				auth_mode = "private-key";
			else
				auth_mode = "unknown";

			snprintf(buf, sizeof(buf),
				"\r\n\r\n"\
				"=============================================\r\n"\
				"Welcome to Teleport-SSH-Server...\r\n"\
				"  - teleport to %s:%d\r\n"\
				"  - authroized by %s\r\n"\
				"=============================================\r\n"\
				"\r\n",
//				\
//				"\033]0;tpssh://%s\007\r\n",
				_this->m_server_ip.c_str(),
				_this->m_server_port, auth_mode
//				,
//				_this->m_server_ip.c_str()
				);

			int buf_len = strlen(buf);
			ex_bin _data;
			_data.resize(buf_len + len);
			memcpy(&_data[0], buf, buf_len);
			memcpy(&_data[buf_len], data, len);

			// 注意，这里虽然可以改变窗口（或者标签页）的标题，但是因为这是服务端发回的第一个包，后面服务端可能还会发类似的包（仅一次）来改变标题
			// 导致窗口标题又被改变，因此理论上应该解析服务端发回的包，如果包含上述格式的，需要替换一次。
			//_write(info->channel, buf, strlen(buf));
			_write(info->channel, &_data[0], _data.size());

			_this->m_recving_from_srv = false;
			return len;
		}
	}
#endif

	ret = _write(info->channel, data, len);
	if (ret == SSH_ERROR) {
		EXLOGE("[ssh] send data(%dB) to client failed (2). [%d][%s][%s]\n", len, ret, ssh_get_error(_this->m_cli_session), ssh_get_error(_this->m_cli_session));
	}

	_this->m_recving_from_srv = false;
	return ret;
}

void SshSession::_on_server_channel_close(ssh_session session, ssh_channel channel, void *userdata) {
	EXLOGD("[ssh] on_server_channel_close().\n");

	SshSession *_this = (SshSession *)userdata;
	TS_SSH_CHANNEL_INFO *info = _this->_get_cli_channel(channel);
	if (NULL == info || NULL == info->channel) {
		EXLOGW("[ssh] when server channel close, not found client channel, maybe it already closed.\n");
		return;
	}

	if (!ssh_channel_is_eof(channel))
		ssh_channel_send_eof(channel);
	if (!ssh_channel_is_closed(channel))
		ssh_channel_close(channel);
	//ssh_channel_free(channel);

	if (!ssh_channel_is_eof(info->channel))
		ssh_channel_send_eof(info->channel);
	if (!ssh_channel_is_closed(info->channel))
		ssh_channel_close(info->channel);
	//ssh_channel_free(info->channel);

	{
		ExThreadSmartLock locker(_this->m_lock);

		ts_ssh_channel_map::iterator it = _this->m_channel_srv_cli.find(channel);
		if (it != _this->m_channel_srv_cli.end()) {
			delete it->second;
			_this->m_channel_srv_cli.erase(it);
		}
		else {
			EXLOGW("[ssh] when remove server channel, it not in charge..\n");
		}

		it = _this->m_channel_cli_srv.find(info->channel);
		if (it != _this->m_channel_cli_srv.end()) {
			delete it->second;
			_this->m_channel_cli_srv.erase(it);
		}
		else {
			EXLOGW("[ssh] when remove server channel, not found client channel.\n");
		}
	}
}
