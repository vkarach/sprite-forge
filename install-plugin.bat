@echo off
set DEST=%APPDATA%\Aseprite\extensions\spriteforge
if not exist "%DEST%" mkdir "%DEST%"
copy /Y "%~dp0plugin\*.*" "%DEST%\" >nul
echo Installed to %DEST%. Restart Aseprite.
pause
