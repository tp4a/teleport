#include "telnet_conn.h"
#include "telnet_session.h"
#include "../../common/ts_memstream.h"
#include "../../common/ts_const.h"
#include <teleport_const.h>

ex_astr _uv_str_error(int retcode) {
    ex_astr err;
    err = uv_err_name(retcode);
    err += ":";
    err += uv_strerror(retcode);
    return err;
}

TelnetConn::TelnetConn(TelnetSession *sess, bool is_server_side) : m_session(sess), m_is_server(is_server_side) {
    if (is_server_side) {
        m_name = "cli<->tp";
        m_state = TELNET_CONN_STATE_CONNECTED;
    } else {
        m_name = "tp<->srv";
        m_state = TELNET_CONN_STATE_FREE;
    }

    m_timer_running = false;

    uv_tcp_init(sess->get_loop(), &m_handle);
    m_handle.data = this;
    uv_async_init(sess->get_loop(), &m_stop_handle, _on_stop_cb);
    m_stop_handle.data = this;
}

TelnetConn::~TelnetConn() {
}

bool TelnetConn::start_recv() {
    int err = uv_read_start((uv_stream_t *) &m_handle, _on_alloc, _on_recv);
    if (err != 0) {
        EXLOGE("[telnet] [%s] can not start to read.\n", m_name);
        m_session->close(TP_SESS_STAT_ERR_IO);
        return false;
    }

    return true;
}

void TelnetConn::close() {
    if (m_state == TELNET_CONN_STATE_FREE || m_state == TELNET_CONN_STATE_CLOSING)
        return;
    uv_async_send(&m_stop_handle);
}

void TelnetConn::_do_close() {
    if (m_state == TELNET_CONN_STATE_FREE || m_state == TELNET_CONN_STATE_CLOSING)
        return;

    if (m_timer_running) {
        m_timer_running = false;
        uv_timer_stop(&m_timer_connect_timeout);

        EXLOGW("[telnet] [%s] try to close while it connecting.\n", m_name);
        m_state = TELNET_CONN_STATE_CLOSING;
        uv_close(handle(), NULL);

        return;
    }

    uv_read_stop((uv_stream_t *) &m_handle);
    uv_close(handle(), _uv_on_closed);
}

//static
void TelnetConn::_on_stop_cb(uv_async_t *handle) {
    TelnetConn *_this = (TelnetConn *) handle->data;
    uv_close((uv_handle_t *) &_this->m_stop_handle, _this->_on_stop_handler_closed);
}

//static
void TelnetConn::_on_stop_handler_closed(uv_handle_t *handle) {
    TelnetConn *_this = (TelnetConn *) handle->data;
    _this->_do_close();
}

void TelnetConn::_uv_on_closed(uv_handle_t *handle) {
    TelnetConn *_this = (TelnetConn *) handle->data;
    _this->m_state = TELNET_CONN_STATE_FREE;
    _this->m_session->on_conn_close();
}

void TelnetConn::_on_alloc(uv_handle_t *handle, size_t suggested_size, uv_buf_t *buf) {
//    TelnetConn *_this = (TelnetConn *) handle->data;
    buf->base = (char *) calloc(1, suggested_size);
    buf->len = suggested_size;
}

void TelnetConn::_on_recv(uv_stream_t *handle, ssize_t nread, const uv_buf_t *buf) {
    TelnetConn *_this = (TelnetConn *) handle->data;

    if (nread == 0) {
        free(buf->base);
        return;
    } else if (nread < 0) {
        free(buf->base);

        if (nread == UV_EOF)
            EXLOGD("[telnet] [%s] [recv] disconnected.\n", _this->m_name);
        else if (nread == UV_ECONNRESET)
            EXLOGD("[telnet] [%s] [recv] connection reset by peer.\n", _this->m_name);
        else
            EXLOGD("[telnet] [%s] [recv] %s.\n", _this->m_name, _uv_str_error(nread).c_str());


//         if (nread == -4077)
//             EXLOGD("[telnet] [%s] [recv] disconnected.\n", _this->m_name);
//         else if (nread == -104)
//             EXLOGD("[telnet] [%s] [recv] connection reset by peer.\n", _this->m_name);
//         else
//             EXLOGD("[telnet] [%s] [recv] nread=%d.\n", _this->m_name, nread);

        _this->m_session->close(TP_SESS_STAT_END);
        return;
    } else {
// #ifdef LOG_DATA
// 		if(!_this->m_session->is_relay())
//			EXLOG_BIN((ex_u8*)buf->base, nread, "[telnet] [%s] RECV %d.", _this->m_name, nread);
// #endif
    }

    _this->m_buf_data.append((ex_u8 *) buf->base, nread);
    free(buf->base);

    _this->m_session->do_next(_this);
}

bool TelnetConn::send(MemBuffer &mbuf) {
    return _raw_send(mbuf.data(), mbuf.size());
}

bool TelnetConn::send(const ex_u8 *data, size_t size) {
    return _raw_send(data, size);
}

