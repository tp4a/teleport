#include "ts_main.h"
#include "ts_session.h"
#include "ts_http_rpc.h"
#include "ts_web_rpc.h"
#include "ts_env.h"
#include "tp_tpp_mgr.h"

#include <mbedtls/platform.h>
#include <mbedtls/debug.h>

bool g_exit_flag = false;

TPP_CONNECT_INFO *tpp_get_connect_info(const char *sid) {
    TS_CONNECT_INFO sinfo;
    bool ret = g_session_mgr.get_connect_info(sid, sinfo);
    if (!ret)
        return NULL;

    TPP_CONNECT_INFO *info = (TPP_CONNECT_INFO *) calloc(1, sizeof(TPP_CONNECT_INFO));

    info->sid = (char *) calloc(1, sinfo.sid.length() + 1);
    ex_strcpy(info->sid, sinfo.sid.length() + 1, sinfo.sid.c_str());
    info->user_username = (char *) calloc(1, sinfo.user_username.length() + 1);
    ex_strcpy(info->user_username, sinfo.user_username.length() + 1, sinfo.user_username.c_str());
    info->host_ip = (char *) calloc(1, sinfo.host_ip.length() + 1);
    ex_strcpy(info->host_ip, sinfo.host_ip.length() + 1, sinfo.host_ip.c_str());
    info->conn_ip = (char *) calloc(1, sinfo.conn_ip.length() + 1);
    ex_strcpy(info->conn_ip, sinfo.conn_ip.length() + 1, sinfo.conn_ip.c_str());
    info->client_ip = (char *) calloc(1, sinfo.client_ip.length() + 1);
    ex_strcpy(info->client_ip, sinfo.client_ip.length() + 1, sinfo.client_ip.c_str());
    info->acc_username = (char *) calloc(1, sinfo.acc_username.length() + 1);
    ex_strcpy(info->acc_username, sinfo.acc_username.length() + 1, sinfo.acc_username.c_str());
    info->acc_secret = (char *) calloc(1, sinfo.acc_secret.length() + 1);
    ex_strcpy(info->acc_secret, sinfo.acc_secret.length() + 1, sinfo.acc_secret.c_str());
    info->username_prompt = (char *) calloc(1, sinfo.username_prompt.length() + 1);
    ex_strcpy(info->username_prompt, sinfo.username_prompt.length() + 1, sinfo.username_prompt.c_str());
    info->password_prompt = (char *) calloc(1, sinfo.password_prompt.length() + 1);
    ex_strcpy(info->password_prompt, sinfo.password_prompt.length() + 1, sinfo.password_prompt.c_str());

    info->user_id = sinfo.user_id;
    info->host_id = sinfo.host_id;
    info->acc_id = sinfo.acc_id;
    info->conn_port = sinfo.conn_port;
    info->protocol_type = sinfo.protocol_type;
    info->protocol_sub_type = sinfo.protocol_sub_type;
    info->protocol_flag = sinfo.protocol_flag;
    info->record_flag = sinfo.record_flag;
    info->auth_type = sinfo.auth_type;

    return info;
}

void tpp_free_connect_info(TPP_CONNECT_INFO *info) {
    if (NULL == info)
        return;

    g_session_mgr.free_connect_info(info->sid);

    free(info->sid);
    free(info->user_username);
    free(info->host_ip);
    free(info->conn_ip);
    free(info->client_ip);
    free(info->acc_username);
    free(info->acc_secret);
    free(info->username_prompt);
    free(info->password_prompt);
    free(info);
}

bool tpp_session_begin(const TPP_CONNECT_INFO *info, int *db_id) {
    if (NULL == info || NULL == db_id)
        return false;

    TS_CONNECT_INFO sinfo;
    sinfo.sid = info->sid;
    sinfo.user_id = info->user_id;
    sinfo.host_id = info->host_id;
    sinfo.acc_id = info->acc_id;
    sinfo.user_username = info->user_username;
    sinfo.host_ip = info->host_ip;
    sinfo.conn_ip = info->conn_ip;
    sinfo.client_ip = info->client_ip;
    sinfo.acc_username = info->acc_username;

    sinfo.conn_port = info->conn_port;
    sinfo.protocol_type = info->protocol_type;
    sinfo.protocol_sub_type = info->protocol_sub_type;
    sinfo.auth_type = info->auth_type;

    return ts_web_rpc_session_begin(sinfo, *db_id);
}

