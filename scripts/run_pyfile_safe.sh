#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "[FAIL] usage: scripts/run_pyfile_safe.sh <python_code_file.py> [args...]"
  exit 2
fi

PYFILE="$1"
shift

if [[ ! -f "$PYFILE" ]]; then
  echo "[FAIL] missing python file: $PYFILE"
  exit 2
fi

python "$PYFILE" "$@"
