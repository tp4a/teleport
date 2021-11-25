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

int cpp_main(void* _self, const char* bundle_path, const char* cfg_file, const char* res_path) {
	if(!g_env.init(bundle_path, cfg_file, res_path))
		return -1;
	if(!g_cfg.init())
		return -2;

//	if(0 != http_rpc_start(_self))
//		return -3;
//
    TsWsClient::init_app(_self);
    
	return 0;
}

//uint64_t cpp_getpid()
//{
//    pid_t pid = getpid();
//
//    return static_cast<uint64_t>(pid);
//}

void url_scheme_handler(const std::string& url)
{
    TsWsClient::url_scheme_handler(url);
}
