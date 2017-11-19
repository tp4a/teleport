#ifndef __TS_WEB_RPC_H__
#define __TS_WEB_RPC_H__

#include "ts_session.h"

#include <json/json.h>

// 重置log日志状态
bool ts_web_rpc_register_core();

// 根据连接ID获取远程连接信息（包括服务器IP、端口，用户名、密码或私钥、协议如RDP或SSH等等）
int ts_web_rpc_get_conn_info(int conn_id, TS_CONNECT_INFO& info);

// 记录会话的开始
bool ts_web_rpc_session_begin(TS_CONNECT_INFO& info, int& record_id);
// update session state
bool ts_web_rpc_session_update(int id, int protocol_sub_type, int state);
//session 结束
bool ts_web_rpc_session_end(const char* sid, int id, int ret_code);


#endif // __TS_WEB_RPC_H__
