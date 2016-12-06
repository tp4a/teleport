#include "stdafx.h"
#include "ts_log.h"
#include "ts_thread.h"

#include <vector>
#include <deque>
#include <algorithm>

#ifdef EX_OS_WIN32
#include <io.h>
#include <stdio.h>
#include <direct.h>
#else
#include <dirent.h>
#include <sys/time.h>
#endif

#define LOG_PATH_MAX_LEN 1024
#define LOG_CONTENT_MAX_LEN 2048

#define LOG_FILE_MAX_SIZE 1024*1024*10
#define LOG_FILE_MAX_COUNT 10
typedef enum TS_COLORS
{
	TS_COLOR_BLACK = 0,
	TS_COLOR_BLUE = 1,
	TS_COLOR_GREEN = 2,
	TS_COLOR_CYAN = 3,
	TS_COLOR_RED = 4,
	TS_COLOR_MAGENTA = 5,
	TS_COLOR_YELLOW = 6,
	TS_COLOR_LIGHT_GRAY = 7,
	TS_COLOR_GRAY = 8,
	TS_COLOR_LIGHT_BLUE = 9,
	TS_COLOR_LIGHT_GREEN = 10,
	TS_COLOR_LIGHT_CYAN = 11,
	TS_COLOR_LIGHT_RED = 12,
	TS_COLOR_LIGHT_MAGENTA = 13,
	TS_COLOR_LIGHT_YELLOW = 14,
	TS_COLOR_WHITE = 15,

	TS_COLOR_NORMAL = 0xFF,
}TS_COLORS;

#ifdef EX_OS_WIN32
static HANDLE g_hConsole = NULL;
#endif

int g_log_min_level = TS_LOG_LEVEL_INFO;
ex_wstr g_log_path;
ex_wstr g_log_name;
TsThreadLock g_log_lock;

class TSLogFile
{
public:
	TSLogFile() {
		m_hFile = NULL;
		m_nMaxFileLength = LOG_FILE_MAX_SIZE;
		m_nMaxFileCount = LOG_FILE_MAX_COUNT;
	}
	~TSLogFile() {
	}
	bool WriteData(int level, char* buf, int len);
	bool Init(const ex_astr& log_path, const ex_astr& log_name)
	{
		m_Log_Path = log_path;
#ifdef EX_OS_WIN32
		m_Log_Path += "\\";
#else
		m_Log_Path += "//";
#endif
		m_Log_Path += log_name;

		m_log_name = log_name;

		m_log_file_dir = log_path;

		load_file_list();
		return true;
	}
protected:
	bool open_file();
	bool backup_file();
	bool load_file_list();

protected:
	typedef std::deque<unsigned long long> log_file_deque;
	FILE* m_hFile;
	
	unsigned int  m_nMaxFileLength;
	unsigned int  m_nMaxFileCount;
	std::string m_Log_Path;
	std::string m_log_name;
	std::string m_log_file_dir;
	log_file_deque m_log_file_list;
private:

};
TSLogFile g_log_file;

void TSLOG_INIT(int min_level, const wchar_t*log_file_name, const wchar_t* log_path)
{
	g_log_min_level = min_level;

#ifdef EX_OS_WIN32
	if (NULL == g_hConsole)
		g_hConsole = GetStdHandle(STD_OUTPUT_HANDLE);
#endif

	if (log_file_name)
	{
		g_log_name = log_file_name;
	}
	else
	{
		g_log_name = L"main.log";
	}

	if (log_path)
	{
		g_log_path = log_path;
	}
	else
	{
		ex_exec_file(g_log_path);
		ex_dirname(g_log_path);
		ex_path_join(g_log_path, false, L"log");
	}

	ex_mkdirs(g_log_path);

	ex_astr _path, _file;
	ex_wstr2astr(g_log_path, _path);
	ex_wstr2astr(g_log_name, _file);

	g_log_file.Init(_path, _file);
}

