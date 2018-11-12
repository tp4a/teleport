#include "stdafx.h"
#include "ts_const.h"
#include "dlg_main.h"
#include "resource.h"
#include "ts_ver.h"
#include <shellapi.h>

#pragma comment(lib, "comctl32.lib")
#if defined _M_IX86
#pragma comment(linker,"/manifestdependency:\"type='win32' name='Microsoft.Windows.Common-Controls' version='6.0.0.0' processorArchitecture='x86' publicKeyToken='6595b64144ccf1df' language='*'\"")
#elif defined _M_IA64
#pragma comment(linker,"/manifestdependency:\"type='win32' name='Microsoft.Windows.Common-Controls' version='6.0.0.0' processorArchitecture='ia64' publicKeyToken='6595b64144ccf1df' language='*'\"")
#elif defined _M_X64
#pragma comment(linker,"/manifestdependency:\"type='win32' name='Microsoft.Windows.Common-Controls' version='6.0.0.0' processorArchitecture='amd64' publicKeyToken='6595b64144ccf1df' language='*'\"")
#else
#pragma comment(linker,"/manifestdependency:\"type='win32' name='Microsoft.Windows.Common-Controls' version='6.0.0.0' processorArchitecture='*' publicKeyToken='6595b64144ccf1df' language='*'\"")
#endif

extern HINSTANCE g_hInstance;

HWND g_hDlgMain = nullptr;
static DWORD g_dwTaskbarRecreateMessage = 0;
static BOOL g_IsTrayIconShowed = FALSE;

extern HWND g_hwndBase;

static void show_tray_icon(int icon_id);
static void removeTrayIcon(HWND hwndDlg);
static void showSelf(HWND hwndDlg);
static void center_window(HWND hwndDlg);

static BOOL onInitDialog(HWND hwndDlg);

static wchar_t g_wsz_url[1024] = {0};

INT_PTR CALLBACK eomDlgMainProc(HWND hwndDlg, UINT message, WPARAM wParam, LPARAM lParam)
{
	if (0 != message && g_dwTaskbarRecreateMessage == message)
	{
		removeTrayIcon(hwndDlg);
		show_tray_icon(IDI_TRAY_NORMAL);

		return TRUE;
	}

	if (message == WMU_DLG_MAIN_EXIT)
	{
		EndDialog(hwndDlg, IDOK);
		return TRUE;
	}

	switch (message)
	{
	case WM_INITDIALOG:
		g_hDlgMain = hwndDlg;
		return onInitDialog(hwndDlg);
		break;

	case WM_SYSCOMMAND:
		if (SC_MINIMIZE == wParam || SC_CLOSE == wParam)
		{
			PostMessage(hwndDlg, WM_COMMAND, IDOK, NULL);
			return TRUE;
		}break;

	case WM_COMMAND:
		switch (LOWORD(wParam))
		{
		case IDOK:
		{
			AnimateWindow(hwndDlg, 500, AW_HIDE | AW_BLEND);
			KillTimer(hwndDlg, 0);
			ShowWindow(hwndDlg, SW_HIDE);
			return TRUE;
		}break;
		case IDCANCEL:
		case IDM_EXIT:
		{
			removeTrayIcon(hwndDlg);
			DestroyWindow(g_hwndBase);
			return TRUE;
		}break;

		case IDM_ABOUT:
		case IDM_SHOW_ASSIST:
		{
			showSelf(hwndDlg);
			return TRUE;
		}break;

		case IDM_OPEN_WEB:
		{
			ShellExecute(nullptr, _T("open"), TS_WEB_URL, nullptr, nullptr, SW_SHOW);
			return TRUE;
		}break;

		case IDM_OPEN_CONFIG:
		{
			ShellExecute(nullptr, _T("open"), _T("http://localhost:50022/config"), nullptr, nullptr, SW_SHOW);
			return TRUE;
		}break;

		default:
			break;
		}
		break;

	case WMU_TRAY_NOTIFY:
	{
		UINT uID = (UINT)wParam;
		UINT uMsg = (UINT)lParam;

		if (uMsg == WM_LBUTTONDBLCLK && uID == IDI_TRAY_NORMAL)
		{
			PostMessage(hwndDlg, WM_COMMAND, IDM_ABOUT, NULL);
			return TRUE;
		}
		else if (uMsg == WM_RBUTTONUP && uID == IDI_TRAY_NORMAL)
		{
			POINT pt;
			GetCursorPos(&pt);
			HMENU hMenu = LoadMenu(g_hInstance, MAKEINTRESOURCE(IDR_TRAY_MENU));
			HMENU hPopup = GetSubMenu(hMenu, 0);
			SetMenuDefaultItem(hPopup, IDM_ABOUT, FALSE);

			TrackPopupMenu(hPopup, TPM_LEFTALIGN | TPM_RIGHTBUTTON, pt.x, pt.y, 0, hwndDlg, nullptr);
			DestroyMenu(hMenu);
		}

	}break;

	}

	return FALSE;
}

