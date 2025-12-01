#!/usr/bin/env bash

echo
echo "[GUS v4] Activating virtual environment (if present)..."
if [ -d "venv" ]; then
  source venv/Scripts/activate || echo "[GUS v4] WARNING: Could not activate venv, continuing..."
fi

echo
echo "[GUS v4] Running pytest..."
pytest

echo
echo "[GUS v4] Running main diagnostic..."
python main.py

echo
echo "[GUS v4] Diagnostics run complete."
