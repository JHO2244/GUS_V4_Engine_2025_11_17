# scripts/verify_repo_seals.py
from __future__ import annotations

import sys
from pathlib import Path

# Repo-root import safety (world-facing script invariant)
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import argparse
import subprocess
from typing import Iterable

from utils.console_symbols import sym


DEFAULT_PUBKEY = Path("keys/gus_seal_signing_ed25519_pub.pem")


def run(cmd: list[str]) -> int:
    return subprocess.run(cmd, text=True).returncode


def sh(cmd: list[str]) -> str:
    return subprocess.check_output(cmd, text=True).strip()


def repo_root() -> Path:
    return Path(sh(["git", "rev-parse", "--show-toplevel"]))


def git_porcelain() -> list[str]:
    out = sh(["git", "status", "--porcelain"])
    return [ln for ln in out.splitlines() if ln.strip()]


def head_short_12() -> str:
    return sh(["git", "rev-parse", "--short=12", "HEAD"])


def list_seals(seals_dir: Path) -> list[Path]:
    if not seals_dir.exists():
        return []
    return sorted(seals_dir.glob("seal_*_*.json"))


def find_latest_seal_for_short_hash(seals: list[Path], short_hash: str) -> Path | None:
    matches = [p for p in seals if p.name.startswith(f"seal_{short_hash}_")]
    return matches[-1] if matches else None


def rev_list(limit: int, target: str) -> list[str]:
    out = sh(["git", "rev-list", f"--max-count={limit}", target])
    return [ln.strip() for ln in out.splitlines() if ln.strip()]


