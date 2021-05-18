#ifndef __SSH_PROXY_H__
#define __SSH_PROXY_H__

#include "ssh_session.h"

#include <ex.h>

typedef std::map<SshSession*, unsigned char> ts_ssh_sessions;

class SshProxy : public ExThreadBase {
public:
    SshProxy() noexcept;

    ~SshProxy() override;

    bool init();

    void timer();

    void set_cfg(ex_u32 noop_timeout);

    void kill_sessions(const ex_astrs& sessions);

protected:
    void _thread_loop() override;

    void _on_stop() override;

private:
    ssh_bind m_bind;
    int m_timer_counter_check_noop;
    int m_timer_counter_keep_alive;

    ExThreadLock m_lock;
    bool m_listener_running;

    ex_astr m_host_ip;
    int m_host_port;

    ts_ssh_sessions m_sessions;

    ex_u32 m_noop_timeout_sec;

    uint32_t m_dbg_id;
};

extern SshProxy g_ssh_proxy;

#endif // __SSH_PROXY_H__
