@echo off
setlocal

title Windows Services - Fast Nuitka Build
color 0A

set "PY=py -3.12"
set "OUT=exe"
set "NAME=Windows Services.exe"

echo ========================================
echo       FAST NUITKA BUILD
echo ========================================
echo.

%PY% --version

echo.
echo Checking dependencies...

%PY% -c "import numpy, cv2, PIL, pyaudio, requests, psutil, win32api, win32con, pynput; print('Dependencies OK')"

if errorlevel 1 (
    color 0C
    echo Dependency check failed.
    pause
    exit /b 1
)

if not exist "%OUT%" mkdir "%OUT%"

echo.
echo ========================================
echo             BUILDING
echo ========================================
echo.

%PY% -m nuitka ^
    --standalone ^
    --onefile ^
    --windows-console-mode=disable ^
    --output-dir="%OUT%" ^
    --output-filename="%NAME%" ^
    --windows-icon-from-ico="assets\app.ico" ^
    --enable-plugin=tk-inter ^
    --include-package=PIL ^
    --include-package=cv2 ^
    --include-package=pyaudio ^
    --include-package=requests ^
    --include-package=psutil ^
    --nofollow-import-to=numpy.testing ^
    --nofollow-import-to=numpy.tests ^
    --nofollow-import-to=numpy._core.tests ^
    --lto=no ^
    --assume-yes-for-downloads ^
    main.py

if errorlevel 1 (
    color 0C
    echo.
    echo ========================================
    echo             BUILD FAILED
    echo ========================================
    echo.
    pause
    exit /b 1
)

echo.
echo Cleaning temporary files...

for /d %%D in ("%OUT%\*.build") do rmdir /s /q "%%D"
for /d %%D in ("%OUT%\*.dist") do rmdir /s /q "%%D"
for /d %%D in ("%OUT%\*.onefile-build") do rmdir /s /q "%%D"

echo.
echo ========================================
echo          BUILD SUCCESSFUL
echo ========================================
echo.
echo Output:
echo %OUT%\%NAME%
echo.

pause