bool TelnetConn::_raw_send(const ex_u8 *data, size_t size) {
// #ifdef LOG_DATA
// 	if (!m_session->is_relay())
//		EXLOG_BIN(data, size, "[telnet] [%s] SEND %dB.", m_name, size);
// #endif

    uv_write_t *w = (uv_write_t *) calloc(1, sizeof(uv_write_t));

    ex_u8 *_data = (ex_u8 *) calloc(1, size);
    if (NULL == _data) {
        free(w);
        EXLOGE("[telnet] alloc buffer %dB failed.\n", size);
        return false;
    }
    memcpy(_data, data, size);

    uv_buf_t *_buf = (uv_buf_t *) calloc(1, sizeof(uv_buf_t));
    _buf->base = (char *) _data;
    _buf->len = size;

    w->data = _buf;
    if (0 == uv_write(w, (uv_stream_t *) &m_handle, _buf, 1, _on_send_done))
        return true;
    else {
        EXLOGE("[telnet] [%s] raw_send() failed.\n", m_name);
        return false;
    }
}

void TelnetConn::_on_send_done(uv_write_t *req, int status) {
    uv_buf_t *_buf = (uv_buf_t *) req->data;
    free(_buf->base);
    free(_buf);
    free(req);

    if (status == UV_ECANCELED) {
        EXLOGE("[telnet] _on_send_done() got UV_ECANCELED.\n");
        return;
    }
}

void TelnetConn::connect(const char *server_ip, ex_u16 server_port) {
    m_server_ip = server_ip;
    m_server_port = server_port;

    if (m_state == TELNET_CONN_STATE_CONNECTED) {
        // 当前已经连接上了服务器了，断开重连
        EXLOGV("[telnet] [%s] [%s] try to disconnect from real TELNET server %s:%d and reconnect.\n", m_name,
               m_session->client_addr(), server_ip, server_port);
        m_state = TELNET_CONN_STATE_CLOSING;
        uv_close((uv_handle_t *) &m_handle, _uv_on_reconnect);
        return;
    } else {
        EXLOGV("[telnet] [%s] [%s] try to connect to real TELNET server %s:%d\n", m_name, m_session->client_addr(),
               server_ip, server_port);
    }

    struct sockaddr_in addr;
    uv_ip4_addr(server_ip, server_port, &addr);

    uv_connect_t *conn_req = (uv_connect_t *) calloc(1, sizeof(uv_connect_t));
    conn_req->data = this;

    // 设置一个超时回调，如果超时发生时连接尚未完成，就报错
    uv_timer_init(m_session->get_loop(), &m_timer_connect_timeout);
    m_timer_connect_timeout.data = this;

#ifdef EX_DEBUG
    uv_timer_start(&m_timer_connect_timeout, _uv_on_connect_timeout, 5000, 0);
#else
    uv_timer_start(&m_timer_connect_timeout, _uv_on_connect_timeout, 10000, 0);
#endif

    m_timer_running = true;

    m_state = TELNET_CONN_STATE_CONNECTING;
    int err = 0;
    if ((err = uv_tcp_connect(conn_req, &m_handle, (const struct sockaddr *) &addr, _uv_on_connected)) != 0) {
        free(conn_req);
        EXLOGE("[telnet] [%s] can not connect to server: %s\n", m_name, uv_strerror(err));

        m_timer_running = false;
        uv_timer_stop(&m_timer_connect_timeout);
        uv_close((uv_handle_t *) &m_timer_connect_timeout, NULL);

        m_state = TELNET_CONN_STATE_FREE;
        m_session->close(TP_SESS_STAT_ERR_CONNECT);
    }
}

void TelnetConn::_uv_on_connect_timeout(uv_timer_t *timer) {
    TelnetConn *_this = (TelnetConn *) timer->data;

    if (_this->m_timer_running) {
        _this->m_timer_running = false;
        uv_timer_stop(&_this->m_timer_connect_timeout);
        uv_close((uv_handle_t *) &_this->m_timer_connect_timeout, NULL);
    }

    // 如果在连接成功之前就超时了，则关闭连接
    EXLOGE("[telnet] [%s] timeout when connect to real TELNET server.\n", _this->m_name);
    _this->m_state = TELNET_CONN_STATE_CLOSING;
    uv_close(_this->handle(), _uv_on_closed);
}

void TelnetConn::_uv_on_reconnect(uv_handle_t *handle) {
    TelnetConn *_this = (TelnetConn *) handle->data;
    _this->m_state = TELNET_CONN_STATE_FREE;

    uv_tcp_init(_this->m_session->get_loop(), &_this->m_handle);
    _this->m_handle.data = _this;

    _this->connect(_this->m_server_ip.c_str(), _this->m_server_port);
}

void TelnetConn::_uv_on_connected(uv_connect_t *req, int status) {
    TelnetConn *_this = (TelnetConn *) req->data;
    free(req);

    if (_this->m_timer_running) {
        _this->m_timer_running = false;
        uv_timer_stop(&_this->m_timer_connect_timeout);
        uv_close((uv_handle_t *) &_this->m_timer_connect_timeout, NULL);
    }

    if (status != 0) {
        EXLOGE("[telnet] [%s] cannot connect to real TELNET server. %s\n", _this->m_name, uv_strerror(status));
        _this->m_state = TELNET_CONN_STATE_FREE;
        _this->m_session->close(TP_SESS_STAT_ERR_CONNECT);
        return;
    }

    EXLOGW("[telnet] [%s] real TELNET server connected.\n", _this->m_session->client_addr());
    _this->m_state = TELNET_CONN_STATE_CONNECTED;

    if (!_this->start_recv()) {
        _this->m_session->close(TP_SESS_STAT_ERR_IO);
        return;
    }

    _this->m_session->do_next(_this, s_server_connected);
}

//static
//void TelnetConn::_uv_on_timer_connect_timeout_closed(uv_handle_t *handle) {
//}
