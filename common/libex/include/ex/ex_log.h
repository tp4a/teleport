#ifndef __EX_LOG_H__
#define __EX_LOG_H__

#include "ex_types.h"
#include "ex_thread.h"

#define EX_LOG_LEVEL_DEBUG		0
#define EX_LOG_LEVEL_VERBOSE		1
#define EX_LOG_LEVEL_INFO		2
#define EX_LOG_LEVEL_WARN		3
#define EX_LOG_LEVEL_ERROR		4

#define EX_LOG_FILE_MAX_SIZE 1024*1024*10
#define EX_LOG_FILE_MAX_COUNT 10

class ExLogger
{
public:
	ExLogger();
	~ExLogger();

	bool set_log_file(const ex_wstr& log_path, const ex_wstr& log_name, ex_u32 max_filesize, ex_u8 max_count);
	void log_a(int level, const char* fmt, va_list valist);
	void log_w(int level, const wchar_t* fmt, va_list valist);
	bool write_a(const char* buf);
	bool write_w(const wchar_t* buf);

protected:
	bool _open_file();
	bool _rotate_file(void);		// 将现有日志文件改名备份，然后新开一个日志文件

public:
	ExThreadLock lock;
	int min_level;
	bool debug_mode;
	bool to_console;

#ifdef EX_OS_WIN32
	HANDLE console_handle;
#endif

protected:
	ex_u32 m_filesize;
	ex_u32 m_max_filesize;
	ex_u8 m_max_count;
	ex_wstr m_path;
	ex_wstr m_filename;
	ex_wstr m_fullname;

#ifdef EX_OS_WIN32
	HANDLE m_file;
#else
	FILE* m_file;
#endif
};

//extern ExLogger g_ex_logger;

// extern void* ex_logger;

void EXLOG_USE_LOGGER(ExLogger* logger);

void EXLOG_LEVEL(int min_level);
void EXLOG_DEBUG(bool debug_mode);

// 设定日志文件名及路径，如未指定路径，则为可执行程序所在目录下的log目录。
void EXLOG_FILE(const wchar_t* log_file, const wchar_t* log_path = NULL, ex_u32 max_filesize = EX_LOG_FILE_MAX_SIZE, ex_u8 max_filecount = EX_LOG_FILE_MAX_COUNT);

void EXLOG_CONSOLE(bool output_to_console);

#define EXLOGV ex_printf_v
#define EXLOGI ex_printf_i
#define EXLOGW ex_printf_w
#define EXLOGE ex_printf_e
#define EXLOGD ex_printf_d
#define EXLOG_BIN ex_printf_bin

#ifdef EX_OS_WIN32
#define EXLOGE_WIN ex_printf_e_lasterror
void ex_printf_e_lasterror(const char* fmt, ...);
void ex_printf_e_lasterror(const wchar_t* fmt, ...);
#endif


void ex_printf_d(const char* fmt, ...);
void ex_printf_v(const char* fmt, ...);
void ex_printf_i(const char* fmt, ...);
void ex_printf_w(const char* fmt, ...);
void ex_printf_e(const char* fmt, ...);

void ex_printf_d(const wchar_t* fmt, ...);
void ex_printf_v(const wchar_t* fmt, ...);
void ex_printf_i(const wchar_t* fmt, ...);
void ex_printf_w(const wchar_t* fmt, ...);
void ex_printf_e(const wchar_t* fmt, ...);

void ex_printf_bin(const ex_u8* bin_data, size_t bin_size, const char* fmt, ...);
void ex_printf_bin(const ex_u8* bin_data, size_t bin_size, const wchar_t* fmt, ...);


#endif // __EX_LOG_H__
