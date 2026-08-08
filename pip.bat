@echo off
setlocal

title Python Package Setup

echo ========================================
echo       Python Package Setup
echo ========================================
echo.

where py >nul 2>&1
if not errorlevel 1 (
    set "PY=py -3.12"
    goto FOUND
)

where python >nul 2>&1
if not errorlevel 1 (
    set "PY=python"
    goto FOUND
)

echo ERROR: Python was not found.
pause
exit /b 1

:FOUND

echo Python detected:
%PY% --version
echo.

echo [1/3] Updating pip...
%PY% -m pip install --upgrade pip

if errorlevel 1 (
    echo ERROR: pip update failed.
    pause
    exit /b 1
)

echo.
echo [2/3] Installing project dependencies...
echo.

%PY% -m pip install --upgrade ^
    Pillow ^
    opencv-python ^
    numpy ^
    PyAudio ^
    requests ^
    psutil

if errorlevel 1 (
    echo.
    echo ERROR: Dependency installation failed.
    pause
    exit /b 1
)

echo.
echo [3/3] Installing Nuitka...
echo.

%PY% -m pip install --upgrade Nuitka

if errorlevel 1 (
    echo.
    echo ERROR: Nuitka installation failed.
    pause
    exit /b 1
)

echo.
echo ========================================
echo          SETUP COMPLETE
echo ========================================
echo.

%PY% -c "import numpy, cv2, PIL, pyaudio, requests, psutil; print('All dependencies OK')"

if errorlevel 1 (
    echo.
    echo WARNING: Dependency verification failed.
    pause
    exit /b 1
)

echo.
%PY% -m nuitka --version

echo.
echo Setup completed successfully.
echo.

pause