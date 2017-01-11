#ifndef __TPP_ENV_H__
#define __TPP_ENV_H__

#include "../../common/base_env.h"

class TppEnv : public TppEnvBase
{
public:
	TppEnv();
	~TppEnv();

public:
	ex_astr bind_ip;
	int bind_port;

private:
	bool _on_init(TPP_INIT_ARGS* args);
};

extern TppEnv g_ssh_env;

#endif // __TPP_ENV_H__
