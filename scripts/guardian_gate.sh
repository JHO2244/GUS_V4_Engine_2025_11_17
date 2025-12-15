#!/usr/bin/env bash
set -euo pipefail

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
