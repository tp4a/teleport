// stdafx.cpp : source file that includes just the standard includes
// testssh.pch will be the pre-compiled header
// stdafx.obj will contain the pre-compiled type information

#include "stdafx.h"

// TODO: reference any additional headers you need in STDAFX.H
// and not in this file

#ifdef _DEBUG
#	pragma comment(lib, "debug/ssh.lib")
#else
#	pragma comment(lib, "release/ssh.lib")
#endif
#pragma comment(lib, "libeay32.lib")
#pragma comment(lib, "ws2_32.lib")

