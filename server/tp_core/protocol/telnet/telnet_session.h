#ifndef __TELNET_SESSION_H__
#define __TELNET_SESSION_H__

#include <ex.h>

#include "telnet_recorder.h"
#include "telnet_conn.h"

enum sess_state {
	s_noop,	// 什么都不做，等特定状态满足

	s_client_connect,	// 客户端连接
	s_negotiation_with_client,	// 与客户端进行握手，直到得到客户端发来的登录用户名（其实是SessionID）

	s_server_connected,	// 成功连接上服务器了

	s_relay,	// 正常转发数据

	s_close,	// 关闭会话
	s_closing,			// 正在关闭双方连接
	s_all_conn_closed,	// 两端均已关闭

	s_dead	// 可以销毁此会话了
};

class TelnetProxy;

class TelnetSession
{
public:
	TelnetSession(TelnetProxy* proxy);
	virtual ~TelnetSession();

	TelnetProxy* get_proxy() { return m_proxy; }

	TelnetConn* client() { return m_conn_client; }
	TelnetConn* server() { return m_conn_server; }
	uv_loop_t* get_loop();

	void set_state(int state) { m_state = state; }
	void close(int err_code);
	void on_conn_close();

	void do_next(TelnetConn* conn);
	void do_next(TelnetConn* conn, sess_state status);

	// save record cache into file. be called per 5 seconds.
	void save_record();
	void record(ex_u8 type, const ex_u8* data, size_t size) {
		m_rec.record(type, data, size);
	}
	// 
	void check_noop_timeout(ex_u32 t_now, ex_u32 timeout);
	const ex_astr& sid() { return m_sid; }

	void client_addr(const char* addr) { m_client_addr = addr; }
	const char* client_addr() const { return m_client_addr.c_str(); }

	bool is_relay() { return m_is_relay; }
	bool is_closed() { return m_is_closed; }

protected:
	// 继承自 TppSessionBase
	bool _on_session_begin();
	bool _on_session_end();
	void _session_error(int err_code);

private:
	sess_state _do_client_connect(TelnetConn* conn);
	sess_state _do_negotiation_with_client(TelnetConn* conn);
	sess_state _do_connect_server();
	sess_state _do_server_connected();
	sess_state _do_relay(TelnetConn* conn);
	sess_state _do_close(int err_code);
	sess_state _do_check_closing();

	bool _parse_find_and_send(TelnetConn* conn_recv, TelnetConn* conn_remote, const char* find, const char* send);
	bool _putty_replace_username(TelnetConn* conn_recv, TelnetConn* conn_remote);
	bool _parse_win_size(TelnetConn* conn);

private:
	int m_state;

	TPP_CONNECT_INFO* m_conn_info;
	bool m_startup_win_size_recorded;
	int m_db_id;

	bool m_first_client_pkg;
	bool m_is_relay;	// 是否进入relay模式了（只有进入relay模式才会有录像存在）
	bool m_is_closed;
	ex_u32 m_last_access_timestamp;

	TppTelnetRec m_rec;
	int m_win_width;
	int m_win_height;

	TelnetProxy* m_proxy;
	TelnetConn* m_conn_client; // 与真正客户端通讯的连接（自身作为服务端）
	TelnetConn* m_conn_server; // 与真正服务端通讯的连接（自身作为客户端）

	ExThreadLock m_lock;

	ex_astr m_sid;
	ex_astr m_conn_ip;
	ex_u16 m_conn_port;
	ex_astr m_acc_name;
	ex_astr m_acc_secret;
	ex_astr m_username_prompt;
	ex_astr m_password_prompt;

	sess_state m_status;
	ex_astr m_client_addr;

	bool m_is_putty_mode;
	//bool m_is_putty_eat_username;

	bool m_username_sent;
	bool m_password_sent;
};

#endif // __TELNET_SESSION_H__
