#ifndef __LIB_EX_CONST_H__
#define __LIB_EX_CONST_H__

#include "ex_platform.h"

/*
* On Windows PATH_MAX does not exist but MAX_PATH does.
* WinAPI MAX_PATH limit is only 256. MSVCR fuctions does not have this limit.
* Redefine PATH_MAX for Windows to support longer path names.
*/
#if defined(EX_OS_WIN32)
#	define EX_PATH_MAX 1024
#elif defined(EX_OS_LINUX)
#	ifdef PATH_MAX
#		define EX_PATH_MAX PATH_MAX
#	else
#		define EX_PATH_MAX 1024
#	endif
#elif defined(EX_OS_MACOS)
#	define EX_PATH_MAX 1024  /* Recommended value for OSX. */
#endif

/* Path and string macros. */
#if defined(EX_OS_WIN32)
#	define EX_PATH_SEP      L';'
#	define EX_PATH_SEP_STR  L";"
#	define EX_SEP           L'\\'
#	define EX_SEP_STR       L"\\"
#else
#	define EX_PATH_SEP      L':'
#	define EX_PATH_SEP_STR  L":"
#	define EX_SEP           L'/'
#	define EX_SEP_STR       L"/"
#endif

#define EX_CURRENT_DIR	    L'.'
#define EX_CURRENT_DIR_STR  L"."
#define EX_NULL_END         L'\0'



//====================================================
// error code.
//====================================================
#define EXRV_OK				0
#define EXRV_SYS_ERR			1		// 系统错误，可以使用GetLastError或者errno来获取具体错误值
#define EXRV_FAILED			2		// 操作失败

//#define EXRV_CANNOT_FOUND	9
#define EXRV_CANNOT_CREATE	10
#define EXRV_CANNOT_OPEN		11
#define EXRV_CANNOT_SET		12
#define EXRV_CANNOT_REMOVE	13
#define EXRV_NOT_START		14
#define EXRV_NOT_EXISTS		14

#endif // __LIB_EX_CONST_H__
