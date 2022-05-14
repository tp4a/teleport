#include "stdafx.h"
#include <shellapi.h>
#include <fcntl.h>
#include "resource.h"
#include "dlg_main.h"
//#include "ts_http_rpc.h"
#include "ts_ws_client.h"

#ifdef _DEBUG
// #	include <vld.h>
#endif

#pragma comment(lib, "shlwapi.lib")

#define WMU_INSTANCE_EXIT		(WM_USER + 2)
#define WMU_SHOW_EXIST_DLGUI	(WM_USER + 3)

static ExLogger g_ex_logger;

static ATOM MyRegisterClass();
static BOOL InitInstance();
static LRESULT CALLBACK WndProc(HWND, UINT, WPARAM, LPARAM);
void failed(const char* msg);
void failed(const wchar_t* msg);

static HANDLE g_SingleInstanceMutexHandle = NULL;

HINSTANCE g_hInstance = NULL;
ULONG g_ulSingleInstanceMsgId = 0;
static TCHAR szKernalName[MAX_PATH] = { 0 };

HWND g_hwndBase = NULL;
int g_argc = 0;
wchar_t** g_argv = NULL;

ex_astr g_url_protocol;

#define TP_ASSIST_GUID			_T("A6EFE1250C5F4416BFA819FE92CBD4B4")
#define TP_ASSIST_INSTANCE		_T("TS_ASSIST_SINGLE_INSTANCE")
#define TP_ASSIST_WIN_CLASS		_T("TS_ASSIST_WINDOW_CLASS")
#define MAKEDWORD(low, high)	((DWORD)(((WORD)(((DWORD_PTR)(low)) & 0xffff)) | ((DWORD)((WORD)(((DWORD_PTR)(high)) & 0xffff))) << 16))

//DWORD WINAPI HttpServerThreadProc(LPVOID lpParam) {
//    http_rpc_main_loop(false);
//    return 0;
//}
//
//DWORD WINAPI HttpsServerThreadProc(LPVOID lpParam) {
//    http_rpc_main_loop(true);
//    return 0;
//}

int APIENTRY wWinMain(HINSTANCE hInstance, HINSTANCE hPrevInstance, LPTSTR lpCmdLine, int nShowCmd) {
	EXLOG_USE_LOGGER(&g_ex_logger);

	WORD wVersionRequested;
	WSADATA wsaData;
	int err;

	wVersionRequested = MAKEWORD(1, 1);

	err = WSAStartup(wVersionRequested, &wsaData);
	if (err != 0) {
		return 0;
	}

	if (LOBYTE(wsaData.wVersion) != 1 ||
		HIBYTE(wsaData.wVersion) != 1) {
		WSACleanup();
		return 0;
	}

	g_env.init();

#ifdef EX_DEBUG
	EXLOG_LEVEL(EX_LOG_LEVEL_DEBUG);
#else
	EXLOG_LEVEL(EX_LOG_LEVEL_INFO);
#endif

	EXLOG_FILE(L"tp_assist.log", g_env.m_log_path.c_str(), EX_LOG_FILE_MAX_SIZE, EX_LOG_FILE_MAX_COUNT);

	if (!g_cfg.init()) {
		MessageBox(NULL, _T("无法加载助手配置文件！"), _T("错误"), MB_OK | MB_ICONERROR);
		return FALSE;
	}

	g_hInstance = hInstance;
	_stprintf_s(szKernalName, MAX_PATH, _T("%s_%s"), TP_ASSIST_GUID, TP_ASSIST_INSTANCE);
	g_ulSingleInstanceMsgId = RegisterWindowMessage(szKernalName);
	if (0 == g_ulSingleInstanceMsgId)
		return FALSE;

	LPWSTR szCmdLine = (LPWSTR)::GetCommandLineW(); //获取命令行参数；
	g_argv = CommandLineToArgvW(szCmdLine, &g_argc); //拆分命令行参数字符串；

	for (int i = 0; i < g_argc; ++i) {
		ex_wstr arg = g_argv[i];
		if (0 == lstrcmp(g_argv[i], _T("--stop"))) {
			PostMessage(HWND_BROADCAST, g_ulSingleInstanceMsgId, WMU_INSTANCE_EXIT, 0);
			LocalFree(g_argv);
			g_argv = NULL;
			return -1;
		}
		else if (arg.find(L"teleport://", 0) == 0) {
			// url-protocol
			// teleport://register?param={"ws_url":"ws://127.0.0.1:7190/ws/assist/","assist_id":1234,"session_id":"tp_5678"}

			EXLOGV(L"url-protocol: %s\n", arg.c_str());
			ex_wstr2astr(arg, g_url_protocol);

			break;
		}
	}

	// make sure run single instance.
	_stprintf_s(szKernalName, MAX_PATH, _T("%s_%s"), TP_ASSIST_GUID, TP_ASSIST_INSTANCE);
	g_SingleInstanceMutexHandle = CreateMutex(NULL, FALSE, szKernalName);
	if (GetLastError() == ERROR_ALREADY_EXISTS) {
		// if we got url-protocol, send it by WM_COPYDATA, else just bring running instance to front.
		if (g_url_protocol.empty())
		{
			PostMessage(HWND_BROADCAST, g_ulSingleInstanceMsgId, WMU_SHOW_EXIST_DLGUI, 0);
		}
		else
		{
			HWND hwnd = FindWindow(TP_ASSIST_WIN_CLASS, NULL);
			if (hwnd == NULL) {
				MessageBoxW(NULL, _T("助手已经运行了，但无法定位！"), _T("错误"), MB_OK | MB_ICONERROR);
			}
			else
			{
				COPYDATASTRUCT data;
				data.dwData = NULL;
				data.cbData = g_url_protocol.length() + 1;  // include zero end.
				data.lpData = (void*)g_url_protocol.c_str();
				SendMessage(hwnd, WM_COPYDATA, NULL, (LPARAM)&data);
			}
		}

		CloseHandle(g_SingleInstanceMutexHandle);
		LocalFree(g_argv);
		g_argv = NULL;
		return 0;
	}


	// create dialog-box window.
	MyRegisterClass();

	// Perform application initialization:
	if (!InitInstance()) {
		CloseHandle(g_SingleInstanceMutexHandle);
		LocalFree(g_argv);
		g_argv = NULL;
		return FALSE;
	}

	//HANDLE hThreadHttpServer=NULL;
	//DWORD dwThreadId=0;
	//hThreadHttpServer=CreateThread(NULL, 0, HttpServerThreadProc, NULL, 0, &dwThreadId);

	//HANDLE hThreadHttpsServer=NULL;
	//dwThreadId=0;
	//hThreadHttpsServer=CreateThread(NULL, 0, HttpsServerThreadProc, NULL, 0, &dwThreadId);

	MSG msg;
	while (GetMessage(&msg, NULL, 0, 0)) {
		TranslateMessage(&msg);
		DispatchMessage(&msg);
	}

	//http_rpc_stop(false);
	//WaitForSingleObject(hThreadHttpServer, INFINITE);

	//http_rpc_stop(true);
	//WaitForSingleObject(hThreadHttpsServer, INFINITE);

	CloseHandle(g_SingleInstanceMutexHandle);

	LocalFree(g_argv);
	g_argv = NULL;
	return 0;
}


