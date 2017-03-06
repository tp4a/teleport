#include "ts_web_rpc.h"
#include "ts_env.h"
#include "ts_http_client.h"

#include "../common/ts_const.h"

#include <ex/ex_str.h>

bool ts_web_rpc_register_core()
{
	Json::FastWriter json_writer;
	Json::Value jreq;
	jreq["method"] = "register";
	jreq["param"]["ip"] = g_env.rpc_bind_ip.c_str();
	jreq["param"]["port"] = g_env.rpc_bind_port;

	ex_astr json_param;
	json_param = json_writer.write(jreq);

	ex_astr param;
	ts_url_encode(json_param.c_str(), param);

	ex_astr url = "http://127.0.0.1:7190/rpc?";
	url += param;

	ex_astr body;
	return ts_http_get(url, body);
}

bool ts_web_rpc_get_auth_info(int auth_id, Json::Value& jret)
{
	Json::FastWriter json_writer;
	Json::Value jreq;
	jreq["method"] = "get_auth_info";
	jreq["param"]["authid"] = auth_id;

	ex_astr json_param;
	json_param = json_writer.write(jreq);

	ex_astr param;
	ts_url_encode(json_param.c_str(), param);
	ex_astr url = "http://127.0.0.1:7190/rpc?";
	url += param;

	ex_astr body;
	if (!ts_http_get(url, body))
	{
// 		EXLOGV("request `get_auth_info` from web return: ");
// 		EXLOGV(body.c_str());
// 		EXLOGV("\n");
		return false;
	}

	Json::Reader jreader;

	if (!jreader.parse(body.c_str(), jret))
		return false;
	if (!jret.isObject())
		return false;
	if (!jret["data"].isObject())
		return false;

	Json::Value& _jret = jret["data"];

	if (
		!_jret["host_ip"].isString()
		|| !_jret["host_port"].isInt()
		|| !_jret["sys_type"].isInt()
		|| !_jret["protocol"].isInt()
		|| !_jret["auth_mode"].isInt()
		|| !_jret["account_lock"].isInt()
		|| !_jret["user_name"].isString()
		|| !_jret["user_auth"].isString()
		|| !_jret["user_param"].isString()
		|| !_jret["account_name"].isString()
		)
	{
		return false;
	}

	return true;
}

bool ts_web_rpc_session_begin(TS_SESSION_INFO& info, int& record_id)
{
	Json::FastWriter json_writer;
	Json::Value jreq;

	jreq["method"] = "session_begin";
	jreq["param"]["sid"] = info.sid.c_str();
	jreq["param"]["account_name"] = info.account_name.c_str();
	jreq["param"]["host_ip"] = info.host_ip.c_str();
	jreq["param"]["sys_type"] = info.sys_type;
	jreq["param"]["host_port"] = info.host_port;
	jreq["param"]["auth_mode"] = info.auth_mode,
	jreq["param"]["user_name"] = info.user_name.c_str();
	jreq["param"]["protocol"] = info.protocol;

	ex_astr json_param;
	json_param = json_writer.write(jreq);

	ex_astr param;
	ts_url_encode(json_param.c_str(), param);
	ex_astr url = "http://127.0.0.1:7190/rpc?";
	url += param;

	ex_astr body;
	if (!ts_http_get(url, body))
	{
		// 		EXLOGV("request `get_auth_info` from web return: ");
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

//session ½áÊø
bool ts_web_rpc_session_end(int record_id, int ret_code)
{
	Json::FastWriter json_writer;
	Json::Value jreq;
	jreq["method"] = "session_end";
	jreq["param"]["rid"] = record_id;
	jreq["param"]["code"] = ret_code;

	ex_astr json_param;
	json_param = json_writer.write(jreq);

	ex_astr param;
	ts_url_encode(json_param.c_str(), param);
	ex_astr url = "http://127.0.0.1:7190/rpc?";
	url += param;

// 	ex_astr param;
// 	ts_url_encode("{\"method\":\"session_end\",\"param\":[]}", param);
// 	ex_astr url = "http://127.0.0.1:7190/rpc?";
// 	url += param;

	ex_astr body;
	return ts_http_get(url, body);
}
