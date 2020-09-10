#ifndef __SSH_CLIENT_SIDE_H__
#define __SSH_CLIENT_SIDE_H__

#include <ex.h>
#include <libssh/libssh.h>
#include <libssh/callbacks.h>
#include <libssh/sftp.h>

class SshSession;
class SshClientSide : public ExThreadBase  {
public:
    SshClientSide(SshSession* owner, const std::string &host_ip, uint16_t host_port, const std::string &acc_name, const std::string &thread_name);
    virtual ~SshClientSide();

    uint32_t connect();
    uint32_t auth(int auth_type, const std::string &acc_secret);

    ssh_channel request_new_channel();

    void channel_closed(ssh_channel ch);

protected:
    void _thread_loop();

    void _on_stop();

    void _on_stopped();

    static int _on_server_channel_data(ssh_session session, ssh_channel channel, void *data, unsigned int len, int is_stderr, void *userdata);

    static void _on_server_channel_close(ssh_session session, ssh_channel channel, void *userdata);


private:
    SshSession* m_owner;
    std::string m_host_ip;
    uint16_t m_host_port;
    ex_astr m_acc_name;

    ssh_session m_session;
    struct ssh_channel_callbacks_struct m_channel_cb;

    std::list<ssh_channel> m_channels;

    ExThreadLock m_lock;

    std::string m_dbg_name;

    // 是否需要停止ssh事件处理循环
    bool m_need_stop_poll;

    bool m_need_send_keepalive;


    ex_astr m_acc_secret;
    int m_auth_type;
};


#endif // __SSH_CLIENT_SIDE_H__
