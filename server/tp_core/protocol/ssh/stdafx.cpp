// stdafx.cpp : source file that includes just the standard includes
// tpssh.pch will be the pre-compiled header
// stdafx.obj will contain the pre-compiled type information

#include "stdafx.h"

// TODO: reference any additional headers you need in STDAFX.H
// and not in this file

#include <ex.h>

#ifdef EX_OS_WIN32
#	ifdef EX_DEBUG
#		pragma comment(lib, "..\\..\\..\\..\\external\\libssh\\build\\src\\Debug\\ssh.lib")
#	else
#		pragma comment(lib, "..\\..\\..\\..\\external\\libssh\\build\\src\\Release\\ssh.lib")
#	endif
#	pragma comment(lib, "libeay32.lib")
#	pragma comment(lib, "ws2_32.lib")
#endif

