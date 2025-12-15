#!/usr/bin/env bash
set -euo pipefail

MODE="normal"
if [[ "${1-}" == "--pre-commit" ]]; then
  MODE="pre-commit"
  shift || true
fi

echo "🛡 ${MODE}: Guardian Gate"
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
echo "Repo: ${REPO_ROOT}"

check_working_tree_cleanliness() {
  echo "🛡 Checking working tree cleanliness"

  # 1) Always block on UNSTAGED drift (hidden edits)
  if ! git diff --quiet; then
    echo "✖ BLOCKED: Unstaged changes present (git diff)."
    exit 1
  fi

  # 2) Staged changes:
  #    - pre-commit: expected → warn only
  #    - normal: should be clean → block
  if ! git diff --cached --quiet; then
    if [[ "${MODE}" == "pre-commit" ]]; then
      echo "⚠ Note: Staged changes detected (expected during pre-commit)."
    else
      echo "✖ BLOCKED: Staged but uncommitted changes present (git diff --cached)."
      exit 1
    fi
  fi

  echo "✔ Working tree cleanliness OK (no unstaged deltas)"
}

# --- IMPORTANT: prevent self-invocation recursion ---
# If your script contains any line like:
#   bash scripts/guardian_gate.sh
# delete it. The gate should run checks directly, not re-run itself.
# ---------------------------------------------------

# ... keep the rest of your checks, then call:
check_working_tree_cleanliness

