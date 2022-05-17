#ifndef __TP_ASSIST_DLG_MAIN_H__
#define __TP_ASSIST_DLG_MAIN_H__

#include <windows.h>

#define WMU_TRAY_NOTIFY			(WM_USER + 1)
#define WMU_DLG_MAIN_EXIT		(WM_USER + 2)

extern HWND g_hDlgMain;
INT_PTR CALLBACK tpDlgMainProc(HWND hwndDlg, UINT message, WPARAM wParam, LPARAM lParam);

#endif // __TP_ASSIST_DLG_MAIN_H__
