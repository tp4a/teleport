#include <ex/ex_platform.h>
#include <ex/ex_util.h>
#include <ex/ex_str.h>
#include <ex/ex_log.h>

EX_BOOL ex_initialize(const char *lc_ctype) {
#ifdef EX_OS_UNIX
    const char *_lc_default = "en_US.UTF-8";
    const char *_lc_ctype = NULL;
    char *_loc = NULL;
    if (NULL == lc_ctype)
        _lc_ctype = _lc_default;
    else
        _lc_ctype = lc_ctype;

    _loc = setlocale(LC_CTYPE, _lc_ctype);

    if (NULL == _loc)
        return EX_FALSE;
//	if(0 != strcmp(_loc, _lc_ctype))
//		return EX_FALSE;
    return EX_TRUE;

#else
    return EX_TRUE;
#endif
}


void ex_free(void *buffer) {
    if (NULL == buffer)
        return;
    free(buffer);
}

const ex_u8 *ex_memmem(const ex_u8 *haystack, size_t haystacklen, const ex_u8 *needle, size_t needlelen) {
    const ex_u8 *cursor = NULL;
    const ex_u8 *last_possible_needle_location = haystack + haystacklen - needlelen;

    /** Easy answers */
    if (needlelen > haystacklen) return (NULL);
    if (needle == NULL) return (NULL);
    if (haystack == NULL) return (NULL);
    if (needlelen == 0) return (NULL);
    if (haystacklen == 0) return (NULL);

    for (cursor = haystack; cursor <= last_possible_needle_location; cursor++) {
        if (memcmp(needle, cursor, needlelen) == 0)
            return cursor;
    }
    return (NULL);
}

void ex_mem_reverse(ex_u8 *p, size_t l) {
    ex_u8 temp = 0;
    size_t i = 0, j = 0;

    for (i = 0, j = l - 1; i < j; i++, j--) {
        temp = p[i];
        p[i] = p[j];
        p[j] = temp;
    }
}

