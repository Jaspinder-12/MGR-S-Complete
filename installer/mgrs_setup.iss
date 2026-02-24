; Project: MGR-S (Multi-GPU Runtime System)
; Author: Jaspinder
; Description: Inno Setup installer  v0.2
; Changes from v0.1:
;   - Bumped version to 0.2
;   - Bundles PyInstaller-built mgrs_app.exe (dist\mgrs_app\)
;   - Includes all Python control-plane modules
;   - Installs pip dependencies via install_deps.bat
;   - Added desktop shortcut (checked by default)
;   - Creates logs\ directory on install

[Setup]
AppName=MGR-S
AppVersion=0.2
AppPublisher=Jaspinder
AppPublisherURL=https://github.com/jaspinder/mgr-s
AppSupportURL=https://github.com/jaspinder/mgr-s/issues
DefaultDirName={sd}\MGR-S
DefaultGroupName=MGR-S
UninstallDisplayIcon={app}\mgrs_app.exe
UninstallDisplayName=MGR-S v0.2 Multi-GPU Runtime
Compression=lzma2
SolidCompression=yes
OutputDir=.\Output
OutputBaseFilename=mgrs_setup_0.2
UninstallFilesDir={app}\uninstall
PrivilegesRequired=lowest
ArchitecturesInstallIn64BitMode=x64
ArchitecturesAllowed=x64
WizardStyle=modern
SetupIconFile=.\resources\icon.ico
; MinVersion: Windows 10 1903+
MinVersion=10.0.18362

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon";    Description: "{cm:CreateDesktopIcon}";          GroupDescription: "{cm:AdditionalIcons}"
Name: "startmenu";      Description: "Create Start Menu shortcut";       GroupDescription: "{cm:AdditionalIcons}"
Name: "autostart";      Description: "Launch MGR-S on Windows startup";  GroupDescription: "Startup"; Flags: unchecked

[Files]
; ── PyInstaller bundle (preferred) ──
Source: "..\ui\dist\mgrs_app\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs; Check: FileExists(ExpandConstant('{src}\..\ui\dist\mgrs_app\mgrs_app.exe'))

; ── Raw Python fallback (if exe not built yet) ──
Source: "..\ui\mgrs_gui.py";       DestDir: "{app}\src"; Flags: ignoreversion
Source: "..\ui\mgrs_core.py";      DestDir: "{app}\src"; Flags: ignoreversion
Source: "..\ui\mgrs_monitor.py";   DestDir: "{app}\src"; Flags: ignoreversion
Source: "..\ui\mgrs_scheduler.py"; DestDir: "{app}\src"; Flags: ignoreversion
Source: "..\ui\mgrs_memory.py";    DestDir: "{app}\src"; Flags: ignoreversion
Source: "..\ui\mgrs_tray.py";      DestDir: "{app}\src"; Flags: ignoreversion
Source: "..\ui\requirements.txt";  DestDir: "{app}\src"; Flags: ignoreversion

; ── Icon ──
Source: ".\resources\icon.ico"; DestDir: "{app}"; Flags: ignoreversion

; ── Helper scripts ──
Source: ".\install_deps.bat"; DestDir: "{app}"; Flags: ignoreversion; Check: FileExists(ExpandConstant('{src}.\install_deps.bat'))

[Dirs]
Name: "{app}\logs"
Name: "{app}\src"

[Icons]
; Start menu
Name: "{group}\MGR-S";                    Filename: "{app}\mgrs_app.exe";  WorkingDir: "{app}"; IconFilename: "{app}\icon.ico"; Tasks: startmenu
Name: "{group}\{cm:UninstallProgram,MGR-S}"; Filename: "{uninstallexe}"

; Desktop
Name: "{commondesktop}\MGR-S";            Filename: "{app}\mgrs_app.exe";  WorkingDir: "{app}"; IconFilename: "{app}\icon.ico"; Tasks: desktopicon

; Windows startup (registry)
[Registry]
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "MGRS"; ValueData: """{app}\mgrs_app.exe"""; Flags: uninsdeletevalue; Tasks: autostart

[Run]
; Install pip deps if Python is available and exe doesn't exist
Filename: "cmd.exe"; Parameters: "/c pip install -r ""{app}\src\requirements.txt"" --quiet"; StatusMsg: "Installing Python dependencies…"; Flags: runhidden waituntilterminated; Check: not FileExists(ExpandConstant('{app}\mgrs_app.exe'))

; Launch after install
Filename: "{app}\mgrs_app.exe"; Description: "{cm:LaunchProgram,MGR-S}"; Flags: nowait postinstall skipifsilent; Check: FileExists(ExpandConstant('{app}\mgrs_app.exe'))

[UninstallDelete]
Type: filesandordirs; Name: "{app}"

[Code]
function IsSupportedWindowsVersion(): Boolean;
begin
  Result := (GetWindowsVersion() >= $0A000005); // Windows 10 1903 or later
end;

function InitializeSetup(): Boolean;
begin
  if not IsSupportedWindowsVersion() then
  begin
    MsgBox('MGR-S v0.2 requires Windows 10 version 1903 or later.', mbError, MB_OK);
    Result := False;
    Exit;
  end;
  Result := True;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    // Create empty first_launch marker (GUI reads this to skip welcome on reinstall)
    SaveStringToFile(ExpandConstant('{app}\first_launch.txt'), '1', False);
  end;
end;
