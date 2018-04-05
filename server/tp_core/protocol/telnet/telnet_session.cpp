#include "telnet_session.h"
#include "telnet_proxy.h"
#include "tpp_env.h"
#include <teleport_const.h>

#define TELNET_IAC 255
#define TELNET_DONT 254
#define TELNET_DO 253
#define TELNET_WONT 252
#define TELNET_WILL 251
#define TELNET_SB 250
#define TELNET_SE 240


TelnetSession::TelnetSession(TelnetProxy *proxy) :
	m_proxy(proxy),
	m_conn_info(NULL)
{
	m_client_type = 0;
	m_state = TP_SESS_STAT_RUNNING;
	m_db_id = 0;
	m_is_relay = false;
	m_is_closed = false;

	m_is_putty_mode = false;
	m_is_putty_eat_username = false;

	m_username_sent = false;
	m_password_sent = false;

	m_conn_server = new TelnetConn(this, false);
	m_conn_client = new TelnetConn(this, true);

	m_status = s_client_connect;

	m_client_addr = "unknown-ip";
}

TelnetSession::~TelnetSession() {
	delete m_conn_client;
	delete m_conn_server;

// 	mbedtls_rsa_free(&m_server_pubkey);
// 	mbedtls_rsa_free(&m_proxy_keypair_dynamic);

	if (NULL != m_conn_info) {
		g_telnet_env.free_connect_info(m_conn_info);
	}

	EXLOGD("[telnet] session destroy.\n");
}

void TelnetSession::save_record() {
	m_rec.save_record();
}

void TelnetSession::_session_error(int err_code) {
	int db_id = 0;
	if (!g_telnet_env.session_begin(m_conn_info, &db_id) || db_id == 0)
	{
		EXLOGE("[telnet] can not write session error to database.\n");
		return;
	}

	g_telnet_env.session_end(m_sid.c_str(), db_id, err_code);
}

bool TelnetSession::_on_session_begin() {
	if (!g_telnet_env.session_begin(m_conn_info, &m_db_id)) {
		EXLOGE("[telnet] can not save to database, session begin failed.\n");
		return false;
	}

	if (!g_telnet_env.session_update(m_db_id, m_conn_info->protocol_sub_type, TP_SESS_STAT_STARTED)) {
		EXLOGE("[telnet] can not update state, session begin failed.\n");
		return false;
	}

	m_rec.begin(g_telnet_env.replay_path.c_str(), L"tp-telnet", m_db_id, m_conn_info);

	return true;
}

bool TelnetSession::_on_session_end()
{
	if (m_db_id > 0)
	{
		// 如果会话过程中没有发生错误，则将其状态改为结束，否则记录下错误值
		if (m_state == TP_SESS_STAT_RUNNING || m_state  == TP_SESS_STAT_STARTED)
			m_state = TP_SESS_STAT_END;

		EXLOGD("[telnet] session end with code: %d\n", m_state);
		g_telnet_env.session_end(m_sid.c_str(), m_db_id, m_state);
	}

	return true;
}

uv_loop_t *TelnetSession::get_loop(void) {
	return m_proxy->get_loop();
}

void TelnetSession::close(int err_code) {
	_do_close(err_code);
}

void TelnetSession::do_next(TelnetConn *conn, sess_state status) {
	if (m_status < s_close)
		m_status = status;

	do_next(conn);
}

