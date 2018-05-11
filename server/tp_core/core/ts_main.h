#ifndef __TS_MAIN_H__
#define __TS_MAIN_H__

#include "../common/protocol_interface.h"

int ts_main(void);

TPP_CONNECT_INFO* tpp_get_connect_info(const char* sid);
void tpp_free_connect_info(TPP_CONNECT_INFO* info);
bool tpp_session_begin(const TPP_CONNECT_INFO* info, int* db_id);
bool tpp_session_update(int db_id, int protocol_sub_type, int state);
bool tpp_session_end(const char* sid, int db_id, int ret);


#endif // __TS_MAIN_H__
