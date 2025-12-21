#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

# --- recursion guard (SINGLE, authoritative) ---
if [[ "${GUS_GUARDIAN_GATE_RUNNING:-0}" == "1" ]]; then
  echo "✖ BLOCKED: Guardian Gate recursion detected."
  exit 1
fi
export GUS_GUARDIAN_GATE_RUNNING=1
trap 'unset GUS_GUARDIAN_GATE_RUNNING' EXIT

MODE="normal"
if [[ "${1:-}" == "--pre-commit" ]]; then
  MODE="pre-commit"
fi

die() { echo "✖ $*" >&2; exit 1; }

check_working_tree_cleanliness() {
  # Always block on unstaged drift (hidden edits)
  if ! git diff --quiet; then
    die "Unstaged changes present. Stage or discard them first."
  fi

  # Staged changes are expected during pre-commit
  if ! git diff --cached --quiet; then
    if [[ "${MODE}" == "pre-commit" ]]; then
      echo "ℹ Staged changes detected (expected during pre-commit)."
    else
      die "Staged but uncommitted changes present. Commit them or reset the index."
    fi
  fi
}

# -------------------------
# Main
# -------------------------
echo "🛡 ${MODE}: Guardian Gate"
echo "Repo: ${REPO_ROOT}"

if [[ "${MODE}" == "pre-commit" ]]; then
  check_working_tree_cleanliness
  echo "✅ pre-commit gate passed."
  exit 0
fi

# Normal mode: full audit
check_working_tree_cleanliness

# Signature policy:
# - Default: relaxed (allows untracked seals/*.sig only)
# - If GUS_STRICT_SEALS=1 → strict (requires signature and clean tree)
if [[ "${GUS_STRICT_SEALS:-0}" == "1" ]]; then
  echo "🛡 Verifying seals (HEAD) [sig-strict]"
  python -m scripts.verify_repo_seals --head --sig-strict
else
  echo "🛡 Verifying seals (HEAD) [sig-relaxed]"
  python -m scripts.verify_repo_seals --head --sig-relaxed
fi

echo "✅ normal gate passed."
