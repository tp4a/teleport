//
//  AppDelegate-C-Interface.cpp
//  tp_assist
//
//  Created by ApexLiu on 2017/9/29.
//  Copyright © 2017年 eomsoft. All rights reserved.
//

#include "AppDelegate-C-Interface.h"
#include "csrc/ts_env.h"
#include "csrc/ts_cfg.h"
#include "csrc/ts_http_rpc.h"

bool cpp_main(void* _self, const char* cfg_file, const char* res_path) {
	if(!g_env.init(cfg_file, res_path))
		return false;
	if(!g_cfg.init())
		return false;

	http_rpc_start(_self);
	
	return true;
}