bool tpp_session_update(int db_id, int protocol_sub_type, int state) {
    return ts_web_rpc_session_update(db_id, protocol_sub_type, state);
}

bool tpp_session_end(const char *sid, int db_id, int ret) {
    return ts_web_rpc_session_end(sid, db_id, ret);
}

// typedef struct TPP_LIB
// {
// 	TPP_LIB()
// 	{
// 		dylib = NULL;
// 		init = NULL;
// 	}
// 	~TPP_LIB()
// 	{
// 		if (NULL != dylib)
// 			ex_dlclose(dylib);
// 		dylib = NULL;
// 	}
// 
// 	EX_DYLIB_HANDLE dylib;
// 	TPP_INIT_FUNC init;
// 	TPP_START_FUNC start;
// 	TPP_STOP_FUNC stop;
// 	TPP_TIMER_FUNC timer;
// }TPP_LIB;
// 
// typedef std::list<TPP_LIB*> tpp_libs;
// 
// class TppManager
// {
// public:
// 	TppManager()
// 	{
// 	}
// 	~TppManager()
// 	{
// 		tpp_libs::iterator it = m_libs.begin();
// 		for (; it != m_libs.end(); ++it)
// 		{
// 			delete (*it);
// 		}
// 		m_libs.clear();
// 	}
// 
// 	bool load_tpp(const ex_wstr& libfile);
// 	void stop_all(void);
// 	void timer(void); // 大约1秒调用一次
// 	int count(void) { return m_libs.size(); }
// 
// private:
// 	tpp_libs m_libs;
// };
// 
// static TppManager g_tpp_mgr;
// extern ExLogger g_ex_logger;
// 
// bool TppManager::load_tpp(const ex_wstr& libname)
// {
// 	ex_wstr filename;
// #ifdef EX_OS_WIN32
// 	filename = libname + L".dll";
// #elif defined (EX_OS_LINUX)
//     filename = L"lib";
//     filename += libname;
// 	filename += L".so";
// #elif defined (EX_OS_MACOS)
// 	filename = L"lib";
//     filename += libname;
// 	filename += L".dylib";
// #endif
// 
// 	ex_wstr libfile = g_env.m_exec_path;
// 	ex_path_join(libfile, false, filename.c_str(), NULL);
// 	EXLOGV(L"[core] load protocol lib: %ls\n", libfile.c_str());
// 
// 	TPP_LIB* lib = new TPP_LIB;
// 
// 	lib->dylib = ex_dlopen(libfile.c_str());
// 	if (NULL == lib->dylib)
// 	{
// 		EXLOGE(L"[core] load dylib `%ls` failed.\n", libfile.c_str());
// 		delete lib;
// 		return false;
// 	}
// 
// #ifdef EX_OS_WIN32
// 	lib->init = (TPP_INIT_FUNC)GetProcAddress(lib->dylib, "tpp_init");
// 	lib->start = (TPP_START_FUNC)GetProcAddress(lib->dylib, "tpp_start");
// 	lib->stop = (TPP_STOP_FUNC)GetProcAddress(lib->dylib, "tpp_stop");
// 	lib->timer = (TPP_TIMER_FUNC)GetProcAddress(lib->dylib, "tpp_timer");
// #else
//     lib->init = (TPP_INIT_FUNC)dlsym(lib->dylib, "tpp_init");
//     lib->start = (TPP_START_FUNC)dlsym(lib->dylib, "tpp_start");
// 	lib->stop = (TPP_STOP_FUNC)dlsym(lib->dylib, "tpp_stop");
// 	lib->timer = (TPP_TIMER_FUNC)dlsym(lib->dylib, "tpp_timer");
// #endif
// 
// 	if (lib->init == NULL || lib->start == NULL || lib->stop == NULL || lib->timer == NULL)
// 	{
// 		EXLOGE(L"[core] load dylib `%ls` failed, can not locate all functions.\n", libfile.c_str());
// 		delete lib;
// 		return false;
// 	}
// 
// 	TPP_INIT_ARGS init_args;
// 	init_args.logger = &g_ex_logger;
// 	init_args.exec_path = g_env.m_exec_path;
// 	init_args.etc_path = g_env.m_etc_path;
// 	init_args.replay_path = g_env.m_replay_path;
// 	init_args.cfg = &g_env.get_ini();
// 	init_args.func_get_connect_info = tpp_get_connect_info;
// 	init_args.func_free_connect_info = tpp_free_connect_info;
// 	init_args.func_session_begin = tpp_session_begin;
// 	init_args.func_session_update = tpp_session_update;
// 	init_args.func_session_end = tpp_session_end;
// 
// 	if (EXRV_OK != lib->init(&init_args))
// 	{
// 		EXLOGE(L"[core] failed to init protocol `%ls`.\n", libname.c_str());
// 		delete lib;
// 		return false;
// 	}
// 	if (EXRV_OK != lib->start())
// 	{
// 		EXLOGE(L"[core] failed to start protocol `%ls`.\n", libname.c_str());
// 		delete lib;
// 		return false;
// 	}
// 
// 	m_libs.push_back(lib);
// 	return true;
// }
// 
// void TppManager::stop_all(void) {
// 	tpp_libs::iterator it = m_libs.begin();
// 	for (; it != m_libs.end(); ++it)
// 	{
// 		(*it)->stop();
// 	}
// }
// 
// void TppManager::timer(void) {
// 	tpp_libs::iterator it = m_libs.begin();
// 	for (; it != m_libs.end(); ++it)
// 	{
// 		(*it)->timer();
// 	}
// }