void TelnetSession::do_next(TelnetConn *conn) {
	sess_state new_status;
	ASSERT(m_status != s_dead);

	switch (m_status) {
	case s_noop:
		return;

	case s_client_connect:
		new_status = _do_client_connect(conn);
		break;

	case s_negotiation_with_client:
		new_status = _do_negotiation_with_client(conn);
		break;
// 	case s_ssl_handshake_with_client:    // 与客户端端进行SSL握手
// 		new_status = _do_ssl_handshake_with_client();
// 		break;
// 	case s_connect_server:
// 		new_status = _do_connect_server();
// 		break;
	case s_server_connected:
		new_status = _do_server_connected();
		break;
// 	case s_negotiation_with_server:
// 		new_status = _do_negotiation_with_server();
// 		break;
// 	case s_ssl_handshake_with_server:
// 		new_status = _do_ssl_handshake_with_server();
// 		break;
	case s_relay:
		new_status = _do_relay(conn);
		break;

	case s_close:
		new_status = _do_close(m_state);
		break;
	case s_closing:
		new_status = _do_check_closing();
		break;
	case s_all_conn_closed:
		new_status = s_dead;
		break;
	default:
		//UNREACHABLE();
		return;
	}

	m_status = new_status;

	if (m_status == s_dead) {
		EXLOGW("[telnet] try to remove session.\n");
		_on_session_end();
		//m_proxy->session_finished(this);
		m_is_closed = true;
		m_proxy->clean_session();
	}
}

/*
关闭一个session的策略：
1. 两个TelnetConn实例各自关闭自身，当自己关闭完成时，调用session的 on_conn_closed();
2. session->on_conn_closed()被调用时，检查两个conn是否都关闭完成了，如果都关闭了，标记本session为已关闭.
*/

sess_state TelnetSession::_do_close(int state) {
	EXLOGD("[telnet]   _do_close(). m_status=%d\n", m_status);
	if (m_status >= s_close)
		return m_status;

	if (state == TP_SESS_STAT_END) {
		if (!m_is_relay)
			m_state = TP_SESS_STAT_ERR_INTERNAL;
		else
			m_state = state;
	}
	else {
		if (!m_is_relay)
			_session_error(state);
		m_state = state;
	}
	EXLOGV("[telnet] close session.\n");
	EXLOGD("[telnet]   _do_close(), conn_client::state=%d, conn_server:state=%d\n", m_conn_client->state(), m_conn_server->state());

	m_conn_client->close();
	m_conn_server->close();
	m_status = s_closing;
	return m_status;
}

sess_state TelnetSession::_do_check_closing() {
	if (m_conn_client->state() == TELNET_CONN_STATE_FREE && m_conn_server->state() == TELNET_CONN_STATE_FREE)
		return s_all_conn_closed;
	else
		return s_closing;
}

void TelnetSession::on_conn_close() {
	EXLOGD("[telnet]   on_conn_close(), conn_client::state=%d, conn_server:state=%d\n", m_conn_client->state(), m_conn_server->state());
	if (m_conn_client->state() == TELNET_CONN_STATE_FREE && m_conn_server->state() == TELNET_CONN_STATE_FREE) {
		m_status = s_all_conn_closed;
		do_next(m_conn_client);
	}
}

sess_state TelnetSession::_do_client_connect(TelnetConn* conn) {
	// putty会率先发第一个包，SecureCRT会通过脚本发第一个包
	return _do_negotiation_with_client(conn);
}