static void _ts_printf_a(int level,TS_COLORS clrBackGround, const char* fmt, va_list valist)
{
	if (NULL == fmt || 0 == strlen(fmt))
		return;
	if (g_log_min_level > level)
		return;
	TS_COLORS clrForeGround = TS_COLOR_NORMAL;
	switch (level)
	{
	case TS_LOG_LEVEL_DEBUG:
		{
			clrForeGround = TS_COLOR_GRAY;
		}
		break;
	case TS_LOG_LEVEL_VERBOSE:
		{
			clrForeGround = TS_COLOR_LIGHT_GRAY;
		}
		break;
	case TS_LOG_LEVEL_INFO:
		{
			clrForeGround = TS_COLOR_LIGHT_MAGENTA;
		}
		break;
	case TS_LOG_LEVEL_WARN:
		{
			clrForeGround = TS_COLOR_LIGHT_RED;
		}
		break;
	case TS_LOG_LEVEL_ERROR:
		{
			clrForeGround = TS_COLOR_LIGHT_RED;
		}
		break;
	default:
		break;
	}
	if (TS_COLOR_NORMAL == clrForeGround)
		clrForeGround = TS_COLOR_LIGHT_GRAY;
	if (TS_COLOR_NORMAL == clrBackGround)
		clrBackGround = TS_COLOR_BLACK;

	char szTmp[4096] = { 0 };

#ifdef EX_OS_WIN32
	vsnprintf_s(szTmp, 4096, 4095, fmt, valist);
	if (NULL != g_hConsole)
	{
		SetConsoleTextAttribute(g_hConsole, (WORD)((clrBackGround << 4) | clrForeGround));
		printf_s("%s", szTmp);
		fflush(stdout);
		SetConsoleTextAttribute(g_hConsole, TS_COLOR_GRAY);
	}
	else {
		OutputDebugStringA(szTmp);
	}
#else
	vsnprintf(szTmp, 4095, fmt, valist);
	printf("%s", szTmp);
	fflush(stdout);
#endif
	g_log_file.WriteData(level, szTmp, strlen(szTmp));
}

static void _ts_printf_w(int level, TS_COLORS clrBackGround, const wchar_t* fmt, va_list valist)
{
	if (NULL == fmt || 0 == wcslen(fmt))
		return;
	if (g_log_min_level > level)
		return;
	
	TS_COLORS clrForeGround = TS_COLOR_NORMAL;
	switch (level)
	{
	case TS_LOG_LEVEL_DEBUG:
		{
			clrForeGround = TS_COLOR_GRAY;
		}
		break;
	case TS_LOG_LEVEL_VERBOSE:
		{	
			clrForeGround = TS_COLOR_LIGHT_GRAY;
		}
		break;
	case TS_LOG_LEVEL_INFO:
		{
			clrForeGround = TS_COLOR_LIGHT_MAGENTA;
		}
		break;
	case TS_LOG_LEVEL_WARN:
		{
			clrForeGround = TS_COLOR_LIGHT_RED;
		}
		break;
	case TS_LOG_LEVEL_ERROR:
		{
			clrForeGround = TS_COLOR_LIGHT_RED;
		}
		break;
	default:
		break;
	}
	if (TS_COLOR_NORMAL == clrForeGround)
		clrForeGround = TS_COLOR_LIGHT_GRAY;
	if (TS_COLOR_NORMAL == clrBackGround)
		clrBackGround = TS_COLOR_BLACK;

	wchar_t szTmp[4096] = { 0 };

#ifdef EX_OS_WIN32
	_vsnwprintf_s(szTmp, 4096, 4095, fmt, valist);
	if (NULL != g_hConsole)
	{
		SetConsoleTextAttribute(g_hConsole, (WORD)((clrBackGround << 4) | clrForeGround));
		wprintf_s(_T("%s"), szTmp);
		fflush(stdout);
		SetConsoleTextAttribute(g_hConsole, TS_COLOR_GRAY);
	}
	else {
		OutputDebugStringW(szTmp);
	}
#else
	vswprintf(szTmp, 4095, fmt, valist);
	wprintf(L"%s", szTmp);
	fflush(stdout);
#endif

}

