#!/usr/bin/env bash
# GUS v4 — Guardian Gate (Git Bash)
# Purpose: hard-stop if integrity gates fail
# Gates: compileall + pytest + PAS status + clean working tree (no unstaged/untracked) + no tracked archives

set -euo pipefail

RED=$'\033[31m'
GRN=$'\033[32m'
YLW=$'\033[33m'
RST=$'\033[0m'

die() { echo "${RED}✖ GUARDIAN GATE FAIL:${RST} $*" 1>&2; exit 1; }
ok()  { echo "${GRN}✔${RST} $*"; }
warn(){ echo "${YLW}⚠${RST} $*"; }

repo_root="$(git rev-parse --show-toplevel 2>/dev/null)" || die "Not inside a git repository."
cd "$repo_root"

echo "🛡  GUS v4 — Guardian Gate (Git Bash)"
echo "Repo: $repo_root"
echo ""

# 1) Branch check (strict)
branch="$(git rev-parse --abbrev-ref HEAD)"
[[ "$branch" == "main" ]] || die "Branch is '$branch' (expected 'main')."

ok "Branch is main"

# 2) compileall
ok "Running: python -m compileall ."
python -m compileall . >/dev/null

# 3) pytest (force basetemp inside repo to reduce Windows temp locking noise)
ok "Running: python -m pytest -rs --basetemp .pytest_tmp"
python -m pytest -rs --basetemp .pytest_tmp

# 4) PAS status must be OK (exit 0 + contains OK)
ok "Running: python -m scripts.pas_status"
pas_out="$(python -m scripts.pas_status 2>&1)" || die "PAS status command failed."
echo "$pas_out"
echo "$pas_out" | grep -Eq "Overall PAS status:\s*OK" || die "PAS status not OK."

ok "PAS status OK"

# 5) Working tree must have NO unstaged changes and NO untracked files
ok "Checking: no unstaged changes"
git diff --quiet || die "Unstaged changes detected. Stage or stash them."

ok "Checking: no untracked files"
untracked="$(git ls-files --others --exclude-standard || true)"
[[ -z "$untracked" ]] || { echo "$untracked"; die "Untracked files detected. Add/ignore/stash them."; }

ok "Working tree clean (unstaged/untracked)"

# 6) No tracked archives (.zip)
ok "Checking: no tracked .zip files"
tracked_zips="$(git ls-files | grep -Ei '\.zip$' || true)"
[[ -z "$tracked_zips" ]] || { echo "$tracked_zips"; die "Tracked .zip files detected. Remove from index (git rm --cached <file>) and keep ignored."; }

ok "No tracked zips"

echo ""
echo "${GRN}✅ GUARDIAN GATE PASS:${RST} compileall + pytest + PAS + clean working tree + no tracked archives"
