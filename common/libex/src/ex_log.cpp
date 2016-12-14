#include <ex/ex_log.h>
#include <ex/ex_path.h>
#include <ex/ex_thread.h>
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

#define EX_LOG_CONTENT_MAX_LEN 2048

typedef enum EX_COLORS
{
	EX_COLOR_BLACK = 0,
	EX_COLOR_BLUE = 1,
	EX_COLOR_GREEN = 2,
	EX_COLOR_CYAN = 3,
	EX_COLOR_RED = 4,
	EX_COLOR_MAGENTA = 5,
	EX_COLOR_YELLOW = 6,
	EX_COLOR_LIGHT_GRAY = 7,
	EX_COLOR_GRAY = 8,
	EX_COLOR_LIGHT_BLUE = 9,
	EX_COLOR_LIGHT_GREEN = 10,
	EX_COLOR_LIGHT_CYAN = 11,
	EX_COLOR_LIGHT_RED = 12,
	EX_COLOR_LIGHT_MAGENTA = 13,
	EX_COLOR_LIGHT_YELLOW = 14,
	EX_COLOR_WHITE = 15,

	EX_COLOR_NORMAL = 0xFF,
}EX_COLORS;

ExThreadLock g_log_lock;

typedef std::deque<unsigned long long> log_file_deque;

class ExLogFile
{
public:
	ExLogFile() {
		m_hFile = NULL;
		m_filesize = 0;
	}
	~ExLogFile() {}

	bool init(const ex_wstr& log_path, const ex_wstr& log_name, ex_u32 max_filesize, ex_u8 max_count);

	//bool write(int level, char* buf, int len);
	bool write(int level, const char* buf);
	bool write(int level, const wchar_t* buf);

protected:
	bool _open_file();
	//bool _backup_file();
	bool _rotate_file(void);		// 将现有日志文件改名备份，然后新开一个日志文件
	//bool _load_file_list();

protected:
	FILE* m_hFile;
	ex_u32 m_filesize;

	ex_u32  m_max_filesize;
	ex_u8  m_max_count;
	ex_wstr m_path;
	ex_wstr m_filename;
	ex_wstr m_fullname;
	log_file_deque m_log_file_list;
private:

};


typedef struct EX_LOG_CFG
{
	EX_LOG_CFG()
	{
		min_level = EX_LOG_LEVEL_INFO;
		debug_mode = false;
		to_console = true;

#ifdef EX_OS_WIN32
		console_handle = GetStdHandle(STD_OUTPUT_HANDLE);
#endif
	}

	int min_level;
	bool debug_mode;
	bool to_console;

#ifdef EX_OS_WIN32
	HANDLE console_handle;
#endif

	ExLogFile logfile;
}EX_LOG_CFG;

static EX_LOG_CFG g_log_cfg;

void EXLOG_LEVEL(int min_level)
{
	g_log_cfg.min_level = min_level;
}

void EXLOG_CONSOLE(bool output_to_console)
{
	g_log_cfg.to_console = output_to_console;
}

void EXLOG_FILE(const wchar_t* log_file, const wchar_t* log_path /*= NULL*/, ex_u32 max_filesize /*= EX_LOG_FILE_MAX_SIZE*/, ex_u8 max_filecount /*= EX_LOG_FILE_MAX_COUNT*/)
{
	ex_wstr _path;
	if (NULL == log_path)
	{
		ex_exec_file(_path);
		ex_dirname(_path);
		ex_path_join(_path, false, L"log", NULL);
	}
	else
	{
		_path = log_path;
	}

	g_log_cfg.logfile.init(_path, log_file, max_filesize, max_filecount);
}

