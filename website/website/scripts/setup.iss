; Inno Setup Script for LiveTranslate
; Requirements: Inno Setup 6 (https://jrsoftware.org/isdl.php)
; Usage: Open this file in Inno Setup Compiler and click "Compile" or "Run"

[Setup]
AppId={{5AB3F6D8-19EE-4D2A-B68C-28D8E9F74C78}
AppName=LiveTranslate
AppVersion=1.5.2
AppPublisher=kngo
AppPublisherURL=https://github.com/kotobuki09/LiveTranslate
AppSupportURL=https://github.com/kotobuki09/LiveTranslate/issues
AppUpdatesURL=https://github.com/kotobuki09/LiveTranslate/releases
DefaultDirName={autopf}\LiveTranslate
DisableProgramGroupPage=yes
; To avoid the SmartScreen warning as much as possible, we don't force admin
PrivilegesRequired=lowest
OutputDir=..\plan\release
OutputBaseFilename=LiveTranslate_v1.5.2_Setup
SetupIconFile=..\src\assets\icon.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; The actual executable and its folder structure produced by PyInstaller --onedir
Source: "..\dist\LiveTranslate\LiveTranslate.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\dist\LiveTranslate\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; Note: Don't use "Flags: ignoreversion" on any shared system files

[Icons]
Name: "{autoprograms}\LiveTranslate"; Filename: "{app}\LiveTranslate.exe"; IconFilename: "{app}\LiveTranslate.exe"
Name: "{autodesktop}\LiveTranslate"; Filename: "{app}\LiveTranslate.exe"; IconFilename: "{app}\LiveTranslate.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\LiveTranslate.exe"; Description: "{cm:LaunchProgram,LiveTranslate}"; Flags: nowait postinstall skipifsilent