sess_state TelnetSession::_do_negotiation_with_client(TelnetConn* conn) {
	if (NULL == conn)
		return s_negotiation_with_client;

	if (0 == conn->data().size())
		return s_negotiation_with_client;

	MemBuffer mbuf_msg;
	mbuf_msg.reserve(128);
	MemStream ms_msg(mbuf_msg);

	MemBuffer mbuf_resp;
	mbuf_resp.reserve(conn->data().size());
	MemStream ms_resp(mbuf_resp);

	MemBuffer mbuf_sub;
	mbuf_sub.reserve(128);
	MemStream ms_sub(mbuf_sub);


	MemStream s(conn->data());
	ex_u8 ch = 0;
	ex_u8 ch_cmd = 0;
	for (; s.left() > 0;)
	{
		ch = s.get_u8();
		if (ch == TELNET_IAC)
		{
			if (s.left() < 2)
				return _do_close(TP_SESS_STAT_ERR_BAD_PKG);

			if (mbuf_sub.size() > 0)
			{
				// 已经得到一个sub negotiation，在处理新的数据前，先处理掉旧的
				ms_sub.reset();
			}

			ch_cmd = s.get_u8();
			if (ch_cmd == TELNET_SB)
			{
				// SUB NEGOTIATION，变长数据，以 FF F0 结束
				bool have_SE = false;
				ex_u8 ch_sub = 0;
				for (; s.left() > 0;)
				{
					ch_sub = s.get_u8();
					if (ch_sub == TELNET_IAC)
					{
						if (s.left() > 0)
						{
							if (s.get_u8() == TELNET_SE)
							{
								have_SE = true;
								break;
							}
							else
								return _do_close(TP_SESS_STAT_ERR_BAD_PKG);
						}
					}
					else
					{
						ms_sub.put_u8(ch_sub);
					}
				}

				if (!have_SE)
					return _do_close(TP_SESS_STAT_ERR_BAD_PKG);
			}
			else if (ch_cmd == TELNET_DONT)
			{
				ms_resp.put_u8(TELNET_IAC);
				ms_resp.put_u8(TELNET_WONT);
				ms_resp.put_u8(s.get_u8());
			}
			else if (ch_cmd == TELNET_DO)
			{
				ms_resp.put_u8(TELNET_IAC);
				ms_resp.put_u8(TELNET_WILL);
				ms_resp.put_u8(s.get_u8());
			}
			else if (ch_cmd == TELNET_WONT)
			{
				ms_resp.put_u8(TELNET_IAC);
				ms_resp.put_u8(TELNET_DONT);
				ms_resp.put_u8(s.get_u8());
			}
			else if (ch_cmd == TELNET_WILL)
			{
				ms_resp.put_u8(TELNET_IAC);
				ms_resp.put_u8(TELNET_DO);
				ms_resp.put_u8(s.get_u8());
			}
			else
			{
				s.skip(1);
			}
		}
		else
		{
			ms_msg.put_u8(ch);
		}
	}

	conn->data().empty();

	if (mbuf_resp.size() > 0)
	{
		conn->send(mbuf_resp.data(), mbuf_resp.size());
	}

	if (mbuf_sub.size() == 5)
	{
		if (0 == memcmp(mbuf_sub.data(), "\x1f\x00\x50\x00\x18", 5))
		{
			m_is_putty_mode = true;
			// 			ts_u8 _d[] = {
			// 				0xff, 0xfe, 0x20, 0xff, 0xfd, 0x18, 0xff, 0xfa, 0x27, 0x01, 0xff, 0xf0, 0xff, 0xfa, 0x27, 0x01,
			// 				0x03, 0x53, 0x46, 0x55, 0x54, 0x4c, 0x4e, 0x54, 0x56, 0x45, 0x52, 0x03, 0x53, 0x46, 0x55, 0x54,
			// 				0x4c, 0x4e, 0x54, 0x4d, 0x4f, 0x44, 0x45, 0xff, 0xf0, 0xff, 0xfd, 0x03
			// 			};
			ex_u8 _d[] = {
				0xff, 0xfa, 0x27, 0x01,
				0x03, 0x53, 0x46, 0x55, 0x54, 0x4c, 0x4e, 0x54, 0x56, 0x45, 0x52, 0x03, 0x53, 0x46, 0x55, 0x54,
				0x4c, 0x4e, 0x54, 0x4d, 0x4f, 0x44, 0x45, 0xff, 0xf0
			};
			m_conn_client->send((ex_u8*)_d, sizeof(_d));
		}
	}
	else if (mbuf_sub.size() > 8)
	{
		// 可能含有putty的登录用户名信息（就是SID啦）
		if (0 == memcmp(mbuf_sub.data(), "\x27\x00\x00\x55\x53\x45\x52\x01", 8))	// '..USER.
		{
			mbuf_sub.pop(8);
			for (; mbuf_sub.size() > 0;)
			{
				if (mbuf_sub.data()[mbuf_sub.size() - 1] == 0x0a || mbuf_sub.data()[mbuf_sub.size() - 1] == 0x0d)
					mbuf_sub.size(mbuf_sub.size() - 1);
				else
					break;
			}

			mbuf_sub.append((ex_u8*)"\x00", 1);
			m_sid = (char*)mbuf_sub.data();
		}
	}

	if (mbuf_msg.size() > 0)
	{
		if (0 == memcmp(mbuf_msg.data(), "session:", 8))
		{
			mbuf_msg.pop(8);
			for (; mbuf_msg.size() > 0;)
			{
				if (mbuf_msg.data()[mbuf_msg.size() - 1] == 0x0a || mbuf_msg.data()[mbuf_msg.size() - 1] == 0x0d)
					mbuf_msg.size(mbuf_msg.size() - 1);
				else
					break;
			}

			mbuf_msg.append((ex_u8*)"\x00", 1);
			m_sid = (char*)mbuf_msg.data();
		}
	}

	if (m_sid.length() > 0)
	{
		EXLOGW("[telnet] session-id: %s\n", m_sid.c_str());

		m_conn_info = g_telnet_env.get_connect_info(m_sid.c_str());

		if (NULL == m_conn_info) {
			EXLOGE("[telnet] no such session: %s\n", m_sid.c_str());
			return _do_close(TP_SESS_STAT_ERR_SESSION);
		}
		else {
			m_conn_ip = m_conn_info->conn_ip;
			m_conn_port = m_conn_info->conn_port;
			m_acc_name = m_conn_info->acc_username;
			m_acc_secret = m_conn_info->acc_secret;
			m_username_prompt = m_conn_info->username_prompt;
			m_password_prompt = m_conn_info->password_prompt;

			if (m_conn_info->protocol_type != TP_PROTOCOL_TYPE_TELNET) {
				EXLOGE("[telnet] session '%s' is not for TELNET.\n", m_sid.c_str());
				return _do_close(TP_SESS_STAT_ERR_SESSION);
			}
		}

		// 记录日志，会话开始了
// 		set_info(sess_info);

		// try to connect to real server.
		m_conn_server->connect(m_conn_ip.c_str(), m_conn_port);

		ex_astr szmsg = "Connect to ";
		szmsg += m_conn_ip;
		szmsg += "\r\n";
		m_conn_client->send((ex_u8*)szmsg.c_str(), szmsg.length());

		return s_noop;
	}

	return s_negotiation_with_client;
}

