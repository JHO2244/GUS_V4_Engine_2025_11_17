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

is_epoch_anchor_tag() {
  local tag="$1"
  [[ "$tag" == epoch_*_anchor_* ]]
}

commit_has_epoch_anchor_tag() {
  local commit="$1"
  local tags
  tags="$(git tag --points-at "$commit" 2>/dev/null || true)"
  while IFS= read -r t; do
    [[ -z "$t" ]] && continue
    if is_epoch_anchor_tag "$t"; then
      return 0
    fi
  done <<< "$tags"
  return 1
}

extract_hash12_from_seal_filename() {
  # expects: seals/seal_<HASH12>_YYYYMMDDThhmmssZ.json
  local path="$1"
  local base
  base="$(basename "$path")"
  echo "$base" | sed -E 's/^seal_([0-9a-f]{12})_.*/\1/'
}

enforce_seal_adds_are_for_anchor_commits() {
  local added
  added="$(git diff --cached --name-status | awk '$1=="A" {print $2}' | grep -E '^seals/seal_.*\.json$' || true)"
  [[ -z "$added" ]] && return 0

  local bad=0
  while IFS= read -r f; do
    [[ -z "$f" ]] && continue
    local h12 commit
    h12="$(extract_hash12_from_seal_filename "$f")"

    if [[ ! "$h12" =~ ^[0-9a-f]{12}$ ]]; then
      echo "✖ BLOCKED: seal filename does not contain a valid 12-char hash: $f"
      bad=1
      continue
    fi

    commit="$(git rev-parse "${h12}^{commit}" 2>/dev/null || true)"
    if [[ -z "$commit" ]]; then
      echo "✖ BLOCKED: seal hash does not resolve to a commit: $h12 (file: $f)"
      bad=1
      continue
    fi

    if ! commit_has_epoch_anchor_tag "$commit"; then
      echo "✖ BLOCKED: seal add is NOT for an approved epoch anchor commit"
      echo "  Seal file:   $f"
      echo "  Commit:      $h12"
      echo "  Required:    a tag matching epoch_*_anchor_* must point to that commit"
      echo "  Found tags:  $(git tag --points-at "$commit" 2>/dev/null | tr '\n' ' ')"
      bad=1
    fi
  done <<< "$added"

  if [[ "$bad" == "1" ]]; then
    echo
    echo "If this is truly intentional, re-run with:"
    echo "  GUS_ALLOW_SEAL_CHANGES=1 git commit ..."
    exit 1
  fi
}

enforce_seals_policy() {
  # 🚫 Block ANY staged changes under seals/ except:
  #   ✅ A seals/seal_*.json
  #   ✅ A seals/*.sig
  #
  # Extra lock: seal_*.json adds must be for epoch_*_anchor_* commits only.
  if [[ "${GUS_ALLOW_SEAL_CHANGES:-0}" == "1" ]]; then
    echo "⚠ NOTE: GUS_ALLOW_SEAL_CHANGES=1 set — seals/ policy bypassed."
    return 0
  fi

  if git diff --cached --quiet; then
    return 0
  fi

  local bad=""
  while IFS= read -r line; do
    [[ -z "$line" ]] && continue

    local status path1 path2
    status="$(awk '{print $1}' <<<"$line")"
    path1="$(awk '{print $2}' <<<"$line")"
    path2="$(awk '{print $3}' <<<"$line")"

    if [[ "$status" =~ ^R|^C ]]; then
      if [[ "${path1:-}" == seals/* || "${path2:-}" == seals/* ]]; then
        bad+="$line"$'\n'
      fi
      continue
    fi

    if [[ "${path1:-}" != seals/* ]]; then
      continue
    fi

    if [[ "$status" == "A" && "$path1" =~ ^seals/seal_.*\.json$ ]]; then
      continue
    fi

    if [[ "$status" == "A" && "$path1" =~ ^seals/.*\.sig$ ]]; then
      continue
    fi

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

  enforce_seal_adds_are_for_anchor_commits
}

echo "🛡 ${MODE}: Guardian Gate"
echo "Repo: ${REPO_ROOT}"

check_working_tree_cleanliness
enforce_seals_policy

if [[ "${MODE}" == "pre-commit" ]]; then
  echo "OK: pre-commit gate passed."
  exit 0
fi

# NORMAL gate:
if [[ "${GUS_STRICT_SEALS:-0}" == "1" ]]; then
  python -m scripts.verify_repo_seals --head --sig-strict
else
  python -m scripts.verify_repo_seals --head --no-sig
fi

python -m layer0_uam_v4.linguistic.linguistic_guard || true

echo "OK: normal gate passed."
