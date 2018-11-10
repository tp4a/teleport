#include <ex/ex_path.h>
#include <ex/ex_const.h>
#include <ex/ex_util.h>

static void _wstr_replace(ex_wstr& inout_str, const wchar_t* sfrom, const wchar_t* sto)
{
	ex_wstr::size_type pos = 0;
	size_t len_from = wcslen(sfrom);
	size_t len_to = wcslen(sto);
	while (ex_wstr::npos != (pos = inout_str.find(sfrom, pos)))
	{
		inout_str.replace(pos, len_from, sto);
		pos += (len_to - len_from + 1);
	}
}

wchar_t* ex_fix_path(const wchar_t* in_path)
{
	if (NULL == in_path)
		return NULL;
	ex_wstr _path(in_path);
#ifdef EX_OS_WIN32
	_wstr_replace(_path, L"/", L"\\");
	_wstr_replace(_path, L"\\\\", L"\\");
#else
	_wstr_replace(_path, L"//", L"/");
#endif
	return ex_wcsdup(_path.c_str());
}

wchar_t* ex_exec_file(void)
{
	ex_wstr path;
	if (!ex_exec_file(path))
		return NULL;
	return ex_wcsdup(path.c_str());
}

EX_BOOL ex_is_abspath(const wchar_t* in_path)
{
#ifdef EX_OS_WIN32
	if (wcslen(in_path) >= 2)
	{
		if (in_path[1] == L':')
			return EX_TRUE;
	}
#else
	if (wcslen(in_path) >= 1)
	{
		if (in_path[0] == L'/')
			return EX_TRUE;
	}
#endif
	return EX_FALSE;
}

wchar_t* ex_abspath(const wchar_t* in_path)
{
	ex_wstr tmp(in_path);
	if (!ex_abspath(tmp))
		return NULL;
	else
		return ex_wcsdup(tmp.c_str());
}

wchar_t* ex_abspath_to(const wchar_t* base_abs_path, const wchar_t* relate_path)
{
	ex_wstr tmp;
	if (!ex_abspath_to(base_abs_path, relate_path, tmp))
		return NULL;
	else
		return ex_wcsdup(tmp.c_str());
}

wchar_t* ex_dirname(const wchar_t* in_filename)
{
	ex_wstr tmp(in_filename);
	if (!ex_dirname(tmp))
		return NULL;
	else
		return ex_wcsdup(tmp.c_str());
}

bool ex_dirname(ex_wstr& inout_filename)
{
	size_t len = 0;
	wchar_t *match = NULL;

	wchar_t* ret = ex_wcsdup(inout_filename.c_str());
	if (NULL == ret)
		return false;

	len = wcslen(ret);

	if (ret[len] == EX_SEP)
	{
		ret[len] = EX_NULL_END;
	}

	match = wcsrchr(ret, EX_SEP);
	if (match != NULL)
	{
		*match = EX_NULL_END;
		inout_filename = ret;
		ex_free(ret);
		return true;
	}
	else
	{
		ex_free(ret);
		inout_filename = EX_CURRENT_DIR_STR;
		return true;
	}
//
//	ex_free(ret);
//	return false;
}


EX_BOOL ex_is_dir_exists(const wchar_t* in_path)
{
#ifdef EX_OS_WIN32
	if (!PathFileExists(in_path))
		return false;
	if (!PathIsDirectory(in_path))
		return false;
#else
	struct stat si;
    ex_astr _in_path;
    ex_wstr2astr(in_path, _in_path);
	if (0 != stat(_in_path.c_str(), &si))
		return false;
	if (!S_ISDIR(si.st_mode))
		return false;
#endif
	return true;
}

EX_BOOL ex_is_file_exists(const wchar_t* in_file)
{
#ifdef EX_OS_WIN32
	if (!PathFileExists(in_file))
		return false;
	if (PathIsDirectory(in_file))
		return false;
#else
	struct stat si;
    ex_astr _in_file;
    ex_wstr2astr(in_file, _in_file);
	if (0 != stat(_in_file.c_str(), &si))
		return false;
	if (!S_ISREG(si.st_mode))
		return false;
#endif
	return true;
}


