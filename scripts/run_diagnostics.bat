:: GUS v4 – Unified Diagnostics Runner (cmd.exe)
:: Purpose: Run full test suite + main engine diagnostic (Layers 0–9)
:: Usage:   scripts\run_diagnostics.bat

@echo off


set -e

@echo off
REM GUS v4 - Unified diagnostics runner (Windows .bat)

echo [GUS v4] Activating virtual environment (if present)...

REM Activate venv if it exists (Windows layout)
IF EXIST "venv\Scripts\activate.bat" (
    CALL "venv\Scripts\activate.bat"
)

echo.
echo [GUS v4] Running pytest...
pytest
IF ERRORLEVEL 1 (
    echo [GUS v4] Test suite failed. Aborting diagnostics.
    EXIT /B %ERRORLEVEL%
)

echo.
echo [GUS v4] Running main diagnostic...
python main.py

REM No extra "Diagnostics complete" here – main.py already prints it.
REM This keeps the final line canonical and under Python control.

EXIT /B 0
