#include <ex/ex_winsrv.h>

#ifdef EX_OS_WIN32

#include <ex/ex_const.h>

class winsrv_helper
{
public:
	winsrv_helper(SC_HANDLE scm, SC_HANDLE sc) : m_scm(scm), m_sc(sc)
	{
	}
	~winsrv_helper()
	{
		if(NULL != m_sc)
			CloseServiceHandle(m_sc);
		if(NULL != m_scm)
			CloseServiceHandle(m_scm);
	}

protected:
	SC_HANDLE m_sc;
	SC_HANDLE m_scm;
};


ex_rv ex_winsrv_install(const ex_wstr& srv_name, const ex_wstr& disp_name, const ex_wstr& exec_path)
{
	SC_HANDLE sc = NULL;
	SC_HANDLE scm = NULL;
	winsrv_helper srv(scm, sc);

	scm = OpenSCManager(NULL, NULL, SC_MANAGER_ALL_ACCESS);
	if (scm == NULL)
		return EXRV_CANNOT_OPEN;

	if (NULL == (sc = CreateServiceW(scm, srv_name.c_str(), disp_name.c_str(),
		SERVICE_ALL_ACCESS,
		SERVICE_WIN32_OWN_PROCESS,
		SERVICE_AUTO_START, SERVICE_ERROR_NORMAL, exec_path.c_str(), NULL, NULL, NULL, NULL, NULL))
		)
	{
		return EXRV_CANNOT_CREATE;
	}

	SERVICE_FAILURE_ACTIONS  failure_action;
	failure_action.dwResetPeriod = 0;				// reset failure count to zero  的时间，单位为秒
	failure_action.lpRebootMsg = NULL;				// Message to broadcast to server users before rebooting  
	failure_action.lpCommand = NULL;				// Command line of the process for the CreateProcess function to execute in response 
	failure_action.cActions = 3;						// action数组的个数

	SC_ACTION actionarray[3];
	actionarray[0].Type = SC_ACTION_RESTART;		// 重新启动服务
	actionarray[0].Delay = 60000;					// 单位为毫秒
	actionarray[1].Type = SC_ACTION_RESTART;
	actionarray[1].Delay = 60000;
	actionarray[2].Type = SC_ACTION_RESTART;
	actionarray[2].Delay = 60000;
	failure_action.lpsaActions = actionarray;

	ChangeServiceConfig2(sc, SERVICE_CONFIG_FAILURE_ACTIONS, &failure_action);

	return EXRV_OK;
}

bool ex_winsrv_is_exists(const ex_wstr& srv_name)
{
	SC_HANDLE sc = NULL;
	SC_HANDLE scm = NULL;
	winsrv_helper srv(scm, sc);

	scm = OpenSCManager(NULL, NULL, SC_MANAGER_ALL_ACCESS);
	if (scm == NULL)
		return false;

	sc = OpenServiceW(scm, srv_name.c_str(), SERVICE_ALL_ACCESS);
	if (NULL == sc)
		return false;

	return true;
}

ex_rv ex_winsrv_uninstall(const ex_wstr& srv_name)
{
	SC_HANDLE sc = NULL;
	SC_HANDLE scm = NULL;
	winsrv_helper srv(scm, sc);

	scm = OpenSCManager(NULL, NULL, SC_MANAGER_ALL_ACCESS);
	if (scm == NULL)
		return EXRV_CANNOT_OPEN;

	sc = OpenServiceW(scm, srv_name.c_str(), SERVICE_ALL_ACCESS);
	if (NULL == sc)
		return EXRV_NOT_EXISTS;

	if (!DeleteService(sc))
		return EXRV_CANNOT_REMOVE;
	else
		return EXRV_OK;
}

ex_rv ex_winsrv_start(const ex_wstr& srv_name)
{
	SC_HANDLE sc = NULL;
	SC_HANDLE scm = NULL;
	winsrv_helper srv(scm, sc);

	scm = OpenSCManager(NULL, NULL, SC_MANAGER_ALL_ACCESS);
	if (scm == NULL)
		return EXRV_CANNOT_OPEN;

	sc = OpenServiceW(scm, srv_name.c_str(), SERVICE_START | SERVICE_QUERY_STATUS);
	if (NULL == sc)
		return EXRV_NOT_EXISTS;

	SERVICE_STATUS ss;
	if (!QueryServiceStatus(sc, &ss))
		return EXRV_FAILED;

	if (ss.dwCurrentState == SERVICE_RUNNING)
		return EXRV_OK;

	int i = 0;
	if (ss.dwCurrentState == SERVICE_START_PENDING)
	{
		for (i = 0; i < 100; ++i)
		{
			Sleep(100);
			QueryServiceStatus(sc, &ss);
			if (ss.dwCurrentState != SERVICE_START_PENDING)
				break;
		}
	}

	if (ss.dwCurrentState == SERVICE_STOPPED)
	{
		if (StartService(sc, 0, NULL))
		{
			for (i = 0; i < 100; ++i)
			{
				Sleep(100);
				QueryServiceStatus(sc, &ss);
				if (ss.dwCurrentState == SERVICE_RUNNING)
					return EXRV_OK;
			}
		}
	}

	if (ss.dwCurrentState == SERVICE_RUNNING)
		return EXRV_OK;
	else
		return EXRV_FAILED;
}

