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


def list_seals(seals_dir: Path) -> list[Path]:
    if not seals_dir.exists():
        return []
    return sorted(seals_dir.glob("seal_*_*.json"))


def find_latest_seal_for_short_hash(seals: list[Path], short_hash: str) -> Path | None:
    matches = [p for p in seals if p.name.startswith(f"seal_{short_hash}_")]
    return matches[-1] if matches else None


def git_porcelain() -> list[str]:
    out = sh(["git", "status", "--porcelain"])
    return [ln for ln in out.splitlines() if ln.strip()]


def only_untracked_sig_dirt(lines: list[str]) -> bool:
    """
    Allow ONLY: ?? seals/<anything>.sig
    Disallow: any staged, modified, deleted, renamed, or untracked elsewhere.
    """
    if not lines:
        return True  # clean
    for ln in lines:
        # untracked files begin with "?? "
        if not ln.startswith("?? "):
            return False
        path = ln[3:].strip().replace("\\", "/")
        if not (path.startswith("seals/") and path.endswith(".sig")):
            return False
    return True


def verify_one(
    seal_path: Path,
    verify_sig: bool,
    pubkey: Path,
    allow_dirty_to_verify_seal: bool,
) -> None:
    if not seal_path.exists():
        raise SystemExit(f"✖ Seal file missing: {seal_path}")

    # 1) Content verification
    cmd = [sys.executable, "-m", "scripts.verify_seal_signature", str(seal_path), "--pub", str(pubkey)]

    # If we're in sig-relaxed mode, allow missing .sig to be NOTE (not ERROR)
    if allow_dirty_to_verify_seal:
        cmd.append("--allow-missing-sig")

    rc = run(cmd)

    if rc != 0:
        raise SystemExit(f"✖ verify_seal_signature failed for {seal_path.name}")

    # 2) Signature verification (requires .sig adjacent)
    if verify_sig:
        if not pubkey.exists():
            raise SystemExit(f"✖ Public key missing: {pubkey}")
        cmd = [sys.executable, "-m", "scripts.verify_seal_signature", str(seal_path), "--pub", str(pubkey)]

        # If caller selected sig-relaxed, allow missing .sig to be NOTE-only (non-fatal)
        if allow_dirty_to_verify_seal:
            cmd.append("--allow-missing-sig")

        rc = run(cmd)

        if rc != 0:
            raise SystemExit(f"✖ verify_seal_signature failed for {seal_path.name}")

    print(f"✔ OK: {seal_path.name}")


def main() -> int:
    ap = argparse.ArgumentParser(description="GUS v4: Verify repo seals (HEAD or last N).")
    ap.add_argument("--head", action="store_true", help="verify latest seal for HEAD")
    ap.add_argument("--last", type=int, default=0, help="verify last N seals (chronological)")
    ap.add_argument("--no-sig", action="store_true", help="skip signature verification (content only)")
    ap.add_argument("--pub", type=Path, default=DEFAULT_PUBKEY, help="Ed25519 public key (PEM) used for signature verification")

    pol = ap.add_mutually_exclusive_group()
    pol.add_argument("--sig-strict", action="store_true", help="require signature; refuse dirty tree (default for signed verification)")
    pol.add_argument("--sig-relaxed", action="store_true", help="require signature; allow ONLY untracked seals/*.sig dirt")

    args = ap.parse_args()

    root = repo_root()
    seals_dir = root / "seals"
    seals = list_seals(seals_dir)
    if not seals:
        raise SystemExit(f"✖ No seals found in {seals_dir}")

    porcelain = git_porcelain()

    verify_sig = not args.no_sig
    pubkey = (root / args.pub) if not args.pub.is_absolute() else args.pub

    # Policy resolution
    allow_dirty_to_verify_seal = False

    if verify_sig:
        # default: strict if neither specified
        sig_strict = args.sig_strict or (not args.sig_strict and not args.sig_relaxed)
        if sig_strict:
            if porcelain:
                raise SystemExit("✖ sig-strict refused: working tree is dirty")
        else:
            # sig-relaxed
            if not only_untracked_sig_dirt(porcelain):
                msg = ["✖ sig-relaxed refused: working tree has changes beyond untracked seals/*.sig"]
                msg.extend(porcelain)
                raise SystemExit("\n".join(msg))
            # allow content verification to proceed even though tree is dirty due to untracked .sig
            allow_dirty_to_verify_seal = True
    else:
        # content-only mode (no-sig): keep default strict cleanliness (no allow-dirty here)
        # If you ever want a content-only relaxed mode, add a separate flag later.
        pass

    # Default: verify HEAD
    if args.head or (not args.head and args.last == 0):
        hs = head_short_12()
        p = find_latest_seal_for_short_hash(seals, hs)
        if not p:
            raise SystemExit(f"✖ No seal found for HEAD short hash (12): {hs}")
        print(f"→ Verifying HEAD seal: {p}")
        verify_one(p, verify_sig=verify_sig, pubkey=pubkey, allow_dirty_to_verify_seal=allow_dirty_to_verify_seal)

    if args.last > 0:
        batch = seals[-args.last:]
        print(f"→ Verifying last {len(batch)} seal(s)")
        for p in batch:
            verify_one(p, verify_sig=verify_sig, pubkey=pubkey, allow_dirty_to_verify_seal=allow_dirty_to_verify_seal)

    print("✅ Seal verification complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
