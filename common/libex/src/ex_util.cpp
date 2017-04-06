#include <ex/ex_platform.h>
#include <ex/ex_util.h>
#include <ex/ex_str.h>
#include <ex/ex_log.h>

EX_BOOL ex_initialize(const char* lc_ctype)
{
#ifdef EX_OS_UNIX
	const char* _lc_default = "en_US.UTF-8";
	const char* _lc_ctype = NULL;
	char* _loc = NULL;
	if(NULL == lc_ctype)
		_lc_ctype = _lc_default;
	else
		_lc_ctype = lc_ctype;

	_loc = setlocale(LC_CTYPE, _lc_ctype);

	if(NULL == _loc)
		return EX_FALSE;
//	if(0 != strcmp(_loc, _lc_ctype))
//		return EX_FALSE;
	return EX_TRUE;

#else
	return EX_TRUE;
#endif
}


void ex_free(void* buffer)
{
	if (NULL == buffer)
		return;
	free(buffer);
}

const ex_u8* ex_memmem(const ex_u8* haystack, size_t haystacklen, const ex_u8* needle, size_t needlelen)
{
	const ex_u8* cursor = NULL;
	const ex_u8* last_possible_needle_location = haystack + haystacklen - needlelen;

	/** Easy answers */
	if (needlelen > haystacklen) return(NULL);
	if (needle == NULL) return(NULL);
	if (haystack == NULL) return(NULL);
	if (needlelen == 0) return(NULL);
	if (haystacklen == 0) return(NULL);

	for (cursor = haystack; cursor <= last_possible_needle_location; cursor++)
	{
		if (memcmp(needle, cursor, needlelen) == 0)
			return cursor;
	}
	return(NULL);
}

void ex_mem_reverse(ex_u8* p, size_t l)
{
	ex_u8 temp = 0;
	size_t i = 0, j = 0;

	for (i = 0, j = l - 1; i < j; i++, j--)
	{
		temp = p[i];
		p[i] = p[j];
		p[j] = temp;
	}
}

void ex_printf(const char* fmt, ...)
{
	if (NULL == fmt || 0 == strlen(fmt))
		return;

	va_list valist;
	va_start(valist, fmt);
	//_ts_printf_a(TS_COLOR_GRAY, TS_COLOR_BLACK, fmt, valist);

	char _tmp[4096] = { 0 };
#ifdef EX_OS_WIN32
	vsnprintf_s(_tmp, 4096, 4095, fmt, valist);
	printf_s("%s", _tmp);
	fflush(stdout);
#else
	vsnprintf(_tmp, 4095, fmt, valist);
	printf("%s", _tmp);
	fflush(stdout);
#endif

	va_end(valist);
}

void ex_wprintf(const wchar_t* fmt, ...)
{
	if (NULL == fmt || 0 == wcslen(fmt))
		return;

	va_list valist;
	va_start(valist, fmt);

	wchar_t _tmp[4096] = { 0 };
#ifdef EX_OS_WIN32
	_vsnwprintf_s(_tmp, 4096, 4095, fmt, valist);
	wprintf_s(L"%s", _tmp);
	fflush(stdout);
#else
	vswprintf(_tmp, 4095, fmt, valist);

	ex_astr _astr_tmp;
	ex_wstr2astr(_tmp, _astr_tmp);
	printf("%s", _astr_tmp.c_str());

	fflush(stdout);
#endif

	va_end(valist);
}

