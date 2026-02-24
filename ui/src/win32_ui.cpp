#include "win32_ui.h"
#include <commctrl.h>
#include <strsafe.h>

#pragma comment(lib, "comctl32.lib")
#pragma comment(lib, "shell32.lib")

Win32UI::Win32UI()
    : m_hInstance(nullptr)
    , m_hwnd(nullptr)
    , m_firstLaunch(true)
{}

Win32UI::~Win32UI()
{}

int Win32UI::run(HINSTANCE hInstance, int nCmdShow)
{
    m_hInstance = hInstance;

    // Initialize common controls
    INITCOMMONCONTROLSEX icex;
    icex.dwSize = sizeof(INITCOMMONCONTROLSEX);
    icex.dwICC = ICC_STANDARD_CLASSES;
    if (!InitCommonControlsEx(&icex)) {
        MessageBox(nullptr, TEXT("Failed to initialize common controls"), TEXT("Error"), MB_OK | MB_ICONERROR);
        return 1;
    }

    // Create main window
    m_hwnd = CreateDialog(hInstance, MAKEINTRESOURCE(IDD_DIALOG1), nullptr, DialogProc);
    if (m_hwnd == nullptr) {
        MessageBox(nullptr, TEXT("Failed to create window"), TEXT("Error"), MB_OK | MB_ICONERROR);
        return 1;
    }

    ShowWindow(m_hwnd, nCmdShow);
    UpdateWindow(m_hwnd);

    initializeUI();
    showFirstLaunchDialog();
    m_controller.initialize();
    updateDashboard();

    // Message loop
    MSG msg;
    while (GetMessage(&msg, nullptr, 0, 0)) {
        if (!IsDialogMessage(m_hwnd, &msg)) {
            TranslateMessage(&msg);
            DispatchMessage(&msg);
        }
    }

    return static_cast<int>(msg.wParam);
}

LRESULT CALLBACK Win32UI::DialogProc(HWND hwnd, UINT msg, WPARAM wParam, LPARAM lParam)
{
    Win32UI* pThis = nullptr;

    if (msg == WM_INITDIALOG) {
        pThis = static_cast<Win32UI*>(reinterpret_cast<LPDLGTEMPLATE>(lParam));
        SetWindowLongPtr(hwnd, GWLP_USERDATA, reinterpret_cast<LONG_PTR>(pThis));
    } else {
        pThis = reinterpret_cast<Win32UI*>(GetWindowLongPtr(hwnd, GWLP_USERDATA));
    }

    if (pThis) {
        switch (msg) {
        case WM_COMMAND:
            switch (LOWORD(wParam)) {
            case IDC_EXIT_BUTTON:
                EndDialog(hwnd, 0);
                return TRUE;

            case IDM_DOCUMENTATION:
                ShellExecute(nullptr, TEXT("open"), TEXT("https://mgr-s.github.io/docs"), nullptr, nullptr, SW_SHOW);
                return TRUE;
            }
            break;

        case WM_CLOSE:
            EndDialog(hwnd, 0);
            return TRUE;
        }
    }

    return FALSE;
}

void Win32UI::initializeUI()
{
    // Set initial values
    SetDlgItemText(m_hwnd, IDC_API_VERSION_LABEL, TEXT("API Version: Unavailable"));
    SetDlgItemText(m_hwnd, IDC_GPU_COUNT_LABEL, TEXT("GPU Count: Unavailable"));
    SetDlgItemText(m_hwnd, IDC_AUTHORITY_GPU_LABEL, TEXT("Authority GPU: Unavailable"));
}

void Win32UI::updateDashboard()
{
    // Update state
    auto state = m_controller.getState();
    const char* stateString = m_controller.getStateString().c_str();
    SetDlgItemText(m_hwnd, IDC_STATE_LABEL, TEXT(stateString));

    // Set state color
    HWND hStateLabel = GetDlgItem(m_hwnd, IDC_STATE_LABEL);
    switch (state) {
    case ApplicationController::RuntimeState::RUNNING:
        SetTextColor(GetDC(hStateLabel), RGB(0, 255, 0)); // Green
        break;
    case ApplicationController::RuntimeState::DEGRADED:
        SetTextColor(GetDC(hStateLabel), RGB(255, 165, 0)); // Orange
        break;
    case ApplicationController::RuntimeState::ERROR:
        SetTextColor(GetDC(hStateLabel), RGB(255, 0, 0)); // Red
        break;
    default:
        SetTextColor(GetDC(hStateLabel), RGB(0, 0, 0)); // Black
    }
    UpdateWindow(hStateLabel);

    // Update metrics
    std::string apiVersion = "API Version: " + m_controller.getApiVersionString();
    std::string gpuCount = "GPU Count: " + m_controller.getGpuCountString();
    std::string authorityGpu = "Authority GPU: " + m_controller.getAuthorityGpuString();

    SetDlgItemText(m_hwnd, IDC_API_VERSION_LABEL, TEXT(apiVersion.c_str()));
    SetDlgItemText(m_hwnd, IDC_GPU_COUNT_LABEL, TEXT(gpuCount.c_str()));
    SetDlgItemText(m_hwnd, IDC_AUTHORITY_GPU_LABEL, TEXT(authorityGpu.c_str()));

    // Update log
    logMessage("Dashboard updated - " + std::to_string(GetTickCount()));
}

void Win32UI::logMessage(const char* message)
{
    HWND hLogEdit = GetDlgItem(m_hwnd, IDC_LOG_EDIT);
    int length = GetWindowTextLength(hLogEdit);
    SendMessage(hLogEdit, EM_SETSEL, length, length);
    SendMessage(hLogEdit, EM_REPLACESEL, 0, reinterpret_cast<LPARAM>(message));
    SendMessage(hLogEdit, EM_REPLACESEL, 0, reinterpret_cast<LPARAM>("\r\n"));
}

void Win32UI::showFirstLaunchDialog()
{
    // Check if this is the first launch
    HKEY hKey;
    LPCSTR subKey = "SOFTWARE\\MGR-S";
    DWORD dwValue;
    DWORD dwSize = sizeof(DWORD);
    LONG result = RegOpenKeyExA(HKEY_CURRENT_USER, subKey, 0, KEY_READ, &hKey);

    if (result != ERROR_SUCCESS) {
        // Key doesn't exist - first launch
        MessageBox(m_hwnd, TEXT("MGR-S is a Multi-GPU Runtime System designed to improve performance on systems with multiple GPUs (e.g., iGPU + dGPU).\n\nKey limitations:\n- This is NOT SLI or CrossFire\n- Performance gains are application-specific\n- Only Vulkan applications are supported\n- Some systems may not see any improvement\n\nClick OK to continue."), TEXT("Welcome to MGR-S"), MB_OK | MB_ICONINFORMATION);
        RegCreateKeyExA(HKEY_CURRENT_USER, subKey, 0, nullptr, REG_OPTION_NON_VOLATILE, KEY_WRITE, nullptr, &hKey, nullptr);
        dwValue = 0;
        RegSetValueExA(hKey, "FirstLaunch", 0, REG_DWORD, reinterpret_cast<LPBYTE>(&dwValue), dwSize);
    }

    RegCloseKey(hKey);
}
