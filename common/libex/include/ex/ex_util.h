#ifndef __LIB_EX_UTIL_H__
#define __LIB_EX_UTIL_H__

#include <ex/ex_types.h>
#include <ex/ex_str.h>

#ifdef EX_OS_WIN32
#	include <time.h>
//#	include <io.h>
//#	include <stdio.h>
// #include <direct.h>
#else
// #include <dirent.h>
#	include <sys/time.h>
#endif

EX_BOOL ex_initialize(const char* lc_ctype);

void ex_free(void* buffer);

// 在haystack（长度为haystacklen字节）中查找needle（长度为needlelen）的起始地址，返回NULL表示没有找到
const ex_u8* ex_memmem(const ex_u8* haystack, size_t haystacklen, const ex_u8* needle, size_t needlelen);

void ex_printf(const char* fmt, ...);
void ex_wprintf(const wchar_t* fmt, ...);

ex_u64 ex_get_tick_count(void);
void ex_sleep_ms(int ms);

EX_BOOL ex_localtime_now(int* t, struct tm* dt);


FILE* ex_fopen(const ex_wstr& filename, const wchar_t* mode);


EX_DYLIB_HANDLE ex_dlopen(const wchar_t* dylib_path);
void ex_dlclose(EX_DYLIB_HANDLE dylib);


// inet...
int ex_ip4_name(const struct sockaddr_in* src, char* dst, size_t size);

#endif // __LIB_EX_UTIL_H__
