#ifndef __TP_PROTOCOL_INTERFACE_H__
#define __TP_PROTOCOL_INTERFACE_H__

#include "ts_const.h"
#include <ex.h>

#ifdef EX_OS_WIN32
#	ifdef TPP_EXPORTS
#		define TPP_API __declspec(dllexport)
#	else
#		define TPP_API __declspec(dllimport)
#	endif
#else
#	define TPP_API
#endif

#define TPP_CMD_INIT			0x00000000
#define TPP_CMD_SET_RUNTIME_CFG	0x00000005
#define TPP_CMD_KILL_SESSIONS	0x00000006

typedef struct TPP_CONNECT_INFO
{
	char* sid;

	// 与此连接信息相关的三个要素的ID
	int user_id;
	int host_id;
	int acc_id;

	char* user_username;		// 申请本次连接的用户名

	char* host_ip;	// 真正的远程主机IP（如果是直接连接模式，则与remote_host_ip相同）
	char* conn_ip;	// 要连接的远程主机的IP（如果是端口映射模式，则为路由主机的IP）
	int conn_port;	// 要连接的远程主机的端口（如果是端口映射模式，则为路由主机的端口）
	char* client_ip;

	char* acc_username;		// 远程主机的账号
	char* acc_secret;	// 远程主机账号的密码（或者私钥）
	char* username_prompt;	// for telnet
	char* password_prompt;	// for telnet

	int protocol_type;
	int protocol_sub_type;
	int protocol_flag;
	int record_flag;
	int auth_type;
}TPP_CONNECT_INFO;

typedef TPP_CONNECT_INFO* (*TPP_GET_CONNNECT_INFO_FUNC)(const char* sid);
typedef void(*TPP_FREE_CONNECT_INFO_FUNC)(TPP_CONNECT_INFO* info);
typedef bool(*TPP_SESSION_BEGIN_FUNC)(const TPP_CONNECT_INFO* info, int* db_id);
typedef bool(*TPP_SESSION_UPDATE_FUNC)(int db_id, int protocol_sub_type, int state);
typedef bool(*TPP_SESSION_END_FUNC)(const char* sid, int db_id, int ret);


typedef struct TPP_INIT_ARGS
{
	ExLogger* logger;
	ex_wstr exec_path;
	ex_wstr etc_path;
	ex_wstr replay_path;
	ExIniFile* cfg;

	TPP_GET_CONNNECT_INFO_FUNC func_get_connect_info;
	TPP_FREE_CONNECT_INFO_FUNC func_free_connect_info;
	TPP_SESSION_BEGIN_FUNC func_session_begin;
	TPP_SESSION_UPDATE_FUNC func_session_update;
	TPP_SESSION_END_FUNC func_session_end;
}TPP_INIT_ARGS;

// typedef struct TPP_SET_CFG_ARGS {
// 	ex_u32 noop_timeout; // as second.
// }TPP_SET_CFG_ARGS;

#ifdef __cplusplus
extern "C"
{
#endif

	TPP_API ex_rv tpp_init(TPP_INIT_ARGS* init_args);
	TPP_API ex_rv tpp_start(void);
	TPP_API ex_rv tpp_stop(void);
	TPP_API void tpp_timer(void);
// 	TPP_API void tpp_set_cfg(TPP_SET_CFG_ARGS* cfg_args);

	TPP_API ex_rv tpp_command(ex_u32 cmd, const char* param);

#ifdef __cplusplus
}
#endif

typedef ex_rv (*TPP_INIT_FUNC)(TPP_INIT_ARGS* init_args);
typedef ex_rv (*TPP_START_FUNC)(void);
typedef ex_rv(*TPP_STOP_FUNC)(void);
typedef void(*TPP_TIMER_FUNC)(void);
// typedef void(*TPP_SET_CFG_FUNC)(TPP_SET_CFG_ARGS* cfg_args);

typedef ex_rv(*TPP_COMMAND_FUNC)(ex_u32 cmd, const char* param); // param is a JSON formatted string.

#endif // __TP_PROTOCOL_INTERFACE_H__
