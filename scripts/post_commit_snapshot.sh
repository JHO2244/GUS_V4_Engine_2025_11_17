#!/usr/bin/env bash
set -euo pipefail
echo "🛡 GUS v4 — Post-Commit Repo Snapshot"
python -m scripts.seal_snapshot
