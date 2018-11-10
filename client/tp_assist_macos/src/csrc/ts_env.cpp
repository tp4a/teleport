#include "ts_env.h"

#include <time.h>
#ifdef EX_OS_WIN32
#	include <direct.h>
//#	include <ShlObj.h>
#endif

TsEnv g_env;

//=======================================================
//
//=======================================================

TsEnv::TsEnv()
{}

TsEnv::~TsEnv()
{}

bool TsEnv::init(const char* cfg_file, const char* res_path)
{
	ex_astr2wstr(cfg_file, m_cfg_file);
	ex_astr2wstr(res_path, m_res_path);

#ifdef EX_DEBUG
    m_site_path = L"/Users/apex/work/tp4a/teleport/client/tp_assist_macos/site";
#else
	m_site_path = m_res_path;
	ex_path_join(m_site_path, false, L"site", NULL);
#endif
	
	return true;
}
