#ifndef __TS_SESSION_H__
#define __TS_SESSION_H__

#include "../common/ts_const.h"
#include "../common/protocol_interface.h"

#include <ex.h>

typedef struct TS_CONNECT_INFO
{
	ex_astr sid;

	// 与此连接信息相关的三个要素的ID
	int user_id;
	int host_id;
	int account_id;

	ex_astr user_name;// 申请本次连接的用户名

	ex_astr real_remote_host_ip;// 真正的远程主机IP（如果是直接连接模式，则与remote_host_ip相同）
	ex_astr remote_host_ip;// 要连接的远程主机的IP（如果是端口映射模式，则为路由主机的IP）
	int remote_host_port;// 要连接的远程主机的端口（如果是端口映射模式，则为路由主机的端口）
	ex_astr client_ip;

	ex_astr account_name;	// 远程主机的账号
	ex_astr account_secret;// 远程主机账号的密码（或者私钥）
	ex_astr account_param;

	int protocol_type;
	int protocol_sub_type;
	int auth_type;
	int sys_type;
	
	int ref_count;// 这个连接信息的引用计数，如果创建的连接信息从来未被使用，则超过30秒后自动销毁
	ex_u64 ticket_start;// 此连接信息的创建时间（用于超时未使用就销毁的功能）
}TS_CONNECT_INFO;

typedef std::map<ex_astr, TS_CONNECT_INFO*> ts_connections;

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
	bool get_connect_info(const ex_astr& sid, TS_CONNECT_INFO& info);

protected:
	// 线程循环
	void _thread_loop(void);
	// 设置停止标志，让线程能够正常结束
	void _set_stop_flag(void);

private:
	void _gen_session_id(ex_astr& sid, const TS_CONNECT_INFO* info, int len);
	bool _add_connect_info(ex_astr& sid, TS_CONNECT_INFO* info);
	void _check_connect_info(void);

private:
	ExThreadLock m_lock;
	ts_connections m_connections;
};

extern TsSessionManager g_session_mgr;

#endif // __TS_SESSION_H__