void ex_printf(const char *fmt, ...) {
    if (NULL == fmt || 0 == strlen(fmt))
        return;

    va_list valist;
    va_start(valist, fmt);
    //_ts_printf_a(TS_COLOR_GRAY, TS_COLOR_BLACK, fmt, valist);

    char _tmp[4096] = {0};
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

void ex_wprintf(const wchar_t *fmt, ...) {
    if (NULL == fmt || 0 == wcslen(fmt))
        return;

    va_list valist;
    va_start(valist, fmt);

    wchar_t _tmp[4096] = {0};
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

ex_u64 ex_get_tick_count(void) {
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
    return ((ex_u64) ts.tv_sec * 1000 + (ex_u64) ts.tv_nsec / 1000000);
#endif
}

void ex_sleep_ms(int ms) {
#ifdef EX_OS_WIN32
    Sleep(ms);
#else
    usleep(ms * 1000);
#endif
}

EX_BOOL ex_localtime_now(int *t, struct tm *dt) {
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
        return EX_FALSE;
    if (NULL != dt)
        memcpy(dt, _tmp, sizeof(struct tm));
#endif

    if (NULL != t)
        *t = (int) timep;

    return EX_TRUE;
}

FILE *ex_fopen(const ex_wstr &filename, const wchar_t *mode) {
    FILE *f = NULL;
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

FILE* ex_fopen(const ex_astr& filename, const char* mode) {
	FILE *f = NULL;
#ifdef EX_OS_WIN32
	errno_t err = 0;
	err = fopen_s(&f, filename.c_str(), mode);
	if (0 == err)
		return f;
	else
		return NULL;
#else
	f = fopen(filename.c_str(), mode);
	return f;
#endif
}


bool ex_read_text_file(const ex_wstr &strFileName, ex_astr& file_content) {
    std::vector<char> tmp;

    FILE *f = ex_fopen(strFileName, L"rb");
    if (f == NULL)
        return false;

    fseek(f, 0L, SEEK_END);
    unsigned long ulFileSize = (unsigned long) ftell(f);
    if (-1 == ulFileSize) {
        fclose(f);
        return false;
    }

    unsigned long ulBufSize = ulFileSize + 1;

    tmp.resize(ulBufSize);
    memset(&tmp[0], 0, ulBufSize);

    fseek(f, 0L, SEEK_SET);
    unsigned long ulRead = fread(&tmp[0], 1, ulFileSize, f);

    fclose(f);

    if(ulRead != ulFileSize) {
        return false;
    }

    if ((ulFileSize > 3) && (0 == memcmp(&tmp[0], "\xEF\xBB\xBF", 3))) {
        file_content = &tmp[3];
    } else {
        file_content = &tmp[0];
    }

    return true;
}

bool ex_write_text_file(const ex_wstr &strFileName, const ex_astr& file_content) {
    FILE *f = ex_fopen(strFileName, L"wb");
    if (f == NULL)
        return false;

    unsigned long ulWrite = fwrite(file_content.c_str(), 1, file_content.length(), f);
    fclose(f);

    return ulWrite == file_content.length();
}

EX_DYLIB_HANDLE ex_dlopen(const wchar_t *dylib_path) {
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
    if (!ex_wstr2astr(dylib_path, path, EX_CODEPAGE_UTF8)) {
        EXLOGE("convert dylib_path failed.\n");
        return NULL;
    }

    handle = dlopen(path.c_str(), RTLD_NOW | RTLD_GLOBAL);

    if (NULL == handle) {
        EXLOGE("dlopen() failed: %s.\n", dlerror());
        return NULL;
    }
#endif

    return handle;
}

void ex_dlclose(EX_DYLIB_HANDLE dylib) {
#ifdef EX_OS_WIN32
    FreeLibrary(dylib);
#else
    dlclose(dylib);
#endif
}

// static int _inet_ntop4(const unsigned char *src, char *dst, size_t size) {
//     static const char fmt[] = "%u.%u.%u.%u";
//     char tmp[32];
//     int l;
// 
//     l = snprintf(tmp, sizeof(tmp), fmt, src[0], src[1], src[2], src[3]);
//     if (l <= 0 || (size_t) l >= size) {
//         return -1;
//     }
//     ex_strcpy(dst, size, tmp);
//     dst[size - 1] = '\0';
//     return 0;
// }
// 
// int ex_ip4_name(const struct sockaddr_in *src, char *dst, size_t size) {
//     return _inet_ntop4((const unsigned char *) &(src->sin_addr), dst, size);
// }
// 
static const char * _inet_ntop_v4(const void *src, char *dst, size_t size)
{
	const char digits[] = "0123456789";
	int i;
	struct in_addr *addr = (struct in_addr *)src;
	u_long a = ntohl(addr->s_addr);
	const char *orig_dst = dst;

	if (size < EX_IPV4_NAME_LEN) {
		//errno = ENOSPC;
		return NULL;
	}
	for (i = 0; i < 4; ++i) {
		int n = (a >> (24 - i * 8)) & 0xFF;
		int non_zerop = 0;

		if (non_zerop || n / 100 > 0) {
			*dst++ = digits[n / 100];
			n %= 100;
			non_zerop = 1;
		}
		if (non_zerop || n / 10 > 0) {
			*dst++ = digits[n / 10];
			n %= 10;
			non_zerop = 1;
		}
		*dst++ = digits[n];
		if (i != 3)
			*dst++ = '.';
	}
	*dst++ = '\0';
	return orig_dst;
}

#define IN6ADDRSZ 16 
#define INT16SZ 2
static const char * _inet_ntop_v6(const ex_u8 *src, char *dst, size_t size)
{
	/*
	* Note that int32_t and int16_t need only be "at least" large enough
	* to contain a value of the specified size.  On some systems, like
	* Crays, there is no such thing as an integer variable with 16 bits.
	* Keep this in mind if you think this function should have been coded
	* to use pointer overlays.  All the world's not a VAX.
	*/
	char  tmp[EX_IPV6_NAME_LEN];
	char *tp;
	struct {
		long base;
		long len;
	} best, cur;
	u_long words[IN6ADDRSZ / INT16SZ];
	int    i;

	/* Preprocess:
	*  Copy the input (bytewise) array into a wordwise array.
	*  Find the longest run of 0x00's in src[] for :: shorthanding.
	*/
	memset(words, 0, sizeof(words));
	for (i = 0; i < IN6ADDRSZ; i++)
		words[i / 2] |= (src[i] << ((1 - (i % 2)) << 3));

	best.base = -1;
	cur.base = -1;
	for (i = 0; i < (IN6ADDRSZ / INT16SZ); i++)
	{
		if (words[i] == 0)
		{
            if (cur.base == -1) {
                cur.base = i;
                cur.len = 1;
            }
            else{
                cur.len++;
            }
		}
		else if (cur.base != -1)
		{
			if (best.base == -1 || cur.len > best.len)
				best = cur;
			cur.base = -1;
		}
	}
	if ((cur.base != -1) && (best.base == -1 || cur.len > best.len))
		best = cur;
	if (best.base != -1 && best.len < 2)
		best.base = -1;

	/* Format the result.
	*/
	tp = tmp;
	size_t tmp_size = 0;
	size_t offset = 0;
	for (i = 0; i < (IN6ADDRSZ / INT16SZ); i++)
	{
		/* Are we inside the best run of 0x00's?
		*/
		if (best.base != -1 && i >= best.base && i < (best.base + best.len))
		{
			if (i == best.base) {
				*tp++ = ':';
				offset += 1;
			}
			continue;
		}

		/* Are we following an initial run of 0x00s or any real hex?
		*/
		if (i != 0) {
			*tp++ = ':';
			offset += 1;
		}

		/* Is this address an encapsulated IPv4?
		*/
		if (i == 6 && best.base == 0 &&
			(best.len == 6 || (best.len == 5 && words[5] == 0xffff)))
		{
			if (!_inet_ntop_v4(src + 12, tp, sizeof(tmp) - (tp - tmp)))
			{
				//errno = ENOSPC;
				return (NULL);
			}
			tmp_size = strlen(tp);
			tp += tmp_size;
			offset += tmp_size;
			break;
		}
		//tp += ex_strformat(tp, "%lX", words[i]);
		tmp_size = ex_strformat(tp, EX_IPV6_NAME_LEN-offset, "%lX", words[i]);
		tp += tmp_size;
		offset += tmp_size;
	}

	/* Was it a trailing run of 0x00's?
	*/
	if (best.base != -1 && (best.base + best.len) == (IN6ADDRSZ / INT16SZ))
		*tp++ = ':';
	*tp++ = '\0';

	/* Check for overflow, copy, and we're done.
	*/
	if ((size_t)(tp - tmp) > size)
	{
		//errno = ENOSPC;
		return (NULL);
	}
	//return strcpy(dst, tmp);
	return ex_strcpy(dst, size, tmp);
	//return (NULL);
}

const char* ex_inet_ntop(int af, const void *src, char *dst, size_t size) {
	switch (af) {
	case AF_INET:
		return _inet_ntop_v4(src, dst, size);
	case AF_INET6:
		return _inet_ntop_v6((const ex_u8*)src, dst, size);
	default:
		errno = EAFNOSUPPORT;
		return NULL;
	}
}

int ex_ip4_name(const struct sockaddr_in *src, char *dst, size_t size) {
	if (NULL == _inet_ntop_v4((const unsigned char *)&(src->sin_addr), dst, size))
		return -1;
	return 0;
}