ex_u64 ex_get_tick_count(void)
{
#ifdef EX_OS_WIN32
#	if (_WIN32_WINNT >= 0x0600)
	return GetTickCount64();
#	else
	LARGE_INTEGER TicksPerSecond = { 0 };
	LARGE_INTEGER Tick;
	if (!TicksPerSecond.QuadPart)
		QueryPerformanceFrequency(&TicksPerSecond);
	QueryPerformanceCounter(&Tick);
	ex_u64 Seconds = Tick.QuadPart / TicksPerSecond.QuadPart;
	ex_u64 LeftPart = Tick.QuadPart - (TicksPerSecond.QuadPart*Seconds);
	ex_u64 MillSeconds = LeftPart * 1000 / TicksPerSecond.QuadPart;
	ex_u64 Ret = Seconds * 1000 + MillSeconds;
	return Ret;
#	endif
#else
	struct timespec ts;
	clock_gettime(CLOCK_MONOTONIC, &ts);
	return ((ex_u64)ts.tv_sec * 1000 + (ex_u64)ts.tv_nsec / 1000000);
#endif
}

void ex_sleep_ms(int ms)
{
#ifdef EX_OS_WIN32
	Sleep(ms);
#else
	usleep(ms * 1000);
#endif
}

EX_BOOL ex_localtime_now(int* t, struct tm* dt)
{
// 	if (NULL == dt)
// 		return EX_FALSE;

	//struct tm *_tmp;

#ifdef EX_OS_WIN32
	struct tm _tmp;
	__time32_t timep;
	_time32(&timep);
	if (0 != _localtime32_s(&_tmp, &timep))
		return EX_FALSE;
	if(NULL != dt)
		memcpy(dt, &_tmp, sizeof(struct tm));
#else
	struct tm *_tmp;
	time_t timep;
	time(&timep);
	_tmp = localtime(&timep);   //get server's time
	if (_tmp == NULL)
		return NULL;
	if(NULL != dt)
		memcpy(dt, _tmp, sizeof(struct tm));
#endif

	if (NULL != t)
		*t = (int)timep;

	return EX_TRUE;
}

FILE* ex_fopen(const ex_wstr& filename, const wchar_t* mode)
{
	FILE* f = NULL;
#ifdef EX_OS_WIN32
	errno_t err = 0;
	err = _wfopen_s(&f, filename.c_str(), mode);
	if (0 == err)
		return f;
	else
		return NULL;
#else
	ex_astr _fname;
	ex_wstr2astr(filename, _fname);
	ex_astr _mode;
	ex_wstr2astr(mode, _mode);
	f = fopen(_fname.c_str(), _mode.c_str());
	return f;
#endif
}


EX_DYLIB_HANDLE ex_dlopen(const wchar_t* dylib_path)
{
	EX_DYLIB_HANDLE handle = NULL;

#ifdef EX_OS_WIN32
	handle = LoadLibraryExW(dylib_path, NULL, LOAD_WITH_ALTERED_SEARCH_PATH);
	if (NULL == handle)
	{
		EXLOGE_WIN(L"LoadLibraryEx('%ls') failed.\n", dylib_path);
		return NULL;
	}
#else
	ex_astr path;
	if (!ex_wstr2astr(dylib_path, path, EX_CODEPAGE_UTF8))
	{
		EXLOGE("convert dylib_path failed.\n");
		return NULL;
	}

	handle = dlopen(path.c_str(), RTLD_NOW | RTLD_GLOBAL);

	if (NULL == handle)
	{
		EXLOGE("dlopen() failed: %s.\n", dlerror());
		return NULL;
	}
#endif

	return handle;
}

void ex_dlclose(EX_DYLIB_HANDLE dylib)
{
#ifdef EX_OS_WIN32
	FreeLibrary(dylib);
#else
	dlclose(dylib);
#endif
}

static int _inet_ntop4(const unsigned char *src, char *dst, size_t size) {
	static const char fmt[] = "%u.%u.%u.%u";
	char tmp[32];
	int l;

	l = snprintf(tmp, sizeof(tmp), fmt, src[0], src[1], src[2], src[3]);
	if (l <= 0 || (size_t)l >= size) {
		return -1;
	}
	ex_strcpy(dst, size, tmp);
	dst[size - 1] = '\0';
	return 0;
}

int ex_ip4_name(const struct sockaddr_in* src, char* dst, size_t size)
{
	return _inet_ntop4((const unsigned char*)&(src->sin_addr), dst, size);
}

