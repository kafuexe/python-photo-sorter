[Setup]
AppName=Photo Sorter
AppVersion=1.0
AppPublisher=Ofek
DefaultDirName={autopf}\PhotoSorter
DefaultGroupName=Photo Sorter
UninstallDisplayIcon={app}\PhotoSorter.exe
OutputDir=dist
OutputBaseFilename=PhotoSorterSetup
SetupIconFile=src\ui\assets\logo.ico
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest

[Files]
Source: "dist\PhotoSorter.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "config.json"; DestDir: "{app}"; Flags: onlyifdoesntexist uninsneveruninstall

[Dirs]
Name: "{app}\move-log"; Flags: uninsneveruninstall

[Icons]
Name: "{group}\Photo Sorter"; Filename: "{app}\PhotoSorter.exe"
Name: "{autodesktop}\Photo Sorter"; Filename: "{app}\PhotoSorter.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"

[Run]
Filename: "{app}\PhotoSorter.exe"; Description: "Launch Photo Sorter"; Flags: nowait postinstall skipifsilent