def find_nearest_seal(seals: list[Path], start_ref: str, search_limit: int = 50) -> tuple[str, Path] | None:
    """
    Walk back from start_ref to find the nearest commit that has a seal file.
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
    (CI mode will decide strictness; this is for sig-relaxed policy.)
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

        return False

    return True


def changed_seal_jsons_in_head() -> list[Path]:
    """
    Return seal JSON files introduced by HEAD (union vs parents).
    Only meaningful when HEAD is seal-only.
    """
    root = repo_root()
    changed: set[str] = set()

    out1 = sh(["git", "diff", "--name-only", "HEAD^1..HEAD"])
    for ln in out1.splitlines():
        p = ln.strip().replace("\\", "/")
        if p:
            changed.add(p)

    parents = sh(["git", "rev-list", "--parents", "-n", "1", "HEAD"]).split()
    if len(parents) >= 3:
        out2 = sh(["git", "diff", "--name-only", "HEAD^2..HEAD"])
        for ln in out2.splitlines():
            p = ln.strip().replace("\\", "/")
            if p:
                changed.add(p)

    seal_jsons: list[Path] = []
    for p in sorted(changed):
        if p.startswith("seals/") and p.endswith(".json"):
            seal_jsons.append(root / p)

    return seal_jsons


def head_is_seal_only_commit() -> bool:
    """
    True if HEAD changes only seals/ files (including .sig) and nothing else.
    Merge-safe: union of file changes vs each parent.
    """
    parents = sh(["git", "rev-list", "--parents", "-n", "1", "HEAD"]).split()
    if len(parents) < 2:
        return False

    changed: set[str] = set()

    out1 = sh(["git", "diff", "--name-only", "HEAD^1..HEAD"])
    for ln in out1.splitlines():
        p = ln.strip().replace("\\", "/")
        if p:
            changed.add(p)

    if len(parents) >= 3:
        out2 = sh(["git", "diff", "--name-only", "HEAD^2..HEAD"])
        for ln in out2.splitlines():
            p = ln.strip().replace("\\", "/")
            if p:
                changed.add(p)

    if not changed:
        return False

    return all(p.startswith("seals/") for p in changed)


def is_ancestor(anc: str, desc: str = "HEAD") -> bool:
    return run(["git", "merge-base", "--is-ancestor", anc, desc]) == 0


def verify_content_only(seal_path: Path, allow_dirty: bool) -> None:
    """
    Content verification of the seal (no cryptography).
    """
    if not seal_path.exists():
        raise SystemExit(f"{sym('fail')} Seal file missing: {seal_path}")

    cmd = [sys.executable, "-m", "scripts.verify_seal", str(seal_path)]
    if allow_dirty:
        cmd.append("--allow-dirty")

    rc = run(cmd)
    if rc != 0:
        raise SystemExit(f"{sym('fail')} verify_seal failed for {seal_path.name}")


def verify_signature(seal_path: Path, pubkey: Path, allow_missing_sig: bool) -> None:
    """
    Signature verification of the seal (requires cryptography dependency).
    """
    if not pubkey.exists():
        raise SystemExit(f"{sym('fail')} Public key missing: {pubkey}")

    cmd = [sys.executable, "-m", "scripts.verify_seal_signature", str(seal_path), "--pub", str(pubkey)]
    if allow_missing_sig:
        cmd.append("--allow-missing-sig")

    rc = run(cmd)
    if rc != 0:
        raise SystemExit(f"{sym('fail')} verify_seal_signature failed for {seal_path.name}")


def verify_one(
    seal_path: Path,
    verify_sig: bool,
    pubkey: Path,
    allow_dirty_to_verify_seal: bool,
    allow_missing_sig: bool,
) -> None:
    # 1) Always verify content (no-crypto)
    verify_content_only(seal_path, allow_dirty=allow_dirty_to_verify_seal)

    # 2) Verify signature only if enabled
    if verify_sig:
        verify_signature(seal_path, pubkey=pubkey, allow_missing_sig=allow_missing_sig)

    print(f"{sym('check')} OK: {seal_path.name}")


def main() -> int:
    ap = argparse.ArgumentParser(description="GUS v4: Verify repo seals (HEAD or last N).")
    ap.add_argument("--head", action="store_true", help="verify latest seal for HEAD")
    ap.add_argument("--last", type=int, default=0, help="verify last N seals (chronological)")

    # IMPORTANT: dest must be stable (no_sig)
    ap.add_argument("--no-sig", dest="no_sig", action="store_true", help="skip signature verification (content only)")
    ap.add_argument("--pub", type=Path, default=DEFAULT_PUBKEY, help="Ed25519 public key (PEM) for signature verification")

    ap.add_argument("--sha", default=None, help="Verify a specific commit SHA (or short SHA) instead of HEAD.")
    ap.add_argument("--allow-artifacts", action="store_true", help="Allow untracked artifacts/ directory (LOCAL ONLY)")
    ap.add_argument("--ci", action="store_true", help="CI mode: stricter dirt policy")

    ap.add_argument(
        "--nearest",
        action="store_true",
        help="If target has no seal, search ancestors for nearest sealed commit (default unless --require-target).",
    )
    ap.add_argument("--require-target", action="store_true", help="Require that the target itself has a seal (no fallback).")
    ap.add_argument(
        "--require-head",
        action="store_true",
        help="Strict HEAD mode: require exact HEAD seal; seal-only HEAD is verified via introduced seal(s).",
    )

    pol = ap.add_mutually_exclusive_group()
    pol.add_argument("--sig-strict", action="store_true", help="require signature; refuse dirty tree (default when sig enabled)")
    pol.add_argument("--sig-relaxed", action="store_true", help="require signature; allow ONLY untracked seals/*.sig dirt")

    args = ap.parse_args()

    # Alias: strict HEAD => require_target on HEAD
    if args.require_head:
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

    # Dirt policy
    allow_dirty_to_verify_seal = False
    allow_missing_sig = False

    if verify_sig:
        sig_strict = args.sig_strict or (not args.sig_strict and not args.sig_relaxed)
        if sig_strict:
            if porcelain:
                raise SystemExit(f"{sym('fail')} sig-strict refused: working tree is dirty")
        else:
            if not only_untracked_sig_dirt(porcelain):
                msg = [f"{sym('fail')} sig-relaxed refused: working tree has unauthorized changes"]
                msg.extend(porcelain)
                raise SystemExit("\n".join(msg))
            allow_dirty_to_verify_seal = True
            allow_missing_sig = True
    else:
        # no-sig mode: still require clean tree (GDVS default)
        # (relaxation can be added later via explicit flag if ever needed)
        if porcelain:
            raise SystemExit(f"{sym('fail')} no-sig refused: working tree is dirty")

    # Target selection: HEAD default if nothing else specified
    if args.head or (not args.head and args.last == 0):
        who = "SHA" if args.sha else "HEAD"
        target = args.sha if args.sha else "HEAD"

        hs = sh(["git", "rev-parse", "--short=12", f"{target}^{{}}"])
        seal_path = find_latest_seal_for_short_hash(seals, hs)

        nearest_mode = args.nearest or (not args.require_target)

        if (seal_path is None) and nearest_mode:
            found = find_nearest_seal(seals, target, search_limit=50)
            if not found:
                raise SystemExit(f"{sym('fail')} No seal found for {who} (searched {target} and ancestors)")
            nearest_hs, seal_path = found
            print(f"{sym('arrow')} NOTE: {who} {hs} has no seal; using nearest sealed ancestor {nearest_hs}")

        # Strict target required and still no seal => handle seal-only HEAD exception
        if (seal_path is None) and (not args.sha) and args.require_target and head_is_seal_only_commit():
            candidates = changed_seal_jsons_in_head()
            if not candidates:
                raise SystemExit(f"{sym('fail')} No seal json introduced by seal-only HEAD")

            # Pick newest by filename ordering (timestamp embedded)
            candidates = sorted(candidates)

            picked: Path | None = None
            for c in reversed(candidates):
                parts = c.name.split("_")
                if len(parts) < 3:
                    continue
                short12 = parts[1]
                if is_ancestor(short12, "HEAD"):
                    picked = c
                    break

            if not picked:
                raise SystemExit(f"{sym('fail')} Seal-only HEAD introduced seals, but none target an ancestor commit.")

            print(f"{sym('arrow')} NOTE: HEAD is seal-only; verifying introduced seal {picked.name}")
            print(f"{sym('arrow')} Verifying HEAD seal: {picked}")
            verify_one(
                picked,
                verify_sig=verify_sig,
                pubkey=pubkey,
                allow_dirty_to_verify_seal=allow_dirty_to_verify_seal,
                allow_missing_sig=allow_missing_sig,
            )
            print(f"{sym('check')} Seal verification complete.")
            return 0

        # If strict required and still no seal => fail
        if (seal_path is None) and args.require_target:
            raise SystemExit(f"{sym('fail')} {who} {hs} has no seal (strict mode)")

        if seal_path is None:
            raise SystemExit(f"{sym('fail')} No seal found for {who} {hs}")

        verify_one(
            seal_path,
            verify_sig=verify_sig,
            pubkey=pubkey,
            allow_dirty_to_verify_seal=allow_dirty_to_verify_seal,
            allow_missing_sig=allow_missing_sig,
        )
        print(f"{sym('check')} Seal verification complete.")
        return 0

    if args.last > 0:
        batch = seals[-args.last:]
        print(f"{sym('arrow')} Verifying last {len(batch)} seal(s)")
        for p in batch:
            verify_one(
                p,
                verify_sig=verify_sig,
                pubkey=pubkey,
                allow_dirty_to_verify_seal=allow_dirty_to_verify_seal,
                allow_missing_sig=allow_missing_sig,
            )
        print(f"{sym('check')} Seal verification complete.")
        return 0

    print(f"{sym('check')} Seal verification complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