sess_state TelnetSession::_do_server_connected() {
	m_conn_client->data().empty();
	m_conn_server->data().empty();

	m_status = s_relay;

	if (m_is_putty_mode)
	{
		ex_u8 _d[] = "\xff\xfb\x1f\xff\xfb\x20\xff\xfb\x18\xff\xfb\x27\xff\xfd\x01\xff\xfb\x03\xff\xfd\x03";
		m_conn_server->send(_d, sizeof(_d) - 1);
	}

	EXLOGW("[telnet] enter relay mode.\n");

	return s_relay;
}

sess_state TelnetSession::_do_relay(TelnetConn *conn) {
	TelnetSession* _this = conn->session();
	bool is_processed = false;

	if (conn->is_server_side())
	{
		// 收到了客户端发来的数据
// 		if (!_this->m_is_changle_title_sent)
// 		{
// 			_this->m_is_changle_title_sent = true;
// 			ts_astr msg = "\033]0;TP#telnet://";
// 			msg += m_server_ip;
// 			msg += "\007\x0d\x0a";
// 			m_conn_client->send((ts_u8*)msg.c_str(), msg.length());
// 		}

		if (_this->m_is_putty_mode && !_this->m_is_putty_eat_username)
		{
			if (_this->_eat_username(m_conn_client, m_conn_server))
			{
				_this->m_is_putty_eat_username = true;
				_this->m_username_sent = true;
				is_processed = true;
			}
		}

		if (is_processed)
		{
			m_conn_client->data().empty();
			return s_relay;
		}

		m_conn_server->send(m_conn_client->data().data(), m_conn_client->data().size());
		m_conn_client->data().empty();
	}
	else
	{
		// 收到了服务端返回的数据

		if (!_this->m_username_sent && _this->m_acc_name.length() > 0)
		{
			if (_this->_parse_find_and_send(m_conn_server, m_conn_client, _this->m_username_prompt.c_str(), _this->m_acc_name.c_str()))
			{
				_this->m_username_sent = true;
				is_processed = true;
			}
		}
		if (!_this->m_password_sent && _this->m_password_prompt.length() > 0)
		{
			if (_this->_parse_find_and_send(m_conn_server, m_conn_client, _this->m_password_prompt.c_str(), _this->m_acc_secret.c_str()))
			{
				_this->m_password_sent = true;
				is_processed = true;
			}
		}

		if (is_processed)
		{
			m_conn_server->data().empty();
			return s_relay;
		}


		// 替换会导致客户端窗口标题改变的数据
		//ts_u8* data = m_conn_server->data().data();
		//size_t len = m_conn_server->data().size();
// 		if (len > 5)
// 		{
// 			const ts_u8* _begin = memmem(data, len, (const ts_u8*)"\033]0;", 4);
// 
// 			if (NULL != _begin)
// 			{
// 				size_t len_before = _begin - data;
// 
// 				const ts_u8* _end = memmem(_begin + 4, len - len_before, (const ts_u8*)"\007", 1);
// 				if (NULL != _end)
// 				{
// 					_end++;
// 
// 					// 这个包中含有改变标题的数据，将标题换为我们想要的
// 					size_t len_end = len - (_end - data);
// 					MemBuffer mbuf;
// 
// 					if (len_before > 0)
// 						mbuf.append(data, len_before);
// 
// 					mbuf.append((ts_u8*)"\033]0;TP#ssh://", 13);
// 					mbuf.append((ts_u8*)_this->m_server_ip.c_str(), _this->m_server_ip.length());
// 					mbuf.append((ts_u8*)"\007", 1);
// 
// 					if (len_end > 0)
// 						mbuf.append(_end, len_end);
// 
// 					m_conn_client->send(mbuf.data(), mbuf.size());
// 				}
// 				else
// 				{
// 					m_conn_client->send(m_conn_server->data().data(), m_conn_server->data().size());
// 				}
// 			}
// 			else
// 			{
// 				m_conn_client->send(m_conn_server->data().data(), m_conn_server->data().size());
// 			}
// 		}
// 		else
		{
			m_conn_client->send(m_conn_server->data().data(), m_conn_server->data().size());
		}

		m_conn_server->data().empty();
	}

	return s_relay;
}

