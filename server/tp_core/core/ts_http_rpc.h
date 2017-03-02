#ifndef __TS_HTTP_RPC_H__
#define __TS_HTTP_RPC_H__

#include "mongoose.h"

#include <ex.h>
#include <json/json.h>


/*
//=================================================================
接口使用说明：

本程序启动后，监听 127.0.0.1:52080，接收http请求，请求格式要求如下：

GET 方式
http://127.0.0.1:52080/method/json_param
其中json_param是使用url_encode进行编码后的json格式字符串

POST 方式
http://127.0.0.1:52080/method
post的数据区域是json_param

其中，URI分为三个部分：
method			请求执行的任务方法。
json_param		此任务方法的附加参数，如果没有附加参数，这部分可以省略。

返回格式：执行结束后，返回一个json格式的字符串给请求者，格式如下：

{"code":0,"data":varb}

其中，code是必有的，其值是一个错误编码，0表示成功。如果失败，则可能没有data域。操作成功时，data域就是
操作的返回数据，其格式根据具体执行的任务方法不同而不同。

*/

class TsHttpRpc : public ExThreadBase
{
public:
	TsHttpRpc();
	~TsHttpRpc();

	bool init(void);

protected:
	void _thread_loop(void);
	void _set_stop_flag(void);

private:
	ex_rv _parse_request(struct http_message* req, ex_astr& func_cmd, Json::Value& json_param);
	void _process_request(const ex_astr& func_cmd, const Json::Value& json_param, ex_astr& buf);

	//void _create_json_ret(ex_astr& buf, Json::Value& jr_root);
	void _create_json_ret(ex_astr& buf, int errcode, const Json::Value& jr_data);
	void _create_json_ret(ex_astr& buf, int errcode);
	void _create_json_ret(ex_astr& buf, int errcode, const char* message);

	// 请求一个会话ID
	void _rpc_func_request_session(const Json::Value& json_param, ex_astr& buf);
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
