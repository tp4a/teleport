#ifndef __TS_SESSION_H__
#define __TS_SESSION_H__

#include "../common/ts_const.h"
#include "../common/protocol_interface.h"

#include <ex.h>

typedef struct TS_CONNECT_INFO
{
	// TODO:
	//TPP_CONNECT_INFO conn;

	ex_astr sid;

	// 与此连接信息相关的三个要素的ID
	int user_id;
	int host_id;
	int acc_id;

	ex_astr user_username;// 申请本次连接的用户名

	ex_astr host_ip;// 真正的远程主机IP（如果是直接连接模式，则与remote_host_ip相同）
	ex_astr conn_ip;// 要连接的远程主机的IP（如果是端口映射模式，则为路由主机的IP）
	int conn_port;// 要连接的远程主机的端口（如果是端口映射模式，则为路由主机的端口）
	ex_astr client_ip;

	ex_astr acc_username;	// 远程主机的账号
	ex_astr acc_secret;	// 远程主机账号的密码（或者私钥）
	ex_astr username_prompt;// for telnet
	ex_astr password_prompt;// for telnet

	int protocol_type;
	int protocol_sub_type;
	int protocol_flag;
	int record_flag;
	int auth_type;

	int ref_count;// 这个连接信息的引用计数，如果创建的连接信息从来未被使用，则超过30秒后自动销毁
	ex_u64 ticket_start;// 此连接信息的创建时间（用于超时未使用就销毁的功能）
}TS_CONNECT_INFO;

typedef std::map<ex_astr, TS_CONNECT_INFO*> ts_connections;  // sid -> TS_CONNECT_INFO

class TsSessionManager : public ExThreadBase
{
public:
	TsSessionManager();
	~TsSessionManager();

	// generate a sid for connection info.
	bool request_session(ex_astr& sid, TS_CONNECT_INFO* info);

	// 根据sid得到连接信息（并增加引用计数）
	bool get_connect_info(const ex_astr& sid, TS_CONNECT_INFO& info);
	// 减少引用计数，当引用计数为0时，删除之
	bool free_connect_info(const ex_astr& sid);

protected:
	void _thread_loop(void);

private:
	void _gen_session_id(ex_astr& sid, const TS_CONNECT_INFO* info, int len);

	// 定时检查，超过30秒未进行连接的connect-info会被移除
	void _remove_expired_connect_info(void);

private:
	ExThreadLock m_lock;
	ts_connections m_connections;
};

extern TsSessionManager g_session_mgr;

#endif // __TS_SESSION_H__

