#!/usr/bin/env bash
set -euo pipefail

# ---------------------------
# Guardian Gate (safe to source)
# ---------------------------

die() { echo "✖ $*" >&2; return 1; }

# --- Seal strictness policy (anti-drift + milestone exactness) ---

# Config:
#   GUS_MAX_UNSEALED_COMMITS: how far HEAD may drift past the latest sealed ancestor on main.
#   GUS_REQUIRE_SEALED_ANCHOR: if 1, epoch_*_anchor_* commits must have an exact seal (no fallback).
GUS_MAX_UNSEALED_COMMITS="${GUS_MAX_UNSEALED_COMMITS:-1}"
GUS_REQUIRE_SEALED_ANCHOR="${GUS_REQUIRE_SEALED_ANCHOR:-1}"

head12() { git rev-parse --short=12 HEAD; }

seal_exists_for_hash12() {
  local h12="$1"
  ls "seals/seal_${h12}_"*.json >/dev/null 2>&1
}

head_has_epoch_anchor_tag() {
  git tag --points-at HEAD 2>/dev/null | grep -E '^epoch_.*_anchor_.*$' >/dev/null 2>&1
}

nearest_sealed_ancestor_distance_first_parent() {
  # Walk first-parent history to avoid merge-noise and find closest commit that has a seal file present.
  # Echoes: "<distance> <hash12>" or returns 1 if none found.
  local i=0
  while read -r c; do
    local h12
    h12="$(git rev-parse --short=12 "$c")"
    if seal_exists_for_hash12 "$h12"; then
      echo "$i $h12"
      return 0
    fi
    i=$((i+1))
  done < <(git rev-list --first-parent HEAD)
  return 1
}

enforce_head_seal_strictness() {
  # Only enforce on main (this is your operational safety rail)
  local branch
  branch="$(git branch --show-current 2>/dev/null || true)"
  [[ "$branch" != "main" ]] && return 0

  local h12
  h12="$(head12)"

  # Milestone exactness: if HEAD is an epoch anchor, it must have its own seal.
  if head_has_epoch_anchor_tag && [[ "$GUS_REQUIRE_SEALED_ANCHOR" == "1" ]]; then
    if ! seal_exists_for_hash12 "$h12"; then
      echo "✖ BLOCKED: HEAD is tagged as an epoch anchor, but has NO exact seal committed."
      echo "  HEAD: $h12"
      echo "  Required file: seals/seal_${h12}_*.json"
      echo "  Fix: create the seal for this anchor commit via the lock/seal-* PR flow."
      exit 1
    fi
    return 0
  fi

  # Operational drift limit: do not allow main to drift too far from last sealed ancestor.
  local out dist sealed_h12
  out="$(nearest_sealed_ancestor_distance_first_parent || true)"
  if [[ -z "$out" ]]; then
    echo "✖ BLOCKED: No sealed ancestor found on main. You must establish an epoch anchor + seal."
    exit 1
  fi

  dist="$(awk '{print $1}' <<<"$out")"
  sealed_h12="$(awk '{print $2}' <<<"$out")"

  effective_max="$GUS_MAX_UNSEALED_COMMITS"
  if [[ "${effective_max:-}" -eq 0 ]]; then effective_max=1; fi

  if [[ "$dist" -gt "$effective_max" ]]; then
    echo "✖ BLOCKED: main drifted too far past last sealed ancestor."
    echo "  HEAD:           $h12"
    echo "  Sealed ancestor:$sealed_h12"
    echo "  Distance:       $dist commits (max allowed: $effective_max)"
    echo
    echo "Fix: create a new epoch_*_anchor_* tag on current main, then run the lock/seal PR flow."
    exit 1
  fi
}

check_working_tree_cleanliness() {
  # Unstaged drift (untracked doesn't count here)
  if ! git diff --quiet; then
    die "Unstaged changes present. Stage or discard them first."
    return 1
  fi

  # Staged changes are expected during pre-commit
  if ! git diff --cached --quiet; then
    if [[ "${MODE}" == "pre-commit" ]]; then
      echo "ℹ Staged changes detected (expected during pre-commit)."
    else
      die "Staged but uncommitted changes present. Commit them or reset the index."
      return 1
    fi
  fi

  return 0
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
    return 1
  fi
}

