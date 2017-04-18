#ifndef __TS_ENV_H__
#define __TS_ENV_H__

#include <ex.h>

class TsEnv
{
public:
	TsEnv();
	~TsEnv();

	bool init(bool load_config);

	ExIniFile& get_ini(void) { return m_ini; }

public:
	ex_wstr m_exec_file;
	ex_wstr m_exec_path;
	ex_wstr m_etc_path;
	ex_wstr m_replay_path;

	ex_astr rpc_bind_ip;
	int rpc_bind_port;

	ex_astr web_server_rpc;
	ex_astr core_server_rpc;

private:
	ExIniFile m_ini;
};

extern TsEnv g_env;

#endif // __TS_ENV_H__
