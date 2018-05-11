#include <ex/ex_platform.h>
#include <ex/ex_str.h>
#include <ex/ex_util.h>

char* ex_strcpy(char* target, size_t size, const char* source)
{
	if (target == source)
		return target;

#ifdef EX_OS_WIN32
	if (SUCCEEDED(StringCchCopyA(target, size, source)))
		return target;
	else
		return NULL;
#else
	size_t len = strlen(source);
	if (size > len)
	{
		return strcpy(target, source);
	}
	else
	{
		memmove(target, source, size - 1);
		return NULL;
	}
#endif
}

wchar_t* ex_wcscpy(wchar_t* target, size_t size, const wchar_t* source)
{
	if (target == source)
		return target;

#ifdef EX_OS_WIN32
	if (SUCCEEDED(StringCchCopyW(target, size, source)))
		return target;
	else
		return NULL;
#else
	size_t len = wcslen(source);
	if (size > len)
	{
		return wcscpy(target, source);
	}
	else
	{
		memmove(target, source, (size - 1)*sizeof(wchar_t));
		return NULL;
	}
#endif
}

char* ex_strdup(const char* src)
{
	if (NULL == src)
		return NULL;
	size_t len = strlen(src) + 1;
	char* ret = (char*)calloc(1, len);
	memcpy(ret, src, len);
	return ret;
}

wchar_t* ex_wcsdup(const wchar_t* src)
{
	if (NULL == src)
		return NULL;
	size_t len = wcslen(src) + 1;
	wchar_t* ret = (wchar_t*)calloc(sizeof(wchar_t), len);
	memcpy(ret, src, sizeof(wchar_t)*len);
	return ret;
}

wchar_t* ex_str2wcs_alloc(const char* in_buffer, int code_page)
{
	wchar_t* out_buffer = NULL;
#ifdef EX_OS_WIN32
	int wlen = 0;
	UINT _cp = 0;
	if (code_page == EX_CODEPAGE_ACP)
		_cp = CP_ACP;
	else if (code_page == EX_CODEPAGE_UTF8)
		_cp = CP_UTF8;

	wlen = MultiByteToWideChar(_cp, 0, in_buffer, -1, NULL, 0);
	if (0 == wlen)
		return NULL;

	out_buffer = (wchar_t*)calloc(wlen + 1, sizeof(wchar_t));
	if (NULL == out_buffer)
		return NULL;

	wlen = MultiByteToWideChar(_cp, 0, in_buffer, -1, out_buffer, wlen);
	if (0 == wlen)
	{
		free(out_buffer);
		return NULL;
	}

#else
	size_t wlen = 0;
	wlen = mbstowcs(NULL, in_buffer, 0);
	if (wlen <= 0)
		return NULL;

	out_buffer = (wchar_t*)calloc(wlen + 1, sizeof(wchar_t));
	if (NULL == out_buffer)
		return NULL;

	wlen = mbstowcs(out_buffer, in_buffer, wlen);
	if (wlen <= 0)
	{
		free(out_buffer);
		return NULL;
	}

#endif

	return out_buffer;
}


char* ex_wcs2str_alloc(const wchar_t* in_buffer, int code_page)
{
	char* out_buffer = NULL;

	if(NULL == in_buffer)
		return NULL;

#ifdef EX_OS_WIN32
	int len = 0;
	UINT _cp = 0;
	if (code_page == EX_CODEPAGE_ACP)
		_cp = CP_ACP;
	else if (code_page == EX_CODEPAGE_UTF8)
		_cp = CP_UTF8;

	len = WideCharToMultiByte(_cp, 0, in_buffer, -1, NULL, 0, NULL, NULL);
	if (0 == len)
		return NULL;

	out_buffer = (char*)calloc(len + 1, sizeof(char));
	if (NULL == out_buffer)
		return NULL;

	len = WideCharToMultiByte(_cp, 0, in_buffer, -1, out_buffer, len, NULL, NULL);
	if (0 == len)
	{
		free(out_buffer);
		return NULL;
	}

#else
	size_t len = 0;
	len = wcstombs(NULL, in_buffer, 0);
	if (len <= 0)
		return NULL;

	out_buffer = (char*)calloc(len + 1, sizeof(char));
	if (NULL == out_buffer)
		return NULL;

	len = wcstombs(out_buffer, in_buffer, len);
	if (len <= 0)
	{
		free(out_buffer);
		return NULL;
	}

#endif

	return out_buffer;
}

