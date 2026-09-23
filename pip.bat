```bat
@echo off
setlocal EnableExtensions

title Python Package Setup

echo ========================================
echo       Python Package Setup
echo ========================================
echo.

REM ========================================
REM Find Python
REM ========================================

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
echo Please install Python 3.12 first.
pause
exit /b 1


:FOUND

echo Python detected:
%PY% --version
echo.


REM ========================================
REM [1/4] Upgrade pip
REM ========================================

echo [1/4] Updating pip...
%PY% -m pip install --upgrade pip

if errorlevel 1 (
    echo.
    echo ERROR: pip update failed.
    pause
    exit /b 1
)

echo.


REM ========================================
REM [2/4] Install dependencies
REM ========================================

echo [2/4] Installing project dependencies...
echo.

%PY% -m pip install --upgrade ^
    Pillow ^
    opencv-python ^
    numpy ^
    PyAudio ^
    requests ^
    psutil ^
    pywin32 ^
    pynput

if errorlevel 1 (
    echo.
    echo ERROR: Dependency installation failed.
    pause
    exit /b 1
)

echo.


REM ========================================
REM [3/4] Install Nuitka
REM ========================================

echo [3/4] Installing Nuitka...
echo.

%PY% -m pip install --upgrade Nuitka

if errorlevel 1 (
    echo.
    echo ERROR: Nuitka installation failed.
    pause
    exit /b 1
)

echo.


REM ========================================
REM [4/4] Verify dependencies
REM ========================================

echo [4/4] Verifying dependencies...
echo.

%PY% -c "import numpy; import cv2; import PIL; import pyaudio; import requests; import psutil; import win32api; import pynput; print('All dependencies OK')"

if errorlevel 1 (
    echo.
    echo ERROR: Dependency verification failed.
    pause
    exit /b 1
)

echo.
echo Installed versions:
echo ----------------------------------------

%PY% -c "import numpy; print('NumPy      :', numpy.__version__)"
%PY% -c "import cv2; print('OpenCV     :', cv2.__version__)"
%PY% -c "import PIL; print('Pillow     :', PIL.__version__)"
%PY% -c "import pyaudio; print('PyAudio    :', pyaudio.__version__)"
%PY% -c "import requests; print('Requests   :', requests.__version__)"
%PY% -c "import psutil; print('PSUtil     :', psutil.__version__)"
%PY% -c "import pynput; print('Pynput     :', pynput.__version__)"

echo.
echo Nuitka:
%PY% -m nuitka --version

if errorlevel 1 (
    echo.
    echo WARNING: Nuitka verification failed.
    pause
    exit /b 1
)

echo.
echo ========================================
echo          SETUP COMPLETE
echo ========================================
echo.
echo All Python dependencies are installed
echo and verified successfully.
echo.

pause
```