bool TelnetSession::_parse_find_and_send(TelnetConn* conn_recv, TelnetConn* conn_remote, const char* find, const char* send)
{
	size_t find_len = strlen(find);
	size_t send_len = strlen(send);
	if (0 == find_len || 0 == send_len)
		return false;

	MemBuffer mbuf_msg;
	mbuf_msg.reserve(128);
	MemStream ms_msg(mbuf_msg);

	MemStream s(conn_recv->data());
	ex_u8 ch = 0;
	ex_u8 ch_cmd = 0;
	for (; s.left() > 0;)
	{
		ch = s.get_u8();
		if (ch == TELNET_IAC)
		{
			if (s.left() < 2)
				return false;

			ch_cmd = s.get_u8();
			if (ch_cmd == TELNET_SB)
			{
				// SUB NEGOTIATION，变长数据，以 FF F0 结束
				bool have_SE = false;
				ex_u8 ch_sub = 0;
				for (; s.left() > 0;)
				{
					ch_sub = s.get_u8();
					if (ch_sub == TELNET_IAC)
					{
						if (s.left() > 0)
						{
							if (s.get_u8() == TELNET_SE)
							{
								have_SE = true;
								break;
							}
							else
								return false;
						}
					}
				}

				if (!have_SE)
					return false;
			}
			else
			{
				s.skip(1);
			}
		}
		else
		{
			ms_msg.put_u8(ch);
		}
	}

	if (mbuf_msg.size() < find_len)
		return false;

	int find_range = mbuf_msg.size() - find_len;
	for (int i = 0; i < find_range; ++i)
	{
		if (0 == memcmp(mbuf_msg.data() + i, find, find_len))
		{
			conn_remote->send(conn_recv->data().data(), conn_recv->data().size());
			conn_recv->data().empty();

			mbuf_msg.empty();
			mbuf_msg.append((ex_u8*)send, send_len);
			mbuf_msg.append((ex_u8*)"\x0d\x0a", 2);
			conn_recv->send(mbuf_msg.data(), mbuf_msg.size());
			return true;
		}
	}

	return false;
}

