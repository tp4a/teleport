#include "ts_env.h"
#include "ts_ver.h"
#include "ts_main.h"
#include "ts_http_client.h"

#include <ex.h>

// 命令行参数说明（不带参数运行则以服务方式启动）
// tp_core [-i|-u|--version] [ [-d] start]
//   -d          启动程序并输出调试信息（不会运行为守护进程/服务模式）
//   -i          安装服务然后退出（仅限Win平台）
//   -u          卸载服务然后退出（仅限Win平台）
//   --version  打印版本号然后退出
//   start       以服务方式运行
//   stop        停止运行中的程序
//
ExLogger g_ex_logger;

bool g_is_debug = false;
extern bool g_exit_flag;

#define RUN_UNKNOWN			0
#define RUN_CORE			1
#define RUN_INSTALL_SRV		2
#define RUN_UNINST_SRV		3
#define RUN_STOP			4
static ex_u8 g_run_type = RUN_UNKNOWN;

#define EOM_CORE_SERVICE_NAME	L"Teleport Core Service"

static bool _run_daemon(void);

#ifdef EX_OS_WIN32
static int service_install()
{
	ex_wstr exec_file(g_env.m_exec_file);
	exec_file += L" start";

	if (EXRV_OK == ex_winsrv_install(EOM_CORE_SERVICE_NAME, EOM_CORE_SERVICE_NAME, exec_file))
		return 0;
	else
		return 1;
}

static int service_uninstall()
{
	if (EXRV_OK != ex_winsrv_stop(EOM_CORE_SERVICE_NAME))
		return 1;

	if (EXRV_OK != ex_winsrv_uninstall(EOM_CORE_SERVICE_NAME))
		return 2;

	return 0;
}
#endif

static bool _process_cmd_line(int argc, wchar_t** argv)
{
	if (argc <= 1)
	{
		EXLOGE("nothing to do.\n\n");
		return false;
	}

	g_run_type = RUN_UNKNOWN;
	bool is_py_arg = false;

	if (0 == wcscmp(argv[1], L"--version"))
	{
		EXLOGV("\nTeleport Server, version %ls.\n\n", TP_SERVER_VER);
		return false;
	}
	else if (0 == wcscmp(argv[1], L"-i"))
	{
		g_run_type = RUN_INSTALL_SRV;
	}
	else if (0 == wcscmp(argv[1], L"-u"))
	{
		g_run_type = RUN_UNINST_SRV;
	}
	else
	{
		for (int i = 1; i < argc; ++i)
		{
			if (0 == wcscmp(argv[i], L"start"))
			{
				g_run_type = RUN_CORE;
				continue;
			}
			else if (0 == wcscmp(argv[i], L"stop")) {
				g_run_type = RUN_STOP;
				continue;
			}

			if (0 == wcscmp(argv[i], L"-d"))
			{
				g_is_debug = true;
				continue;
			}

			EXLOGE(L"unknown option: %ls\n", argv[i]);
			return false;
		}
	}

	if (g_run_type == RUN_UNKNOWN)
	{
		EXLOGE("nothing to do.\n\n");
		return false;
	}

	return true;
}


static int _main_loop(void)
{
	if (g_run_type == RUN_CORE)
		return ts_main();
	else
		return 1;
}

