#ifndef __EX_WINSRV_H__
#define __EX_WINSRV_H__

#include "ex_str.h"

#ifdef EX_OS_WIN32

ex_rv ex_winsrv_install(const ex_wstr& srv_name, const ex_wstr& disp_name, const ex_wstr& exec_path);
ex_rv ex_winsrv_uninstall(const ex_wstr& srv_name);
bool ex_winsrv_is_exists(const ex_wstr& srv_name);
ex_rv ex_winsrv_start(const ex_wstr& srv_name);
ex_rv ex_winsrv_stop(const ex_wstr& srv_name);
ex_rv ex_winsrv_status(const ex_wstr& srv_name, ex_ulong& status);
ex_rv ex_winsrv_pause(const ex_wstr& srv_name);
ex_rv ex_winsrv_resume(const ex_wstr& srv_name);
ex_rv ex_winsrv_config(const ex_wstr& srv_name, QUERY_SERVICE_CONFIG& cfg);
ex_rv ex_winsrv_pid(const ex_wstr& srv_name, ex_ulong& pid);

#endif

#endif // __EX_WINSRV_H__