bool TelnetSession::_eat_username(TelnetConn* conn_recv, TelnetConn* conn_remote)
{
	bool replaced = false;

	MemBuffer mbuf_msg;
	mbuf_msg.reserve(128);
	MemStream ms_msg(mbuf_msg);

	MemStream s(conn_recv->data());
	ex_u8 ch = 0;
	ex_u8 ch_cmd = 0;
	for (; s.left() > 0;)
	{
		ch = s.get_u8();
		if (ch == TELNET_IAC)
		{
			if (s.left() < 2)
				return false;

			ch_cmd = s.get_u8();
			if (ch_cmd == TELNET_SB)
			{
				size_t _begin = s.offset();
				size_t _end = 0;


				// SUB NEGOTIATION，变长数据，以 FF F0 结束
				bool have_SE = false;
				ex_u8 ch_sub = 0;
				for (; s.left() > 0;)
				{
					_end = s.offset();
					ch_sub = s.get_u8();
					if (ch_sub == TELNET_IAC)
					{
						if (s.left() > 0)
						{
							if (s.get_u8() == TELNET_SE)
							{
								have_SE = true;
								break;
							}
							else
								return false;
						}
					}
				}

				if (!have_SE)
					return false;

				size_t len = _end - _begin;
				if (len <= 8 || 0 != memcmp("\x27\x00\x00\x55\x53\x45\x52\x01", conn_recv->data().data() + _begin, 8))
				{
					ms_msg.put_u8(TELNET_IAC);
					ms_msg.put_u8(TELNET_SB);
					ms_msg.put_bin(conn_recv->data().data() + _begin, len);
					ms_msg.put_u8(TELNET_IAC);
					ms_msg.put_u8(TELNET_SE);
					continue;
				}

				// 到这里就找到了客户端发来的用户名，我们将其抛弃掉，发给服务端的是一个无用户名的包，这样
				// 服务端就会提示输入用户名（login:），后续检测到服务端的提示就会发送用户名了。

				ms_msg.put_u8(TELNET_IAC);
				ms_msg.put_u8(TELNET_SB);
				ms_msg.put_bin((ex_u8*)"\x27\x00\x00\x55\x53\x45\x52\x01", 8);

				ms_msg.put_bin((ex_u8*)m_acc_name.c_str(), m_acc_name.length());

				ms_msg.put_u8(TELNET_IAC);
				ms_msg.put_u8(TELNET_SE);

				replaced = true;
			}
			else
			{
				ms_msg.put_u8(ch);
				ms_msg.put_u8(ch_cmd);
				ms_msg.put_u8(s.get_u8());
			}
		}
		else
		{
			ms_msg.put_u8(ch);
		}
	}

	if (replaced)
	{
		conn_remote->send(mbuf_msg.data(), mbuf_msg.size());
		return true;
	}

	return false;
}

