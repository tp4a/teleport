#ifndef __TPP_ENV_H__
#define __TPP_ENV_H__

#include "../../common/base_env.h"

class TppTelnetEnv : public TppEnvBase
{
public:
	TppTelnetEnv();
	~TppTelnetEnv();

public:
	ex_astr bind_ip;
	int bind_port;

private:
	bool _on_init(TPP_INIT_ARGS* args);
};

extern TppTelnetEnv g_telnet_env;

#endif // __TPP_ENV_H__