ex_rv ex_winsrv_config(const ex_wstr& srv_name, QUERY_SERVICE_CONFIG& cfg)
{
	SC_HANDLE sc = NULL;
	SC_HANDLE scm = NULL;
	winsrv_helper srv(scm, sc);


	scm = OpenSCManager(NULL, NULL, SC_MANAGER_ALL_ACCESS);
	if (scm == NULL)
		return EXRV_CANNOT_OPEN;

	sc = OpenServiceW(scm, srv_name.c_str(), SERVICE_QUERY_CONFIG);
	if (sc == NULL)
		return EXRV_NOT_EXISTS;

	DWORD dwBytesNeeded;
	if (!QueryServiceConfig(sc, &cfg, 4096, &dwBytesNeeded))
		return EXRV_FAILED;
	else
		return EXRV_OK;
}

ex_rv ex_winsrv_status(const ex_wstr& srv_name, ex_ulong& status)
{
	SC_HANDLE sc = NULL;
	SC_HANDLE scm = NULL;
	winsrv_helper srv(scm, sc);

	scm = OpenSCManager(NULL, NULL, SC_MANAGER_ALL_ACCESS);
	if (scm == NULL)
		return EXRV_CANNOT_OPEN;

	sc = OpenServiceW(scm, srv_name.c_str(), SERVICE_QUERY_STATUS);
	if (NULL == sc)
		return EXRV_NOT_EXISTS;

	SERVICE_STATUS ss;
	if (!QueryServiceStatus(sc, &ss))
		return EXRV_FAILED;

	status = ss.dwCurrentState;
	return EXRV_OK;
}

ex_rv ex_winsrv_stop(const ex_wstr& srv_name)
{
	SC_HANDLE sc = NULL;
	SC_HANDLE scm = NULL;
	winsrv_helper srv(scm, sc);

	scm = OpenSCManager(NULL, NULL, SC_MANAGER_ALL_ACCESS);
	if (scm == NULL)
		return EXRV_CANNOT_OPEN;

	sc = OpenServiceW(scm, srv_name.c_str(), SERVICE_STOP | SERVICE_QUERY_STATUS);
	if (NULL == sc)
		return EXRV_NOT_EXISTS;

	SERVICE_STATUS ss;
	if (!QueryServiceStatus(sc, &ss))
		return EXRV_FAILED;

	if (ss.dwCurrentState == SERVICE_STOPPED)
		return EXRV_OK;

	int i = 0;

	DWORD dwStatus = ss.dwCurrentState;
	if (ss.dwCurrentState == SERVICE_START_PENDING || ss.dwCurrentState == SERVICE_PAUSE_PENDING || ss.dwCurrentState == SERVICE_CONTINUE_PENDING || ss.dwCurrentState == SERVICE_STOP_PENDING)
	{
		for (i = 0; i < 100; ++i)
		{
			Sleep(100);
			QueryServiceStatus(sc, &ss);
			if (ss.dwCurrentState != dwStatus)
				break;
		}
	}

	if (ss.dwCurrentState == SERVICE_RUNNING || ss.dwCurrentState == SERVICE_PAUSED)
	{
		if (ControlService(sc, SERVICE_CONTROL_STOP, &ss))
		{
			for (i = 0; i < 100; ++i)
			{
				Sleep(100);
				QueryServiceStatus(sc, &ss);
				if (ss.dwCurrentState == SERVICE_STOPPED)
					return EXRV_OK;
			}
		}
	}

	if (ss.dwCurrentState == SERVICE_STOPPED)
		return EXRV_OK;
	else
		return EXRV_FAILED;
}