static void _ts_printf_a(int level, EX_COLORS clrBackGround, const char* fmt, va_list valist)
{
	if (NULL == fmt)
		return;

	if (g_log_cfg.min_level > level)
		return;

	EX_COLORS clrForeGround = EX_COLOR_NORMAL;
	switch (level)
	{
	case EX_LOG_LEVEL_DEBUG:
		if (!g_log_cfg.debug_mode)
			return;
		clrForeGround = EX_COLOR_GRAY;
		break;
	case EX_LOG_LEVEL_VERBOSE:
		clrForeGround = EX_COLOR_LIGHT_GRAY;
		break;
	case EX_LOG_LEVEL_INFO:
		clrForeGround = EX_COLOR_LIGHT_MAGENTA;
		break;
	case EX_LOG_LEVEL_WARN:
		clrForeGround = EX_COLOR_LIGHT_RED;
		break;
	case EX_LOG_LEVEL_ERROR:
		clrForeGround = EX_COLOR_LIGHT_RED;
		break;
	}

	if (EX_COLOR_NORMAL == clrForeGround)
		clrForeGround = EX_COLOR_LIGHT_GRAY;
	if (EX_COLOR_NORMAL == clrBackGround)
		clrBackGround = EX_COLOR_BLACK;

	if (0 == strlen(fmt))
		return;

	char szTmp[4096] = { 0 };

#ifdef EX_OS_WIN32
	vsnprintf_s(szTmp, 4096, 4095, fmt, valist);
	if (NULL != g_log_cfg.console_handle)
	{
		SetConsoleTextAttribute(g_log_cfg.console_handle, (WORD)((clrBackGround << 4) | clrForeGround));
		printf_s("%s", szTmp);
		fflush(stdout);
		SetConsoleTextAttribute(g_log_cfg.console_handle, EX_COLOR_GRAY);
	}
	else
	{
		OutputDebugStringA(szTmp);
	}
#else
	vsnprintf(szTmp, 4095, fmt, valist);
	printf("%s", szTmp);
	fflush(stdout);
#endif

	// #ifdef LOG_TO_FILE
	// 	g_log_file.WriteData(level, szTmp, strlen(szTmp));
	// #endif
	g_log_cfg.logfile.write(level, szTmp);
}

static void _ts_printf_w(int level, EX_COLORS clrBackGround, const wchar_t* fmt, va_list valist)
{
	if (NULL == fmt || 0 == wcslen(fmt))
		return;
	if (g_log_cfg.min_level > level)
		return;

	EX_COLORS clrForeGround = EX_COLOR_NORMAL;
	switch (level)
	{
	case EX_LOG_LEVEL_DEBUG:
		if (!g_log_cfg.debug_mode)
			return;
		clrForeGround = EX_COLOR_GRAY;
		break;
	case EX_LOG_LEVEL_VERBOSE:
		clrForeGround = EX_COLOR_LIGHT_GRAY;
		break;
	case EX_LOG_LEVEL_INFO:
		clrForeGround = EX_COLOR_LIGHT_MAGENTA;
		break;
	case EX_LOG_LEVEL_WARN:
		clrForeGround = EX_COLOR_LIGHT_RED;
		break;
	case EX_LOG_LEVEL_ERROR:
		clrForeGround = EX_COLOR_LIGHT_RED;
		break;
	}

	if (EX_COLOR_NORMAL == clrForeGround)
		clrForeGround = EX_COLOR_LIGHT_GRAY;
	if (EX_COLOR_NORMAL == clrBackGround)
		clrBackGround = EX_COLOR_BLACK;

	wchar_t szTmp[4096] = { 0 };

#ifdef EX_OS_WIN32
	_vsnwprintf_s(szTmp, 4096, 4095, fmt, valist);
	if (NULL != g_log_cfg.console_handle)
	{
		SetConsoleTextAttribute(g_log_cfg.console_handle, (WORD)((clrBackGround << 4) | clrForeGround));
		wprintf_s(_T("%s"), szTmp);
		fflush(stdout);
		SetConsoleTextAttribute(g_log_cfg.console_handle, EX_COLOR_GRAY);
	}
	else
	{
		OutputDebugStringW(szTmp);
	}
#else
	vswprintf(szTmp, 4095, fmt, valist);
	wprintf(L"%s", szTmp);
	fflush(stdout);
#endif

	g_log_cfg.logfile.write(level, szTmp);
}

