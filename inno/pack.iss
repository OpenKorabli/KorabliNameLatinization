#define MyAppName "战舰名拉丁化工具MK"
#define MyAppVersion "0.0.2"
#define MyAppPublisher "OpenKorabli"
#define MyAppURL "https://github.com/OpenKorabli/KorabliNameLatinization"
#define MyAppExeName "latinization.exe"

[Setup]
; NOTE: The value of AppId uniquely identifies this application. Do not use the same AppId value in installers for other applications.
; (To generate a new GUID, click Tools | Generate GUID inside the IDE.)
AppId={{4D3BD3E3-92EB-44FA-99C0-58D52A6D3B03}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
;AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
SetupIconFile=..\resources\icon.ico
WizardImageFile=..\resources\wizard.bmp
WizardSmallImageFile=..\resources\wizard_s.bmp
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\KorabliNameLatinization
DisableWelcomePage=no
DisableProgramGroupPage=yes
; Uncomment the following line to run in non administrative install mode (install for current user only.)
;PrivilegesRequired=lowest
OutputBaseFilename="OpenKorabli·战舰名拉丁化工具-{#SetupSetting("AppVersion")}"
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "chinese"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"; InfoBeforeFile: "..\resources\welcome.txt"; LicenseFile: "..\resources\license.txt";

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "..\dist\latinization\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\dist\latinization\_internal\*"; DestDir: "{app}\_internal"; Flags: ignoreversion recursesubdirs createallsubdirs
; NOTE: Don't use "Flags: ignoreversion" on any shared system files

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

