@echo off
setlocal EnableExtensions EnableDelayedExpansion

REM GUS v4 – Unified Diagnostics Runner (cmd.exe)
REM Purpose: Run full test suite + main engine diagnostic (Layers 0–9)
REM Usage:   scripts\run_diagnostics.bat

REM Force repo root (directory above this script)
cd /d "%~dp0\.." || (echo [GUS v4] ERROR: cannot cd to repo root & exit /b 1)

REM Choose explicit Python (prefer venv)
set "PY=python"
if exist "venv\Scripts\python.exe" set "PY=venv\Scripts\python.exe"

echo [GUS v4] Using Python: %PY%

echo.
echo [GUS v4] Running pytest...
"%PY%" -m pytest -q
IF ERRORLEVEL 1 (
    echo [GUS v4] Test suite failed. Aborting diagnostics.
    exit /b %ERRORLEVEL%
)

echo.
echo [GUS v4] Running main diagnostic...
"%PY%" main.py
IF ERRORLEVEL 1 (
    echo [GUS v4] main.py failed.
    exit /b %ERRORLEVEL%
)

exit /b 0