wchar_t** ex_make_wargv(int argc, char** argv)
{
	int i = 0;
	wchar_t** ret = NULL;

	ret = (wchar_t**)calloc(argc + 1, sizeof(wchar_t*));
	if (!ret)
	{
		return NULL;
	}

	for (i = 0; i < argc; ++i)
	{
		ret[i] = ex_str2wcs_alloc(argv[i], EX_CODEPAGE_DEFAULT);
		if (NULL == ret[i])
			goto err;
	}

	return ret;

err:
	ex_free_wargv(argc, ret);
	return NULL;
}

void ex_free_wargv(int argc, wchar_t** argv)
{
	int i = 0;
	for (i = 0; i < argc; ++i)
		free(argv[i]);

	free(argv);
}

EX_BOOL ex_str_only_white_space(const wchar_t* src)
{
	if (ex_only_white_space(src))
		return EX_TRUE;
	else
		return EX_FALSE;
}

EX_BOOL ex_wcs_only_white_space(const char* src)
{
	if (ex_only_white_space(src))
		return EX_TRUE;
	else
		return EX_FALSE;
}

int ex_strformat(char* out_buf, size_t buf_size, const char* fmt, ...)
{
	int ret = 0;
	va_list valist;
	va_start(valist, fmt);
	//_ts_printf_a(level, EX_COLOR_BLACK, fmt, valist);
#ifdef EX_OS_WIN32
	ret = vsnprintf(out_buf, buf_size, fmt, valist);
#else
	ret = vsprintf(out_buf, fmt, valist);
#endif
	va_end(valist);
	return ret;
}

int ex_wcsformat(wchar_t* out_buf, size_t buf_size, const wchar_t* fmt, ...)
{
	int ret = 0;
	va_list valist;
	va_start(valist, fmt);
	//_ts_printf_a(level, EX_COLOR_BLACK, fmt, valist);
#ifdef EX_OS_WIN32
	//ret = vsnprintf(out_buf, buf_size, fmt, valist);
	ret = _vsnwprintf_s(out_buf, buf_size, buf_size, fmt, valist);
#else
	//ret = vsprintf(out_buf, fmt, valist);
	ret = vswprintf(out_buf, buf_size, fmt, valist);
#endif
	va_end(valist);
	return ret;
}


#ifdef __cplusplus
bool ex_wstr2astr(const ex_wstr& in_str, ex_astr& out_str, int code_page/* = EX_CODEPAGE_DEFAULT*/)
{
	return ex_wstr2astr(in_str.c_str(), out_str, code_page);
}

bool ex_wstr2astr(const wchar_t* in_str, ex_astr& out_str, int code_page/* = EX_CODEPAGE_DEFAULT*/)
{
	char* astr = ex_wcs2str_alloc(in_str, code_page);
	if (NULL == astr)
		return false;

	out_str = astr;
	ex_free(astr);
	return true;
}

bool ex_astr2wstr(const ex_astr& in_str, ex_wstr& out_str, int code_page/* = EX_CODEPAGE_DEFAULT*/)
{
	return ex_astr2wstr(in_str.c_str(), out_str, code_page);
}

bool ex_astr2wstr(const char* in_str, ex_wstr& out_str, int code_page/* = EX_CODEPAGE_DEFAULT*/)
{
	wchar_t* wstr = ex_str2wcs_alloc(in_str, code_page);
	if (NULL == wstr)
		return false;

	out_str = wstr;
	ex_free(wstr);
	return true;
}

