#ifndef __TPP_ENV_H__
#define __TPP_ENV_H__

#include "../../common/base_env.h"

class TppSshEnv : public TppEnvBase
{
public:
	TppSshEnv();
	~TppSshEnv();

public:
	ex_astr bind_ip;
	int bind_port;

private:
	bool _on_init(TPP_INIT_ARGS* args);
};

extern TppSshEnv g_ssh_env;

#endif // __TPP_ENV_H__
