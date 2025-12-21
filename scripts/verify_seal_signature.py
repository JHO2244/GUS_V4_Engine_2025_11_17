from __future__ import annotations

import argparse
import subprocess
from pathlib import Path
import sys

DEFAULT_PUBKEY = Path("keys/gus_seal_signing_ed25519.pub")


def run(cmd: list[str]) -> int:
    p = subprocess.run(cmd, text=True)
    return p.returncode


def sh(cmd: list[str]) -> str:
    return subprocess.check_output(cmd, text=True).strip()


def repo_root() -> Path:
    return Path(sh(["git", "rev-parse", "--show-toplevel"]))


def head_short_12() -> str:
    return sh(["git", "rev-parse", "--short=12", "HEAD"])


def list_seals(seals_dir: Path) -> list[Path]:
    if not seals_dir.exists():
        return []
    return sorted(seals_dir.glob("seal_*_*.json"))


def find_latest_seal_for_short_hash(seals: list[Path], short_hash: str) -> Path | None:
    matches = [p for p in seals if p.name.startswith(f"seal_{short_hash}_")]
    return matches[-1] if matches else None


def verify_one(seal_path: Path, verify_sig: bool, pubkey: Path | None) -> None:
    if not seal_path.exists():
        raise SystemExit(f"✖ Seal file missing: {seal_path}")

    # 1) Structural + content verification
    rc = run([sys.executable, "-m", "scripts.verify_seal", str(seal_path)])
    if rc != 0:
        raise SystemExit(f"✖ verify_seal failed for {seal_path.name}")

    # 2) Signature verification (strict, wired to your CLI)
    if verify_sig:
        if pubkey is None:
            raise SystemExit("✖ Signature verification enabled but no --pub provided (unexpected).")
        if not pubkey.exists():
            raise SystemExit(f"✖ Public key missing: {pubkey}")
        rc = run([sys.executable, "-m", "scripts.verify_seal_signature", str(seal_path), "--pub", str(pubkey)])
        if rc != 0:
            raise SystemExit(f"✖ verify_seal_signature failed for {seal_path.name}")

    print(f"✔ OK: {seal_path.name}")


def main() -> int:
    ap = argparse.ArgumentParser(description="GUS v4: Verify repo seals (HEAD or last N).")
    ap.add_argument("--head", action="store_true", help="verify latest seal for HEAD")
    ap.add_argument("--last", type=int, default=0, help="verify last N seals (chronological)")
    ap.add_argument("--no-sig", action="store_true", help="skip signature verification")
    ap.add_argument("--pub", type=Path, default=DEFAULT_PUBKEY, help="Ed25519 public key (PEM) for signature verification")
    args = ap.parse_args()

    root = repo_root()
    seals_dir = root / "seals"
    seals = list_seals(seals_dir)
    if not seals:
        raise SystemExit(f"✖ No seals found in {seals_dir}")

    verify_sig = not args.no_sig
    pubkey = (root / args.pub) if not args.pub.is_absolute() else args.pub

    # default: verify HEAD
    if args.head or (not args.head and args.last == 0):
        hs = head_short_12()
        p = find_latest_seal_for_short_hash(seals, hs)
        if not p:
            raise SystemExit(f"✖ No seal found for HEAD short hash (12): {hs}")
        print(f"→ Verifying HEAD seal: {p}")
        verify_one(p, verify_sig=verify_sig, pubkey=pubkey)

    if args.last > 0:
        batch = seals[-args.last:]
        print(f"→ Verifying last {len(batch)} seal(s)")
        for p in batch:
            verify_one(p, verify_sig=verify_sig, pubkey=pubkey)

    print("✅ Seal verification complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
