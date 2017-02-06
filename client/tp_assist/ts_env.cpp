#include "stdafx.h"
#include "ts_env.h"

#include <time.h>
#ifdef EX_OS_WIN32
#	include <direct.h>
#	include <ShlObj.h>
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

	TCHAR szBuf[PATH_MAX] = { 0 };
	SHGetSpecialFolderPathW(NULL, szBuf, CSIDL_APPDATA, FALSE);

	m_ssh_client_conf_file = szBuf;// m_exec_path;
	ex_path_join(m_ssh_client_conf_file, false, _T("eomsoft"), _T("teleport"), _T("assist"), _T("cfg"), _T("ssh.ini"), NULL);

	m_scp_client_conf_file = szBuf;// m_exec_path;
	ex_path_join(m_scp_client_conf_file, false, _T("eomsoft"), _T("teleport"), _T("assist"), _T("cfg"), _T("scp.ini"), NULL);
	
	m_telnet_client_conf_file = szBuf;// m_exec_path;
	ex_path_join(m_telnet_client_conf_file, false, _T("eomsoft"), _T("teleport"), _T("assist"), _T("cfg"), _T("telnet.ini"), NULL);

	m_log_path = szBuf;// m_exec_path;
	ex_path_join(m_log_path, false, _T("eomsoft"), _T("teleport"), _T("assist"), _T("log"), NULL);

	m_site_path = m_exec_path;
	ex_path_join(m_site_path, false, _T("site"), NULL);
	
	m_tools_path = m_exec_path;
	ex_path_join(m_tools_path, false, _T("tools"), NULL);

	return true;
}
