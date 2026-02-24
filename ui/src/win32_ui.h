#pragma once

#include <Windows.h>
#include "ApplicationController.h"

// Resource IDs
#define IDR_MENU1 101
#define IDD_DIALOG1 102
#define IDI_ICON1 103
#define IDM_DOCUMENTATION 201
#define IDC_LOGO_LABEL 301
#define IDC_VERSION_LABEL 302
#define IDC_STATE_LABEL 303
#define IDC_API_VERSION_LABEL 304
#define IDC_GPU_COUNT_LABEL 305
#define IDC_AUTHORITY_GPU_LABEL 306
#define IDC_LOG_EDIT 307
#define IDC_EXIT_BUTTON 308

class Win32UI {
public:
    Win32UI();
    ~Win32UI();

    int run(HINSTANCE hInstance, int nCmdShow);

private:
    static LRESULT CALLBACK DialogProc(HWND hwnd, UINT msg, WPARAM wParam, LPARAM lParam);
    void initializeUI();
    void updateDashboard();
    void logMessage(const char* message);
    void showFirstLaunchDialog();

    HINSTANCE m_hInstance;
    HWND m_hwnd;
    ApplicationController m_controller;
    bool m_firstLaunch;
};