bool ex_only_white_space(const ex_astr& str_check)
{
	ex_astr::size_type pos = 0;
	ex_astr strFilter(" \t\r\n");
	pos = str_check.find_first_not_of(strFilter);
	if (ex_astr::npos == pos)
		return true;
	else
		return false;
}

bool ex_only_white_space(const ex_wstr& str_check)
{
	ex_wstr::size_type pos = 0;
	ex_wstr strFilter(L" \t\r\n");
	pos = str_check.find_first_not_of(strFilter);
	if (ex_wstr::npos == pos)
		return true;
	else
		return false;
}

void ex_remove_white_space(ex_astr& str_fix, int ulFlag /*= EX_RSC_ALL*/)
{
	ex_astr::size_type pos = 0;
	ex_astr strFilter(" \t\r\n");

	if (ulFlag & EX_RSC_BEGIN)
	{
		pos = str_fix.find_first_not_of(strFilter);
		if (ex_astr::npos != pos)
			str_fix.erase(0, pos);
		// FIXME
	}
	if (ulFlag & EX_RSC_END)
	{
		pos = str_fix.find_last_not_of(strFilter);
		if (ex_astr::npos != pos)
			str_fix.erase(pos + 1);
		// FIXME
	}
}

void ex_remove_white_space(ex_wstr& str_fix, int ulFlag /*= EX_RSC_ALL*/)
{
	ex_wstr::size_type pos = 0;
	ex_wstr strFilter(L" \t\r\n");

	if (ulFlag & EX_RSC_BEGIN)
	{
		pos = str_fix.find_first_not_of(strFilter);
		if (ex_wstr::npos != pos)
			str_fix.erase(0, pos);
		// FIXME
	}
	if (ulFlag & EX_RSC_END)
	{
		pos = str_fix.find_last_not_of(strFilter);
		if (ex_wstr::npos != pos)
			str_fix.erase(pos + 1);
		// FIXME
	}
}

ex_astr& ex_replace_all(ex_astr& str, const ex_astr& old_value, const ex_astr& new_value)
{
	for (ex_astr::size_type pos(0); pos != ex_astr::npos; pos += new_value.length())
	{
		if ((pos = str.find(old_value, pos)) != ex_astr::npos)
			str.replace(pos, old_value.length(), new_value);
		else
			break;
	}

	return str;
}

ex_wstr& ex_replace_all(ex_wstr& str, const ex_wstr& old_value, const ex_wstr& new_value)
{
	for (ex_wstr::size_type pos(0); pos != ex_wstr::npos; pos += new_value.length())
	{
		if ((pos = str.find(old_value, pos)) != ex_wstr::npos)
			str.replace(pos, old_value.length(), new_value);
		else
			break;
	}

	return str;
}



#ifndef EX_OS_WIN32

#define BYTE ex_u8
#define DWORD ex_u32
#define WCHAR ex_i16
#define LPWSTR WCHAR*
#define BOOL int
#define TRUE 1
#define FALSE 0
#define UINT unsigned int
#define LPCSTR const char*
#define CP_UTF8 1

typedef enum
{
	conversionOK,   /* conversion successful */
	sourceExhausted, /* partial character in source, but hit end */
	targetExhausted, /* insuff. room in target for conversion */
	sourceIllegal  /* source sequence is illegal/malformed */
} ConversionResult;

typedef enum
{
	strictConversion = 0,
	lenientConversion
} ConversionFlags;

static const char trailingBytesForUTF8[256] =
{
	0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0, 0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
	0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0, 0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
	0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0, 0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
	0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0, 0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
	0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0, 0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
	0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0, 0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
	1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1, 1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,
	2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2, 3,3,3,3,3,3,3,3,4,4,4,4,5,5,5,5
};

