#ifndef __TELNET_PROXY_H__
#define __TELNET_PROXY_H__

#include <uv.h>
#include <ex.h>

#include "telnet_session.h"

typedef std::map<TelnetSession *, unsigned char> ts_telnet_sessions;

class TelnetProxy : public ExThreadBase {
public:
    TelnetProxy();

    ~TelnetProxy();

    bool init();

    void timer();

    void set_cfg(ex_u32 noop_timeout);

    void kill_sessions(const ex_astrs &sessions);

    uv_loop_t *get_loop() { return &m_loop; }

    void clean_session();

protected:
    void _thread_loop();

    void _on_stop();

    void _close_all_sessions();

    void _close_clean_session_handle();

private:
    static void _on_client_connect(uv_stream_t *server, int status);

    static void _on_listener_closed(uv_handle_t *handle);

    static void _on_clean_session_cb(uv_async_t *handle);

//    static void _on_clean_session_handle_closed(uv_handle_t *handle);

    static void _on_stop_cb(uv_async_t *handle);

    static void _on_stop_handle_closed(uv_handle_t *handle);

    bool _on_accept(uv_stream_t *server);

private:
    int m_timer_counter;
    ex_u32 m_noop_timeout_sec;

    uv_loop_t m_loop;
    uv_tcp_t m_listener_handle;
    uv_async_t m_clean_session_handle;
    uv_async_t m_stop_handle;  // event for stop whole listener handler.

    ExThreadLock m_lock;

    ex_astr m_host_ip;
    int m_host_port;

    ts_telnet_sessions m_sessions;
};

extern TelnetProxy g_telnet_proxy;

#endif // __TELNET_PROXY_H__