void failed(const char* msg) {
	OutputDebugStringA(msg);
}
void failed(const wchar_t* msg) {
	OutputDebugStringW(msg);
}

ATOM MyRegisterClass() {
	WNDCLASSEX wcex;

	wcex.cbSize = sizeof(WNDCLASSEX);

	wcex.style = CS_HREDRAW | CS_VREDRAW;
	wcex.lpfnWndProc = WndProc;
	wcex.cbClsExtra = 0;
	wcex.cbWndExtra = 0;
	wcex.hInstance = g_hInstance;
	wcex.hIcon = LoadIcon(g_hInstance, MAKEINTRESOURCE(IDI_NORMAL_BIG));
	wcex.hCursor = LoadCursor(NULL, IDC_ARROW);
	wcex.hbrBackground = (HBRUSH)(COLOR_WINDOW + 1);
	wcex.lpszMenuName = MAKEINTRESOURCE(IDR_ASSIST);
	wcex.lpszClassName = TP_ASSIST_WIN_CLASS;
	wcex.hIconSm = LoadIcon(wcex.hInstance, MAKEINTRESOURCE(IDI_NORMAL_SMALL));

	return RegisterClassEx(&wcex);
}

BOOL InitInstance(void) {
	g_hwndBase = CreateWindow(TP_ASSIST_WIN_CLASS, _T(""), WS_OVERLAPPEDWINDOW, 8, 0, 8, 0, NULL, NULL, g_hInstance, NULL);
	if (!g_hwndBase)
		return FALSE;

	ShowWindow(g_hwndBase, SW_HIDE);

	return TRUE;
}

LRESULT CALLBACK WndProc(HWND hWnd, UINT message, WPARAM wParam, LPARAM lParam) {
	if (g_ulSingleInstanceMsgId == message) {
		if (WMU_INSTANCE_EXIT == wParam) {
			PostMessage(g_hDlgMain, WM_COMMAND, MAKEDWORD(IDCANCEL, 0), NULL);
			return 0;
		}
		else if (WMU_SHOW_EXIST_DLGUI == wParam) {
			ShowWindow(g_hDlgMain, SW_SHOW);
			SetWindowPos(g_hDlgMain, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOSIZE | SWP_NOMOVE);
			SetActiveWindow(g_hDlgMain);
			BringWindowToTop(g_hDlgMain);
			SetWindowPos(g_hDlgMain, HWND_NOTOPMOST, 0, 0, 0, 0, SWP_NOSIZE | SWP_NOMOVE);
			return 0;
		}
	}

	switch (message) {
	case WM_CREATE:
		PostMessage(hWnd, WM_COMMAND, MAKEDWORD(IDM_MAIN, 0), NULL);

		if (!g_url_protocol.empty())
		{
			TsWsClient::url_scheme_handler(g_url_protocol);
		}

		return DefWindowProc(hWnd, message, wParam, lParam);
		break;
	case WM_COMMAND:
		if (IDM_MAIN == LOWORD(wParam)) {
			CreateDialog(g_hInstance, MAKEINTRESOURCE(IDD_DLG_MAIN), hWnd, eomDlgMainProc);
			ShowWindow(g_hDlgMain, SW_HIDE);
		}
		break;
	case WM_DESTROY:
		TsWsClient::stop_all_client();
		SendMessage(g_hDlgMain, WMU_DLG_MAIN_EXIT, NULL, NULL);
		PostQuitMessage(0);
		break;
	case WM_COPYDATA:
	{
		COPYDATASTRUCT* data = (COPYDATASTRUCT*)lParam;
		ex_astr url_protocol((char*)data->lpData);
		// MessageBoxA(hWnd, url_protocol.c_str(), "url-protocol", MB_OK);
		TsWsClient::url_scheme_handler(url_protocol);
		break;
	}
	default:
		return DefWindowProc(hWnd, message, wParam, lParam);
	}
	return 0;
}
