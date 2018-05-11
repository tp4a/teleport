#include "telnet_proxy.h"
#include "tpp_env.h"
#include <teleport_const.h>

TelnetProxy g_telnet_proxy;

TelnetProxy::TelnetProxy() : ExThreadBase("telnet-proxy-thread")
{
	memset(&m_loop, 0, sizeof(uv_loop_t));
	m_timer_counter = 0;
	m_noop_timeout_sec = 900;
}

TelnetProxy::~TelnetProxy()
{
	if (m_sessions.size() > 0)
		EXLOGE("[telnet] not all session stopped.\n");
}

bool TelnetProxy::init()
{
	if (0 != uv_loop_init(&m_loop))
		return false;

	if (0 != uv_async_init(&m_loop, &m_clean_session_handle, _on_clean_session_cb))
		return false;
	m_clean_session_handle.data = this;

	m_host_ip = g_telnet_env.bind_ip;
	m_host_port = g_telnet_env.bind_port;

	if (0 != uv_tcp_init(&m_loop, &m_handle))
		return false;
	m_handle.data = this;

	return true;
}

void TelnetProxy::timer() {
	// timer() will be called per one second, and I will do my job per 5 seconds.
	m_timer_counter++;
	if (m_timer_counter < 5)
		return;

	m_timer_counter = 0;

	ExThreadSmartLock locker(m_lock);
	ex_u32 t_now = (ex_u32)time(NULL);
	ts_telnet_sessions::iterator it = m_sessions.begin();
	for (; it != m_sessions.end(); ++it)
	{
		it->first->save_record();
		if(0 != m_noop_timeout_sec)
			it->first->check_noop_timeout(t_now, m_noop_timeout_sec);
	}
}

void TelnetProxy::set_cfg(ex_u32 noop_timeout) {
	m_noop_timeout_sec = noop_timeout;
}

void TelnetProxy::kill_sessions(const ex_astrs& sessions) {
	ExThreadSmartLock locker(m_lock);
	ts_telnet_sessions::iterator it = m_sessions.begin();
	for (; it != m_sessions.end(); ++it) {
		for (size_t i = 0; i < sessions.size(); ++i) {
			if (it->first->sid() == sessions[i]) {
				EXLOGW("[telnet] try to kill %s\n", sessions[i].c_str());
				it->first->check_noop_timeout(0, 0); // 立即结束
			}
		}
	}
}

void TelnetProxy::_thread_loop(void)
{
	struct sockaddr_in addr;
	if (0 != uv_ip4_addr(m_host_ip.c_str(), m_host_port, &addr)) {
		EXLOGE("[telnet] invalid ip/port for TELNET listener.\n");
		return;
	}

	if (0 != uv_tcp_bind(&m_handle, (const struct sockaddr*) &addr, 0)) {
		EXLOGE("[telnet] can not bind %s:%d.\n", m_host_ip.c_str(), m_host_port);
		return;
	}

	// 开始监听，有客户端连接到来时，会回调 _on_client_connect()
	if (0 != uv_listen((uv_stream_t*)&m_handle, 8, _on_client_connect)) {
		EXLOGE("[telnet] can not listen on %s:%d.\n", m_host_ip.c_str(), m_host_port);
		return;
	}

	EXLOGI("[telnet] TeleportServer-TELNET ready on %s:%d\n", m_host_ip.c_str(), m_host_port);

	int err = 0;
	if ((err = uv_run(&m_loop, UV_RUN_DEFAULT)) != 0) {
		EXLOGE("[telnet] main-loop end. %s\n", uv_strerror(err));
	}

	// 注意，如果在 uv_loop_close() 内部崩溃，可能某个uv的handle未关闭。
	uv_loop_close(&m_loop);

	EXLOGV("[telnet] main-loop end.\n");
}

void TelnetProxy::_set_stop_flag(void) {
	m_stop_flag = true;

	if (m_is_running) {
		uv_close((uv_handle_t*)&m_handle, _on_listener_closed);
	}
}

// static
void TelnetProxy::_on_listener_closed(uv_handle_t* handle)
{
	TelnetProxy* _this = (TelnetProxy*)handle->data;
	EXLOGV("[telnet] listener close.\n");

	_this->_close_all_sessions();
}

void TelnetProxy::clean_session() {
	uv_async_send(&m_clean_session_handle);
}

void TelnetProxy::_close_all_sessions(void)
{
	ExThreadSmartLock locker(m_lock);

	if (m_sessions.size() == 0) {
		_close_clean_session_handle();
		return;
	}

	ts_telnet_sessions::iterator it = m_sessions.begin();
	for (; it != m_sessions.end(); ++it)
	{
		it->first->close(TP_SESS_STAT_ERR_RESET);
	}
}

// static
void TelnetProxy::_on_clean_session_cb(uv_async_t* handle)
{
	TelnetProxy* _this = (TelnetProxy*)handle->data;

	// check closed session
	ExThreadSmartLock locker(_this->m_lock);

	ts_telnet_sessions::iterator it = _this->m_sessions.begin();
	for (; it != _this->m_sessions.end(); )
	{
		if (it->first->is_closed()) {
			delete it->first;
			_this->m_sessions.erase(it++);
			EXLOGD("[telnet]   - removed one session.\n");
		}
		else {
			it++;
		}
	}

	if (_this->m_stop_flag && _this->m_sessions.size() == 0) {
		_this->_close_clean_session_handle();
	}
}

//static
void TelnetProxy::_on_clean_session_handle_closed(uv_handle_t *handle) {
}


// static
void TelnetProxy::_on_client_connect(uv_stream_t* server, int status)
{
	if (0 != status)
		return;

	TelnetProxy* _this = (TelnetProxy*)server->data;
	_this->_on_accept(server);
}

bool TelnetProxy::_on_accept(uv_stream_t* server)
{
	TelnetSession* sess = new TelnetSession(this);

	if (0 != uv_accept(server, sess->client()->stream_handle()))
	{
		EXLOGE("[telnet] socket accept failed.\n");
		delete sess;
		return false;
	}

	if (m_stop_flag)
	{
		delete sess;
		return false;
	}

	// 获取客户端IP地址和端口号
	struct sockaddr sock_client;
	int namelen = sizeof(sock_client);
	if (0 == uv_tcp_getpeername(sess->client()->tcp_handle(), &sock_client, &namelen))
	{
		sockaddr_in* addrin = (sockaddr_in*)&sock_client;
		char ip[17] = { 0 };
		if (0 == uv_ip4_name(addrin, ip, sizeof(ip)))
		{
			char client_addr[64] = { 0 };
			snprintf(client_addr, 64, "%s:%d", ip, addrin->sin_port);
			sess->client_addr(client_addr);
		}
	}

	EXLOGV("\n===================  NEW TELNET CLIENT [%s]  ============\n", sess->client_addr());

	{
		ExThreadSmartLock locker(m_lock);
		m_sessions.insert(std::make_pair(sess, 0));
	}

	sess->client()->start_recv();

	return true;
}

void TelnetProxy::_close_clean_session_handle() {
	uv_close((uv_handle_t*)&m_clean_session_handle, _on_clean_session_handle_closed);
}
