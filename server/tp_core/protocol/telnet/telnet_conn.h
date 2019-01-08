#ifndef __TELNET_CONN_H__
#define __TELNET_CONN_H__

#include <uv.h>

#include "../../common/ts_membuf.h"
#include "../../common/ts_memstream.h"

//#define LOG_DATA

#define TELNET_CONN_STATE_FREE              0  // not connected yet or closed
#define TELNET_CONN_STATE_CONNECTING        1  // connecting
#define TELNET_CONN_STATE_CONNECTED         2  // connected.
#define TELNET_CONN_STATE_CLOSING           3  // closing.


class TelnetSession;

class TelnetConn {
public:
    TelnetConn(TelnetSession *sess, bool is_server_side);

    ~TelnetConn();

    TelnetSession *session() { return m_session; }

    // just for debug-info
    const char *name() const { return m_name; }

    bool is_server_side() const { return m_is_server; }

    ex_u8 state() const { return m_state; }

    uv_handle_t *handle() { return (uv_handle_t *) &m_handle; }

    uv_tcp_t *tcp_handle() { return &m_handle; }

    uv_stream_t *stream_handle() { return (uv_stream_t *) &m_handle; }

    MemBuffer &data() { return m_buf_data; }

    bool send(MemBuffer &mbuf);

    bool send(const ex_u8 *data, size_t size);

    // connect to real server, for proxy-client-side only.
    void connect(const char *server_ip, ex_u16 server_port = 3389);

    // try to close this connection. return current TELNET_CONN_STATE_XXXX.
    void close();

    bool start_recv();

private:
    static void _on_alloc(uv_handle_t *handle, size_t suggested_size, uv_buf_t *buf);

    static void _on_recv(uv_stream_t *handle, ssize_t nread, const uv_buf_t *buf);

    static void _on_send_done(uv_write_t *req, int status);

    static void _uv_on_connect_timeout(uv_timer_t *timer);

    static void _uv_on_connected(uv_connect_t *req, int status);

    static void _uv_on_reconnect(uv_handle_t *handle);

    static void _uv_on_closed(uv_handle_t *handle);

//	static void _uv_on_timer_connect_timeout_closed(uv_handle_t *handle);
    static void _on_stop_cb(uv_async_t *handle);

    static void _on_stop_handler_closed(uv_handle_t *handle);

    void _do_close();

    bool _raw_send(const ex_u8 *data, size_t size);

private:
    TelnetSession *m_session;
    bool m_is_server;

    // for debug-info.
    const char *m_name;

    uv_tcp_t m_handle;
    uv_timer_t m_timer_connect_timeout;
    bool m_timer_running;  // does m_timer_connect_timeout initialized and started.
    uv_async_t m_stop_handle;  // event for stop whole listener handler.

    ex_u8 m_state; // TELNET_CONN_STATE_XXXX

    // 作为client需要的数据（远程主机信息）
    std::string m_server_ip;
    ex_u16 m_server_port;

    MemBuffer m_buf_data;
};

#endif // __TELNET_CONN_H__
