#ifndef __SSH_PROXY_H__
#define __SSH_PROXY_H__

#include "tpssh_session.h"

#include <ex.h>

typedef std::list<SshSession*> tp_ssh_sessions;

class SshProxy : public ExThreadBase
{
public:
	SshProxy();
	~SshProxy();

	bool init();
	void timer();
	void set_cfg(ex_u32 noop_timeout);
	void kill_sessions(const ex_astrs& sessions);

protected:
	void _thread_loop();
	void _on_stop();

	// 异步方式清理已经结束的会话实例
	void _clean_closed_session();

private:
	ssh_bind m_bind;
    int m_timer_counter_check_noop;
    int m_timer_counter_keep_alive;

	ExThreadLock m_lock;
    bool m_listener_running;

	ex_astr m_host_ip;
	int m_host_port;

	tp_ssh_sessions m_sessions;

	//
	ex_u32 m_cfg_noop_timeout_sec;
};

extern SshProxy g_ssh_proxy;

#endif // __SSH_PROXY_H__
