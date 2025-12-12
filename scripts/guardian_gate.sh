#!/usr/bin/env bash
# GUS v4 — Guardian Gate (Git Bash)
# Purpose: hard-stop if integrity gates fail (compile, tests, PAS status, cleanliness, no tracked archives)
# Usage:   ./scripts/guardian_gate.sh

set -euo pipefail

RED=$'\033[31m'
GRN=$'\033[32m'
YLW=$'\033[33m'
RST=$'\033[0m'

die() {
  echo "${RED}✖ GUARDIAN GATE FAIL:${RST} $*" 1>&2
  exit 1
}

ok() { echo "${GRN}✔${RST} $*"; }
warn() { echo "${YLW}⚠${RST} $*"; }

# Ensure we are in a git repo
git rev-parse --show-toplevel >/dev/null 2>&1 || die "Not inside a git repository."

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

echo "🛡  GUS v4 — Guardian Gate (Git Bash)"
echo "Repo: $REPO_ROOT"
echo

# 1) Branch check (warn only)
BRANCH="$(git rev-parse --abbrev-ref HEAD)"
if [[ "$BRANCH" != "main" ]]; then
  warn "You are on branch '$BRANCH' (expected 'main')."
else
  ok "Branch is main"
fi

# 2) compileall
ok "Running: python -m compileall ."
python -m compileall . >/dev/null || die "compileall failed."

# 3) pytest (use python -m so it works even if pytest isn't on PATH)
ok "Running: python -m pytest -rs"
python -m pytest -rs || die "pytest failed."

# 4) PAS status
ok "Running: python -m scripts.pas_status"
PAS_OUT="$(python -m scripts.pas_status 2>&1)" || die "PAS status command failed. Output:\n$PAS_OUT"
echo "$PAS_OUT" | grep -Fq "Overall PAS status: OK" || die "PAS status not OK. Output:\n$PAS_OUT"
ok "PAS status OK"

# 5) Clean tree
ok "Checking: git status --porcelain"
if [[ -n "$(git status --porcelain)" ]]; then
  echo
  git status --porcelain
  echo
  die "Working tree not clean. Commit or stash changes."
fi
ok "Working tree clean"

# 6) No tracked zips
ok "Checking: no tracked .zip files"
if git ls-files | grep -Ei '\.zip$' >/dev/null 2>&1; then
  echo
  git ls-files | grep -Ei '\.zip$' || true
  echo
  die "Tracked .zip files detected. Remove from index + keep ignored."
fi
ok "No tracked zips"

echo
echo "${GRN}✅ GUARDIAN GATE PASS:${RST} compileall + pytest + PAS + clean tree + no tracked archives"
