#include "tp_tpp_mgr.h"
#include "ts_main.h"
// #include "ts_session.h"
// #include "ts_http_rpc.h"
// #include "ts_web_rpc.h"
#include "ts_env.h"

// #include <mbedtls/platform.h>
// #include <mbedtls/debug.h>

TppManager g_tpp_mgr;

extern ExLogger g_ex_logger;

bool TppManager::load_tpp(const ex_wstr& libname)
{
	ex_wstr filename;
#ifdef EX_OS_WIN32
	filename = libname + L".dll";
#elif defined (EX_OS_LINUX)
    filename = L"lib";
    filename += libname;
	filename += L".so";
#elif defined (EX_OS_MACOS)
	filename = L"lib";
    filename += libname;
	filename += L".dylib";
#endif

	ex_wstr libfile = g_env.m_exec_path;
	ex_path_join(libfile, false, filename.c_str(), NULL);
	EXLOGV(L"[core] load protocol lib: %ls\n", libfile.c_str());

	TPP_LIB* lib = new TPP_LIB;

	lib->dylib = ex_dlopen(libfile.c_str());
	if (NULL == lib->dylib)
	{
		EXLOGE(L"[core] load dylib `%ls` failed.\n", libfile.c_str());
		delete lib;
		return false;
	}

#ifdef EX_OS_WIN32
	lib->init = (TPP_INIT_FUNC)GetProcAddress(lib->dylib, "tpp_init");
	lib->start = (TPP_START_FUNC)GetProcAddress(lib->dylib, "tpp_start");
	lib->stop = (TPP_STOP_FUNC)GetProcAddress(lib->dylib, "tpp_stop");
	lib->timer = (TPP_TIMER_FUNC)GetProcAddress(lib->dylib, "tpp_timer");
// 	lib->set_cfg = (TPP_SET_CFG_FUNC)GetProcAddress(lib->dylib, "tpp_set_cfg");
	lib->command = (TPP_COMMAND_FUNC)GetProcAddress(lib->dylib, "tpp_command");
#else
    lib->init = (TPP_INIT_FUNC)dlsym(lib->dylib, "tpp_init");
    lib->start = (TPP_START_FUNC)dlsym(lib->dylib, "tpp_start");
	lib->stop = (TPP_STOP_FUNC)dlsym(lib->dylib, "tpp_stop");
	lib->timer = (TPP_TIMER_FUNC)dlsym(lib->dylib, "tpp_timer");
// 	lib->set_cfg = (TPP_SET_CFG_FUNC)dlsym(lib->dylib, "tpp_set_cfg");
	lib->command = (TPP_COMMAND_FUNC)dlsym(lib->dylib, "tpp_command");
#endif

	if (
		lib->init == NULL
		|| lib->start == NULL
		|| lib->stop == NULL
		|| lib->timer == NULL
		//|| lib->set_cfg == NULL
		|| lib->command == NULL
		)
	{
		EXLOGE(L"[core] load dylib `%ls` failed, can not locate all functions.\n", libfile.c_str());
		delete lib;
		return false;
	}

	TPP_INIT_ARGS init_args;
	init_args.logger = &g_ex_logger;
	init_args.exec_path = g_env.m_exec_path;
	init_args.etc_path = g_env.m_etc_path;
	init_args.replay_path = g_env.m_replay_path;
	init_args.cfg = &g_env.get_ini();
	init_args.func_get_connect_info = tpp_get_connect_info;
	init_args.func_free_connect_info = tpp_free_connect_info;
	init_args.func_session_begin = tpp_session_begin;
	init_args.func_session_update = tpp_session_update;
	init_args.func_session_end = tpp_session_end;

	if (EXRV_OK != lib->init(&init_args))
	{
		EXLOGE(L"[core] failed to init protocol `%ls`.\n", libname.c_str());
		delete lib;
		return false;
	}
	if (EXRV_OK != lib->start())
	{
		EXLOGE(L"[core] failed to start protocol `%ls`.\n", libname.c_str());
		delete lib;
		return false;
	}

	m_libs.push_back(lib);
	return true;
}

void TppManager::stop_all(void) {
	tpp_libs::iterator it = m_libs.begin();
	for (; it != m_libs.end(); ++it)
	{
		(*it)->stop();
	}
}

void TppManager::timer(void) {
	tpp_libs::iterator it = m_libs.begin();
	for (; it != m_libs.end(); ++it)
	{
		(*it)->timer();
	}
}

// void TppManager::set_config(int noop_timeout) {
// 
// 	TPP_SET_CFG_ARGS args;
// 	args.noop_timeout = noop_timeout;
// 
// 	tpp_libs::iterator it = m_libs.begin();
// 	for (; it != m_libs.end(); ++it)
// 	{
// 		(*it)->set_cfg(&args);
// 	}
// }

void TppManager::set_runtime_config(const ex_astr& sp) {
	tpp_libs::iterator it = m_libs.begin();
	for (; it != m_libs.end(); ++it) {
		(*it)->command(TPP_CMD_SET_RUNTIME_CFG, sp.c_str());
	}
}

void TppManager::kill_sessions(const ex_astr& sp) {
	tpp_libs::iterator it = m_libs.begin();
	for (; it != m_libs.end(); ++it) {
		(*it)->command(TPP_CMD_KILL_SESSIONS, sp.c_str());
	}
}

