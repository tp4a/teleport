#ifndef __TS_HTTP_RPC_H__
#define __TS_HTTP_RPC_H__

#include "mongoose.h"

#include <ex.h>
#include <json/json.h>

// JSON-RPC documentation at:
// https://github.com/tp4a/teleport/wiki/TELEPORT-CORE-JSON-RPC

class TsHttpRpc : public ExThreadBase
{
public:
	TsHttpRpc();
	~TsHttpRpc();

	bool init(void);

protected:
	void _thread_loop(void);

private:
	ex_rv _parse_request(struct http_message* req, ex_astr& func_cmd, Json::Value& json_param);
	void _process_request(const ex_astr& func_cmd, const Json::Value& json_param, ex_astr& buf);

	//void _create_json_ret(ex_astr& buf, Json::Value& jr_root);
	void _create_json_ret(ex_astr& buf, int errcode, const Json::Value& jr_data);
	void _create_json_ret(ex_astr& buf, int errcode);
	void _create_json_ret(ex_astr& buf, int errcode, const char* message);

	// 获取core服务的配置信息（主要是支持的各个协议是否启用，以及其端口号等）
	void _rpc_func_get_config(const Json::Value& json_param, ex_astr& buf);
	// set run-time configuration, like no-op-timeout.
	void _rpc_func_set_config(const Json::Value& json_param, ex_astr& buf);
	// 请求一个会话ID
	void _rpc_func_request_session(const Json::Value& json_param, ex_astr& buf);
	// 强行终止会话
	void _rpc_func_kill_sessions(const Json::Value& json_param, ex_astr& buf);
	// 加密一个字符串（返回的是密文的BASE64编码）
	void _rpc_func_enc(const Json::Value& json_param, ex_astr& buf);
	// 要求整个核心服务退出
	void _rpc_func_exit(const Json::Value& json_param, ex_astr& buf);

	static void _mg_event_handler(struct mg_connection *nc, int ev, void *ev_data);

private:
	ex_astr m_host_ip;
	int m_host_port;

	struct mg_mgr m_mg_mgr;
};

#endif // __TS_HTTP_RPC_H__
