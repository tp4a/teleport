//
//  wrap_c_objc.h
//  tp_assist
//
//  Created by ApexLiu on 2017/9/27.
//

#ifndef wrap_c_objc_h
#define wrap_c_objc_h

int AppDelegate_start_ssh_client (void *_self, const char* cmd_line, const char* term_type, const char* term_theme, const char* term_title);
int AppDelegate_select_app (void *_self);

// for cpp global object initialize.
int cpp_main(void* _self, const char* cfg_file, const char* res_path);

#endif /* wrap_c_objc_h */
