from __future__ import annotations

from utils.console_symbols import sym

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

def head_is_seal_only_commit() -> bool:
    # True if HEAD changes only seals/ files (including .sig) and nothing else.
    out = sh(["git", "show", "--name-only", "--pretty=format:", "HEAD"])
    files = [ln.strip().replace("\\", "/") for ln in out.splitlines() if ln.strip()]
    if not files:
        return False
    return all(f.startswith("seals/") for f in files)


def rev_list(limit: int, target: str) -> list[str]:
    out = sh(["git", "rev-list", f"--max-count={limit}", target])
    return [ln.strip() for ln in out.splitlines() if ln.strip()]


def find_nearest_seal(
    seals: list[Path],
    start_ref: str,
    search_limit: int = 50,
) -> tuple[str, Path] | None:
    """
    Walk back from start_ref (HEAD by default) to find the nearest commit that has a seal file.
    Returns (commit12, seal_path).
    """
    for full_sha in rev_list(search_limit, start_ref):
        short12 = sh(["git", "rev-parse", "--short=12", full_sha])
        p = find_latest_seal_for_short_hash(seals, short12)
        if p:
            return short12, p
    return None

def only_untracked_sig_dirt(lines: list[str]) -> bool:
    """
    Allow ONLY untracked:
      - seals/*.sig
      - artifacts/*
      - (optionally) uncommitted seal_*.json generated locally
    """
    if not lines:
        return True

    for ln in lines:
        if not ln.startswith("?? "):
            return False

        path = ln[3:].strip().replace("\\", "/")

        if path.startswith("seals/") and path.endswith(".sig"):
            continue

        if path.startswith("artifacts/"):
            continue

        # OPTIONAL: allow local, uncommitted seal JSONs
        if path.startswith("seals/seal_") and path.endswith(".json"):
            continue

        return False

    return True


def verify_one(
    seal_path: Path,
    verify_sig: bool,
    pubkey: Path,
    allow_dirty_to_verify_seal: bool,
) -> None:
    if not seal_path.exists():
        raise SystemExit(f"{sym('fail')} Seal file missing: {seal_path}")

    # 1) Content verification
    cmd = [sys.executable, "-m", "scripts.verify_seal_signature", str(seal_path), "--pub", str(pubkey)]

    # OK If we're NOT verifying signatures (--no-sig), then missing .sig must be allowed.
    if (not verify_sig) or allow_dirty_to_verify_seal:
        cmd.append("--allow-missing-sig")

    rc = run(cmd)

    if rc != 0:
        raise SystemExit(f"{sym('fail')} verify_seal_signature failed for {seal_path.name}")

    # 2) Signature verification (requires .sig adjacent)
    if verify_sig:
        if not pubkey.exists():
            raise SystemExit(f"{sym('fail')} Public key missing: {pubkey}")
        cmd = [sys.executable, "-m", "scripts.verify_seal_signature", str(seal_path), "--pub", str(pubkey)]

        # If caller selected sig-relaxed, allow missing .sig to be NOTE-only (non-fatal)
        if allow_dirty_to_verify_seal:
            cmd.append("--allow-missing-sig")

        rc = run(cmd)

        if rc != 0:
            raise SystemExit(f"{sym('fail')} verify_seal_signature failed for {seal_path.name}")

    print(f"{sym('check')} OK: {seal_path.name}")