#define EX_PRINTF_X(fn, level) \
void fn(const char* fmt, ...) \
{ \
	ExThreadSmartLock locker(g_log_lock); \
	va_list valist; \
	va_start(valist, fmt); \
	_ts_printf_a(level, EX_COLOR_BLACK, fmt, valist); \
	va_end(valist); \
} \
void fn(const wchar_t* fmt, ...) \
{ \
	ExThreadSmartLock locker(g_log_lock); \
	va_list valist; \
	va_start(valist, fmt); \
	_ts_printf_w(level, EX_COLOR_BLACK, fmt, valist); \
	va_end(valist); \
}

EX_PRINTF_X(ex_printf_d, EX_LOG_LEVEL_DEBUG)
EX_PRINTF_X(ex_printf_v, EX_LOG_LEVEL_VERBOSE)
EX_PRINTF_X(ex_printf_i, EX_LOG_LEVEL_INFO)
EX_PRINTF_X(ex_printf_w, EX_LOG_LEVEL_WARN)
EX_PRINTF_X(ex_printf_e, EX_LOG_LEVEL_ERROR)


#ifdef EX_OS_WIN32
void ex_printf_e_lasterror(const char* fmt, ...)
{
	ExThreadSmartLock locker(g_log_lock);

	va_list valist;
	va_start(valist, fmt);
	_ts_printf_a(EX_COLOR_LIGHT_RED, EX_COLOR_BLACK, fmt, valist);
	va_end(valist);

	//=========================================

	LPVOID lpMsgBuf;
	DWORD dw = GetLastError();

	FormatMessageA(FORMAT_MESSAGE_ALLOCATE_BUFFER | FORMAT_MESSAGE_FROM_SYSTEM | FORMAT_MESSAGE_IGNORE_INSERTS,
		NULL, dw, MAKELANGID(LANG_NEUTRAL, SUBLANG_DEFAULT),
		(LPSTR)&lpMsgBuf, 0, NULL);

	ex_printf_e(" - WinErr(%d): %s\n", dw, (LPSTR)lpMsgBuf);
	LocalFree(lpMsgBuf);
}
#endif

void ex_printf_bin(const ex_u8* bin_data, size_t bin_size, const char* fmt, ...)
{
	if (!g_log_cfg.debug_mode)
		return;

	ExThreadSmartLock locker(g_log_lock);

	va_list valist;
	va_start(valist, fmt);
	_ts_printf_a(EX_COLOR_GRAY, EX_COLOR_BLACK, fmt, valist);
	va_end(valist);

	ex_printf_d(" (%d/0x%02x Bytes)\n", bin_size, bin_size);

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

		ex_printf_d("%s", szTmp);

		offset += thisline;
		line += thisline;
	}

	fflush(stdout);
}

bool ExLogFile::init(const ex_wstr& log_path, const ex_wstr& log_name, ex_u32 max_filesize, ex_u8 max_count)
{
	m_max_filesize = max_filesize;
	m_max_count = max_count;

	m_filename = log_name;

	m_path = log_path;
	ex_abspath(m_path);

	m_fullname = m_path;
	ex_path_join(m_fullname, false, log_name.c_str(), NULL);

	return _open_file();
}


bool ExLogFile::_open_file()
{
	if (m_hFile)
	{
		fclose(m_hFile);
		m_hFile = NULL;
	}

	ex_astr _fullname;
	ex_wstr2astr(m_fullname, _fullname);
#ifdef EX_OS_WIN32
	// 注意：这里必须使用 _fsopen 来指定共享读方式打开日志文件，否则进程退出前别的进程无法查看日志文件内容。
	m_hFile = _fsopen(_fullname.c_str(), "a", _SH_DENYWR);
#else
	m_hFile = fopen(_fullname.c_str(), "a");
#endif

	if (NULL == m_hFile)
	{
		return false;
}
	fseek(m_hFile, 0, SEEK_END);
	m_filesize = ftell(m_hFile);

	return _rotate_file();
}

