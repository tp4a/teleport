#include "stdafx.h"
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

bool TsEnv::init(void)
{
	if (!ex_exec_file(m_exec_file))
		return false;

	m_exec_path = m_exec_file;
	if (!ex_dirname(m_exec_path))
		return false;

	m_cfg_file = m_exec_path;
	ex_path_join(m_cfg_file, false, L"cfg", L"tp-assist.json", NULL);

	m_log_path = m_exec_path;
	ex_path_join(m_log_path, false, L"log", NULL);

	ex_wstr cfg_default;

#ifdef _DEBUG
	m_site_path = m_exec_path;
	ex_path_join(m_site_path, true, L"..", L"..", L"..", L"..", L"client", L"tp_assist_win", L"site", NULL);

	m_tools_path = m_exec_path;
	ex_path_join(m_tools_path, true, L"..", L"..", L"..", L"..", L"client", L"tools", NULL);

	cfg_default = m_exec_path;
	ex_path_join(cfg_default, true, L"..", L"..", L"..", L"..", L"client", L"tp_assist_win", L"cfg", L"tp-assist.default.json", NULL);

#else
	m_site_path = m_exec_path;
	ex_path_join(m_site_path, false, L"site", NULL);

	m_tools_path = m_exec_path;
	ex_path_join(m_tools_path, false, L"tools", NULL);

	cfg_default = m_exec_path;
	ex_path_join(cfg_default, false, L"tp-assist.default.json", NULL);
#endif

	if (!ex_is_file_exists(m_cfg_file.c_str())) {
		ex_wstr cfg_path = m_exec_path;
		ex_path_join(cfg_path, false, L"cfg", NULL);

		ex_mkdirs(cfg_path);

		if (!ex_copy_file(cfg_default.c_str(), m_cfg_file.c_str()))
			return false;
}

	return true;
}