BOOL onInitDialog(HWND hwndDlg)
{
	center_window(hwndDlg);

	ex_wstr ver = L"°æ±¾£º";
	ver += TP_ASSIST_VER;

	SetWindowText(GetDlgItem(hwndDlg, IDC_VERSION), ver.c_str());

	show_tray_icon(IDI_TRAY_NORMAL);

	return TRUE;
}

void showSelf(HWND hwndDlg)
{
	ShowWindow(hwndDlg, SW_NORMAL);
	SetWindowPos(hwndDlg, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOSIZE | SWP_NOMOVE);
	SetActiveWindow(hwndDlg);
	BringWindowToTop(hwndDlg);
	SetWindowPos(hwndDlg, HWND_NOTOPMOST, 0, 0, 0, 0, SWP_NOSIZE | SWP_NOMOVE);
}

void show_tray_icon(int icon_id)
{
	wchar_t* msg = TS_TRAY_MSG;

	NOTIFYICONDATA tnd = { 0 };
	tnd.cbSize = sizeof(NOTIFYICONDATA);
	tnd.uFlags = NIF_MESSAGE | NIF_ICON | NIF_TIP;
	tnd.hIcon = (HICON)LoadImage(g_hInstance, MAKEINTRESOURCE(icon_id), IMAGE_ICON, GetSystemMetrics(SM_CXSMICON), GetSystemMetrics(SM_CYSMICON), LR_DEFAULTSIZE | LR_SHARED);
	tnd.hWnd = g_hDlgMain;
	tnd.uID = IDI_TRAY_NORMAL;
	tnd.uCallbackMessage = WMU_TRAY_NOTIFY;
	tnd.szTip[0] = 0;
	StringCchCopy(tnd.szTip, 128, msg);

	if(!g_IsTrayIconShowed)
		Shell_NotifyIcon(NIM_ADD, &tnd);
	else
		Shell_NotifyIcon(NIM_MODIFY, &tnd);

	g_IsTrayIconShowed = TRUE;
}

void removeTrayIcon(HWND hwndDlg)
{
	NOTIFYICONDATA tnd = { 0 };
	tnd.cbSize = sizeof(NOTIFYICONDATA);

	tnd.hWnd = hwndDlg;
	tnd.uID = IDI_TRAY_NORMAL;

	Shell_NotifyIcon(NIM_DELETE, &tnd);
}

void center_window(HWND hwndDlg)
{
	RECT rc;
	ZeroMemory(&rc, sizeof(RECT));
	GetWindowRect(hwndDlg, &rc);
	{
		int cxScreen = 0;
		int cyScreen = 0;
		cxScreen = GetSystemMetrics(SM_CXSCREEN);
		cyScreen = GetSystemMetrics(SM_CYSCREEN);

		if (cxScreen <= 0)
			cxScreen = 640;
		if (cyScreen <= 0)
			cxScreen = 480;

		rc.left = (cxScreen - (rc.right - rc.left)) / 2;
		rc.top = (cyScreen - (rc.bottom - rc.top)) / 3;
	}

	SetWindowPos(hwndDlg, nullptr, rc.left, rc.top, 0, 0, SWP_NOSIZE);

	return;
}
