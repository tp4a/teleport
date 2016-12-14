#include <ex/ex_platform.h>
#include <ex/ex_util.h>
#include <ex/ex_str.h>

// #include <vld.h>

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
	return ((ts_u64)ts.tv_sec * 1000 + (ts_u64)ts.tv_nsec / 1000000);
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
