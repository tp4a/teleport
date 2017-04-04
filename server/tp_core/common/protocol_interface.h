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

typedef struct TS_SESSION_INFO
{
	ex_astr sid;
	ex_astr account_name;	// 申请本次连接的用户名

	int auth_id;
	ex_astr host_ip;
	int host_port;
	int protocol;
	ex_astr user_name;
	ex_astr user_auth;
	ex_astr user_param;
	int auth_mode;
	int sys_type;

	int ref_count;	// 这个session可以被take_session()多少次
	ex_u64 ticket_start;
}TS_SESSION_INFO;


typedef bool(*TPP_TAKE_SESSION_FUNC)(const ex_astr& sid, TS_SESSION_INFO& info);
typedef bool(*TPP_SESSION_BEGIN_FUNC)(TS_SESSION_INFO& info, int& db_id);
typedef bool(*TPP_SESSION_END_FUNC)(int db_id, int ret);


typedef struct TPP_INIT_ARGS
{
	ExLogger* logger;
	ex_wstr exec_path;
	ex_wstr etc_path;
	ex_wstr replay_path;
	ExIniFile* cfg;

	TPP_TAKE_SESSION_FUNC func_take_session;
	TPP_SESSION_BEGIN_FUNC func_session_begin;
	TPP_SESSION_END_FUNC func_session_end;
}TPP_INIT_ARGS;



#ifdef __cplusplus
extern "C"
{
#endif

	TPP_API ex_rv tpp_init(TPP_INIT_ARGS* init_args);
	TPP_API ex_rv tpp_start(void);
	TPP_API ex_rv tpp_stop(void);

#ifdef __cplusplus
}
#endif

typedef ex_rv (*TPP_INIT_FUNC)(TPP_INIT_ARGS* init_args);
typedef ex_rv (*TPP_START_FUNC)(void);
typedef ex_rv (*TPP_STOP_FUNC)(void);

#endif // __TP_PROTOCOL_INTERFACE_H__
