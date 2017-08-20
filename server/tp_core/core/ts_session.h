#ifndef __TS_SESSION_H__
#define __TS_SESSION_H__

#include "../common/ts_const.h"
#include "../common/protocol_interface.h"

#include <ex.h>

typedef struct TS_SESSION_INFO
{
	ex_astr sid;
	ex_astr account_name;	// 申请本次连接的用户名

	//int auth_id;
	ex_astr host_ip;
	int host_port;
	int protocol;
	ex_astr user_name;
	ex_astr user_auth;
	ex_astr user_param;
	int auth_mode;
	int sys_type;

	int ref_count;
	ex_u64 ticket_start;
}TS_SESSION_INFO;

typedef std::map<ex_astr, TS_SESSION_INFO*> ts_sessiones;

class TsSessionManager : public ExThreadBase
{
public:
	TsSessionManager();
	~TsSessionManager();

	// 申请一个session-id。
	ex_rv request_session(
		ex_astr& sid,	// 返回的session-id
		ex_astr account_name,
		int auth_id,
		const ex_astr& host_ip, // 要连接的主机IP
		int host_port,  // 要连接的主机端口
		int sys_type,   // 主机操作系统类型
		int protocol,  // 要使用的协议，1=rdp, 2=ssh
		const ex_astr& user_name, // 认证信息中的用户名
		const ex_astr& user_auth, // 认证信息，密码或私钥
		const ex_astr& user_param, //
		int auth_mode // 认证方式，1=password，2=private-key
	);

	// 根据sid得到session信息
	bool get_session(const ex_astr& sid, TS_SESSION_INFO& info);

protected:
	// 线程循环
	void _thread_loop(void);
	// 设置停止标志，让线程能够正常结束
	void _set_stop_flag(void);

private:
	bool _add_session(ex_astr& sid, TS_SESSION_INFO* info);
	void _gen_session_id(ex_astr& sid, const TS_SESSION_INFO* info, int len);
	void _check_sessions(void);

private:
	ExThreadLock m_lock;
	ts_sessiones m_sessions;
};

extern TsSessionManager g_session_mgr;

#endif // __TS_SESSION_H__