#define TS_PRINTF_X(fn, level) \
void fn(const char* fmt, ...) \
{ \
	TsThreadSmartLock locker(g_log_lock); \
	va_list valist; \
	va_start(valist, fmt); \
	_ts_printf_a(level, TS_COLOR_BLACK, fmt, valist); \
	va_end(valist); \
} \
void fn(const wchar_t* fmt, ...) \
{ \
	TsThreadSmartLock locker(g_log_lock); \
	va_list valist; \
	va_start(valist, fmt); \
	_ts_printf_w(level, TS_COLOR_BLACK, fmt, valist); \
	va_end(valist); \
}

TS_PRINTF_X(ts_printf_d, TS_LOG_LEVEL_DEBUG)
TS_PRINTF_X(ts_printf_v, TS_LOG_LEVEL_VERBOSE)
TS_PRINTF_X(ts_printf_i, TS_LOG_LEVEL_INFO)
TS_PRINTF_X(ts_printf_w, TS_LOG_LEVEL_WARN)
TS_PRINTF_X(ts_printf_e, TS_LOG_LEVEL_ERROR)

#ifdef EX_OS_WIN32
void ts_printf_e_lasterror(const char* fmt, ...)
{
	TsThreadSmartLock locker(g_log_lock);

	va_list valist;
	va_start(valist, fmt);
	_ts_printf_a(TS_COLOR_LIGHT_RED, TS_COLOR_BLACK, fmt, valist);
	va_end(valist);

	//=========================================

	LPVOID lpMsgBuf;
	DWORD dw = GetLastError();

	FormatMessageA(FORMAT_MESSAGE_ALLOCATE_BUFFER | FORMAT_MESSAGE_FROM_SYSTEM | FORMAT_MESSAGE_IGNORE_INSERTS,
		NULL, dw, MAKELANGID(LANG_NEUTRAL, SUBLANG_DEFAULT),
		(LPSTR)&lpMsgBuf, 0, NULL);

	ts_printf_e(" - WinErr(%d): %s\n", dw, (LPSTR)lpMsgBuf);
	LocalFree(lpMsgBuf);
}
#endif

void ts_printf_bin(ex_u8* bin_data, size_t bin_size, const char* fmt, ...)
{
	TsThreadSmartLock locker(g_log_lock);

	va_list valist;
	va_start(valist, fmt);
	_ts_printf_a(TS_COLOR_GRAY, TS_COLOR_BLACK, fmt, valist);
	va_end(valist);

	ts_printf_d(" (%d/0x%02x Bytes)\n", bin_size, bin_size);

	const ex_u8* line = bin_data;
	size_t thisline = 0;
	size_t offset = 0;
	unsigned int i = 0;

	char szTmp[128] = { 0 };
	int _offset = 0;

	while (offset < bin_size)
	{
		memset(szTmp, 0, 128);
		_offset = 0;

		snprintf(szTmp + _offset, 128 - _offset, "%06x  ", (int)offset);
		_offset += 8;

		thisline = bin_size - offset;
		if (thisline > 16)
			thisline = 16;

		for (i = 0; i < thisline; i++)
		{
			snprintf(szTmp + _offset, 128 - _offset, "%02x ", line[i]);
			_offset += 3;
		}

		snprintf(szTmp + _offset, 128 - _offset, "  ");
		_offset += 2;

		for (; i < 16; i++)
		{
			snprintf(szTmp + _offset, 128 - _offset, "   ");
			_offset += 3;
		}

		for (i = 0; i < thisline; i++)
		{
			snprintf(szTmp + _offset, 128 - _offset, "%c", (line[i] >= 0x20 && line[i] < 0x7f) ? line[i] : '.');
			_offset += 1;
		}

		snprintf(szTmp + _offset, 128 - _offset, "\n");
		_offset += 1;

		ts_printf_d("%s", szTmp);

		offset += thisline;
		line += thisline;
	}

	fflush(stdout);
}

