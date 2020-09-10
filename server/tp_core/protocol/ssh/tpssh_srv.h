#ifndef __SSH_SESSION_H__
#define __SSH_SESSION_H__

#include <ex.h>

#include <libssh/libssh.h>
#include <libssh/server.h>
#include <libssh/callbacks.h>
#include <libssh/sftp.h>

#include <vector>
#include <list>

#include "tpssh_rec.h"
#include "tpssh_cli.h"
#include "tpssh_channel.h"


#define TS_SSH_CHANNEL_TYPE_UNKNOWN     0
#define TS_SSH_CHANNEL_TYPE_SHELL       1
#define TS_SSH_CHANNEL_TYPE_SFTP        2

#define TP_SSH_CLIENT_SIDE        1
#define TP_SSH_SERVER_SIDE        2

class SshProxy;
class SshSession;

#if 0
class SshServerSide;

class SshClientSide;

class TP_SSH_CHANNEL_PAIR {

    friend class SshServerSide;

    friend class SshClientSide;

public:
    TP_SSH_CHANNEL_PAIR();

private:
    int type;    // TS_SSH_CHANNEL_TYPE_SHELL or TS_SSH_CHANNEL_TYPE_SFTP

    ssh_channel cli_channel;
    ssh_channel srv_channel;

    TppSshRec rec;
    ex_u32 last_access_timestamp;

    int state;
    int db_id;
    int channel_id;    // for debug only.

    int win_width; // window width, in char count.

    bool is_first_server_data;
    bool need_close;

    // for ssh command record cache.
    bool server_ready;
    bool maybe_cmd;
    bool process_srv;
    bool client_single_char;
    std::list<char> cmd_char_list;
    std::list<char>::iterator cmd_char_pos;
};

typedef std::list<TP_SSH_CHANNEL_PAIR *> tp_channels;
#endif

class SshServerSide : public ExThreadBase {
public:
    SshServerSide(SshSession *s, ssh_session sess_tp2cli, const std::string &thread_name);

    virtual ~SshServerSide();

    // SshProxy *get_proxy() { return m_proxy; }

    //TP_SSH_CHANNEL_PAIR *_get_channel_pair(int channel_side, ssh_channel channel);

    //void client_ip(const char* ip) { m_client_ip = ip; }
    const char *client_ip() const { return m_client_ip.c_str(); }

    //void client_port(ex_u16 port) { m_client_port = port; }
    ex_u16 client_port() const { return m_client_port; }

    bool init();

    const ex_astr &sid() { return m_sid; }

    void channel_closed(ssh_channel ch);
protected:
    void _thread_loop();

    void _on_stop();

    void _on_stopped();

    // record an error when session connecting or auth-ing.
//    void _session_error(int err_code);

//    // when client<->server channel created, start to record.
//    bool _record_begin(TP_SSH_CHANNEL_PAIR *cp);
//
//    // stop record because channel closed.
//    void _record_end(TP_SSH_CHANNEL_PAIR *cp);
//
//    void _process_ssh_command(TP_SSH_CHANNEL_PAIR *cp, int from, const ex_u8 *data, int len);
//
//    void _process_sftp_command(TP_SSH_CHANNEL_PAIR *cp, const ex_u8 *data, int len);

private:

    void _close_channels();

    // void _check_channels();

    int _auth(const char *user, const char *password);

    static int _on_auth_password_request(ssh_session session, const char *user, const char *password, void *userdata);

    static ssh_channel _on_new_channel_request(ssh_session session, void *userdata);

    static int _on_client_pty_request(ssh_session session, ssh_channel channel, const char *term, int x, int y, int px, int py, void *userdata);

    static int _on_client_shell_request(ssh_session session, ssh_channel channel, void *userdata);

    static void _on_client_channel_close(ssh_session session, ssh_channel channel, void *userdata);

    static int _on_client_channel_data(ssh_session session, ssh_channel channel, void *data, unsigned int len, int is_stderr, void *userdata);

    static int _on_client_pty_win_change(ssh_session session, ssh_channel channel, int width, int height, int pxwidth, int pwheight, void *userdata);

    static int _on_client_channel_subsystem_request(ssh_session session, ssh_channel channel, const char *subsystem, void *userdata);

    static int _on_client_channel_exec_request(ssh_session session, ssh_channel channel, const char *command, void *userdata);

//    static int _on_server_channel_data(ssh_session session, ssh_channel channel, void *data, unsigned int len, int is_stderr, void *userdata);
//
//    static void _on_server_channel_close(ssh_session session, ssh_channel channel, void *userdata);

private:
    SshSession *m_owner;

    // 认证阶段发生的错误。认证阶段出错时并不返回错误，避免客户端反复提示用户输入密码，而是返回认证成功，但记录错误值，
    // 下一步在申请开启通道时，先检查记录的错误值，如果认证过程中已经出错，则不打开通道，而是断开连接。
    uint32_t m_auth_error;
    // 是否是首次认证（仅用于允许用户自行输入密码的情况，即，未在TP中设置远程账号密码，否则首次认证失败，就结束会话）
    bool m_first_auth;
    // 是否允许用户自行输入密码
    bool m_allow_user_input_password;
    // 用户自行输入密码的错误计数器。超过3次中断会话，不允许继续尝试
    int m_auth_fail_count;

    ssh_session m_session;
    std::list<ssh_channel> m_channels;

    ExThreadLock m_lock;

    ex_astr m_client_ip;
    ex_u16 m_client_port;

    TPP_CONNECT_INFO *m_conn_info;

    ex_astr m_sid;
    ex_astr m_conn_ip;
    ex_u16 m_conn_port;
    ex_astr m_acc_name;
    ex_astr m_acc_secret;
    ex_u32 m_flags;
    int m_auth_type;

    bool m_is_logon;

    int m_ssh_ver;

    // 是否需要停止ssh事件处理循环
    bool m_need_stop_poll;

    bool m_need_send_keepalive;

    bool m_recving_from_srv;        // 是否正在从服务器接收数据？
    bool m_recving_from_cli;        // 是否正在从客户端接收数据？

    struct ssh_server_callbacks_struct m_srv_cb;
    struct ssh_channel_callbacks_struct m_channel_with_cli_cb;
//    struct ssh_channel_callbacks_struct m_srv_channel_cb;
};

#endif // __SSH_SESSION_H__
