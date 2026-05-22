@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo Creating desktop shortcuts...

set "DESKTOP=%USERPROFILE%\Desktop"

powershell -Command ^
"$ws = New-Object -ComObject WScript.Shell;" ^
"$s1 = $ws.CreateShortcut('%DESKTOP%\PDF笔记生成器.lnk');" ^
"$s1.TargetPath = '%~dp0一键生成笔记.bat';" ^
"$s1.WorkingDirectory = '%~dp0';" ^
"$s1.Save();" ^
"$s2 = $ws.CreateShortcut('%DESKTOP%\PDF笔记生成器(GUI).lnk');" ^
"$s2.TargetPath = '%~dp0launch_noter.bat';" ^
"$s2.WorkingDirectory = '%~dp0';" ^
"$s2.Save();" ^
"Write-Host 'Done!';" ^
"Start-Sleep 1"

echo.
echo Both shortcuts have been recreated!
echo   1. PDF笔记生成器 (drag and drop)
echo   2. PDF笔记生成器(GUI) (double click)
echo.
pause
