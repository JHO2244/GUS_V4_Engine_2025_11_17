# scripts/verify_repo_seals.py
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

DEFAULT_PUBKEY = Path("keys/gus_seal_signing_ed25519_pub.pem")


def run(cmd: list[str]) -> int:
    return subprocess.run(cmd, text=True).returncode


def sh(cmd: list[str]) -> str:
    return subprocess.check_output(cmd, text=True).strip()


def repo_root() -> Path:
    return Path(sh(["git", "rev-parse", "--show-toplevel"]))


def head_short_12() -> str:
    return sh(["git", "rev-parse", "--short=12", "HEAD"])


def seals_dir(root: Path) -> Path:
    return root / "seals"


def list_seals(sd: Path) -> list[Path]:
    if not sd.exists():
        return []
    return sorted(sd.glob("seal_*_*.json"))


def latest_seal_for_short_hash(seals: list[Path], short_hash: str) -> Path | None:
    matches = [p for p in seals if p.name.startswith(f"seal_{short_hash}_")]
    return matches[-1] if matches else None


def porcelain() -> list[str]:
    out = sh(["git", "status", "--porcelain"])
    return [ln for ln in out.splitlines() if ln.strip()]


def sig_relaxed_ok(lines: list[str]) -> bool:
    """
    Only allow untracked seals/*.sig. Anything else = fail.
    Accepts: '?? seals/<name>.sig'
    """
    for ln in lines:
        # Example: "?? seals/seal_xxx.json.sig"
        if not (ln.startswith("?? ") and ln[3:].startswith("seals/") and ln.endswith(".sig")):
            return False
    return True


def enforce_sig_policy(sig_policy: str) -> None:
    lines = porcelain()
    if not lines:
        return

    if sig_policy == "strict":
        raise SystemExit("✖ sig-strict refused: working tree is dirty\n" + "\n".join(lines))

    # relaxed
    if not sig_relaxed_ok(lines):
        raise SystemExit("✖ sig-relaxed refused: working tree has changes beyond untracked seals/*.sig\n" + "\n".join(lines))


def verify_one(seal: Path, verify_sig: bool, pubkey: Path, allow_dirty_to_verify_seal: bool) -> None:
    if not seal.exists():
        raise SystemExit(f"✖ Seal missing: {seal}")

    cmd = [sys.executable, "-m", "scripts.verify_seal", str(seal)]
    if allow_dirty_to_verify_seal:
        cmd.append("--allow-dirty")

    rc = run(cmd)
    if rc != 0:
        raise SystemExit(f"✖ verify_seal failed for {seal.name}")

    if verify_sig:
        sig_path = seal.with_suffix(seal.suffix + ".sig")
        if not sig_path.exists():
            raise SystemExit("ERROR: signature file missing")

        rc = run([sys.executable, "-m", "scripts.verify_seal_signature", str(seal), "--pub", str(pubkey)])
        if rc != 0:
            raise SystemExit(f"✖ verify_seal_signature failed for {seal.name}")

    print(f"✔ OK: {seal.name}")


def main() -> int:
    ap = argparse.ArgumentParser(description="GUS v4: Verify repo seals (HEAD or last N).")
    ap.add_argument("--head", action="store_true", help="verify latest seal for HEAD")
    ap.add_argument("--last", type=int, default=0, help="verify last N seals (chronological)")
    ap.add_argument("--no-sig", action="store_true", help="skip signature verification (content only)")
    ap.add_argument("--pub", type=Path, default=DEFAULT_PUBKEY, help="Ed25519 public key (PEM) for signature verification")

    g = ap.add_mutually_exclusive_group()
    g.add_argument("--sig-strict", action="store_true", help="require signature; refuse ANY dirty tree")
    g.add_argument("--sig-relaxed", action="store_true", help="require signature; allow ONLY untracked seals/*.sig dirt")

    ap.add_argument("--allow-dirty-to-verify-seal", action="store_true", help="pass --allow-dirty to scripts.verify_seal")
    args = ap.parse_args()

    root = repo_root()
    sd = seals_dir(root)
    seals = list_seals(sd)
    if not seals:
        raise SystemExit(f"✖ No seals found in {sd}")

    pubkey = args.pub if args.pub.is_absolute() else (root / args.pub)

    # Determine whether we are verifying signatures
    if args.no_sig:
        verify_sig = False
        sig_policy = "none"
    else:
        verify_sig = True
        sig_policy = "strict" if args.sig_strict else ("relaxed" if args.sig_relaxed else "strict")

    # If signatures are required, enforce policy BEFORE verification
    if verify_sig:
        enforce_sig_policy(sig_policy)

    # Default: HEAD
    if args.head or args.last == 0:
        hs = head_short_12()
        seal = latest_seal_for_short_hash(seals, hs)
        if not seal:
            raise SystemExit(f"✖ No seal found for HEAD short hash (12): {hs}")
        print(f"→ Verifying HEAD seal: {seal}")
        verify_one(seal, verify_sig=verify_sig, pubkey=pubkey, allow_dirty_to_verify_seal=args.allow_dirty_to_verify_seal)

    if args.last > 0:
        batch = seals[-args.last :]
        print(f"→ Verifying last {len(batch)} seal(s)")
        for s in batch:
            verify_one(s, verify_sig=verify_sig, pubkey=pubkey, allow_dirty_to_verify_seal=args.allow_dirty_to_verify_seal)

    print("✅ Seal verification complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
