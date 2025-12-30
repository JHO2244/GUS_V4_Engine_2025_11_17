#!/usr/bin/env bash
set -euo pipefail

# GUS v4 — Epoch Lock Prep (anchor + seal commit, ready for PR)
#
# What it does:
#  1) Syncs main
#  2) Creates a new prep branch
#  3) Creates + pushes an annotated epoch anchor tag on HEAD
#  4) Generates a seal snapshot for HEAD
#  5) Commits ONLY the seal json for HEAD (anchor)
#  6) Pushes the branch (PR-ready)
#
# Usage (run from repo root while on main and clean):
#   bash scripts/epoch_lock_prep.sh
#
# Optional overrides:
#   EPOCH_TAG=epoch_YYYYMMDD_anchor_main bash scripts/epoch_lock_prep.sh
#   PREP_BRANCH=chore/epoch-anchor-YYYYMMDD bash scripts/epoch_lock_prep.sh

die(){ echo "✖ $*" >&2; exit 1; }

command -v git >/dev/null || die "git not found"
git rev-parse --show-toplevel >/dev/null 2>&1 || die "Not inside a git repo"

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

# Must be clean (staged + unstaged)
if ! git diff --quiet || ! git diff --cached --quiet; then
  die "Working tree not clean. Commit/stash/reset first."
fi

# Must run from main
CUR_BRANCH="$(git branch --show-current 2>/dev/null || true)"
[[ "$CUR_BRANCH" == "main" ]] || die "Must run from main (current: $CUR_BRANCH)"

# Sync main
git fetch origin
git pull --ff-only

DATE_UTC="$(date -u +%Y%m%d)"
TIME_UTC="$(date -u +%Y%m%dT%H%M%SZ)"
HEAD12="$(git rev-parse --short=12 HEAD)"

EPOCH_TAG="${EPOCH_TAG:-epoch_${DATE_UTC}_anchor_main}"
# Back-compat: allow BRANCH=... to behave like PREP_BRANCH=...
if [[ -n "${BRANCH:-}" && -z "${PREP_BRANCH:-}" ]]; then
  PREP_BRANCH="$BRANCH"
fi
PREP_BRANCH="${PREP_BRANCH:-chore/epoch-anchor-${DATE_UTC}}"

# Tag must not already exist (local or remote)
if git rev-parse -q --verify "refs/tags/${EPOCH_TAG}" >/dev/null; then
  die "Tag already exists locally: ${EPOCH_TAG}. Set EPOCH_TAG=... to a new value."
fi
if git ls-remote --exit-code --tags origin "refs/tags/${EPOCH_TAG}" >/dev/null 2>&1; then
  die "Tag already exists on origin: ${EPOCH_TAG}. Set EPOCH_TAG=... to a new value."
fi

echo "✅ Repo:      ${REPO_ROOT}"
echo "✅ HEAD:      ${HEAD12}"
echo "✅ Epoch tag: ${EPOCH_TAG}"
echo "✅ Prep br:   ${PREP_BRANCH}"
echo

# Create prep branch
git switch -c "$PREP_BRANCH"

# Create annotated tag on current HEAD and push tag immediately
git tag -a "$EPOCH_TAG" -m "epoch anchor: main @ ${TIME_UTC}"
git push origin "$EPOCH_TAG"

# Generate seal snapshot (creates seals/seal_<HEAD12>_*.json)
python -m scripts.seal_snapshot

seal_file="$(ls -1t "seals/seal_${HEAD12}_"*.json 2>/dev/null | head -n 1 || true)"
[[ -n "${seal_file}" ]] || die "Expected seal file not found for HEAD12=${HEAD12} (seals/seal_${HEAD12}_*.json)"

# Stage ONLY this seal json
git add "$seal_file"

# Commit
git commit -m "chore(epoch): seal ${EPOCH_TAG}"

# Push prep branch
git push -u origin "$PREP_BRANCH"

echo
echo "✅ Epoch lock PREP complete."
echo "NEXT (PR = MANUAL): open a PR on GitHub:"
echo "  Base:    main"
echo "  Compare: ${PREP_BRANCH}"
echo "  Title:   chore(epoch): seal ${EPOCH_TAG}"
