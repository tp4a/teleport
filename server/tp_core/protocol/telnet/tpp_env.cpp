#include "tpp_env.h"

TppTelnetEnv g_telnet_env;

TppTelnetEnv::TppTelnetEnv()
{}

TppTelnetEnv::~TppTelnetEnv()
{}

bool TppTelnetEnv::_on_init(TPP_INIT_ARGS* args) {
	ex_path_join(replay_path, false, L"telnet", NULL);

	ExIniSection* ps = args->cfg->GetSection(L"protocol-telnet");
	if (NULL == ps) {
		EXLOGE("[telnet] invalid config(2).\n");
		return false;
	}

	ex_wstr tmp;
	if (!ps->GetStr(L"bind-ip", tmp)) {
		bind_ip = TS_TELNET_PROXY_HOST;
	}
	else {
		ex_wstr2astr(tmp, bind_ip);
	}

	if (!ps->GetInt(L"bind-port", bind_port)) {
		bind_port = TS_TELNET_PROXY_PORT;
	}

	return true;
}
