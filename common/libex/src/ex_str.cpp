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
	if (wlen < 0)
		return NULL;

	out_buffer = (wchar_t*)calloc(wlen + 1, sizeof(wchar_t));
	if (NULL == out_buffer)
		return NULL;

	wlen = mbstowcs(out_buffer, in_buffer, wlen);
	if (wlen < 0)
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
	if (len < 0)
		return NULL;

	out_buffer = (char*)calloc(len + 1, sizeof(char));
	if (NULL == out_buffer)
		return NULL;

	len = wcstombs(out_buffer, in_buffer, len);
	if (len < 0)
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

#endif
