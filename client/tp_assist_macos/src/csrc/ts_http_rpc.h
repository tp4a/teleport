#ifndef __TS_HTTP_RPC_H__
#define __TS_HTTP_RPC_H__

#include "ts_const.h"

#include <vector>
#include <string>
#include <map>

#include <ex.h>
#include <json/json.h>

#include "../../external/mongoose/mongoose.h"

/*
//=================================================================
接口使用说明：

本程序启动后，监听 127.0.0.1:50022，接收http请求，请求格式要求如下：

GET 方式
http://127.0.0.1:50022/method/json_param
其中json_param是使用url_encode进行编码后的json格式字符串

POST 方式
http://127.0.0.1:50022/method
post的数据区域是json_param

其中，URI分为三个部分：
method			请求执行的任务方法。
json_param		此任务方法的附加参数，如果没有附加参数，这部分可以省略。

返回格式：执行结束后，返回一个json格式的字符串给请求者，格式如下：

{"code":0,"data":varb}

其中，code是必有的，其值是一个错误编码，0表示成功。如果失败，则可能没有data域。操作成功时，data域就是
操作的返回数据，其格式根据具体执行的任务方法不同而不同。

*/

int http_rpc_start(void* app);
void http_rpc_stop(void);

typedef std::map<ex_astr, ex_astr> content_type_map;

class TsHttpRpc : public ExThreadBase
{
public:
	TsHttpRpc();
	~TsHttpRpc();

	bool init(const char* ip, int port);

	ex_astr get_content_type(ex_astr file_suffix)
	{
		content_type_map::iterator it = m_content_type_map.find(file_suffix);
		if (it != m_content_type_map.end())
		{
			return it->second;
		}
		else
		{
			return "application/octet-stream";
		}
	};

protected:
	void _thread_loop(void);
	void _set_stop_flag(void);
	
private:
	int _parse_request(struct http_message* req, ex_astr& func_cmd, ex_astr& func_args);
	void _process_js_request(const ex_astr& func_cmd, const ex_astr& func_args, ex_astr& buf);
	void _create_json_ret(ex_astr& buf, int errcode);
	void _create_json_ret(ex_astr& buf, Json::Value& jr_root);

	void _rpc_func_run_client(const ex_astr& func_args, ex_astr& buf);
	void _rpc_func_check(const ex_astr& func_args, ex_astr& buf);
	void _rpc_func_rdp_play(const ex_astr& func_args, ex_astr& buf);
	void _rpc_func_get_config(const ex_astr& func_args, ex_astr& buf);
	void _rpc_func_set_config(const ex_astr& func_args, ex_astr& buf);
	void _rpc_func_file_action(const ex_astr& func_args, ex_astr& buf);
	void _rpc_func_get_version(const ex_astr& func_args, ex_astr& buf);

	static void _mg_event_handler(struct mg_connection *nc, int ev, void *ev_data);

private:
	content_type_map m_content_type_map;
	struct mg_mgr m_mg_mgr;
};

#endif // __TS_HTTP_RPC_H__