enforce_seals_policy() {
  # 🚫 Block ANY staged changes under seals/ except:
  #   ✅ A seals/seal_*.json
  #   ✅ A seals/*.sig
  #
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

    local status path1 path2
    status="$(awk '{print $1}' <<<"$line")"
    path1="$(awk '{print $2}' <<<"$line")"
    path2="$(awk '{print $3}' <<<"$line")"

    # For rename/copy, any touch of seals/ is forbidden
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
    return 1
  fi

  # Extra lock: seal JSON adds must be for epoch anchor commits only
  enforce_seal_adds_are_for_anchor_commits
}

main() {
  REPO_ROOT="$(git rev-parse --show-toplevel)"
  cd "$REPO_ROOT"

  # --- recursion guard (SINGLE, authoritative) ---
  if [[ "${GUS_GUARDIAN_GATE_RUNNING:-0}" == "1" ]]; then
    echo "ERROR: BLOCKED: Guardian Gate recursion detected."
    exit 1
  fi
  export GUS_GUARDIAN_GATE_RUNNING=1
  trap 'unset GUS_GUARDIAN_GATE_RUNNING' EXIT

  # --- Mode must be defined BEFORE any checks use it (set -u safety) ---
  MODE="normal"
  if [[ "${1:-}" == "--pre-commit" ]]; then
    MODE="pre-commit"
  fi


  # --- Mode must be defined BEFORE any checks use it (set -u safety) ---
  # --- Guardrail: prevent feature commits directly on main ---
  if [[ "${MODE}" == "pre-commit" ]]; then
    branch="$(git branch --show-current 2>/dev/null || true)"
    if [[ "$branch" == "main" ]]; then
      # Prefer the *current* commit message being authored (not the last commit)
      msg_file="$(git rev-parse --git-path COMMIT_EDITMSG 2>/dev/null || true)"
      msg=""
      if [[ -n "${msg_file:-}" && -f "$msg_file" ]]; then
        msg="$(tr '[:upper:]' '[:lower:]' < "$msg_file" | sed -e 's/^[[:space:]]*//' )"
      else
        msg="$(git log -1 --pretty=%B | tr '[:upper:]' '[:lower:]')"
      fi

      if [[ "$msg" =~ ^feat\( || "$msg" =~ ^feat: || "$msg" =~ ^feature ]]; then
        echo "✖ BLOCKED: Feature commits are not allowed directly on main."
        echo
        echo "Reason:"
        echo "  main is protected for merge-only feature integration."
        echo
        echo "Fix:"
        echo "  git switch -c feat/<short-name>"
        echo "  git commit ..."
        exit 1
      fi
    fi
  fi



  echo "🛡 ${MODE}: Guardian Gate"
  echo "Repo: ${REPO_ROOT}"

  check_working_tree_cleanliness || exit 1
  enforce_seals_policy || exit 1
  enforce_head_seal_strictness

  if [[ "${MODE}" == "pre-commit" ]]; then
    echo "OK: pre-commit gate passed."
    exit 0
  fi

   # NORMAL gate: verify seals
  # Milestone mode (file-flag) requires an exact HEAD seal (no fallback).
  if [[ -f ".gus/milestone_required" ]]; then
    echo "🧱 milestone: strict HEAD seal required"
    if [[ "${GUS_STRICT_SEALS:-0}" == "1" ]]; then
      python -m scripts.verify_repo_seals --head --require-head --sig-strict
    else
      python -m scripts.verify_repo_seals --head --require-head --no-sig
    fi
  else
    # Dev flow: nearest sealed ancestor fallback allowed (current behavior).
    if [[ "${GUS_STRICT_SEALS:-0}" == "1" ]]; then
      python -m scripts.verify_repo_seals --head --sig-strict
    else
      python -m scripts.verify_repo_seals --head --no-sig
    fi
  fi


  # 🧠 Linguistic Guard (non-blocking)
  python -m layer0_uam_v4.linguistic.linguistic_guard || true

  echo "OK: normal gate passed."
}

# ✅ KEY FIX: If sourced, do nothing (only load functions). If executed, run main.
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  main "$@"
fi