static const DWORD offsetsFromUTF8[6] = { 0x00000000UL, 0x00003080UL, 0x000E2080UL, 0x03C82080UL, 0xFA082080UL, 0x82082080UL
};

static const BYTE firstByteMark[7] = { 0x00, 0x00, 0xC0, 0xE0, 0xF0, 0xF8, 0xFC };

static const int halfShift = 10; /* used for shifting by 10 bits */

static const DWORD halfBase = 0x0010000UL;
static const DWORD halfMask = 0x3FFUL;

#define UNI_SUR_HIGH_START  (DWORD)0xD800
#define UNI_SUR_HIGH_END    (DWORD)0xDBFF
#define UNI_SUR_LOW_START   (DWORD)0xDC00
#define UNI_SUR_LOW_END     (DWORD)0xDFFF

#define UNI_REPLACEMENT_CHAR	(DWORD)0x0000FFFD
#define UNI_MAX_BMP		(DWORD)0x0000FFFF
#define UNI_MAX_UTF16		(DWORD)0x0010FFFF
#define UNI_MAX_UTF32		(DWORD)0x7FFFFFFF
#define UNI_MAX_LEGAL_UTF32	(DWORD)0x0010FFFF


static ConversionResult ConvertUTF16toUTF8(const WCHAR** sourceStart, const WCHAR* sourceEnd, BYTE** targetStart, BYTE* targetEnd, ConversionFlags flags)
{
	BYTE* target;
	const WCHAR* source;
	BOOL computeLength;
	ConversionResult result;
	computeLength = (!targetEnd) ? TRUE : FALSE;
	source = *sourceStart;
	target = *targetStart;
	result = conversionOK;

	while (source < sourceEnd)
	{
		DWORD ch;
		unsigned short bytesToWrite = 0;
		const DWORD byteMask = 0xBF;
		const DWORD byteMark = 0x80;
		const WCHAR* oldSource = source; /* In case we have to back up because of target overflow. */
		ch = *source++;

		/* If we have a surrogate pair, convert to UTF32 first. */
		if (ch >= UNI_SUR_HIGH_START && ch <= UNI_SUR_HIGH_END)
		{
			/* If the 16 bits following the high surrogate are in the source buffer... */
			if (source < sourceEnd)
			{
				DWORD ch2 = *source;

				/* If it's a low surrogate, convert to UTF32. */
				if (ch2 >= UNI_SUR_LOW_START && ch2 <= UNI_SUR_LOW_END)
				{
					ch = ((ch - UNI_SUR_HIGH_START) << halfShift)
						+ (ch2 - UNI_SUR_LOW_START) + halfBase;
					++source;
				}
				else if (flags == strictConversion)
				{
					/* it's an unpaired high surrogate */
					--source; /* return to the illegal value itself */
					result = sourceIllegal;
					break;
				}
			}
			else
			{
				/* We don't have the 16 bits following the high surrogate. */
				--source; /* return to the high surrogate */
				result = sourceExhausted;
				break;
			}
		}
		else if (flags == strictConversion)
		{
			/* UTF-16 surrogate values are illegal in UTF-32 */
			if (ch >= UNI_SUR_LOW_START && ch <= UNI_SUR_LOW_END)
			{
				--source; /* return to the illegal value itself */
				result = sourceIllegal;
				break;
			}
		}

		/* Figure out how many bytes the result will require */
		if (ch < (DWORD)0x80)
		{
			bytesToWrite = 1;
		}
		else if (ch < (DWORD)0x800)
		{
			bytesToWrite = 2;
		}
		else if (ch < (DWORD)0x10000)
		{
			bytesToWrite = 3;
		}
		else if (ch < (DWORD)0x110000)
		{
			bytesToWrite = 4;
		}
		else
		{
			bytesToWrite = 3;
			ch = UNI_REPLACEMENT_CHAR;
		}

		target += bytesToWrite;

		if ((target > targetEnd) && (!computeLength))
		{
			source = oldSource; /* Back up source pointer! */
			target -= bytesToWrite;
			result = targetExhausted;
			break;
		}

		if (!computeLength)
		{
			switch (bytesToWrite)
			{
				/* note: everything falls through. */
			case 4:
				*--target = (BYTE)((ch | byteMark) & byteMask);
				ch >>= 6;

			case 3:
				*--target = (BYTE)((ch | byteMark) & byteMask);
				ch >>= 6;

			case 2:
				*--target = (BYTE)((ch | byteMark) & byteMask);
				ch >>= 6;

			case 1:
				*--target = (BYTE)(ch | firstByteMark[bytesToWrite]);
			}
		}
		else
		{
			switch (bytesToWrite)
			{
				/* note: everything falls through. */
			case 4:
				--target;
				ch >>= 6;

			case 3:
				--target;
				ch >>= 6;

			case 2:
				--target;
				ch >>= 6;

			case 1:
				--target;
			}
		}

		target += bytesToWrite;
	}

	*sourceStart = source;
	*targetStart = target;
	return result;
}