bool TSLogFile::open_file()
{
	if (m_hFile) 
	{
		fclose(m_hFile);
		m_hFile = 0;
	}

	// 注意：这里必须使用 _fsopen 来指定共享读方式打开日志文件，否则进程推出前无法查看日志文件内容。
	m_hFile = _fsopen(m_Log_Path.c_str(), "a", _SH_DENYWR);
	if (NULL == m_hFile)
		return false;

	fseek(m_hFile, 0, SEEK_END);
	unsigned long file_size = ftell(m_hFile);
	if (file_size > (unsigned long)m_nMaxFileLength)
	{
		//备份文件
		if (backup_file()) 
		{
			//打开文件
			return open_file();
		}
	}
	return true;
}

bool TSLogFile::backup_file() 
{
	char szNewFileLogName[LOG_PATH_MAX_LEN] = {0};
	char szBaseNewFileLogName[LOG_PATH_MAX_LEN] = { 0 };
#ifdef EX_OS_WIN32
	SYSTEMTIME st;
	GetLocalTime(&st);
	sprintf_s(szNewFileLogName, LOG_PATH_MAX_LEN, "%s\\%04d%02d%02d%02d%02d%02d.log",
		m_log_file_dir.c_str(),st.wYear, st.wMonth, st.wDay, st.wHour, st.wMinute, st.wSecond);

	sprintf_s(szBaseNewFileLogName, LOG_PATH_MAX_LEN, "%04d%02d%02d%02d%02d%02d",
		st.wYear, st.wMonth, st.wDay, st.wHour, st.wMinute, st.wSecond);
#else
	time_t timep;
	struct tm *p;
	time(&timep);
	p = localtime(&timep);   //get server's time
	if (p == NULL)
	{
		return NULL;
	}
	sprintf(szNewFileLogName, "%s//%04d%02d%02d%02d%02d%02d.log",
		m_log_file_dir.c_str(),p->tm_year + 1900, p->tm_mon + 1, p->tm_mday, p->tm_hour, p->tm_min, p->tm_sec);
	sprintf(szBaseNewFileLogName, "%04d%02d%02d%02d%02d%02d",
		p->tm_year + 1900, p->tm_mon + 1, p->tm_mday, p->tm_hour, p->tm_min, p->tm_sec);
#endif
	if (m_hFile)
	{
		fclose(m_hFile);
		m_hFile = 0;
	}
#ifdef EX_OS_WIN32
	if (!MoveFileA(m_Log_Path.c_str(), szNewFileLogName))
	{
		DWORD dwError = GetLastError();

		DeleteFileA(szNewFileLogName);

		MoveFileA(m_Log_Path.c_str(), szNewFileLogName);
	}
#else
	if (rename(m_Log_Path.c_str(), szNewFileLogName) != 0)
	{
		remove(szNewFileLogName);

		rename(m_Log_Path.c_str(), szNewFileLogName);
	}
#endif
	unsigned long long value = atoll(szBaseNewFileLogName);
	if (value !=0 )
	{
		m_log_file_list.push_back(value);
	}
	int try_count = 0;
	while ((m_log_file_list.size() > m_nMaxFileCount))
	{
		unsigned long long value = m_log_file_list.front();
		char szDeleteFile[256] = { 0 };
#ifdef EX_OS_WIN32
		sprintf_s(szDeleteFile, 256, "%s\\%llu.log", m_log_file_dir.c_str(), value);
		if (DeleteFileA(szDeleteFile)) 
		{
			m_log_file_list.pop_front();
		}
#else
		sprintf(szDeleteFile, "%s//%llu.log", m_log_file_dir.c_str(), value);
		if (remove(szDeleteFile) == 0)
		{
			m_log_file_list.pop_front();
		}
#endif
		else
		{
			if (try_count > 5)
			{
				break;
			}
			try_count++;
		}

	} 

	return true;
}

