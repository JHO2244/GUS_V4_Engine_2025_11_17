#!/usr/bin/env bash
set -euo pipefail

die() { echo "✖ $*" >&2; exit 1; }

usage() {
  cat <<'TXT'
LOCK_EPOCH.sh — sign + verify the current HEAD seal (no infinite loops by default)

Usage:
  bash scripts/LOCK_EPOCH.sh --priv "Z:/GuardianKeys/gus_seal_signing_ed25519_priv.pem"
  bash scripts/LOCK_EPOCH.sh --priv "Z:/GuardianKeys/gus_seal_signing_ed25519_priv.pem" --commit-sig

Env:
  GUS_SEAL_PRIV   Path to Ed25519 private key (offline). Used if --priv not provided.
  GUS_SEAL_PUB    Path to Ed25519 public key (PEM). Default: keys/gus_seal_signing_ed25519_pub.pem

Options:
  --priv PATH       Offline private key (PEM PKCS8)
  --pub PATH        Public key (PEM). Default from env or keys/...
  --commit-sig      Stage + commit the generated .sig file (WARNING: creates a new seal on commit)
  -h, --help        Show help

Notes:
  - This script signs the *current* HEAD seal. If you then commit the .sig, a *new* seal will be created for the new HEAD.
  - That’s why --commit-sig is optional. Use it only for formal releases/epoch locks.
TXT
}

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$REPO_ROOT"


# 🧠 Linguistic Guard (non-blocking): generates SSL ledger tied to this epoch lock
python -m layer0_uam_v4.linguistic.linguistic_guard || true


PRIV="${GUS_SEAL_PRIV:-}"
PUB="${GUS_SEAL_PUB:-keys/gus_seal_signing_ed25519_pub.pem}"
COMMIT_SIG=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --priv) PRIV="${2:-}"; shift 2 ;;
    --pub)  PUB="${2:-}"; shift 2 ;;
    --commit-sig) COMMIT_SIG=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) die "Unknown arg: $1 (use --help)" ;;
  esac
done

[[ -n "$PRIV" ]] || die "Missing --priv (or set env GUS_SEAL_PRIV)"
[[ -f "$PRIV" ]] || die "Private key not found: $PRIV"
[[ -f "$PUB"  ]] || die "Public key not found:  $PUB"

# Enforce CLEAN start (epoch must be intentional)
git diff --quiet || die "Working tree has unstaged changes. Commit/stash first."
git diff --cached --quiet || die "Index has staged changes. Commit/stash first."

SEALS_DIR="seals"
[[ -d "$SEALS_DIR" ]] || die "Missing ./seals directory"

SHORT="$(git rev-parse --short=12 HEAD)"
# Find latest matching seal for this short hash
SEAL="$(ls -1 "$SEALS_DIR"/seal_"$SHORT"_*.json 2>/dev/null | sort | tail -n 1 || true)"
[[ -n "$SEAL" ]] || die "No seal found for HEAD short hash: $SHORT"

echo "🧷 Repo:  $REPO_ROOT"
echo "🧷 HEAD:  $(git rev-parse HEAD)"
echo "🧷 Seal:  $SEAL"

if [[ -z "$SEAL" ]]; then
  echo "ℹ No HEAD seal found; generating one now..."
  python -m scripts.seal_snapshot >/dev/null
  SEAL="$(ls -1 "$SEALS_DIR"/seal_"$SHORT"_*.json 2>/dev/null | sort | tail -n 1 || true)"
  [[ -n "$SEAL" ]] || die "Still no seal for HEAD after snapshot."
fi

# Sign
./venv/Scripts/python -m scripts.sign_seal_signature "$SEAL" --priv "$PRIV"

SIG="${SEAL}.sig"
[[ -f "$SIG" ]] || die "Signature not created: $SIG"

# Verify signature immediately (direct verifier)
./venv/Scripts/python scripts/verify_seal_signature.py "$SEAL" --pub "$PUB"

echo "✅ Epoch seal signed + verified."

if [[ "$COMMIT_SIG" == "1" ]]; then
  echo "⚠ You enabled --commit-sig"
  echo "⚠ Committing the .sig will create a NEW HEAD (and therefore a NEW seal)."
  echo "⚠ That new seal will NOT be signed unless you run LOCK_EPOCH again."

  git add "$SIG"
  git commit -m "chore: add signature for $(basename "$SEAL") (epoch lock)"
  git push origin main
  echo "✅ .sig committed. New HEAD seal has been created (unsigned by default)."
else
  echo "ℹ .sig NOT committed (default). This avoids infinite seal loops."
fi
