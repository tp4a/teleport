#include "ts_web_rpc.h"
#include "ts_env.h"
#include "ts_crypto.h"
#include "ts_http_client.h"

#include "../common/ts_const.h"

#include <ex/ex_str.h>
#include <teleport_const.h>

bool ts_web_rpc_register_core()
{
	Json::FastWriter json_writer;
	Json::Value jreq;
	jreq["method"] = "register_core";
	jreq["param"]["rpc"] = g_env.core_server_rpc;

	ex_astr json_param;
	json_param = json_writer.write(jreq);

	ex_astr param;
	ts_url_encode(json_param.c_str(), param);

	ex_astr url = g_env.web_server_rpc;
	url += "?";
	url += param;

	ex_astr body;
	return ts_http_get(url, body);
}

int ts_web_rpc_get_conn_info(int conn_id, TS_CONNECT_INFO& info)
{
	Json::FastWriter json_writer;
	Json::Value jreq;
	jreq["method"] = "get_conn_info";
	jreq["param"]["conn_id"] = conn_id;

	ex_astr json_param;
	json_param = json_writer.write(jreq);

	ex_astr param;
	ts_url_encode(json_param.c_str(), param);

	ex_astr url = g_env.web_server_rpc;
	url += "?";
	url += param;

	ex_astr body;
	if (!ts_http_get(url, body))
	{
// 		EXLOGV("request `get_auth_info` from web return: ");
// 		EXLOGV(body.c_str());
// 		EXLOGV("\n");
		return TPE_NETWORK;
	}

	Json::Reader jreader;
	Json::Value jret;

	if (!jreader.parse(body.c_str(), jret))
		return TPE_PARAM;
	if (!jret.isObject())
		return TPE_PARAM;
	if (!jret["data"].isObject())
		return TPE_PARAM;

	Json::Value& _jret = jret["data"];

	if (
		!_jret["user_id"].isInt()
		|| !_jret["host_id"].isInt()
		|| !_jret["account_id"].isInt()
		|| !_jret["remote_host_port"].isInt()
		|| !_jret["protocol_type"].isInt()
		|| !_jret["protocol_sub_type"].isInt()
		|| !_jret["auth_type"].isInt()
		|| !_jret["connect_flag"].isInt()
		|| !_jret["_enc"].isInt()

		|| !_jret["user_name"].isString()
		|| !_jret["real_remote_host_ip"].isString()
		|| !_jret["remote_host_ip"].isString()
		|| !_jret["client_ip"].isString()
		|| !_jret["account_name"].isString()
		|| !_jret["account_secret"].isString()
		|| !_jret["username_prompt"].isString()
		|| !_jret["password_prompt"].isString()
		)
	{
		EXLOGE("got connection info from web-server, but not all info valid.\n");
		return TPE_PARAM;
	}
	
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
	ex_astr username_prompt;
	ex_astr password_prompt;
	int protocol_type;
	int protocol_sub_type;
	int auth_type;
	int connect_flag;
	bool _enc;

	user_id = _jret["user_id"].asInt();
	host_id = _jret["host_id"].asInt();
	account_id = _jret["account_id"].asInt();
	user_name = _jret["user_name"].asString();
	real_remote_host_ip = _jret["real_remote_host_ip"].asString();
	remote_host_ip = _jret["remote_host_ip"].asString();
	remote_host_port = _jret["remote_host_port"].asInt();
	client_ip = _jret["client_ip"].asString();
	account_name = _jret["account_name"].asString();
	account_secret = _jret["account_secret"].asString();
	username_prompt = _jret["username_prompt"].asString();
	password_prompt = _jret["password_prompt"].asString();
	protocol_type = _jret["protocol_type"].asInt();
	protocol_sub_type = _jret["protocol_sub_type"].asInt();
	connect_flag = _jret["connect_flag"].asInt();
	auth_type = _jret["auth_type"].asInt();
	_enc = _jret["_enc"].asBool();


	// 进一步判断参数是否合法
	// 注意，account_id可以为-1，表示这是一次测试连接。
	if (user_id <= 0 || host_id <= 0
		|| user_name.length() == 0
		|| real_remote_host_ip.length() == 0 || remote_host_ip.length() == 0 || client_ip.length() == 0
		|| remote_host_port <= 0 || remote_host_port >= 65535
		|| account_name.length() == 0 || account_secret.length() == 0
		|| connect_flag == 0
		|| !(protocol_type == TP_PROTOCOL_TYPE_RDP || protocol_type == TP_PROTOCOL_TYPE_SSH || protocol_type == TP_PROTOCOL_TYPE_TELNET)
		|| !(auth_type == TP_AUTH_TYPE_NONE || auth_type == TP_AUTH_TYPE_PASSWORD || auth_type == TP_AUTH_TYPE_PRIVATE_KEY)
		)
	{
		return TPE_PARAM;
	}

	if (_enc) {
		ex_astr _auth;
		if (!ts_db_field_decrypt(account_secret, _auth))
			return TPE_FAILED;

		account_secret = _auth;
	}

	info.user_id = user_id;
	info.host_id = host_id;
	info.account_id = account_id;
	info.user_name = user_name;
	info.real_remote_host_ip = real_remote_host_ip;
	info.remote_host_ip = remote_host_ip;
	info.remote_host_port = remote_host_port;
	info.client_ip = client_ip;
	info.account_name = account_name;
	info.account_secret = account_secret;
	info.username_prompt = username_prompt;
	info.password_prompt = password_prompt;
	info.protocol_type = protocol_type;
	info.protocol_sub_type = protocol_sub_type;
	info.auth_type = auth_type;
	info.connect_flag = connect_flag;

	return TPE_OK;
}

