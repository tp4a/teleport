#ifndef __SSH_PROXY_H__
#define __SSH_PROXY_H__

#include "ssh_session.h"

#include <ex.h>

typedef std::map<SshSession*, unsigned char> ts_ssh_sessions;

typedef struct TS_SFTP_SESSION_INFO
{
	ex_astr host_ip;
	int host_port;
	ex_astr user_name;
	ex_astr user_auth;
	int auth_mode;
	int ref_count; // 引用计数器，但所有引用本登录信息的ssh-sftp通道关闭，就销毁之
}TS_SFTP_SESSION_INFO;

typedef std::map<ex_astr, TS_SFTP_SESSION_INFO*> ts_sftp_sessions;

class SshProxy : public ExThreadBase
{
public:
	SshProxy();
	~SshProxy();

	bool init(void);

	void add_sftp_session_info(
		const ex_astr& sid,
		const ex_astr& host_ip,
		int host_port,
		const ex_astr& user_name,
		const ex_astr& user_auth,
		int auth_mode
		);
	bool get_sftp_session_info(const ex_astr& sid, TS_SFTP_SESSION_INFO& info);
	void remove_sftp_sid(const ex_astr& sid);

	void session_finished(SshSession* sess);

protected:
	void _thread_loop(void);
	void _set_stop_flag(void);

	void _run(void);

private:
	void _dump_sftp_sessions(void);

private:
	ssh_bind m_bind;
	bool m_stop_flag;

	ExThreadLock m_lock;

	ex_astr m_host_ip;
	int m_host_port;

	ts_ssh_sessions m_sessions;
	ts_sftp_sessions m_sftp_sessions;

	ExThreadManager m_thread_mgr;
};

extern SshProxy g_ssh_proxy;

#endif // __SSH_PROXY_H__
