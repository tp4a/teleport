#include "ssh_proxy.h"
#include "tpp_env.h"

#include <teleport_const.h>
#include <json/json.h>

TPP_API ex_rv tpp_init(TPP_INIT_ARGS* init_args)
{
#ifdef EX_OS_UNIX
	ssh_threads_set_callbacks(ssh_threads_get_pthread());
	ssh_init();
#else
	ssh_init();
#endif

	if (!g_ssh_env.init(init_args))
		return TPE_FAILED;

	return 0;
}

TPP_API ex_rv tpp_start(void)
{
	if (!g_ssh_proxy.init())
		return TPE_FAILED;
	if (!g_ssh_proxy.start())
		return TPE_FAILED;

	return 0;
}

TPP_API ex_rv tpp_stop(void)
{
	g_ssh_proxy.stop();
	return 0;
}

TPP_API void tpp_timer(void) {
	// be called per one second.
	g_ssh_proxy.timer();
}

// TPP_API void tpp_set_cfg(TPP_SET_CFG_ARGS* cfg_args) {
// 	//g_ssh_proxy.set_cfg(cfg_args);
// }

static ex_rv _set_runtime_config(const char* param) {
	Json::Value jp;
	Json::Reader jreader;

	if (!jreader.parse(param, jp))
		return TPE_JSON_FORMAT;

	if (!jp.isObject())
		return TPE_PARAM;

	if (jp["noop_timeout"].isNull() || !jp["noop_timeout"].isUInt())
		return TPE_PARAM;

	ex_u32 noop_timeout = jp["noop_timeout"].asUInt();
	if (noop_timeout == 0)
		return TPE_PARAM;

	g_ssh_proxy.set_cfg(noop_timeout * 60);

	return TPE_PARAM;
}

static ex_rv _kill_sessions(const char* param) {
	Json::Value jp;
	Json::Reader jreader;

	if (!jreader.parse(param, jp))
		return TPE_JSON_FORMAT;

	if (!jp.isArray())
		return TPE_PARAM;

	ex_astrs ss;
	int cnt = jp.size();
	for (int i = 0; i < cnt; ++i)
	{
		if (!jp[i].isString()) {
			return TPE_PARAM;
		}

		ss.push_back(jp[i].asString());
	}

	g_ssh_proxy.kill_sessions(ss);

	return TPE_PARAM;
}

TPP_API ex_rv tpp_command(ex_u32 cmd, const char* param) {
	switch (cmd) {
	case TPP_CMD_SET_RUNTIME_CFG:
		if (param == NULL || strlen(param) == 0)
			return TPE_PARAM;
		return _set_runtime_config(param);
	case TPP_CMD_KILL_SESSIONS:
		if (param == NULL || strlen(param) == 0)
			return TPE_PARAM;
		return _kill_sessions(param);
	default:
		return TPE_UNKNOWN_CMD;
	}

	return TPE_NOT_IMPLEMENT;
}
