#include "stdafx.h"
#include "ts_env.h"

#include <time.h>
#ifdef EX_OS_WIN32
#	include <direct.h>
#endif

TsEnv g_env;

//=======================================================
//
//=======================================================

TsEnv::TsEnv()
{}

TsEnv::~TsEnv()
{}

bool TsEnv::init(void)
{
	if (!ex_exec_file(m_exec_file))
		return false;

	m_exec_path = m_exec_file;
	if (!ex_dirname(m_exec_path))
		return false;

	m_ssh_client_conf_file = m_exec_path;
	ex_path_join(m_ssh_client_conf_file, false, _T("ssh_client.ini"), NULL);

	m_scp_client_conf_file = m_exec_path;
	ex_path_join(m_scp_client_conf_file, false, _T("scp_client.ini"), NULL);
	
	m_telnet_client_conf_file = m_exec_path;
	ex_path_join(m_telnet_client_conf_file, false, _T("telnet_client.ini"), NULL);

	m_log_path = m_exec_path;
	ex_path_join(m_log_path, false, _T("log"), NULL);

	m_site_path = m_exec_path;
	ex_path_join(m_site_path, false, _T("site"), NULL);
	
	m_tools_path = m_exec_path;
	ex_path_join(m_tools_path, false, _T("tools"), NULL);

	return true;
}
