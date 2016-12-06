#ifndef __LIB_EX_UTIL_H__
#define __LIB_EX_UTIL_H__

#include <ex/ex_types.h>

EX_BOOL ex_initialize(const char* lc_ctype);

void ex_free(void* buffer);


void ex_printf(const char* fmt, ...);
void ex_wprintf(const wchar_t* fmt, ...);

ex_u64 ex_get_tick_count(void);
void ex_sleep_ms(int ms);


#endif // __LIB_EX_UTIL_H__
