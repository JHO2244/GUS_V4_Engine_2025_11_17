#!/usr/bin/env bash
set -euo pipefail

echo "🛡 GUS v4 — Post-Commit Repo Snapshot"
python -m scripts.seal_snapshot

# Keep repo clean: do NOT leave untracked seal JSONs lying around after a commit.
# Epoch locks are the ONLY time we intentionally commit a seal JSON.
bash scripts/seals_clean_untracked.sh >/dev/null || true
