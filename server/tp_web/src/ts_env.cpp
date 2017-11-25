#include "ts_env.h"

TsEnv g_env;

TsEnv::TsEnv()
{}

TsEnv::~TsEnv()
{}

bool TsEnv::init(bool load_config)
{
	EXLOG_LEVEL(EX_LOG_LEVEL_INFO);

	ex_exec_file(m_exec_file);

	m_exec_path = m_exec_file;
	ex_dirname(m_exec_path);

	if (!load_config)
		return true;

    // check development flag file, if exists, run in development mode for trace and debug.
    ex_wstr dev_flag_file = m_exec_path;
    ex_path_join(dev_flag_file, false, L"dev_mode", NULL);

	ex_wstr base_path = m_exec_path;
    ex_wstr log_path;
    ex_wstr conf_file;

    if (ex_is_file_exists(dev_flag_file.c_str()))
	{
        EXLOGW("===== DEVELOPMENT MODE =====\n");

        ex_path_join(base_path, true, L"..", L"..", L"..", L"..", L"server", NULL);
        conf_file = base_path;
        ex_path_join(conf_file, false, L"share", L"etc", L"web.ini", NULL);

        log_path = base_path;
		ex_path_join(log_path, false, L"share", L"log", NULL);
	}
	else	// not in development mode
	{
		base_path = m_exec_path;
		ex_path_join(base_path, true, L"..", NULL);

// #ifdef EX_OS_WIN32
		conf_file = base_path;
		ex_path_join(conf_file, false, L"data", L"etc", L"web.ini", NULL);
		log_path = base_path;
		ex_path_join(log_path, false, L"data", L"log", NULL);
// #else
// 		conf_file = L"/etc/teleport/web.ini";
// 		log_path = L"/var/log/teleport";
// 
// #endif
	}

	m_www_path = base_path;
	ex_path_join(m_www_path, false, L"www", NULL);

	if (!ex_is_file_exists(conf_file.c_str()))
	{
		EXLOGE(L"[tpweb] `%s` not found.\n", conf_file.c_str());
		return false;
	}

	ExIniFile cfg;
	if (!cfg.LoadFromFile(conf_file))
	{
		EXLOGE("[tpweb] can not load web.ini.\n");
		return false;
	}

	ex_wstr log_file;
	// 	ExIniSection* ps = cfg.GetDumySection();
	ExIniSection* ps = cfg.GetSection(L"common");
	if (NULL == ps)
		ps = cfg.GetDumySection();
	if (!ps->GetStr(L"log-file", log_file))
	{
		EXLOG_FILE(L"tpweb.log", log_path.c_str());
	}
	else
	{
		ex_remove_white_space(log_file);
		if (log_file[0] == L'"' || log_file[0] == L'\'')
			log_file.erase(0, 1);
		if (log_file[ log_file.length() - 1 ] == L'"' || log_file[log_file.length() - 1] == L'\'')
			log_file.erase(log_file.length() - 1, 1);

		log_path = log_file;
		ex_dirname(log_path);
		ex_wstr file_name;
		file_name.assign(log_file, log_path.length() + 1, log_file.length());

		EXLOG_FILE(file_name.c_str(), log_path.c_str());
	}

	int log_level = EX_LOG_LEVEL_INFO;
	if (ps->GetInt(L"log-level", log_level))
	{
		EXLOG_LEVEL(log_level);
	}

	int debug_mode = 0;
	if (ps->GetInt(L"debug-mode", debug_mode))
	{
		if (1 == debug_mode) {
            EXLOG_LEVEL(EX_LOG_LEVEL_DEBUG);
            EXLOG_DEBUG(true);
		}
	}

	return true;
}