int _app_main(int argc, wchar_t** argv)
{
	EXLOG_USE_LOGGER(&g_ex_logger);

	if (!_process_cmd_line(argc, argv))
		return 1;

#ifdef EX_DEBUG
	EXLOG_LEVEL(EX_LOG_LEVEL_DEBUG);
#endif

#ifdef EX_OS_WIN32
	if (g_run_type == RUN_INSTALL_SRV)
	{
		if (!g_env.init(false))
		{
			EXLOGE("[core] env init failed.\n");
			return 1;
		}

		return service_install();
	}
	else if (g_run_type == RUN_UNINST_SRV)
	{
		if (!g_env.init(false))
		{
			EXLOGE("[core] env init failed.\n");
			return 1;
		}

		return service_uninstall();
	}
#endif

	if (!g_env.init(true))
	{
		EXLOGE("[core] env init failed.\n");
		return 1;
	}

	if (g_run_type == RUN_STOP) {
		char url[1024] = {0};
		ex_strformat(url, 1023, "http://%s:%d/rpc?{\"method\":\"exit\"}", g_env.rpc_bind_ip.c_str(), g_env.rpc_bind_port);
		ex_astr body;
		ts_http_get(url, body);
		ex_printf("%s\n", body.c_str());
		return 0;
	}

	if (!g_is_debug)
	{
		if (!_run_daemon())
		{
			EXLOGE("[core] can not run in daemon mode.\n");
			return 1;
		}

#ifdef EX_OS_WIN32
		return 0;
#endif
	}

	return _main_loop();
}



#ifdef EX_OS_WIN32

#ifdef EX_DEBUG
#include <vld.h>
#endif

static SERVICE_STATUS g_ServiceStatus = { 0 };
static SERVICE_STATUS_HANDLE g_hServiceStatusHandle = NULL;
HANDLE g_hWorkerThread = NULL;

VOID WINAPI service_main(DWORD argc, wchar_t** argv);
void WINAPI service_handler(DWORD fdwControl);

static DWORD WINAPI service_thread_func(LPVOID lpParam);

int main()
{
	int ret = 0;
	LPWSTR szCmdLine = (LPWSTR)::GetCommandLineW(); //获取命令行参数；

	int _argc = 0;
	wchar_t** _argv = ::CommandLineToArgvW(szCmdLine, &_argc); //拆分命令行参数字符串；

	ret = _app_main(_argc, _argv);
	
	LocalFree(_argv);
	_argv = NULL;

	return ret;
}

static bool _run_daemon(void)
{
	SERVICE_TABLE_ENTRY DispatchTable[2];
	DispatchTable[0].lpServiceName = EOM_CORE_SERVICE_NAME;
	DispatchTable[0].lpServiceProc = service_main;
	DispatchTable[1].lpServiceName = NULL;
	DispatchTable[1].lpServiceProc = NULL;

	if (!StartServiceCtrlDispatcher(DispatchTable))
	{
		EXLOGE_WIN("StartServiceCtrlDispatcher()");
		return false;
	}

	return true;
}


static DWORD WINAPI service_thread_func(LPVOID lpParam)
{
	int ret = _main_loop();

	// 更新服务状态（如果服务还在运行，将其设置为停止状态）
	g_ServiceStatus.dwWin32ExitCode = 0;
	g_ServiceStatus.dwCurrentState = SERVICE_STOPPED;
	g_ServiceStatus.dwCheckPoint = 0;
	g_ServiceStatus.dwWaitHint = 0;
	if (!SetServiceStatus(g_hServiceStatusHandle, &g_ServiceStatus))
		EXLOGE_WIN("SetServiceStatus()");

	return ret;
}

static void WINAPI service_handler(DWORD fdwControl)
{
	switch (fdwControl)
	{
	case SERVICE_CONTROL_STOP:
	case SERVICE_CONTROL_SHUTDOWN:
	{
		if (g_hWorkerThread)
		{
			// TerminateThread(g_hWorkerThread, 1);
			// g_hWorkerThread = NULL;
			g_exit_flag = true;

			g_ServiceStatus.dwWin32ExitCode = 0;
			g_ServiceStatus.dwCurrentState = SERVICE_STOP_PENDING;
			g_ServiceStatus.dwCheckPoint = 0;
			g_ServiceStatus.dwWaitHint = 0;
		}
		else {
			g_ServiceStatus.dwWin32ExitCode = 0;
			g_ServiceStatus.dwCurrentState = SERVICE_STOPPED;
			g_ServiceStatus.dwCheckPoint = 0;
			g_ServiceStatus.dwWaitHint = 0;
		}

	}break;

	default:
		return;
	};

	if (!SetServiceStatus(g_hServiceStatusHandle, &g_ServiceStatus))
	{
		EXLOGE_WIN("SetServiceStatus(STOP)");
		return;
	}
}

