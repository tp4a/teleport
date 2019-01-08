#ifndef __LIB_EX_PATH_H__
#define __LIB_EX_PATH_H__

#include "ex_platform.h"
#include "ex_types.h"
#include "ex_str.h"

// fix `in_path` for current platform.
// must use ex_free() to release returned value.
// e.g.: "/usr//local/../test.txt" => "/usr/local/../test.txt"
// e.g.: "C:/abc/def\\..\\test.txt" => "C:\\abc\\def\\..\\test.txt"
wchar_t* ex_fix_path(const wchar_t* in_path);

wchar_t* ex_exec_file(void);						// must use ex_free() to release returned value.
EX_BOOL ex_is_abspath(const wchar_t* in_path);
wchar_t* ex_abspath(const wchar_t* in_path);		// must use ex_free() to release returned value.
wchar_t* ex_dirname(const wchar_t* in_filename);	// must use ex_free() to release returned value.

EX_BOOL ex_is_dir_exists(const wchar_t* in_path);
EX_BOOL ex_is_file_exists(const wchar_t* in_file);

EX_BOOL ex_copy_file(const wchar_t* from_file, const wchar_t* to_file);

// join a path, last param must be NULL.
// must use ex_free() to release returned value.
wchar_t* ex_path_join(const wchar_t* in_path, EX_BOOL auto_abspath, ...);

// calc an abs-path, `relate_path` relate to `base_abs_path`.
// must use ex_free() to release returned value.
// e.g.: ("/usr/local/abc", "../../etc/abc.ini") => "/usr/etc/abc.ini"
wchar_t* ex_abspath_to(const wchar_t* base_abs_path, const wchar_t* relate_path);


#ifdef __cplusplus
bool ex_exec_file(ex_wstr& out_filename);
bool ex_abspath(ex_wstr& inout_path);
bool ex_dirname(ex_wstr& inout_filename);
bool ex_path_join(ex_wstr& inout_path, EX_BOOL auto_abspath, ...);
bool ex_abspath_to(const ex_wstr& base_abs_path, const ex_wstr& relate_path, ex_wstr& out_path);
bool ex_mkdirs(const ex_wstr& in_path);

// 获取文件名中的扩展名部分（不包括.，例如abc.py，返回 py）
bool ex_path_ext_name(const ex_wstr& in_filename, ex_wstr& out_ext);

#endif

#endif // __LIB_EX_PATH_H__
