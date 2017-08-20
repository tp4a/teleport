#include "ts_web_rpc.h"
#include "ts_env.h"
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

int ts_web_rpc_get_conn_info(int conn_id, Json::Value& jret)
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

	if (!jreader.parse(body.c_str(), jret))
		return TPE_PARAM;
	if (!jret.isObject())
		return TPE_PARAM;
	if (!jret["data"].isObject())
		return TPE_PARAM;

	Json::Value& _jret = jret["data"];

	if (
		!_jret["host_ip"].isString()
		|| !_jret["host_port"].isInt()
//		|| !_jret["sys_type"].isInt()

		|| !_jret["protocol_type"].isInt()
		|| !_jret["protocol_sub_type"].isInt()
		|| !_jret["auth_type"].isInt()
		|| !_jret["account_name"].isString()
		|| !_jret["secret"].isString()
//		|| !_jret["user_param"].isString()
//		|| !_jret["conn_param"].isInt()

		|| !_jret["user_name"].isString()
		|| !_jret["client_ip"].isString()

		|| !_jret["_enc"].isInt()
		|| !_jret["_test"].isInt()
		)
	{
		EXLOGE("got connection info from web-server, but not all info valid.\n");
		return TPE_PARAM;
	}

	return TPE_OK;
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

	ex_astr url = g_env.web_server_rpc;
	url += "?";
	url += param;

	ex_astr body;
	return ts_http_get(url, body);
}