bool ExLogFile::_rotate_file(void)
{
	if (m_filesize < m_max_filesize)
		return true;

	if (m_hFile)
	{
		fclose(m_hFile);
		m_hFile = NULL;
	}

	//if (!_backup_file())
	//	return false;

	// make a name for backup file.
	wchar_t _tmpname[64] = { 0 };
#ifdef EX_OS_WIN32
	SYSTEMTIME st;
	GetLocalTime(&st);
	//StringCbPrintf(_tmpname, 64, L"%s.%04d%02d%02d%02d%02d%02d.bak", m_filename.c_str(), st.wYear, st.wMonth, st.wDay, st.wHour, st.wMinute, st.wSecond);
	swprintf_s(_tmpname, 64, L"%s.%04d%02d%02d%02d%02d%02d.bak", m_filename.c_str(), st.wYear, st.wMonth, st.wDay, st.wHour, st.wMinute, st.wSecond);
	// 	sprintf_s(szBaseNewFileLogName, EX_LOG_PATH_MAX_LEN, "%04d%02d%02d%02d%02d%02d",
	// 		st.wYear, st.wMonth, st.wDay, st.wHour, st.wMinute, st.wSecond);
#else
	time_t timep;
	time(&timep);
	struct tm *p = localtime(&timep);
	if (p == NULL)
		return false;

	swprintf(_tmpname, L"%s.%04d%02d%02d%02d%02d%02d.bak", m_filename.c_str(), p->tm_year + 1900, p->tm_mon + 1, p->tm_mday, p->tm_hour, p->tm_min, p->tm_sec);
	// 	sprintf(szBaseNewFileLogName, "%04d%02d%02d%02d%02d%02d",
	// 		p->tm_year + 1900, p->tm_mon + 1, p->tm_mday, p->tm_hour, p->tm_min, p->tm_sec);
#endif

	ex_wstr _new_fullname(m_path);
	ex_path_join(_new_fullname, false, _tmpname, NULL);

#ifdef EX_OS_WIN32
	if (!MoveFileW(m_fullname.c_str(), _new_fullname.c_str()))
	{
		EXLOGE_WIN("can not rename log file, remove old one and try again.");
		DeleteFileW(_new_fullname.c_str());
		if (!MoveFileW(m_fullname.c_str(), _new_fullname.c_str()))
			return false;
	}
#else
	ex_astr _a_fullname;
	ex_astr _a_new_fullname;
	ex_wstr2astr(m_fullname, _a_fullname);
	ex_wstr2astr(_new_fullname, _a_new_fullname);

	if (rename(_a_fullname.c_str(), _a_new_fullname.c_str()) != 0)
	{
		remove(_a_new_fullname.c_str());
		if (0 != (rename(_a_fullname.c_str(), _a_new_fullname.c_str())))
			return false;
	}
#endif

	return _open_file();
}

