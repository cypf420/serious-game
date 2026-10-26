@echo off
setlocal EnableExtensions
chcp 65001 >nul
title Serious Game Launcher

set "LAUNCHER_DIR=%~dp0"
set "PYTHON_EXE="

if exist "%LAUNCHER_DIR%.venv\Scripts\python.exe" set "PYTHON_EXE=%LAUNCHER_DIR%.venv\Scripts\python.exe"

if not defined PYTHON_EXE (
    for /f "delims=" %%I in ('where python.exe 2^>nul') do (
        if not defined PYTHON_EXE (
            "%%I" -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)" >nul 2>&1
            if not errorlevel 1 set "PYTHON_EXE=%%I"
        )
    )
)

if not defined PYTHON_EXE (
    for /f "delims=" %%I in ('py.exe -3 -c "import sys; print(sys.executable)" 2^>nul') do (
        if not defined PYTHON_EXE (
            "%%I" -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)" >nul 2>&1
            if not errorlevel 1 set "PYTHON_EXE=%%I"
        )
    )
)

if not defined PYTHON_EXE goto :missing_python
if not exist "%LAUNCHER_DIR%launcher.py" goto :missing_project

"%PYTHON_EXE%" "%LAUNCHER_DIR%launcher.py" %*
set "LAUNCH_EXIT=%ERRORLEVEL%"
if not "%LAUNCH_EXIT%"=="0" pause
exit /b %LAUNCH_EXIT%

:missing_project
echo [ERROR] launcher.py was not found beside BEGIN.BAT.
pause
exit /b 1

:missing_python
echo [ERROR] Python 3.11 or newer was not found.
echo Install Python and enable "Add Python to PATH", then run BEGIN.BAT again.
pause
exit /b 1
