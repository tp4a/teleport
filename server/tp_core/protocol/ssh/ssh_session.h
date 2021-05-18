#ifndef __SSH_SESSION_H__
#define __SSH_SESSION_H__

#include <ex.h>

#include <libssh/libssh.h>
#include <libssh/server.h>
#include <libssh/callbacks.h>
#include <libssh/sftp.h>

#include <vector>
#include <list>
#include <queue>

#include "ssh_channel_pair.h"

// #define TEST_SSH_SESSION_000000

#define TS_SSH_CHANNEL_TYPE_UNKNOWN     0
#define TS_SSH_CHANNEL_TYPE_SHELL       1
#define TS_SSH_CHANNEL_TYPE_SFTP        2

enum SSH_SESSION_STATUS {
    SSH_SESSION_STATE_NO_CHANNEL = 0,
    SSH_SESSION_STATE_STARTING,
    SSH_SESSION_STATE_AUTHING,
    SSH_SESSION_STATE_AUTH_END,
    SSH_SESSION_STATE_RUNNING,
    SSH_SESSION_STATE_CLOSING
};

class SshProxy;

class SshSession;

class SshSession : public ExThreadBase {
public:
    SshSession(SshProxy* proxy, ssh_session rs_tp2cli, uint32_t dbg_id, const char* client_ip, uint16_t client_port);

    virtual ~SshSession();

    const std::string& dbg_name() const {
        return m_dbg_name;
    }

    const std::string& dbg_client() const {
        return m_dbg_client;
    }

    const std::string& dbg_server() const {
        return m_dbg_server;
    }

    const std::string& sid() {
        return m_sid;
    }

    // save record cache into file. be called per 5 seconds.
    void save_record();

    //
    void check_noop_timeout(ex_u32 t_now, ex_u32 timeout);


    void keep_alive();

    bool all_channel_closed() const {
        return m_state == SSH_SESSION_STATE_NO_CHANNEL;
    }

    ssh_session get_peer_raw_session(ssh_session session) {
        if (session == m_rs_tp2cli)
            return m_rs_tp2srv;
        else if (session == m_rs_tp2srv)
            return m_rs_tp2cli;
        else
            return nullptr;
    }

    // --------------------------
    // 通道管理
    // --------------------------
    // void set_channel_tp2srv_callbacks(ssh_channel ch_tp2srv);

    bool make_channel_pair(ssh_channel ch_tp2cli, ssh_channel ch_tp2srv);

    SshChannelPair* get_channel_pair(ssh_channel ch);

    void check_channels();

protected:
    void _thread_loop() override;

    void _on_stop() override;

    void _on_stopped() override;

    // record an error when session connecting or auth-ing.
    // void _session_error(int err_code);

private:
    void _close_channels();

    int _do_auth(const char* user, const char* secret);

    void _set_last_error(int err_code);

    bool _send(ssh_channel channel_to, int is_stderr, void* data, uint32_t len);

    static int _on_auth_password_request(ssh_session session, const char* user, const char* password, void* userdata);

    static ssh_channel _on_new_channel_request(ssh_session session, void* userdata);

    static int _on_client_pty_request(ssh_session session, ssh_channel channel, const char* term, int x, int y, int px, int py, void* userdata);

    static int _on_client_shell_request(ssh_session session, ssh_channel channel, void* userdata);

    static void _on_client_channel_close(ssh_session session, ssh_channel channel, void* userdata);

    static int _on_client_channel_data(ssh_session session, ssh_channel channel, void* data, unsigned int len, int is_stderr, void* userdata);

    static int _on_client_pty_win_change(ssh_session session, ssh_channel channel, int width, int height, int pxwidth, int pwheight, void* userdata);

    static int _on_client_channel_subsystem_request(ssh_session session, ssh_channel channel, const char* subsystem, void* userdata);

    static int _on_client_channel_exec_request(ssh_session session, ssh_channel channel, const char* command, void* userdata);

    static int _on_server_channel_data(ssh_session session, ssh_channel channel, void* data, unsigned int len, int is_stderr, void* userdata);

    static void _on_server_channel_close(ssh_session session, ssh_channel channel, void* userdata);

private:
    SshProxy* m_proxy;
    SSH_SESSION_STATUS m_state;
    ssh_session m_rs_tp2cli;
    ssh_session m_rs_tp2srv;

    ExThreadLock m_lock;

    uint32_t m_dbg_id;
    std::string m_dbg_name;
    std::string m_dbg_client;
    std::string m_dbg_server;

    TPP_CONNECT_INFO* m_conn_info;

    std::string m_sid;
    std::string m_conn_ip;
    uint16_t m_conn_port;
    std::string m_acc_name;
    std::string m_acc_secret;
    uint32_t m_flags;
    int m_auth_type;
    bool m_allow_user_input_password;

    bool m_first_auth;
    // 远程主机认证是否通过
    bool m_auth_passed;
    // 如果认证过程中发生了错误，记录错误提示，后续建立通道后可以发送给客户端进行提示
    std::string m_auth_err_msg;
    // 发生了不可逆的错误，需要关闭整个会话（包括所有的通道）
    bool m_fault;

    // 管理两端的通道对
    uint32_t m_pair_id; // for debug.
    TPChannelPairs m_pairs;
    // 用于快速查找
    channel_map m_channel_map;
    // 本会话中的所有通道（无论哪一端的）
    std::list<ssh_channel> m_channels;

    bool m_need_send_keepalive;

    struct ssh_server_callbacks_struct m_srv_cb;
    struct ssh_channel_callbacks_struct m_cli_channel_cb;
    struct ssh_channel_callbacks_struct m_srv_channel_cb;
};

#endif // __SSH_SESSION_H__
