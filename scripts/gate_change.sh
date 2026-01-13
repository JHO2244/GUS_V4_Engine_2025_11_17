#!/usr/bin/env bash
set -euo pipefail

# Guardian Change Gate v0.1
# Enforces: commit -> seal -> verify -> pytest (and optional push)

if [[ "${1:-}" == "" ]]; then
  echo "USAGE:"
  echo "  bash scripts/gate_change.sh "<commit message>" [--push] [--require-clean]"
  exit 2
fi

MSG="$1"
shift || true

DO_PUSH="no"
REQUIRE_CLEAN="no"
for arg in "$@"; do
  if [[ "$arg" == "--push" ]]; then DO_PUSH="yes"; fi
  if [[ "$arg" == "--require-clean" ]]; then REQUIRE_CLEAN="yes"; fi
done

cd "$(git rev-parse --show-toplevel)"

echo "=== 0) status ==="
STATUS="$(git status --porcelain)"
echo "$STATUS"

if [[ "$REQUIRE_CLEAN" == "yes" ]]; then
  if [[ -n "$STATUS" ]]; then
    echo "[FAIL] --require-clean set, but working tree is dirty. Refusing to run."
    exit 1
  fi
fi

# Require that something is staged or modified (prevents empty gate runs)
if [[ -z "$STATUS" ]]; then
  echo "[FAIL] No changes detected. Refusing to run gate."
  exit 1
fi

echo "=== 1) commit (includes any staged changes) ==="
git add -A
git commit -m "$MSG"

echo "=== 2) seal head (mandatory) ==="
python scripts/seal_snapshot.py --no-sig --require-head

echo "=== 3) commit the new seal file ==="
git add seals/*.json
git commit -m "Seal: record HEAD (post change gate)"

echo "=== 4) verify repo seals (CI mode) ==="
python -m scripts.verify_repo_seals --head --no-sig --require-head --ci

echo "=== 5) pytest ==="
python -m pytest -q

if [[ "$DO_PUSH" == "yes" ]]; then
  echo "=== 6) push (guarded by pytest already) ==="
  git push
fi

echo "=== OK: Change gate complete ==="