bool ts_web_rpc_session_begin(TS_CONNECT_INFO& info, int& record_id)
{
	Json::FastWriter json_writer;
	Json::Value jreq;

	jreq["method"] = "session_begin";
	jreq["param"]["sid"] = info.sid.c_str();
	jreq["param"]["user_name"] = info.user_name.c_str();
	jreq["param"]["account_name"] = info.account_name.c_str();
	jreq["param"]["real_remote_host_ip"] = info.real_remote_host_ip.c_str();
	jreq["param"]["remote_host_ip"] = info.remote_host_ip.c_str();
	jreq["param"]["client_ip"] = info.client_ip.c_str();
	//jreq["param"]["sys_type"] = info.sys_type;
	jreq["param"]["remote_host_port"] = info.remote_host_port;
	jreq["param"]["auth_type"] = info.auth_type;
	jreq["param"]["protocol_type"] = info.protocol_type;
	jreq["param"]["protocol_sub_type"] = info.protocol_sub_type;

	ex_astr json_param;
	json_param = json_writer.write(jreq);

	ex_astr param;
	ts_url_encode(json_param.c_str(), param);

	ex_astr url = g_env.web_server_rpc;
	url += "?";
	url += param;

	ex_astr body;
	if (!ts_http_get(url, body))
	{
		// 		EXLOGV("request `rpc::session_begin` from web return: ");
		// 		EXLOGV(body.c_str());
		// 		EXLOGV("\n");
		return false;
	}

	Json::Reader jreader;
	Json::Value jret;

	if (!jreader.parse(body.c_str(), jret))
		return false;
	if (!jret.isObject())
		return false;
	if (!jret["data"].isObject())
		return false;
	if (!jret["data"]["rid"].isUInt())
		return false;

	record_id = jret["data"]["rid"].asUInt();

	return true;
}

//session 结束
bool ts_web_rpc_session_end(const char* sid, int record_id, int ret_code)
{
	// TODO: 对指定的sid相关的会话的引用计数减一（但减到0时销毁）


	Json::FastWriter json_writer;
	Json::Value jreq;
	jreq["method"] = "session_end";
	jreq["param"]["rid"] = record_id;
	jreq["param"]["code"] = ret_code;

	ex_astr json_param;
	json_param = json_writer.write(jreq);

	ex_astr param;
	ts_url_encode(json_param.c_str(), param);

	ex_astr url = g_env.web_server_rpc;
	url += "?";
	url += param;

	ex_astr body;
	return ts_http_get(url, body);
}
