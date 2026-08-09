@echo off
setlocal EnableExtensions

title Windows Services - Startup Manager
color 0A

set "APP_NAME=Windows Services.exe"
set "APP=%~dp0%APP_NAME%"
set "STARTUP=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "DEST_DIR=%LOCALAPPDATA%\Windows Services"
set "DEST_APP=%DEST_DIR%\%APP_NAME%"
set "SHORTCUT=%STARTUP%\Windows Services.lnk"

:MENU
cls
echo.
echo  ==================================================
echo              WINDOWS SERVICES
echo  ==================================================
echo.
echo       [1] RUN And Enable Auto Startup 
echo       [2] Disable Auto Startup
echo       [3] Exit
echo.
echo  ==================================================
echo.

choice /c 123 /n /m "  Select option: "

if errorlevel 3 goto EXIT
if errorlevel 2 goto DISABLE
if errorlevel 1 goto ENABLE


:ENABLE
cls
echo.
echo  ==================================================
echo               ENABLE AUTO STARTUP
echo  ==================================================
echo.

if not exist "%APP%" (
    color 0C
    echo  [ERROR] %APP_NAME% not found in current folder.
    color 0A
    echo.
    pause
    goto MENU
)

echo  [OK] Starting application from current location...
start "" "%APP%"

echo  [INFO] Copying application to persistent location...
if not exist "%DEST_DIR%" mkdir "%DEST_DIR%"
copy /Y "%APP%" "%DEST_APP%" >nul

if errorlevel 1 (
    color 0C
    echo  [ERROR] Failed to copy application.
    color 0A
    echo.
    pause
    goto MENU
)

if not exist "%STARTUP%" mkdir "%STARTUP%"

powershell -NoProfile -ExecutionPolicy Bypass -Command "$W=New-Object -ComObject WScript.Shell; $S=$W.CreateShortcut('%SHORTCUT%'); $S.TargetPath='%DEST_APP%'; $S.WorkingDirectory='%DEST_DIR%'; $S.Description='Windows Services'; $S.Save()"

if errorlevel 1 (
    color 0C
    echo  [ERROR] Failed to create Startup shortcut.
    color 0A
    echo.
    pause
    goto MENU
)

echo  [OK] Auto Startup enabled.
echo  [OK] Application copied to:
echo      %DEST_APP%
echo  [OK] Startup shortcut created.
echo.
timeout /t 3 >nul
goto MENU


:DISABLE
cls
echo.
echo  ==================================================
echo              DISABLE AUTO STARTUP
echo  ==================================================
echo.

if exist "%SHORTCUT%" (
    del /f /q "%SHORTCUT%"
    echo  [OK] Startup shortcut removed. Auto-start disabled.
) else (
    echo  [INFO] Auto Startup is already disabled.
)

echo  [INFO] Running application is NOT closed.
echo.
timeout /t 3 >nul
goto MENU


:EXIT
color 07
endlocal
exit /b 0