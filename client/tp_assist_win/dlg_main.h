#ifndef __EOMASSIST_DLG_MAIN_H__
#define __EOMASSIST_DLG_MAIN_H__

#include <windows.h>

#define WMU_TRAY_NOTIFY			(WM_USER + 1)
#define WMU_DLG_MAIN_EXIT		(WM_USER + 2)

extern HWND g_hDlgMain;
INT_PTR CALLBACK eomDlgMainProc(HWND hwndDlg, UINT message, WPARAM wParam, LPARAM lParam);

#endif // __EOMASSIST_DLG_MAIN_H__
