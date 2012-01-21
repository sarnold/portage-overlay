; $Id: bitpim.iss 4437 2007-10-31 21:24:32Z djpham $
; This file has various values substituted when building package
[Setup]

AppID=%%GUID%%

AppName=%%NAME%%
AppVerName=BitPim %%VERSION%%
AppCopyright=%%COPYRIGHT%%
AppPublisher=%%PUBLISHER%%
AppPublisherURL=%%URL%%
AppVersion=%%VERSION%%
AppSupportURL=%%SUPPORTURL%%
DefaultGroupName=%%NAME%%
DefaultDirName={pf}\%%NAME%%
OutputBaseFilename=%%OUTFILE%%
OutputDir=.
Compression=lzma/ultra
SolidCompression=yes
InternalCompressLevel=ultra
ChangesAssociations=yes
LicenseFile=..\src\LICENSE

[Registry]
Root: HKCR; Subkey: ".bitpim"; ValueType: string; ValueName: ""; ValueData: "BitPimConfigFile"; Flags: uninsdeletevalue
Root: HKCR; Subkey: "BitPimConfigFile"; ValueType: string; ValueName: ""; ValueData: "BitPim Config File"; Flags: uninsdeletekey
Root: HKCR; Subkey: "BitPimConfigFile\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\bitpimw.exe,0"
Root: HKCR; Subkey: "BitPimConfigFile\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\bitpimw.exe"" -c ""%1"""

[Files]
; the file locations are relative to the location of where the substituted version of this script ends up
; which is the dist directory
Source: files\*; DestDir: "{app}" ; Flags: sortfilesbyextension replacesameversion ignoreversion overwritereadonly recursesubdirs
Source: "..\packaging\bitpim.url"; DestDir: "{app}"
; We need unicows on Win9x, but not NT/2k/XP
Source: ..\buildrelease\winpkg\unicows.dll; DestDir: "{app}"; Flags: sortfilesbyextension replacesameversion ignoreversion overwritereadonly; MinVersion: 4.0,0

[Icons]
Name: "{group}\BitPim" ; Filename: "{app}\bitpimw.exe"; Comment: "The main BitPim program"
Name: "{group}\Help"; Filename: "{app}\resources\bitpim.chm"
Name: "{group}\BitFling" ; Filename: "{app}\bitpimw.exe"; Parameters: "bitfling"; Comment: "A tool to allow BitPim to access phones on other machines"
Name: "{group}\Visit The BitPim Web Site"; Filename: "{app}\bitpim.url"

[Run]
Filename: "{app}\bitpimw.exe"; Description: "Start BitPim"; Flags: "postinstall nowait"

[Messages]
SetupLdrStartupMessage=This will install %%NAME%% %%VERSION%%. Do you wish to continue?