static BOOL isLegalUTF8(const BYTE* source, int length)
{
	BYTE a;
	const BYTE* srcptr = source + length;

	switch (length)
	{
	default:
		return FALSE;

		/* Everything else falls through when "TRUE"... */
	case 4:
		if ((a = (*--srcptr)) < 0x80 || a > 0xBF) return FALSE;

	case 3:
		if ((a = (*--srcptr)) < 0x80 || a > 0xBF) return FALSE;

	case 2:
		if ((a = (*--srcptr)) > 0xBF) return FALSE;

		switch (*source)
		{
			/* no fall-through in this inner switch */
		case 0xE0:
			if (a < 0xA0) return FALSE;

			break;

		case 0xED:
			if (a > 0x9F) return FALSE;

			break;

		case 0xF0:
			if (a < 0x90) return FALSE;

			break;

		case 0xF4:
			if (a > 0x8F) return FALSE;

			break;

		default:
			if (a < 0x80) return FALSE;
		}

	case 1:
		if (*source >= 0x80 && *source < 0xC2) return FALSE;
	}

	if (*source > 0xF4)
		return FALSE;

	return TRUE;
}

static ConversionResult _ConvertUTF8toUTF16(const BYTE** sourceStart, const BYTE* sourceEnd, WCHAR** targetStart, WCHAR* targetEnd, ConversionFlags flags)
{
	WCHAR* target;
	const BYTE* source;
	BOOL computeLength;
	ConversionResult result;
	computeLength = (!targetEnd) ? TRUE : FALSE;
	result = conversionOK;
	source = *sourceStart;
	target = *targetStart;

	while (source < sourceEnd)
	{
		DWORD ch = 0;
		unsigned short extraBytesToRead = trailingBytesForUTF8[*source];

		if ((source + extraBytesToRead) >= sourceEnd)
		{
			result = sourceExhausted;
			break;
		}

		/* Do this check whether lenient or strict */
		if (!isLegalUTF8(source, extraBytesToRead + 1))
		{
			result = sourceIllegal;
			break;
		}

		/*
		* The cases all fall through. See "Note A" below.
		*/
		switch (extraBytesToRead)
		{
		case 5:
			ch += *source++;
			ch <<= 6; /* remember, illegal UTF-8 */

		case 4:
			ch += *source++;
			ch <<= 6; /* remember, illegal UTF-8 */

		case 3:
			ch += *source++;
			ch <<= 6;

		case 2:
			ch += *source++;
			ch <<= 6;

		case 1:
			ch += *source++;
			ch <<= 6;

		case 0:
			ch += *source++;
		}

		ch -= offsetsFromUTF8[extraBytesToRead];

		if ((target >= targetEnd) && (!computeLength))
		{
			source -= (extraBytesToRead + 1); /* Back up source pointer! */
			result = targetExhausted;
			break;
		}

		if (ch <= UNI_MAX_BMP)
		{
			/* Target is a character <= 0xFFFF */
			/* UTF-16 surrogate values are illegal in UTF-32 */
			if (ch >= UNI_SUR_HIGH_START && ch <= UNI_SUR_LOW_END)
			{
				if (flags == strictConversion)
				{
					source -= (extraBytesToRead + 1); /* return to the illegal value itself */
					result = sourceIllegal;
					break;
				}
				else
				{
					if (!computeLength)
						*target++ = UNI_REPLACEMENT_CHAR;
					else
						target++;
				}
			}
			else
			{
				if (!computeLength)
					*target++ = (WCHAR)ch; /* normal case */
				else
					target++;
			}
		}
		else if (ch > UNI_MAX_UTF16)
		{
			if (flags == strictConversion)
			{
				result = sourceIllegal;
				source -= (extraBytesToRead + 1); /* return to the start */
				break; /* Bail out; shouldn't continue */
			}
			else
			{
				if (!computeLength)
					*target++ = UNI_REPLACEMENT_CHAR;
				else
					target++;
			}
		}
		else
		{
			/* target is a character in range 0xFFFF - 0x10FFFF. */
			if ((target + 1 >= targetEnd) && (!computeLength))
			{
				source -= (extraBytesToRead + 1); /* Back up source pointer! */
				result = targetExhausted;
				break;
			}

			ch -= halfBase;

			if (!computeLength)
			{
				*target++ = (WCHAR)((ch >> halfShift) + UNI_SUR_HIGH_START);
				*target++ = (WCHAR)((ch & halfMask) + UNI_SUR_LOW_START);
			}
			else
			{
				target++;
				target++;
			}
		}
	}

	*sourceStart = source;
	*targetStart = target;
	return result;
}