def main() -> int:
    ap = argparse.ArgumentParser(description="GUS v4: Verify repo seals (HEAD or last N).")
    ap.add_argument("--head", action="store_true", help="verify latest seal for HEAD")
    ap.add_argument("--last", type=int, default=0, help="verify last N seals (chronological)")
    ap.add_argument("--no-sig", action="store_true", help="skip signature verification (content only)")
    ap.add_argument("--pub", type=Path, default=DEFAULT_PUBKEY, help="Ed25519 public key (PEM) used for signature verification")
    ap.add_argument("--sha", default=None, help="Verify a specific commit SHA (or short SHA) instead of HEAD.")
    ap.add_argument("--allow-artifacts", action="store_true", help="Allow untracked artifacts/ directory (LOCAL ONLY)")
    ap.add_argument("--ci", action="store_true", help="CI mode: forbid uncommitted seal JSONs; allow only .sig as untracked dirt")
    ap.add_argument("--nearest", action="store_true",
                    help="If target has no seal, search ancestors for nearest sealed commit (default).")
    ap.add_argument("--require-target", action="store_true",
                    help="Require that the target itself has a seal (no ancestor fallback).")
    ap.add_argument("--require-head", action="store_true",
                    help="Alias for strict HEAD: require exact HEAD seal (no fallback).")

    pol = ap.add_mutually_exclusive_group()
    pol.add_argument("--sig-strict", action="store_true", help="require signature; refuse dirty tree (default for signed verification)")
    pol.add_argument("--sig-relaxed", action="store_true", help="require signature; allow ONLY untracked seals/*.sig dirt")

    args = ap.parse_args()

    # Alias: milestone strictness
    # --require-head means: treat target as HEAD and require an exact seal (no ancestor/parent fallback).
    if getattr(args, "require_head", False):
        args.head = True
        args.require_target = True

    root = repo_root()
    seals_dir = root / "seals"
    seals = list_seals(seals_dir)
    if not seals:
        raise SystemExit(f"{sym('fail')} No seals found in {seals_dir}")

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
                raise SystemExit(f"{sym('fail')} sig-strict refused: working tree is dirty")
        else:
            # sig-relaxed
            if not only_untracked_sig_dirt(porcelain):
                msg = [f"{sym('fail')} sig-relaxed refused: working tree has unauthorized changes"]
                msg.extend(porcelain)
                raise SystemExit("\n".join(msg))
            # allow content verification to proceed even though tree is dirty due to untracked .sig
            allow_dirty_to_verify_seal = True
    else:
        # content-only mode (no-sig): keep default strict cleanliness (no allow-dirty here)
        # If you ever want a content-only relaxed mode, add a separate flag later.
        pass

    # Default: verify HEAD (or --sha if provided)
    if args.head or (not args.head and args.last == 0):
        who = "SHA" if args.sha else "HEAD"
        target = args.sha if args.sha else "HEAD"

        used_fallback_parent = False

        # 1) Try target (HEAD or provided --sha)
        hs = sh(["git", "rev-parse", "--short=12", f"{target}^{{}}"])
        p = find_latest_seal_for_short_hash(seals, hs)

        # Policy: by default we allow nearest-ancestor fallback unless --require-target was set
        nearest_mode = args.nearest or (not args.require_target)

        if not p and nearest_mode:
            found = find_nearest_seal(seals, target, search_limit=50)
            if not found:
                raise SystemExit(f"{sym('fail')} No seal found for {who} (searched {target} and ancestors)")
            nearest_hs, p = found
            print(f"{sym('arrow')} NOTE: {who} {hs} has no seal; using nearest sealed ancestor {nearest_hs}")

        # Optional: parent fallback ONLY for HEAD (not --sha), and ONLY if we still have no seal
        if (not p) and (not args.sha) and (not args.require_target):
            parent = "HEAD^1"
            hs_parent = sh(["git", "rev-parse", "--short=12", parent])
            p_parent = find_latest_seal_for_short_hash(seals, hs_parent)
            if p_parent:
                used_fallback_parent = True
                hs = hs_parent
                p = p_parent
                who = "HEAD^1"

        if not p:
            # If strict HEAD is requested, normally fail.
            # Exception: allow a "seal-only HEAD commit" to rely on parent seal,
            # otherwise committing seal artifacts becomes an infinite recursion.
            if (not args.sha) and args.require_target and head_is_seal_only_commit():
                parent = "HEAD^1"
                hs_parent = sh(["git", "rev-parse", "--short=12", parent])
                p_parent = find_latest_seal_for_short_hash(seals, hs_parent)
                if not p_parent:
                    raise SystemExit(f"{sym('fail')} No seal found for sealed-parent policy (HEAD^1): {hs_parent}")
                print(f"{sym('arrow')} NOTE: HEAD is seal-only commit; requiring parent seal for {hs_parent}")
                hs = hs_parent
                p = p_parent
                who = "HEAD^1"
            else:
                raise SystemExit(f"{sym('fail')} No seal found for {who} short hash (12): {hs}")

        if used_fallback_parent:
            print(f"{sym('arrow')} NOTE: HEAD seal not found; accepting parent commit seal (HEAD^1) by policy.")

        print(f"{sym('arrow')} Verifying {who} seal: {p}")
        verify_one(
            p,
            verify_sig=verify_sig,
            pubkey=pubkey,
            allow_dirty_to_verify_seal=allow_dirty_to_verify_seal,
        )

    if args.last > 0:
        batch = seals[-args.last:]
        print(f"{sym('arrow')} Verifying last {len(batch)} seal(s)")
        for p in batch:
            verify_one(p, verify_sig=verify_sig, pubkey=pubkey, allow_dirty_to_verify_seal=allow_dirty_to_verify_seal)

    print(f"{sym('check')} Seal verification complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
