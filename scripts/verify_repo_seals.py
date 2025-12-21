from __future__ import annotations

import argparse
import subprocess
from pathlib import Path
import sys

DEFAULT_PUBKEY = Path("keys/gus_seal_signing_ed25519_pub.pem")


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


def git_porcelain() -> list[str]:
    # Status format: XY <path> (or "?? <path>" for untracked)
    out = sh(["git", "status", "--porcelain"])
    return [line.rstrip("\n") for line in out.splitlines() if line.strip()]


def assert_relaxed_dirty_is_only_untracked_sig(repo: Path) -> None:
    """
    Relaxed mode allows 'dirty' only if it is strictly:
      - untracked files (??) AND
      - path matches seals/*.sig
    Anything else: hard fail.
    """
    lines = git_porcelain()
    if not lines:
        return

    bad: list[str] = []
    for line in lines:
        # Untracked: "?? path"
        if not line.startswith("?? "):
            bad.append(line)
            continue
        path = line[3:].strip()
        p = (repo / path).resolve()
        # Must be seals/*.sig
        if "/seals/" not in p.as_posix() and "\\seals\\" not in str(p):
            bad.append(line)
            continue
        if not path.replace("\\", "/").startswith("seals/") or not path.endswith(".sig"):
            bad.append(line)
            continue

    if bad:
        msg = "\n".join(bad)
        raise SystemExit(
            "✖ sig-relaxed refused: working tree has changes beyond untracked seals/*.sig\n"
            f"{msg}"
        )


def verify_one(seal_path: Path, verify_sig: bool, pubkey: Path, allow_dirty_to_verify_seal: bool) -> None:
    if not seal_path.exists():
        raise SystemExit(f"✖ Seal file missing: {seal_path}")

    # 1) Content verification
    cmd = [sys.executable, "-m", "scripts.verify_seal", str(seal_path)]
    if allow_dirty_to_verify_seal:
        cmd.append("--allow-dirty")

    rc = run(cmd)
    if rc != 0:
        raise SystemExit(f"✖ verify_seal failed for {seal_path.name}")

    # 2) Signature verification
    if verify_sig:
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
    ap.add_argument("--no-sig", action="store_true", help="skip signature verification (content only)")
    ap.add_argument("--pub", type=Path, default=DEFAULT_PUBKEY, help="Ed25519 public key (PEM) used for signature verification")

    sig_mode = ap.add_mutually_exclusive_group()
    sig_mode.add_argument("--sig-strict", action="store_true", help="require signature; refuse dirty tree (default behavior)")
    sig_mode.add_argument("--sig-relaxed", action="store_true", help="require signature; allow ONLY untracked seals/*.sig dirt")

    args = ap.parse_args()

    root = repo_root()
    seals_dir = root / "seals"
    seals = list_seals(seals_dir)
    if not seals:
        raise SystemExit(f"✖ No seals found in {seals_dir}")

    # Determine signature behavior
    if args.no_sig:
        verify_sig = False
    else:
        verify_sig = True

    # If user didn't specify sig mode explicitly:
    # - if verify_sig == True, default to strict (safer)
    # - if verify_sig == False, doesn't matter
    sig_strict = args.sig_strict or (verify_sig and not args.sig_relaxed)
    sig_relaxed = args.sig_relaxed

    pubkey = (root / args.pub) if not args.pub.is_absolute() else args.pub

    # In sig-relaxed: enforce that dirt is ONLY untracked seals/*.sig
    # and pass --allow-dirty to verify_seal so the content check can proceed.
    allow_dirty_to_verify_seal = False
    if sig_relaxed:
        assert_relaxed_dirty_is_only_untracked_sig(root)
        allow_dirty_to_verify_seal = True

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