EX_BOOL ex_copy_file(const wchar_t* from_file, const wchar_t* to_file) {
#ifdef EX_OS_WIN32
	if (CopyFile(from_file, to_file, TRUE))
		return EX_TRUE;
	else
		return EX_FALSE;
#else
	ex_astr source;
	ex_astr target;
	ex_wstr2astr(from_file, source);
	ex_wstr2astr(to_file, target);

	struct stat src_stat;
	if (lstat(source.c_str(), &src_stat) == -1)
		return EX_FALSE;

	if (S_ISLNK(src_stat.st_mode)) {
		char lnk[1024] = {0};
		ssize_t lnk_size;
		if ((lnk_size = readlink(source.c_str(), lnk, 1023)) == -1)
			return EX_FALSE;
		lnk[lnk_size] = '\0';
		if (symlink(lnk, target.c_str()) == -1)
			return EX_FALSE;
	}
	else if (S_ISREG(src_stat.st_mode)) {
		int src = -1, dst = -1;
		ssize_t rsize = 0;
		char buf[1024] = {0};
		if ((src = open(source.c_str(), O_RDONLY)) == -1) {
			close(dst);
			return EX_FALSE;
		}
		if ((dst = creat(target.c_str(), src_stat.st_mode)) == -1)
			return EX_FALSE;

		while ((rsize = read(src, buf, 1024))) {
			if (rsize == -1 && errno == EINTR)
				continue;
			if (rsize == -1) {
				close(src);
				close(dst);
				return EX_FALSE;
			}
			while (write(dst, buf, rsize) == -1) {
				if (errno != EINTR) {
					close(src);
					close(dst);
					return EX_FALSE;
				}
			}
		}
		close(src);
		close(dst);
	}
	else {
		return EX_FALSE;
	}
	return EX_TRUE;
#endif
}


//=====================================================

bool ex_exec_file(ex_wstr& out_filename)
{
#ifdef EX_OS_WIN32
	wchar_t modulename_w[EX_PATH_MAX];
	if (!GetModuleFileNameW(NULL, modulename_w, EX_PATH_MAX))
		return false;

	out_filename = modulename_w;
	return ex_abspath(out_filename);

#elif defined(EX_OS_MACOS)
	char buffer[EX_PATH_MAX];
	//char out_path[PATH_MAX];
	uint32_t length = EX_PATH_MAX;

	memset(buffer, 0, EX_PATH_MAX);
	//memset(out_filename, 0, EX_PATH_MAX);

	/* Mac OS X has special function to obtain path to executable.
	* This may return a symlink.
	*/
	if (_NSGetExecutablePath(buffer, &length) != 0)
		return false;

	if (!ex_astr2wstr(buffer, out_filename))
		return false;

	//return ex_abspath(out_filename);
	return true;

#else
	char buffer[EX_PATH_MAX];
	ssize_t result = -1;

	memset(buffer, 0, EX_PATH_MAX);

	// On Linux, FreeBSD, and Solaris, we try these /proc paths first
#if defined(EX_OS_LINUX)
	result = readlink("/proc/self/exe", buffer, EX_PATH_MAX);  // Linux
#elif defined(EX_OS_FREEBSD)
	result = readlink("/proc/curproc/file", buffer, EX_PATH_MAX);  // FreeBSD
#else
#	error not implement.
#endif

	if (-1 != result)
	{
		/* execfile is not yet zero-terminated. result is the byte count. */
		*(buffer + result) = '\0';
		if (!ex_astr2wstr(buffer, out_filename))
			return false;
		return ex_abspath(out_filename);
	}
	else
	{
		return false;
	}
#endif
}

// bool ex_abspath(ex_wstr& inout_path)
// {
// #ifdef EX_OS_WIN32
// 	wchar_t _tmp[EX_PATH_MAX] = { 0 };
// 	if (NULL == _wfullpath(_tmp, inout_path.c_str(), EX_PATH_MAX))
// 		return false;
// 	if (!PathFileExists(_tmp))
// 		return false;
// 	inout_path = _tmp;
// 	return true;
// #else
// 	ex_astr _path;
// 	if (!ex_wstr2astr(inout_path, _path, EX_CODEPAGE_UTF8))
// 		return false;
// 	char _tmp[EX_PATH_MAX] = { 0 };
// 	if (NULL == realpath(_path.c_str(), _tmp))
// 		return false;
// 	_path = _tmp;
// 	return ex_astr2wstr(_path, inout_path, EX_CODEPAGE_UTF8);
// #endif
// }