VOID WINAPI service_main(DWORD argc, wchar_t** argv)
{
	g_ServiceStatus.dwServiceType = SERVICE_WIN32;
	g_ServiceStatus.dwCurrentState = SERVICE_START_PENDING;
	g_ServiceStatus.dwControlsAccepted = SERVICE_ACCEPT_STOP | SERVICE_ACCEPT_SHUTDOWN;
	g_ServiceStatus.dwWin32ExitCode = 0;
	g_ServiceStatus.dwServiceSpecificExitCode = 0;
	g_ServiceStatus.dwCheckPoint = 0;
	g_ServiceStatus.dwWaitHint = 0;
	g_hServiceStatusHandle = RegisterServiceCtrlHandler(EOM_CORE_SERVICE_NAME, service_handler);
	if (g_hServiceStatusHandle == 0)
	{
		EXLOGE_WIN("RegisterServiceCtrlHandler()");
		return;
	}

	DWORD tid = 0;
	g_hWorkerThread = CreateThread(NULL, 0, service_thread_func, NULL, 0, &tid);
	if (NULL == g_hWorkerThread)
	{
		EXLOGE_WIN("CreateThread()");

		g_ServiceStatus.dwWin32ExitCode = 0;
		g_ServiceStatus.dwCurrentState = SERVICE_STOPPED;
		g_ServiceStatus.dwCheckPoint = 0;
		g_ServiceStatus.dwWaitHint = 0;
		if (!SetServiceStatus(g_hServiceStatusHandle, &g_ServiceStatus))
			EXLOGE_WIN("SetServiceStatus()");

		return;
	}

	g_ServiceStatus.dwCurrentState = SERVICE_RUNNING;
	g_ServiceStatus.dwCheckPoint = 0;
	g_ServiceStatus.dwWaitHint = 9000;
	if (!SetServiceStatus(g_hServiceStatusHandle, &g_ServiceStatus))
	{
		EXLOGE_WIN("SetServiceStatus()");
		return;
	}
}

#else
// not EX_OS_WIN32
#include <fcntl.h>
#include <signal.h>

static void _sig_handler(int signum, siginfo_t* info, void* ptr);

int main(int argc, char** argv)
{
	struct sigaction act;
	memset(&act, 0, sizeof(act));
	act.sa_sigaction = _sig_handler;
	act.sa_flags = SA_SIGINFO;
	sigaction(SIGINT, &act, NULL);

	wchar_t** wargv = ex_make_wargv(argc, argv);
	int ret = _app_main(argc, wargv);

	ex_free_wargv(argc, wargv);

	return ret;
}

void _sig_handler(int signum, siginfo_t* info, void* ptr)
{
	if (signum == SIGINT || signum == SIGTERM)
	{
		EXLOGW("\n[core] received signal SIGINT, exit now.\n");
		g_exit_flag = true;
	}
}

static bool _run_daemon(void)
{
	pid_t pid = fork();
	if (pid < 0)
	{
		EXLOGE("[core] can not fork daemon.\n");
		exit(EXIT_FAILURE);
	}
	else if (pid > 0)
	{
		exit(EXIT_SUCCESS);	// parent exit.
	}

	// now I'm first children.
	if (setsid() == -1)
	{
		EXLOGE("[core] setsid() failed.\n");
		assert(0);
		exit(EXIT_FAILURE);
	}

	umask(0);

	pid = fork();
	if (pid < 0)
	{
		EXLOGE("[core] can not fork daemon.\n");
		exit(EXIT_FAILURE);
	}
	else if (pid > 0)
	{
		exit(0);	// first children exit.
	}

	// now I'm second children.
	int ret = chdir("/");
	close(STDIN_FILENO);

	int stdfd = open("/dev/null", O_RDWR);
	close(STDOUT_FILENO);
	close(STDERR_FILENO);
	dup2(stdfd, STDOUT_FILENO);
	dup2(stdfd, STDERR_FILENO);

	return true;
}

#endif
