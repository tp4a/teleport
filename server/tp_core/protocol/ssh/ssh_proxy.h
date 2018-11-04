#ifndef __SSH_PROXY_H__
#define __SSH_PROXY_H__

#include "ssh_session.h"

#include <ex.h>

typedef std::map<SshSession*, unsigned char> ts_ssh_sessions;

class SshProxy : public ExThreadBase
{
public:
	SshProxy();
	~SshProxy();

	bool init();
	void timer();
	void set_cfg(ex_u32 noop_timeout);
	void kill_sessions(const ex_astrs& sessions);

	void session_finished(SshSession* sess);

protected:
	void _thread_loop();
	void _on_stop();

private:
	ssh_bind m_bind;
	int m_timer_counter;

	ExThreadLock m_lock;

	ex_astr m_host_ip;
	int m_host_port;

	ts_ssh_sessions m_sessions;

// 	ExThreadManager m_thread_mgr;

	// 
	ex_u32 m_noop_timeout_sec;
};

extern SshProxy g_ssh_proxy;

#endif // __SSH_PROXY_H__
