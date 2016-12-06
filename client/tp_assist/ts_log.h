#ifndef __TS_LOG_H__
#define __TS_LOG_H__

#include <ex.h>

#define TS_LOG_LEVEL_DEBUG		0
#define TS_LOG_LEVEL_VERBOSE	1
#define TS_LOG_LEVEL_INFO		2
#define TS_LOG_LEVEL_WARN		3
#define TS_LOG_LEVEL_ERROR		4

void TSLOG_INIT(int min_level, const wchar_t* log_file_name, const wchar_t* log_path = NULL);

#define TSLOGV ts_printf_v
#define TSLOGI ts_printf_i
#define TSLOGW ts_printf_w
#define TSLOGE ts_printf_e

#ifdef TS_DEBUG
#	define TSLOGD ts_printf_d
#	define TSLOG_BIN ts_printf_bin
#else
#	define TSLOGD
#	define TSLOG_BIN
#endif

#ifdef EX_OS_WIN32
#define TSLOGE_WIN ts_printf_e_lasterror
void ts_printf_e_lasterror(const char* fmt, ...);
void ts_printf_e_lasterror(const wchar_t* fmt, ...);
#endif


void ts_printf_d(const char* fmt, ...);
void ts_printf_v(const char* fmt, ...);
void ts_printf_i(const char* fmt, ...);
void ts_printf_w(const char* fmt, ...);
void ts_printf_e(const char* fmt, ...);

void ts_printf_d(const wchar_t* fmt, ...);
void ts_printf_v(const wchar_t* fmt, ...);
void ts_printf_i(const wchar_t* fmt, ...);
void ts_printf_w(const wchar_t* fmt, ...);
void ts_printf_e(const wchar_t* fmt, ...);

void ts_printf_bin(ex_u8* bin_data, size_t bin_size, const char* fmt, ...);
void ts_printf_bin(ex_u8* bin_data, size_t bin_size, const wchar_t* fmt, ...);


#endif // __TS_LOG_H__
