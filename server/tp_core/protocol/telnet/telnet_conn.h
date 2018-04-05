#ifndef __TELNET_CONN_H__
#define __TELNET_CONN_H__

#include <uv.h>

// typedef time_t mbedtls_time_t;

// #include <mbedtls/arc4.h>
// #include <mbedtls/ssl.h>
// #include <mbedtls/entropy.h>
// #include <mbedtls/ctr_drbg.h>

// #include "telnet_package.h"
#include "../../common/ts_membuf.h"
#include "../../common/ts_memstream.h"
// #include "telnet_bulk.h"



//#define LOG_DATA

#define TELNET_CONN_STATE_FREE				0  // not connected yet or closed
#define TELNET_CONN_STATE_CONNECTING		1  // connecting
#define TELNET_CONN_STATE_CONNECTED			2  // connected.
#define TELNET_CONN_STATE_CLOSING			3  // closing.


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
//     bool send(TelnetPkgBase &pkg);
    bool send(const ex_u8 *data, size_t size);
    bool raw_send(const ex_u8 *data, size_t size);

	// connect to real server, for proxy-client-side only.
    void connect(const char *server_ip, ex_u16 server_port = 3389);
	// try to close this connection. return current RDP_CONN_STATE_XXXX.
	void close();
	bool start_recv();


    // 密钥相关
//     void gen_session_keys(ex_u8 *client_random, ex_u8 *server_random);
//     void decrypt(ex_u8 *buf_data, size_t buf_size, bool update_counter);
//     void encrypt(ex_u8 *buf_data, size_t buf_size, bool update_counter);
//     ex_u32 get_dec_counter() { return m_decrypt_total; }
//     ex_u32 get_enc_counter() { return m_encrypt_total; }
//     void calc_mac(ex_u8 *buf_data, size_t buf_size, ex_u8 *signature, bool with_counter = false, ex_u32 counter = 0);

    // RDP-SSL 相关
//     bool ssl_prepare();

//     mbedtls_ssl_context *ssl_context() { return &m_ssl_ctx; }

// 	bool ssl_is_in_handshake() { return m_ssl_ctx.state != MBEDTLS_SSL_HANDSHAKE_OVER; }
//     int ssl_do_handshake();
//     int ssl_do_read();

//     bool ssl_send(MemBuffer &mbuf);
//     bool ssl_send(TelnetPkgBase &pkg);
//     bool ssl_send(const ex_u8 *data, size_t size);

//     MemBuffer &ssl_data() { return m_ssl_mbuf; }

//     static int on_ssl_read(void *ctx, ex_u8 *buf, size_t len);
//     static int on_ssl_write(void *ctx, const ex_u8 *buf, size_t len);

	//RDP_BULK* get_bulk() { return m_bulk; }

private:
    static void _on_alloc(uv_handle_t *handle, size_t suggested_size, uv_buf_t *buf);
    static void _on_recv(uv_stream_t *handle, ssize_t nread, const uv_buf_t *buf);
    static void _on_send_done(uv_write_t *req, int status);
	static void _uv_on_connect_timeout(uv_timer_t *timer);
    static void _uv_on_connected(uv_connect_t *req, int status);
    static void _uv_on_reconnect(uv_handle_t *handle);
	static void _uv_on_shutdown(uv_shutdown_t *req, int status);
	static void _uv_on_closed(uv_handle_t *handle);
	static void _uv_on_timer_connect_timeout_closed(uv_handle_t *handle);

//     static void _sec_hash_48(ex_u8 *buf_out, ex_u8 *buf_in, ex_u8 *salt1, ex_u8 *salt2, ex_u8 salt);
// 	static void _sec_hash_16(ex_u8 *buf_out, ex_u8 *buf_in, ex_u8 *salt1, ex_u8 *salt2);
//     void _sec_update(ex_u8 *init_key, ex_u8 *curr_key);

    bool _raw_send(const ex_u8 *data, size_t size);
//     bool _ssl_send(const ex_u8 *data, size_t size);
//     bool _ssl_prepare_as_server();
//     bool _ssl_prepare_as_client();

private:
    TelnetSession *m_session;
    bool m_is_server;

	// for debug-info.
    const char *m_name;

    uv_tcp_t m_handle;
	uv_timer_t m_timer_connect_timeout;
	bool m_timer_running;  // does m_timer_connect_timeout initialized and started.

	ex_u8 m_state; // RDP_CONN_STATE_XXXX

    // 作为client需要的数据（远程主机信息）
    std::string m_server_ip;
    ex_u16 m_server_port;
    bool m_is_recving;      // does this connection is receiving data?

    ExThreadLock m_locker_send;
    ExThreadLock m_locker_recv;
    MemBuffer m_buf_data;


    // 会话密钥相关
//     ex_u8 m_rc4_key_len;
//     ex_u8 m_mac_key[16];
//     ex_u8 m_init_enc_key[16];
//     ex_u8 m_init_dec_key[16];
//     ex_u8 m_curr_enc_key[16];
//     ex_u8 m_curr_dec_key[16];
//     mbedtls_arc4_context m_rc4_encrypt_key;
//     mbedtls_arc4_context m_rc4_decrypt_key;

//     ex_u32 m_encrypt_count;
//     ex_u32 m_decrypt_count;
//     ex_u32 m_encrypt_total;
//     ex_u32 m_decrypt_total;


    // RDP-SSL相关
//     MemBuffer m_ssl_mbuf;     // 存放接收到的数据（经过ssl解密）的缓冲区，等待处理。处理函数处理之后，应该将已经处理过的数据弹掉。
//     mbedtls_ssl_context m_ssl_ctx;
//     mbedtls_x509_crt m_ssl_node_cert;
//     mbedtls_pk_context m_ssl_node_key;
//     mbedtls_ssl_config m_ssl_conf;
//     mbedtls_entropy_context m_ssl_entropy;
//     mbedtls_ctr_drbg_context m_ssl_ctr_drbg;
//     mbedtls_x509_crt m_ssl_ca_cert;

	// 数据包解析相关
	//RDP_BULK* m_bulk;
};

#endif // __TELNET_CONN_H__