int ts_main(void) {
    ExIniFile &ini = g_env.get_ini();

    EXLOGI(L"\n");
    EXLOGI(L"###############################################################\n");
    EXLOGI(L"Load config file: %ls.\n", ini.get_filename().c_str());
    EXLOGI(L"Teleport Core Server starting ...\n");

    ex_ini_sections &secs = ini.GetAllSections();
    TsHttpRpc rpc;

    // 枚举配置文件中的[protocol-xxx]小节，加载对应的协议动态库
    bool all_ok = true;

    do {
        if (!g_session_mgr.start()) {
            EXLOGE(L"[core] failed to start session-id manager.\n");
            all_ok = false;
            break;
        }

        if (!rpc.init() || !rpc.start()) {
            EXLOGE(L"[core] rpc init/start failed.\n");
            all_ok = false;
            break;
        }

        ex_ini_sections::iterator it = secs.begin();
        for (; it != secs.end(); ++it) {
            if (it->first.length() > 9 && 0 == wcsncmp(it->first.c_str(), L"protocol-", 9)) {
                ex_wstr libname;
                if (!it->second->GetStr(L"lib", libname))
                    continue;

                bool enabled = false;
                it->second->GetBool(L"enabled", enabled, false);
                if (!enabled) {
                    EXLOGV(L"[core] `%ls` not enabled.\n", libname.c_str());
                    continue;
                }

                if (!g_tpp_mgr.load_tpp(libname)) {
                    all_ok = false;
                    break;
                }
            }
        }

    } while (0);

    if (0 == g_tpp_mgr.count()) {
        all_ok = false;
    }

    if (!all_ok) {
        g_exit_flag = true;
    }

    if (!g_exit_flag) {
        ts_web_rpc_register_core();

        EXLOGV("[core] ---- initialized, ready for service ----\n");
        while (!g_exit_flag) {
            ex_sleep_ms(1000);
            g_tpp_mgr.timer();
        }
    }

    EXLOGW("[core] try to stop all thread and exit.\n");
    g_tpp_mgr.stop_all();
    rpc.stop();
    g_session_mgr.stop();

    return 0;
}
