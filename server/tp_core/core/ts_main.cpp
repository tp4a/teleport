#include "ts_main.h"
#include "ts_session.h"
#include "ts_http_rpc.h"
#include "ts_db.h"
#include "ts_env.h"
//#include "ts_http_client.h"
//#include "ts_ver.h"
//#include "ts_crypto.h"

//#include "../common/protocol_interface.h"


#include <mbedtls/platform.h>
#include <mbedtls/debug.h>
//#include <list>

bool g_exit_flag = false;

//static unsigned char ToHex(unsigned char x)
//{
//	return  x > 9 ? x + 55 : x + 48;
//}
//
//ex_astr UrlEncode(const ex_astr& str)
//{
//	ex_astr strTemp = "";
//	size_t length = str.length();
//	for (size_t i = 0; i < length; i++)
//	{
//		if (isalnum((unsigned char)str[i]) ||
//			(str[i] == '-') ||
//			(str[i] == '_') ||
//			(str[i] == '.') ||
//			(str[i] == '~'))
//		{
//			strTemp += str[i];
//		}
//		else if (str[i] == ' ')
//		{
//			strTemp += "+";
//		}
//		else
//		{
//			strTemp += '%';
//			strTemp += ToHex((unsigned char)str[i] >> 4);
//			strTemp += ToHex((unsigned char)str[i] % 16);
//		}
//	}
//
//	return strTemp;
//}

bool tpp_take_session(const ex_astr& sid, TS_SESSION_INFO& info)
{
	return g_session_mgr.take_session(sid, info);
}

bool tpp_session_begin(TS_SESSION_INFO& info, int& db_id)
{
	return g_db.session_begin(info, db_id);
}

bool tpp_session_end(int db_id, int ret)
{
	return g_db.session_end(db_id, ret);
}

typedef struct TPP_LIB
{
	TPP_LIB()
	{
		dylib = NULL;
		init = NULL;
	}
	~TPP_LIB()
	{
		if (NULL != dylib)
			ex_dlclose(dylib);
		dylib = NULL;
	}

	EX_DYLIB_HANDLE dylib;
	TPP_INIT_FUNC init;
	TPP_START_FUNC start;
	TPP_STOP_FUNC stop;
}TPP_LIB;

typedef std::list<TPP_LIB*> tpp_libs;

class TppManager
{
public:
	TppManager()
	{
	}
	~TppManager()
	{
		tpp_libs::iterator it = m_libs.begin();
		for (; it != m_libs.end(); ++it)
		{
			delete (*it);
		}
		m_libs.clear();
	}

	bool load_tpp(const ex_wstr& libfile);
	void stop_all(void);
	int count(void) { return m_libs.size(); }

private:
	tpp_libs m_libs;
};

static TppManager g_tpp_mgr;
extern ExLogger g_ex_logger;

bool TppManager::load_tpp(const ex_wstr& libname)
{
	ex_wstr filename;
#ifdef EX_OS_WIN32
	filename = libname + L".dll";
#else
    filename = L"lib";
    filename += libname;
	filename += L".so";
#endif

	ex_wstr libfile = g_env.m_exec_path;
	ex_path_join(libfile, false, filename.c_str(), NULL);
	EXLOGV(L"[core] load protocol lib: %ls\n", libfile.c_str());

	TPP_LIB* lib = new  TPP_LIB;

	lib->dylib = ex_dlopen(libfile.c_str());
	if (NULL == lib->dylib)
	{
		EXLOGE(L"[core] load dylib `%ls` failed, maybe it not exists.\n", libfile.c_str());
		delete lib;
		return false;
	}

#ifdef EX_OS_WIN32
	lib->init = (TPP_INIT_FUNC)GetProcAddress(lib->dylib, "tpp_init");
	lib->start = (TPP_START_FUNC)GetProcAddress(lib->dylib, "tpp_start");
	lib->stop = (TPP_STOP_FUNC)GetProcAddress(lib->dylib, "tpp_stop");
#else
    lib->init = (TPP_INIT_FUNC)dlsym(lib->dylib, "tpp_init");
    lib->start = (TPP_START_FUNC)dlsym(lib->dylib, "tpp_start");
    lib->stop = (TPP_STOP_FUNC)dlsym(lib->dylib, "tpp_stop");
#endif

	if (lib->init == NULL || lib->start == NULL || lib->stop == NULL)
	{
		EXLOGE(L"[core] load dylib `%ls` failed, can not locate all functions.\n", libfile.c_str());
		delete lib;
		return false;
	}

	TPP_INIT_ARGS init_args;
	init_args.logger = &g_ex_logger;
	init_args.exec_path = g_env.m_exec_path;
	init_args.etc_path = g_env.m_etc_path;
	init_args.cfg = &g_env.get_ini();
	init_args.func_take_session = tpp_take_session;
	init_args.func_session_begin = tpp_session_begin;
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

void TppManager::stop_all(void)
{
	tpp_libs::iterator it = m_libs.begin();
	for (; it != m_libs.end(); ++it)
	{
		(*it)->stop();
	}
}

int ts_main(void)
{
	EXLOGI("\n");
	EXLOGI("###############################################################\n");
	EXLOGI("Teleport Core Server starting ...\n");

	ExIniFile& ini = g_env.get_ini();
	ex_ini_sections& secs = ini.GetAllSections();
	TsHttpRpc rpc;

	// 枚举配置文件中的[protocol-xxx]小节，加载对应的协议动态库
	bool all_ok = true;

	do {
		if (!g_session_mgr.start())
		{
			EXLOGE("[core] failed to start session-id manager.\n");
			all_ok = false;
			break;
		}

		if (!rpc.init() || !rpc.start())
		{
			EXLOGE("[core] rpc init/start failed.\n");
			all_ok = false;
			break;
		}

		ex_ini_sections::iterator it = secs.begin();
		for (; it != secs.end(); ++it)
		{
			if (it->first.length() > 9 && 0 == wcsncmp(it->first.c_str(), L"protocol-", 9))
			{
				ex_wstr libname;
				if (!it->second->GetStr(L"lib", libname))
					continue;

				bool enabled = false;
				it->second->GetBool(L"enabled", enabled, false);
				if (!enabled)
				{
					EXLOGV(L"[core] `%ls` not enabled.\n", libname.c_str());
					continue;
				}

				if (!g_tpp_mgr.load_tpp(libname))
				{
					all_ok = false;
					break;
				}
			}
		}

	} while (0);

	if (0 == g_tpp_mgr.count())
	{
		all_ok = false;
	}

	if (!all_ok)
	{
		g_exit_flag = true;
	}







	// 	if (!g_cfg.init())
	// 	{
	// // 		EXLOGE("[ERROR] can not load configuration.\n");
	// 		return 1;
	// 	}
	// 	//TS_DB_AUTH_INFO info;
	// 	//g_db.get_auth_info(17, info);
	g_db.update_reset_log();

	//mbedtls_debug_set_threshold(9999);

	EXLOGV("[core] ---- initialized, ready for service ----\n");

	while (!g_exit_flag)
	{
		ex_sleep_ms(1000);
	}

	g_tpp_mgr.stop_all();
	rpc.stop();
	g_session_mgr.stop();

	return 0;
}
