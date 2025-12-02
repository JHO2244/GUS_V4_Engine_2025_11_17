#!/usr/bin/env bash
set -e

echo "[GUS v4] Locating repo root..."

# Resolve script directory and repo root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

echo "[GUS v4] Activating virtual environment (if present)..."

# On Git Bash in Windows, the venv is usually Scripts/activate
if [ -f "venv/Scripts/activate" ]; then
  # shellcheck source=/dev/null
  source "venv/Scripts/activate"
  echo "[GUS v4] venv activated."
else
  echo "[GUS v4] venv already active or missing – continuing."
fi

echo
echo "[GUS v4] Running pytest..."
pytest

echo
echo "[GUS v4] Running main diagnostic (python main.py)..."
python main.py

echo
echo "[GUS v4] Diagnostics run complete."
