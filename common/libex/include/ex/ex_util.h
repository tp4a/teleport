#ifndef __LIB_EX_UTIL_H__
#define __LIB_EX_UTIL_H__

#include "ex_types.h"
#include "ex_str.h"

#ifdef EX_OS_WIN32
#	include <time.h>
//#	include <io.h>
//#	include <stdio.h>
// #include <direct.h>
#pragma comment(lib, "ws2_32.lib")
#else
// #include <dirent.h>
#   include <dlfcn.h>
#	include <sys/time.h>
#endif

EX_BOOL ex_initialize(const char* lc_ctype);

void ex_free(void* buffer);

// 在haystack（长度为haystacklen字节）中查找needle（长度为needlelen）的起始地址，返回NULL表示没有找到
const ex_u8* ex_memmem(const ex_u8* haystack, size_t haystacklen, const ex_u8* needle, size_t needlelen);
void ex_mem_reverse(ex_u8* p, size_t l);

void ex_printf(const char* fmt, ...);
void ex_wprintf(const wchar_t* fmt, ...);

ex_u64 ex_get_tick_count(void);
void ex_sleep_ms(int ms);

EX_BOOL ex_localtime_now(int* t, struct tm* dt);


FILE* ex_fopen(const ex_wstr& filename, const wchar_t* mode);
FILE* ex_fopen(const ex_astr& filename, const char* mode);

// open a text file and read all content.
bool ex_read_text_file(const ex_wstr& file_name, ex_astr& file_content);
// open a file and write content.
bool ex_write_text_file(const ex_wstr& file_name, const ex_astr& file_content);

EX_DYLIB_HANDLE ex_dlopen(const wchar_t* dylib_path);
void ex_dlclose(EX_DYLIB_HANDLE dylib);


// inet...
int ex_ip4_name(const struct sockaddr_in* src, char* dst, size_t size);

#define EX_IPV4_NAME_LEN   16
#define EX_IPV6_NAME_LEN   46
const char* ex_inet_ntop(int af, const void *src, char *dst, size_t size);

#endif // __LIB_EX_UTIL_H__