ex_rv ex_winsrv_pause(const ex_wstr& srv_name)
{
	SC_HANDLE sc = NULL;
	SC_HANDLE scm = NULL;
	winsrv_helper srv(scm, sc);

	scm = OpenSCManager(NULL, NULL, SC_MANAGER_ALL_ACCESS);
	if (scm == NULL)
		return EXRV_CANNOT_OPEN;

	sc = OpenServiceW(scm, srv_name.c_str(), SERVICE_PAUSE_CONTINUE | SERVICE_QUERY_STATUS);
	if (NULL == sc)
		return EXRV_NOT_EXISTS;

	SERVICE_STATUS ss;
	if(!QueryServiceStatus(sc, &ss))
		return EXRV_FAILED;

	if (ss.dwCurrentState == SERVICE_PAUSED)
		return EXRV_OK;

	int i = 0;

	DWORD dwStatus = ss.dwCurrentState;
	if (ss.dwCurrentState == SERVICE_START_PENDING || ss.dwCurrentState == SERVICE_PAUSE_PENDING || ss.dwCurrentState == SERVICE_CONTINUE_PENDING)
	{
		for (i = 0; i < 100; ++i)
		{
			Sleep(100);
			QueryServiceStatus(sc, &ss);
			if (ss.dwCurrentState != dwStatus)
				break;
		}
	}

	if (ss.dwCurrentState == SERVICE_RUNNING)
	{
		if (ControlService(sc, SERVICE_CONTROL_PAUSE, &ss))
		{
			for (i = 0; i < 100; ++i)
			{
				Sleep(100);
				QueryServiceStatus(sc, &ss);
				if (ss.dwCurrentState == SERVICE_PAUSED)
					return EXRV_OK;
			}
		}
	}

	if (ss.dwCurrentState == SERVICE_PAUSED)
		return EXRV_OK;
	else
		return EXRV_FAILED;
}

ex_rv ex_winsrv_resume(const ex_wstr& srv_name)
{
	SC_HANDLE sc = NULL;
	SC_HANDLE scm = NULL;
	winsrv_helper srv(scm, sc);

	scm = OpenSCManager(NULL, NULL, SC_MANAGER_ALL_ACCESS);
	if (scm == NULL)
		return EXRV_CANNOT_OPEN;

	sc = OpenServiceW(scm, srv_name.c_str(), SERVICE_PAUSE_CONTINUE | SERVICE_QUERY_STATUS);
	if (NULL == sc)
		return EXRV_NOT_EXISTS;

	SERVICE_STATUS ss;
	if (!QueryServiceStatus(sc, &ss))
		return EXRV_FAILED;

	if (ss.dwCurrentState == SERVICE_RUNNING)
		return EXRV_OK;

	int i = 0;

	DWORD dwStatus = ss.dwCurrentState;
	if (ss.dwCurrentState == SERVICE_START_PENDING || ss.dwCurrentState == SERVICE_PAUSE_PENDING || ss.dwCurrentState == SERVICE_CONTINUE_PENDING)
	{
		for (i = 0; i < 100; ++i)
		{
			Sleep(100);
			QueryServiceStatus(sc, &ss);
			if (ss.dwCurrentState != dwStatus)
				break;
		}
	}

	if (ss.dwCurrentState == SERVICE_PAUSED)
	{
		if (ControlService(sc, SERVICE_CONTROL_CONTINUE, &ss))
		{
			for (i = 0; i < 100; ++i)
			{
				Sleep(100);
				QueryServiceStatus(sc, &ss);
				if (ss.dwCurrentState == SERVICE_RUNNING)
					return EXRV_OK;
			}
		}
	}

	if (ss.dwCurrentState == SERVICE_RUNNING)
		return EXRV_OK;
	else
		return EXRV_FAILED;
}

ex_rv ex_winsrv_pid(const ex_wstr& srv_name, ex_ulong& pid)
{
	SC_HANDLE sc = NULL;
	SC_HANDLE scm = NULL;
	winsrv_helper srv(scm, sc);

	scm = OpenSCManager(NULL, NULL, SC_MANAGER_ALL_ACCESS);
	if (scm == NULL)
		return EXRV_CANNOT_OPEN;

	sc = OpenServiceW(scm, srv_name.c_str(), SERVICE_QUERY_STATUS);
	if (NULL == sc)
		return EXRV_NOT_EXISTS;

	DWORD byteneeded = 0;
	ex_u8 buf[1024] = { 0 };
	QueryServiceStatusEx(sc, SC_STATUS_PROCESS_INFO, buf, 1024, &byteneeded);

	LPSERVICE_STATUS_PROCESS lp = (LPSERVICE_STATUS_PROCESS)buf;
	if (lp->dwCurrentState != SERVICE_RUNNING)
		return EXRV_NOT_START;

	pid = lp->dwProcessId;

	return EXRV_OK;
}
#endif
