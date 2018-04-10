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
		EXLOGE("[core] get conn info from web-server failed: can not connect to web-server.\n");
		return TPE_NETWORK;
	}
	if (body.length() == 0) {
		EXLOGE("[core] get conn info from web-server failed: got nothing.\n");
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

    if(!_jret["user_id"].isInt())
        EXLOGE("connection info: need `user_id`.\n");
    if(!_jret["host_id"].isInt())
        EXLOGE("connection info: need `host_id`.\n");
    if(!_jret["acc_id"].isInt())
        EXLOGE("connection info: need `acc_id`.\n");
    if(!_jret["conn_port"].isInt())
        EXLOGE("connection info: need `conn_port`.\n");
    if(!_jret["protocol_type"].isInt())
        EXLOGE("connection info: need `protocol_type`.\n");
    if(!_jret["protocol_sub_type"].isInt())
        EXLOGE("connection info: need `protocol_sub_type`.\n");
    if(!_jret["auth_type"].isInt())
        EXLOGE("connection info: need `auth_type`.\n");
	if (!_jret["protocol_flag"].isUInt())
		EXLOGE("connection info: need `protocol_flag`.\n");
	if (!_jret["record_flag"].isUInt())
		EXLOGE("connection info: need `record_flag`.\n");
	if (!_jret["_enc"].isInt())
        EXLOGE("connection info: need `_enc`.\n");
    if(!_jret["user_username"].isString())
        EXLOGE("connection info: need `user_username`.\n");
    if(!_jret["host_ip"].isString())
        EXLOGE("connection info: need `host_ip`.\n");
    if(!_jret["conn_ip"].isString())
        EXLOGE("connection info: need `conn_ip`.\n");
    if(!_jret["client_ip"].isString())
        EXLOGE("connection info: need `client_ip`.\n");
    if(!_jret["acc_username"].isString())
        EXLOGE("connection info: need `acc_username`.\n");
    if(!_jret["acc_secret"].isString())
        EXLOGE("connection info: need `acc_secret`.\n");
    if(!_jret["username_prompt"].isString())
        EXLOGE("connection info: need `username_prompt`.\n");
    if(!_jret["password_prompt"].isString())
        EXLOGE("connection info: need `password_prompt`.\n");

	if (
		!_jret["user_id"].isInt()
		|| !_jret["host_id"].isInt()
		|| !_jret["acc_id"].isInt()
		|| !_jret["conn_port"].isInt()
		|| !_jret["protocol_type"].isInt()
		|| !_jret["protocol_sub_type"].isInt()
		|| !_jret["auth_type"].isInt()
		|| !_jret["protocol_flag"].isUInt()
		|| !_jret["record_flag"].isUInt()
		|| !_jret["_enc"].isInt()

		|| !_jret["user_username"].isString()
		|| !_jret["host_ip"].isString()
		|| !_jret["conn_ip"].isString()
		|| !_jret["client_ip"].isString()
		|| !_jret["acc_username"].isString()
		|| !_jret["acc_secret"].isString()
		|| !_jret["username_prompt"].isString()
		|| !_jret["password_prompt"].isString()
		)
	{
		EXLOGE("got connection info from web-server, but not all info valid.\n");
		return TPE_PARAM;
	}
	
	int user_id;
	int host_id;
	int acc_id;
	ex_astr user_username;// 申请本次连接的用户名
	ex_astr host_ip;// 真正的远程主机IP（如果是直接连接模式，则与remote_host_ip相同）
	ex_astr conn_ip;// 要连接的远程主机的IP（如果是端口映射模式，则为路由主机的IP）
	int conn_port;// 要连接的远程主机的端口（如果是端口映射模式，则为路由主机的端口）
	ex_astr client_ip;
	ex_astr acc_username;	// 远程主机的账号
	ex_astr acc_secret;// 远程主机账号的密码（或者私钥）
	ex_astr username_prompt;
	ex_astr password_prompt;
	int protocol_type = 0;
	int protocol_sub_type = 0;
	int auth_type = 0;
	int protocol_flag = 0;
	int record_flag = 0;
	bool _enc;

	user_id = _jret["user_id"].asInt();
	host_id = _jret["host_id"].asInt();
	acc_id = _jret["acc_id"].asInt();
	user_username = _jret["user_username"].asString();
	host_ip = _jret["host_ip"].asString();
	conn_ip = _jret["conn_ip"].asString();
	conn_port = _jret["conn_port"].asInt();
	client_ip = _jret["client_ip"].asString();
	acc_username = _jret["acc_username"].asString();
	acc_secret = _jret["acc_secret"].asString();
	username_prompt = _jret["username_prompt"].asString();
	password_prompt = _jret["password_prompt"].asString();
	protocol_type = _jret["protocol_type"].asInt();
	protocol_sub_type = _jret["protocol_sub_type"].asInt();
	protocol_flag = _jret["protocol_flag"].asUInt();
	record_flag = _jret["record_flag"].asUInt();
	auth_type = _jret["auth_type"].asInt();
	_enc = _jret["_enc"].asBool();


	// 进一步判断参数是否合法
	// 注意，account_id可以为-1，表示这是一次测试连接。
	if (user_id <= 0 || host_id <= 0
		|| user_username.length() == 0
		|| host_ip.length() == 0 || conn_ip.length() == 0 || client_ip.length() == 0
		|| conn_port <= 0 || conn_port >= 65535
		|| acc_username.length() == 0 || acc_secret.length() == 0
		|| !(protocol_type == TP_PROTOCOL_TYPE_RDP || protocol_type == TP_PROTOCOL_TYPE_SSH || protocol_type == TP_PROTOCOL_TYPE_TELNET)
		|| !(auth_type == TP_AUTH_TYPE_NONE || auth_type == TP_AUTH_TYPE_PASSWORD || auth_type == TP_AUTH_TYPE_PRIVATE_KEY)
		)
	{
		return TPE_PARAM;
	}

	if (_enc) {
		ex_astr _auth;
		if (!ts_db_field_decrypt(acc_secret, _auth))
			return TPE_FAILED;

		acc_secret = _auth;
	}

	info.user_id = user_id;
	info.host_id = host_id;
	info.acc_id = acc_id;
	info.user_username = user_username;
	info.host_ip = host_ip;
	info.conn_ip = conn_ip;
	info.conn_port = conn_port;
	info.client_ip = client_ip;
	info.acc_username = acc_username;
	info.acc_secret = acc_secret;
	info.username_prompt = username_prompt;
	info.password_prompt = password_prompt;
	info.protocol_type = protocol_type;
	info.protocol_sub_type = protocol_sub_type;
	info.auth_type = auth_type;
	info.protocol_flag = protocol_flag;
	info.record_flag = record_flag;

	return TPE_OK;
}

bool ts_web_rpc_session_begin(TS_CONNECT_INFO& info, int& record_id)
{
	Json::FastWriter json_writer;
	Json::Value jreq;

	jreq["method"] = "session_begin";
	jreq["param"]["sid"] = info.sid.c_str();
	jreq["param"]["user_id"] = info.user_id;
	jreq["param"]["host_id"] = info.host_id;
	jreq["param"]["acc_id"] = info.acc_id;
	jreq["param"]["user_username"] = info.user_username.c_str();
	jreq["param"]["acc_username"] = info.acc_username.c_str();
	jreq["param"]["host_ip"] = info.host_ip.c_str();
	jreq["param"]["conn_ip"] = info.conn_ip.c_str();
	jreq["param"]["client_ip"] = info.client_ip.c_str();
	//jreq["param"]["sys_type"] = info.sys_type;
	jreq["param"]["conn_port"] = info.conn_port;
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

bool ts_web_rpc_session_update(int record_id, int protocol_sub_type, int state) {
	Json::FastWriter json_writer;
	Json::Value jreq;
	jreq["method"] = "session_update";
	jreq["param"]["rid"] = record_id;
	jreq["param"]["protocol_sub_type"] = protocol_sub_type;
	jreq["param"]["code"] = state;

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