bool ex_abspath(ex_wstr& inout_path)
{
    wchar_t* _path = NULL;
#ifdef EX_OS_UNIX
    if(ex_is_abspath(inout_path.c_str()))
    {
        _path = ex_fix_path(inout_path.c_str());
    }
    else
    {
        char sz_cwd[PATH_MAX] = {0};
        if(NULL == getcwd(sz_cwd, PATH_MAX)) {
            return false;
        }
        ex_wstr str_cwd;
        if(!ex_astr2wstr(sz_cwd, str_cwd))
            return false;

        ex_wstr str_abs_path;
        if(!ex_abspath_to(str_cwd, inout_path, str_abs_path))
            return false;

        _path = ex_wcsdup(str_abs_path.c_str());
    }

#else
    // TODO: fixed ex_abspath() for Windows.

    _path = ex_fix_path(inout_path.c_str());
#endif

    if(_path == NULL)
        return false;

	ex_wstrs paths;
	wchar_t* _str = _path;
	wchar_t* _tmp = NULL;
	for (;;)
	{
		_tmp = wcschr(_str, EX_SEP);
		if (NULL == _tmp)
		{
			if (wcslen(_str) > 0)
				paths.push_back(_str);
			break;
		}
		else
		{
			_tmp[0] = EX_NULL_END;
   			paths.push_back(_str);
			_str = _tmp + 1;
		}
	}
	ex_free(_path);

	ex_wstrs::iterator it = paths.begin();
	for (; it != paths.end(); )
	{
		if ((*it) == L"..")
		{
			if (it == paths.begin())
				return false;
			ex_wstrs::iterator it_tmp = it;
			--it_tmp;
			paths.erase(it);
			paths.erase(it_tmp);
			it = paths.begin();
		}
		else if ((*it) == L".")
		{
			paths.erase(it);
			it = paths.begin();
		}
		else
		{
			++it;
		}
	}


	inout_path.clear();
	bool is_first = true;
	it = paths.begin();
	for (; it != paths.end(); ++it)
	{
		if (is_first)
		{
#ifdef EX_OS_WIN32
			if ((*it)[1] != L':')
				return false;
#else
//			if ((*it)[0] != L'/')
#endif
//				return false;
		}

		if (!is_first)
			inout_path += EX_SEP_STR;

		inout_path += (*it);
		is_first = false;
	}

	return true;
}

bool ex_path_join(ex_wstr& inout_path, EX_BOOL auto_abspath, ...)
{
	wchar_t* tmp;

	ex_wstr _path(inout_path);

	va_list argp;
	va_start(argp, auto_abspath);
	for (;;)
	{
		tmp = va_arg(argp, wchar_t*);
		if (NULL == tmp)
			break;

		if (_path.length() > 0)
		{
			if (_path[_path.length() - 1] != EX_SEP)
				_path += EX_SEP_STR;
		}

		_path += tmp;
	}
	va_end(argp);

	if (auto_abspath)
		if (!ex_abspath(_path))
			return false;

	inout_path = _path;
	return true;
}

wchar_t* ex_path_join(const wchar_t* in_path, EX_BOOL auto_abspath, ...)
{
	wchar_t* tmp;

	ex_wstr _path(in_path);

	va_list argp;
	va_start(argp, auto_abspath);
	for (;;)
	{
		tmp = va_arg(argp, wchar_t*);
		if (NULL == tmp)
			break;

		if (_path.length() > 0)
		{
			if (_path[_path.length() - 1] != EX_SEP)
				_path += EX_SEP_STR;
		}

		_path += tmp;
	}
	va_end(argp);

	if (auto_abspath)
		if (!ex_abspath(_path))
			return NULL;

	return ex_wcsdup(_path.c_str());
}


bool ex_abspath_to(const ex_wstr& base_abs_path, const ex_wstr& relate_path, ex_wstr& out_path)
{
	out_path = base_abs_path;
	out_path += EX_SEP_STR;
	out_path += relate_path;

	return ex_abspath(out_path);
}

bool ex_mkdirs(const ex_wstr& in_path)
{
	if (ex_is_dir_exists(in_path.c_str()))
		return true;

	ex_wstr tmp_path(in_path);
	if (!ex_path_join(tmp_path, false, L"..", NULL))
		return false;
	if (!ex_abspath(tmp_path))
		return false;

	if (!ex_mkdirs(tmp_path))
		return false;

	ex_astr _path;
#ifdef EX_OS_WIN32
	ex_wstr2astr(in_path, _path);
	if (0 == _mkdir(_path.c_str()))
		return true;
#else
	ex_wstr2astr(in_path, _path);
	int status = mkdir(_path.c_str(), S_IRWXU | S_IRWXG | S_IROTH | S_IXOTH);
	if (0 != status)
		return false;
#endif

	return true;
}

bool ex_path_ext_name(const ex_wstr& in_filename, ex_wstr& out_ext)
{
	ex_wstr::size_type pos_dot = in_filename.rfind(L'.');
	ex_wstr::size_type pos_sep = in_filename.rfind(EX_SEP);

	if (pos_dot == ex_wstr::npos || pos_dot <= pos_sep)
		return false;

	out_ext.assign(in_filename, pos_dot + 1, in_filename.length() - pos_dot - 1);
	return true;
}