bool TSLogFile::WriteData(int level, char* buf, int len) 
{
	if (len > LOG_CONTENT_MAX_LEN)
	{
		return false;
	}

	// TODO: 这里每次写日志时都会导致判断文件大小来决定是否新开一个日志文件，效率低下。应该改为缓存文件大小，每次写入完毕后更新大小值，超过阀值则新开日志文件。
	if (!open_file()) 
	{
		return false;
	}

	
#ifdef EX_OS_WIN32
	unsigned long _tid = GetCurrentThreadId();
#else
	unsigned long _tid = pthread_self();
#endif
#ifdef EX_OS_WIN32
	unsigned long now = GetTickCount();
#else
//	unsigned long now = 0;
	struct timeval tv;
	if (gettimeofday(&tv, NULL /* tz */) != 0) return false;
	unsigned long now = (double)tv.tv_sec + (((double)tv.tv_usec) / 1000.0);
#endif

	char szLog[LOG_CONTENT_MAX_LEN + 100] = {0};
#ifdef EX_OS_WIN32
	SYSTEMTIME st;
	GetLocalTime(&st);
	sprintf_s(szLog, LOG_CONTENT_MAX_LEN + 100, "[%04d-%02d-%02d %02d:%02d:%02d] %s", 
		st.wYear, st.wMonth, st.wDay, st.wHour, st.wMinute, st.wSecond, buf);
#else
	time_t timep;
	struct tm *p;
	time(&timep);
	p = localtime(&timep);   //get server's time
	if (p == NULL)
	{
		return NULL;
	}
	sprintf(szLog, "[%04d-%02d-%02d %02d:%02d:%02d] %s",
		p->tm_year + 1900, p->tm_mon + 1, p->tm_mday, p->tm_hour, p->tm_min, p->tm_sec, buf);
#endif
	// TODO: 在这里统计文件大小
	fwrite(szLog, strlen(szLog), 1, m_hFile);
	fflush(m_hFile);
	return true;
}

bool TSLogFile::load_file_list()
{
#ifdef EX_OS_WIN32
	struct _finddata_t data;
	std::string log_match = m_log_file_dir;
	log_match += "\\";
	log_match += "*.log";
	long hnd = _findfirst(log_match.c_str(), &data);
	if (hnd < 0)
	{
		return false;
	}
	int  nRet = (hnd <0) ? -1 : 1;
	while (nRet > 0)
	{
		if (data.attrib == _A_SUBDIR)
			printf("   [%s]*\n", data.name);
		else {
			
			if (m_log_name.compare(data.name) == 0)
			{
			}
			else {
				char* match = strrchr(data.name, '.');
				if (match != NULL)
				{
					*match = '\0';
				}
				unsigned long long value = atoll(data.name);
				if (value == 0)
				{
					continue;
				}
				m_log_file_list.push_back(value);
			}
			
			
		}
			
		nRet = _findnext(hnd, &data);
	}
	_findclose(hnd);
#else
	DIR *dir;

	struct dirent *ptr;

	dir = opendir(m_log_file_dir.c_str());

	while ((ptr = readdir(dir)) != NULL)
	{
		if(ptr->d_type == 8)
		{
			char temp_file_name[PATH_MAX] = {0};
			strcpy(temp_file_name,ptr->d_name);
			if (m_log_name.compare(temp_file_name) == 0)
			{

			}else{
				char* match = strrchr(temp_file_name, '.');
				if (match != NULL)
				{
					*match = '\0';
				}
				unsigned long long value = atoll(temp_file_name);
				if (value == 0)
				{
					continue;
				}
				m_log_file_list.push_back(value);
			}
		}
//		printf("d_name: %s d_type: %d\n", ptr->d_name, ptr->d_type);
	}


	closedir(dir);
#endif // EX_OS_WIN32

	std::sort(m_log_file_list.begin(), m_log_file_list.end(), std::less<unsigned long long>());
	return true;
}
