; Script de configuración para Inno Setup
; Genera un instalador profesional tipo Wizard (.exe) para Windows 11 / 10

#define MyAppName "Editor de Boletas PDF"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "AO Digital"
#define MyAppExeName "EditorBoletasPDF.exe"

[Setup]
AppId={{D37E84B1-6284-4E87-8A2F-9289C3246830}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=dist_instalador
OutputBaseFilename=Instalador_EditorBoletas_Setup
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequired=lowest
CloseApplications=yes
RestartApplications=no

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "Crear un acceso directo en el Escritorio"; GroupDescription: "Accesos directos:"

[Files]
; Incluye todos los archivos generados por PyInstaller en dist\EditorBoletasPDF
Source: "dist\EditorBoletasPDF\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Desinstalar {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Ejecutar {#MyAppName} ahora"; Flags: nowait postinstall skipifsilent