static int MultiByteToWideChar(UINT CodePage, DWORD dwFlags, LPCSTR lpMultiByteStr, int cbMultiByte, LPWSTR lpWideCharStr, int cchWideChar)
{
	int length;
	LPWSTR targetStart;
	const BYTE* sourceStart;
	ConversionResult result;

	/* If cbMultiByte is 0, the function fails */

	if (cbMultiByte == 0)
		return 0;

	/* If cbMultiByte is -1, the string is null-terminated */

	if (cbMultiByte == -1)
		cbMultiByte = (int)strlen((char*)lpMultiByteStr) + 1;

	/*
	* if cchWideChar is 0, the function returns the required buffer size
	* in characters for lpWideCharStr and makes no use of the output parameter itself.
	*/

	if (cchWideChar == 0)
	{
		sourceStart = (const BYTE*)lpMultiByteStr;
		targetStart = (WCHAR*)NULL;

		result = _ConvertUTF8toUTF16(&sourceStart, &sourceStart[cbMultiByte],
			&targetStart, NULL, strictConversion);

		length = (int)(targetStart - ((WCHAR*)NULL));
		cchWideChar = length;
	}
	else
	{
		sourceStart = (const BYTE*)lpMultiByteStr;
		targetStart = lpWideCharStr;

		result = _ConvertUTF8toUTF16(&sourceStart, &sourceStart[cbMultiByte],
			&targetStart, &targetStart[cchWideChar], strictConversion);

		length = (int)(targetStart - ((WCHAR*)lpWideCharStr));
		cchWideChar = length;
	}

	return cchWideChar;
}

#endif



bool ex_utf8_to_utf16le(const std::string& from, ex_str_utf16le& to)
{
	int iSize = MultiByteToWideChar(CP_UTF8, 0, from.c_str(), -1, NULL, 0);
	if (iSize <= 0)
		return false;

	//++iSize;
	to.resize(iSize);
	memset(&to[0], 0, sizeof(ex_utf16));

	MultiByteToWideChar(CP_UTF8, 0, from.c_str(), -1, &to[0], iSize);

	return true;
}

#endif
