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
  # Unstaged drift (untracked doesn't count here)
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

enforce_seals_policy() {
  # 🚫 Block ANY staged changes under seals/ except:
  #   ✅ A seals/seal_*.json
  #   ✅ A seals/*.sig
  #
  # This prevents D/R/M chaos, renames, edits, etc.
  # Override ONLY if explicitly set: GUS_ALLOW_SEAL_CHANGES=1
  if [[ "${GUS_ALLOW_SEAL_CHANGES:-0}" == "1" ]]; then
    echo "⚠ NOTE: GUS_ALLOW_SEAL_CHANGES=1 set — seals/ policy bypassed."
    return 0
  fi

  # Nothing staged -> nothing to enforce
  if git diff --cached --quiet; then
    return 0
  fi

  local bad=""
  while IFS= read -r line; do
    [[ -z "$line" ]] && continue

    # Parse name-status lines (handles rename format too)
    # Examples:
    #  A\tseals/seal_x.json
    #  M\tseals/seal_x.json
    #  D\tseals/seal_x.json
    #  R100\tseals/old.json\tseals/new.json
    local status path1 path2
    status="$(awk '{print $1}' <<<"$line")"
    path1="$(awk '{print $2}' <<<"$line")"
    path2="$(awk '{print $3}' <<<"$line")"

    # Normalize: for rename/copy, check BOTH paths
    # We treat ANY R/C touching seals/ as forbidden by default.
    if [[ "$status" =~ ^R|^C ]]; then
      if [[ "${path1:-}" == seals/* || "${path2:-}" == seals/* ]]; then
        bad+="$line"$'\n'
      fi
      continue
    fi

    # Only care about seals/ paths
    if [[ "${path1:-}" != seals/* ]]; then
      continue
    fi

    # Allow ONLY added seal json
    if [[ "$status" == "A" && "$path1" =~ ^seals/seal_.*\.json$ ]]; then
      continue
    fi

    # Allow ONLY added sig files
    if [[ "$status" == "A" && "$path1" =~ ^seals/.*\.sig$ ]]; then
      continue
    fi

    # Everything else under seals/ is forbidden
    bad+="$line"$'\n'
  done < <(git diff --cached --name-status)

  if [[ -n "$bad" ]]; then
    echo "✖ BLOCKED: Unauthorized staged change(s) under seals/."
    echo
    echo "Allowed ONLY:"
    echo "  ✅ A  seals/seal_*.json"
    echo "  ✅ A  seals/*.sig"
    echo
    echo "Found:"
    printf "%s" "$bad"
    echo
    echo "If this is truly intentional, re-run with:"
    echo "  GUS_ALLOW_SEAL_CHANGES=1 git commit ..."
    exit 1
  fi
}

echo "🛡 ${MODE}: Guardian Gate"
echo "Repo: ${REPO_ROOT}"

check_working_tree_cleanliness
enforce_seals_policy

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
