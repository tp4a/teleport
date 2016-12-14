#include "pys_util.h"

FILE* pys_open_file(const ex_wstr& file_name, const wchar_t* mode)
{
	FILE* f = NULL;
#ifdef EX_OS_WIN32
	errno_t err = 0;
	err = _wfopen_s(&f, file_name.c_str(), mode);
	if (0 == err)
		return f;
	else
		return NULL;
#else
	ex_astr _file_name, _mode;
	ex_wstr2astr(file_name, _file_name, EX_CODEPAGE_UTF8);
	ex_wstr2astr(mode, _mode, EX_CODEPAGE_UTF8);
	f = fopen(_file_name.c_str(), _mode.c_str());
	return f;
#endif
}
