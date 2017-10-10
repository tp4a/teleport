//#include "stdafx.h"
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

//	if (!ex_exec_file(m_exec_file))
//		return false;
//
//	m_exec_path = m_exec_file;
//	if (!ex_dirname(m_exec_path))
//		return false;
//
//	m_ssh_client_conf_file = m_exec_path;
//	ex_path_join(m_ssh_client_conf_file, false, L"cfg", L"ssh.ini", NULL);
//
//	m_scp_client_conf_file = m_exec_path;
//	ex_path_join(m_scp_client_conf_file, false, L"cfg", L"scp.ini", NULL);
//
//	m_telnet_client_conf_file = m_exec_path;
//	ex_path_join(m_telnet_client_conf_file, false, L"cfg", L"telnet.ini", NULL);
//
//	m_log_path = m_exec_path;
//	ex_path_join(m_log_path, false, L"log", NULL);

#ifdef EX_DEBUG
	m_site_path = L"/Users/apex/work/eomsoft/teleport-dev/client/tp_assist_macos/site";
#else
	m_site_path = m_res_path;
	ex_path_join(m_res_path, false, L"site", NULL);
#endif
	
//	m_tools_path = m_exec_path;
//	ex_path_join(m_tools_path, false, L"tools", NULL);

	return true;
}
