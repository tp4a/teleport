//
//  AppDelegate-C-Interface.cpp
//  tp_assist
//
//  Created by ApexLiu on 2017/9/29.
//

#include "AppDelegate-C-Interface.h"
#include "csrc/ts_env.h"
#include "csrc/ts_cfg.h"
#include "csrc/ts_http_rpc.h"
#include "csrc/ts_ws_client.h"

void* g_app = NULL;
static ExLogger g_ex_logger;

int cpp_main(void* _self, const char* bundle_path, const char* cfg_file, const char* res_path, const char* log_path) {
    g_app = _self;
    
    EXLOG_USE_LOGGER(&g_ex_logger);
    
    if(!g_env.init(bundle_path, cfg_file, res_path, log_path))
        return -1;

#ifdef EX_DEBUG
    EXLOG_LEVEL(EX_LOG_LEVEL_DEBUG);
#else
    EXLOG_LEVEL(EX_LOG_LEVEL_INFO);
#endif
    
    EXLOG_FILE(L"tp_assist.log", g_env.m_log_path.c_str(), EX_LOG_FILE_MAX_SIZE, EX_LOG_FILE_MAX_COUNT);


    if(!g_cfg.init())
		return -2;

	if(!g_http_interface.init())
		return -3;
    if(!g_http_interface.start())
        return -3;
		
    g_ws_client.init();
    
	return 0;
}
