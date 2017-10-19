#ifndef __LIB_EX_PLATFORM_H__
#define __LIB_EX_PLATFORM_H__

#if defined(_WIN32) || defined(WIN32)
#	define EX_OS_WIN32
#elif defined(__linux__)
#	define EX_OS_LINUX
#	define EX_OS_UNIX
#elif defined(__APPLE__)
#	define EX_OS_MACOS
#	define EX_OS_UNIX
#else
#	error unsupported platform.
#endif

// compiler
#ifdef EX_OS_WIN32
#	ifndef _MSC_VER
#		error need VisualStudio on Windows.
#	endif
#	if _MSC_VER < 1900	// need VisualStudio 2015 and above.
#		error need VisualStudio 2015 and above.
#	endif
#endif

#ifdef EX_OS_WIN32
#	if !defined(UNICODE) && !defined(_UNICODE)
#		error "Does not support `Multi-Byte Character Set` on Windows."
#	endif
#	ifdef _DEBUG
#		ifndef EX_DEBUG
#			define EX_DEBUG
#		endif
#	endif
#endif

#ifdef EX_OS_MACOS
#	ifdef DEBUG
#		define EX_DEBUG
#	endif
#endif


#ifdef EX_OS_WIN32
#	ifndef _WIN32_WINNT
#		define _WIN32_WINNT 0x0502     // 0x0502 = WinServer2003 (libuv need this)  0x0501 = WinXP, 0x0500 = Win2000
#	endif
#	define WIN32_LEAN_AND_MEAN             // Exclude rarely-used stuff from Windows headers
#	define _CRT_RAND_S		// for rand_s().
#	include <windows.h>
#	include <tchar.h>
#	include <shlwapi.h>
#	include <shellapi.h>
#	define _CSTDIO_
#	define _CSTRING_
#	define _CWCHAR_
#	include <strsafe.h>
#	include <WinSock2.h>
#	include <direct.h>
#else
#	include <locale.h>
#   include <string.h>
#	include <stdio.h>
#	include <stdlib.h>	// free()
#	include <stdarg.h>	// va_start()
#	include <unistd.h>	// readlink()
#	include <fcntl.h>   // O_RDONLY, etc.
#	include <errno.h>
#	include <wchar.h>
#	include <sys/stat.h>
#	include <sys/types.h>
#	include <sys/socket.h>
#	include <netinet/in.h>
#endif

#ifdef EX_OS_MACOS
#   include <mach-o/dyld.h> // for _NSGetExecutablePath
#   ifndef _T
#       define _T(x) L##x
#   endif
#endif


/*
* On Windows PATH_MAX does not exist but MAX_PATH does.
* WinAPI MAX_PATH limit is only 256. MSVCR fuctions does not have this limit.
* Redefine PATH_MAX for Windows to support longer path names.
*/
#if defined(EX_OS_WIN32)
#	ifdef PATH_MAX
#		undef PATH_MAX  /* On Windows override PATH_MAX if defined. */
#	endif
#	define PATH_MAX 1024
#elif defined(EX_OS_LINUX)
#   ifndef PATH_MAX
#      define PATH_MAX 1024
#   endif
#elif defined(EX_OS_MACOS)
#	define PATH_MAX 1024  /* Recommended value for OSX. */
#endif

// assert
#ifdef EX_DEBUG
#	define ASSERT(exp)
#	define CHECK(exp)   do { if (!(exp)) abort(); } while (0)
//#	define DEBUG_CHECKS (0)
#else
#   include <assert.h>
#	define ASSERT(exp)  assert(exp)
#	define CHECK(exp)   assert(exp)
//#	define DEBUG_CHECKS (1)
#endif

#define UNREACHABLE() CHECK(!"Unreachable code reached.")

#ifndef UNUSED
#	if defined(_MSC_VER)
#		define UNUSED(x) (void)(x)
#	elif defined(__GUNC__)
#		defined UNUSED(x) UNUSED_ ## x __attribute__((unused))
#	elif defined(__LCLINT__)
#		define UNUSED(x) /*@unused@*/ x
#	elif defined(__cplusplus)
#		define UNUSED(x)
#	else
#		define UNUSED(x) (void)(x)
#	endif
#endif

/* check endian */
#if !(defined(L_ENDIAN) || defined(B_ENDIAN))
#	if !defined(__BYTE_ORDER) && defined(__linux__)
#		include <endian.h>
#	endif

#	if defined(BYTE_ORDER)
#		if BYTE_ORDER == BIG_ENDIAN
#			define B_ENDIAN
#		else
#			define L_ENDIAN
#		endif
#	endif

#	if !(defined(L_ENDIAN) || defined(B_ENDIAN))
#		if defined(__sparc__) || defined(__PPC__) || defined(__ppc__) || defined(__hppa__)
#			define B_ENDIAN
#		else
#			define L_ENDIAN
#		endif
#	endif
#endif

#ifdef EX_OS_WIN32
#	pragma comment(lib, "shlwapi.lib")
#endif


#endif // __LIB_EX_PLATFORM_H__
