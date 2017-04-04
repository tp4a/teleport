#ifndef __TS_ENV_H__
#define __TS_ENV_H__

#include <ex.h>

class TsEnv
{
public:
	TsEnv();
	~TsEnv();

	bool init(bool load_config);

public:
	ex_wstr m_exec_file;
	ex_wstr m_exec_path;
	ex_wstr m_www_path;
};

extern TsEnv g_env;

#endif // __TS_ENV_H__
