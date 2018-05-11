// stdafx.cpp : source file that includes just the standard includes
// tpssh.pch will be the pre-compiled header
// stdafx.obj will contain the pre-compiled type information

#include "stdafx.h"

// TODO: reference any additional headers you need in STDAFX.H
// and not in this file

#include <ex.h>

#ifdef EX_OS_WIN32
//#	pragma comment(lib, "libeay32.lib")
#	pragma comment(lib, "ws2_32.lib")
#endif

