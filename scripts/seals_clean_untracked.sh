#!/usr/bin/env bash
set -euo pipefail

# Deletes ONLY untracked seal JSON files (safe).
# Does NOT touch committed seals.

echo "🧼 Cleaning ONLY untracked seals/seal_*.json ..."
git clean -f -- seals/seal_*.json
echo "✅ Done."
