#ifndef __LIB_EX_TYPE_H__
#define __LIB_EX_TYPE_H__

#include "ex_platform.h"

#include <vector>

typedef signed char ex_i8;
typedef signed short ex_i16;

typedef unsigned char ex_u8;
typedef unsigned short ex_u16;
typedef unsigned int ex_u32;
typedef unsigned long ex_ulong;

#if defined(EX_OS_WIN32)
typedef unsigned __int64 ex_u64;
typedef signed __int64 ex_i64;
typedef wchar_t ex_utf16;
#else
typedef unsigned long long ex_u64;
typedef signed long long ex_i64;
typedef ex_i16 ex_utf16;
#endif

typedef int EX_BOOL;
#define EX_TRUE      1
#define EX_FALSE     0


typedef std::vector<ex_u8> ex_bin;
typedef std::vector<char> ex_chars;

typedef ex_u32 ex_rv;


#if defined(EX_OS_WIN32)
#	define EX_DYLIB_HANDLE		HINSTANCE
#else
#	define EX_DYLIB_HANDLE		void*
#endif


#endif // __LIB_EX_TYPE_H__
