#!/usr/bin/env bash
# Install tracked hook templates into .git/hooks
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel)"
cd "$repo_root"

src="scripts/hooks/pre-commit"
dst=".git/hooks/pre-commit"

if [[ ! -f "$src" ]]; then
  echo "✖ Missing template: $src" 1>&2
  exit 1
fi

mkdir -p ".git/hooks"
cp "$src" "$dst"

# Best-effort executable bit (may not matter on Windows)
chmod +x "$dst" 2>/dev/null || true

echo "✅ Hooks installed: $dst"
echo "Tip: test with: git commit --allow-empty -m \"test: hooks\""
