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

int cpp_main(void* _self, const char* cfg_file, const char* res_path) {
	if(!g_env.init(cfg_file, res_path))
		return -1;
	if(!g_cfg.init())
		return -2;

	if(0 != http_rpc_start(_self))
		return -3;
	
	return 0;
}
