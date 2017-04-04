#ifndef __TS_WEB_RPC_H__
#define __TS_WEB_RPC_H__

#include "ts_session.h"

#include <json/json.h>

// 重置log日志状态
bool ts_web_rpc_register_core();

// 根据认证ID获取认证信息（包括服务器IP、端口，用户名、密码或私钥、协议如RDP或SSH等等）
bool ts_web_rpc_get_auth_info(int auth_id, Json::Value& jret);

// 记录会话的开始
bool ts_web_rpc_session_begin(TS_SESSION_INFO& info, int& record_id);
//session 结束
bool ts_web_rpc_session_end(int id, int ret_code);


#endif // __TS_WEB_RPC_H__