#if 0
bool ExLogFile::_backup_file()
{
	char szNewFileLogName[EX_LOG_PATH_MAX_LEN] = { 0 };
	char szBaseNewFileLogName[EX_LOG_PATH_MAX_LEN] = { 0 };
#ifdef EX_OS_WIN32
	SYSTEMTIME st;
	GetLocalTime(&st);
	sprintf_s(szNewFileLogName, EX_LOG_PATH_MAX_LEN, "%s\\%04d%02d%02d%02d%02d%02d.log",
		m_log_file_dir.c_str(), st.wYear, st.wMonth, st.wDay, st.wHour, st.wMinute, st.wSecond);

	sprintf_s(szBaseNewFileLogName, EX_LOG_PATH_MAX_LEN, "%04d%02d%02d%02d%02d%02d",
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
	sprintf(szNewFileLogName, "%s/%04d%02d%02d%02d%02d%02d.log",
		m_log_file_dir.c_str(), p->tm_year + 1900, p->tm_mon + 1, p->tm_mday, p->tm_hour, p->tm_min, p->tm_sec);
	sprintf(szBaseNewFileLogName, "%04d%02d%02d%02d%02d%02d",
		p->tm_year + 1900, p->tm_mon + 1, p->tm_mday, p->tm_hour, p->tm_min, p->tm_sec);
#endif
	if (m_hFile)
	{
		fclose(m_hFile);
		m_hFile = 0;
	}
#ifdef EX_OS_WIN32
	if (!MoveFileA(m_path.c_str(), szNewFileLogName))
	{
		DWORD dwError = GetLastError();

		DeleteFileA(szNewFileLogName);

		MoveFileA(m_path.c_str(), szNewFileLogName);
	}
#else
	if (rename(m_path.c_str(), szNewFileLogName) != 0)
	{
		remove(szNewFileLogName);

		rename(m_path.c_str(), szNewFileLogName);
	}
#endif
	unsigned long long value = atoll(szBaseNewFileLogName);
	if (value != 0)
	{
		m_log_file_list.push_back(value);
	}
	int try_count = 0;
	while ((m_log_file_list.size() > m_max_count))
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
		sprintf(szDeleteFile, "%s/%llu.log", m_log_file_dir.c_str(), value);
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
#endif // if 0

bool ExLogFile::write(int level, const char* buf)
{
	if (NULL == m_hFile)
		return false;

	size_t len = strlen(buf);

	if (len > EX_LOG_CONTENT_MAX_LEN)
		return false;

	char szTime[100] = { 0 };
#ifdef EX_OS_WIN32
	SYSTEMTIME st;
	GetLocalTime(&st);
	sprintf_s(szTime, 100, "[%04d-%02d-%02d %02d:%02d:%02d] ", st.wYear, st.wMonth, st.wDay, st.wHour, st.wMinute, st.wSecond);
#else
	time_t timep;
	struct tm *p;
	time(&timep);
	p = localtime(&timep);
	if (p == NULL)
		return false;
	sprintf(szTime, "[%04d-%02d-%02d %02d:%02d:%02d] , p->tm_year + 1900, p->tm_mon + 1, p->tm_mday, p->tm_hour, p->tm_min, p->tm_sec);
#endif

	int lenTime = strlen(szTime);
	fwrite(szTime, lenTime, 1, m_hFile);
	m_filesize += lenTime;
	fwrite(buf, len, 1, m_hFile);
	m_filesize += len;

	fflush(m_hFile);

	return _rotate_file();
}

bool ExLogFile::write(int level, const wchar_t* buf)
{
	ex_astr _buf;
	ex_wstr2astr(buf, _buf, EX_CODEPAGE_UTF8);
	return write(level, _buf.c_str());
}


#if 0
bool ExLogFile::_load_file_list()
{
#ifdef EX_OS_WIN32
	struct _finddata_t data;
	std::string log_match = m_log_file_dir;
	log_match += "\\*.log";
	//log_match += "*.log";
	long hnd = _findfirst(log_match.c_str(), &data);    // find the first file match `*.log`
	if (hnd < 0)
	{
		return false;
	}
	int  nRet = (hnd < 0) ? -1 : 1;
	int count = 0;
	while (nRet > 0)
	{
		if (data.attrib == _A_SUBDIR)
		{
			// do nothing to a folder.
		}
		else
		{
			if (m_filename.compare(data.name) == 0)
			{
			}
			else
			{
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
		count++;
		if (count > 100)
		{
			break;
		}
	}
	_findclose(hnd);
#else
	DIR *dir;

	struct dirent *ptr;

	dir = opendir(m_log_file_dir.c_str());

	while ((ptr = readdir(dir)) != NULL)
	{
		if (ptr->d_type == 8)
		{
			char temp_file_name[PATH_MAX] = { 0 };
			strcpy(temp_file_name, ptr->d_name);
			if (m_filename.compare(temp_file_name) == 0)
			{

			}
			else
			{
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
	}

	closedir(dir);
#endif // EX_OS_WIN32

	std::sort(m_log_file_list.begin(), m_log_file_list.end(), std::less<unsigned long long>());
	return true;
}
#endif // if 0
