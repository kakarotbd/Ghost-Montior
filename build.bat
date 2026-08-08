@echo off
setlocal EnableExtensions

title Build

set "PY=py -3.12"
set "OUT=exe"
set "NAME=Windows Services.exe"

echo ========================================
echo          FAST NUITKA BUILD
echo ========================================
echo.

%PY% --version
if errorlevel 1 exit /b 1

echo.
echo Checking modules...

%PY% -c "import audioop,numpy,cv2,PIL,pyaudio,requests,psutil; print('Dependencies OK')"
if errorlevel 1 exit /b 1

echo.
echo Checking Nuitka...

%PY% -m nuitka --version
if errorlevel 1 exit /b 1

if exist "%OUT%" rmdir /s /q "%OUT%"
mkdir "%OUT%"

echo.
echo ========================================
echo              BUILDING
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
    --include-package=numpy ^
    --include-package=pyaudio ^
    --include-package=requests ^
    --include-package=psutil ^
    --lto=no ^
    --assume-yes-for-downloads ^
    main.py

if errorlevel 1 (
    echo.
    echo BUILD FAILED
    pause
    exit /b 1
)

echo.
echo ========================================
echo BUILD COMPLETE
echo ========================================
echo.
echo %OUT%\%NAME%
echo.

pause