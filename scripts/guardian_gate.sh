#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

# --- recursion guard (SINGLE, authoritative) ---
if [[ "${GUS_GUARDIAN_GATE_RUNNING:-0}" == "1" ]]; then
  echo "ERROR: BLOCKED: Guardian Gate recursion detected."
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
  # Unstaged drift (including untracked?) is handled by git diff; untracked doesn't count here.
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

echo "🛡 ${MODE}: Guardian Gate"
echo "Repo: ${REPO_ROOT}"

check_working_tree_cleanliness

if [[ "${MODE}" == "pre-commit" ]]; then
  # FAST gate: no heavy calls, no signatures, no seal verification
  echo "OK: pre-commit gate passed."
  exit 0
fi

# NORMAL gate:
# Default = content-only verification (no signature) so we don't create infinite signing loops.
# If you want strict signatures, set GUS_STRICT_SEALS=1 explicitly.
if [[ "${GUS_STRICT_SEALS:-0}" == "1" ]]; then
  python -m scripts.verify_repo_seals --head --sig-strict
else
  python -m scripts.verify_repo_seals --head --no-sig
fi

# 🧠 Linguistic Guard (non-blocking)
python -m layer0_uam_v4.linguistic.linguistic_guard || true

echo "OK: normal gate passed."

# 🚫 Block accidental deletion of committed seal JSONs
# Allow override only if user explicitly sets: GUS_ALLOW_SEAL_DELETIONS=1
if [[ "${GUS_ALLOW_SEAL_DELETIONS:-0}" != "1" ]]; then
  if git diff --cached --name-status | awk '$1=="D" {print $2}' | grep -q '^seals/seal_.*\.json$'; then
    echo "✖ BLOCKED: Attempt to delete committed seal JSON(s) under seals/"
    echo "  If this is truly intentional, re-run with:"
    echo "    GUS_ALLOW_SEAL_DELETIONS=1 git commit ..."
    exit 1
  fi
fi
