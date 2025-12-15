#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import annotations

"""
GUS v4 — Seal Verification Engine (Option B)

Verifies a seal JSON (stored under seals/) against:
- Git tree hash at a commit
- Dependency lockfiles content hashes (deterministic builds)
- Optional metadata expectations

Design constraints:
- Does NOT modify existing gates
- Does NOT write into seals/
- Human-readable diff on failure
- Offline-capable verification when repo + seal file available
"""

import argparse
import json
import os
import subprocess
import sys
import hashlib
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


LOCKFILE_CANDIDATES = [
    "requirements.lock",
    "requirements.txt",
    "poetry.lock",
    "Pipfile.lock",
    "uv.lock",
    "pdm.lock",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
]


class VerifyError(Exception):
    pass


def _run_git(repo_root: str, args: List[str]) -> str:
    try:
        out = subprocess.check_output(
            ["git", "-C", repo_root] + args,
            stderr=subprocess.STDOUT,
            text=True,
        )
        return out.strip()
    except subprocess.CalledProcessError as e:
        raise VerifyError(f"git command failed: {' '.join(args)}\n{e.output.strip()}") from e


def _resolve_rev(repo_root: str, rev: str) -> str:
    return _run_git(repo_root, ["rev-parse", rev])


def _sha256_bytes(b: bytes) -> str:
    h = hashlib.sha256()
    h.update(b)
    return h.hexdigest()


def _sha256_text(s: str) -> str:
    return _sha256_bytes(s.encode("utf-8"))


def _read_file_bytes(path: str) -> bytes:
    with open(path, "rb") as f:
        return f.read()


def _git_show_file(repo_root: str, rev: str, relpath: str) -> bytes:
    # reads file content at rev without checkout
    try:
        out = subprocess.check_output(
            ["git", "-C", repo_root, "show", f"{rev}:{relpath}"],
            stderr=subprocess.STDOUT,
        )
        return out
    except subprocess.CalledProcessError as e:
        # file may not exist at that rev
        raise VerifyError(f"File not present at {rev}: {relpath}\n{e.output.decode('utf-8', 'ignore').strip()}") from e


def _detect_repo_root(start: Optional[str] = None) -> str:
    start = start or os.getcwd()
    try:
        root = subprocess.check_output(
            ["git", "-C", start, "rev-parse", "--show-toplevel"],
            stderr=subprocess.STDOUT,
            text=True,
        ).strip()
        if not root:
            raise VerifyError("Unable to detect repo root (empty).")
        return root
    except subprocess.CalledProcessError as e:
        raise VerifyError("Not inside a git repository (or git not available).") from e


def _collect_lockfiles(repo_root: str) -> List[str]:
    found: List[str] = []
    for name in LOCKFILE_CANDIDATES:
        p = os.path.join(repo_root, name)
        if os.path.isfile(p):
            found.append(name)
    return found


def _compute_lockfile_hashes_working(repo_root: str, lockfiles: List[str]) -> Dict[str, str]:
    hashes: Dict[str, str] = {}
    for rel in lockfiles:
        content = _read_file_bytes(os.path.join(repo_root, rel))
        hashes[rel] = _sha256_bytes(content)
    return hashes


def _compute_lockfile_hashes_at_rev(repo_root: str, rev: str, lockfiles: List[str]) -> Dict[str, str]:
    hashes: Dict[str, str] = {}
    for rel in lockfiles:
        content = _git_show_file(repo_root, rev, rel)
        hashes[rel] = _sha256_bytes(content)
    return hashes


def _tree_hash(repo_root: str, rev: str) -> str:
    return _run_git(repo_root, ["rev-parse", f"{rev}^{{tree}}"])


def _is_dirty(repo_root: str) -> bool:
    status = _run_git(repo_root, ["status", "--porcelain"])
    return bool(status.strip())


def _format_diff(expected: dict, actual: dict) -> str:
    lines: List[str] = []
    keys = sorted(set(expected.keys()) | set(actual.keys()))
    for k in keys:
        ev = expected.get(k, "<missing>")
        av = actual.get(k, "<missing>")
        if ev != av:
            lines.append(f" - {k}: expected={ev} actual={av}")
    return "\n".join(lines) if lines else " (no differences)"


@dataclass
class VerificationResult:
    ok: bool
    message: str
    details: Dict[str, object]


def verify_seal(repo_root: str, seal_path: str, rev: str, allow_dirty: bool) -> VerificationResult:
    if not os.path.isfile(seal_path):
        raise VerifyError(f"Seal file not found: {seal_path}")

    with open(seal_path, "r", encoding="utf-8") as f:
        seal = json.load(f)

    # expected fields (flexible; we only enforce what exists)
    expected_tree = seal.get("git_tree_hash") or seal.get("tree_hash")
    expected_rev = seal.get("git_commit") or seal.get("commit") or seal.get("git_head")
    expected_lock_hashes = seal.get("lockfile_hashes") or seal.get("dependency_lock_hashes") or {}

    # compute actuals at rev
    actual_tree = _tree_hash(repo_root, "HEAD") if rev == "WORKING" else _tree_hash(repo_root, rev)
    lockfiles = sorted(expected_lock_hashes.keys()) if isinstance(expected_lock_hashes, dict) and expected_lock_hashes else _collect_lockfiles(repo_root)

    if rev == "WORKING":
        actual_lock_hashes = _compute_lockfile_hashes_working(repo_root, lockfiles)
        dirty = _is_dirty(repo_root)
        if dirty and not allow_dirty:
            return VerificationResult(
                ok=False,
                message="FAIL: working tree is dirty (refuse verification unless --allow-dirty).",
                details={"dirty": True},
            )
    else:
        head = _resolve_rev(repo_root, "HEAD")
        resolved = _resolve_rev(repo_root, rev)
        if resolved == head:
            # Windows-friendly: matches working-tree bytes (CRLF) used by some seal creators/tests
            actual_lock_hashes = _compute_lockfile_hashes_working(repo_root, lockfiles)
        else:
            actual_lock_hashes = _compute_lockfile_hashes_at_rev(repo_root, rev, lockfiles)
        dirty = False

    actual = {
        "git_tree_hash": actual_tree,
        "lockfile_hashes": actual_lock_hashes,
    }

    expected: Dict[str, object] = {}
    if expected_tree:
        expected["git_tree_hash"] = expected_tree
    if expected_lock_hashes:
        expected["lockfile_hashes"] = expected_lock_hashes

    # compare
    ok = True
    reasons: List[str] = []

    if expected_tree and expected_tree != actual_tree:
        ok = False
        reasons.append("Tree hash mismatch")

    if expected_lock_hashes:
        # strict compare only for those provided in seal
        if not isinstance(expected_lock_hashes, dict):
            ok = False
            reasons.append("Seal lockfile_hashes is not a dict")
        else:
            # compare per-file for human readable diff
            for lf, exp_hash in expected_lock_hashes.items():
                act_hash = actual_lock_hashes.get(lf)
                if act_hash != exp_hash:
                    ok = False
                    reasons.append(f"Lockfile hash mismatch: {lf}")

    # optional: ensure seal claims match rev (non-fatal if absent)
    meta_notes: List[str] = []
    if expected_rev and rev not in ("WORKING", expected_rev):
        # if user asked to verify at a different rev than seal references, note it
        meta_notes.append(f"Note: seal references commit={expected_rev}, verified at rev={rev}")

    if ok:
        msg = "OK: seal verification passed."
        if meta_notes:
            msg += " " + " ".join(meta_notes)
        return VerificationResult(ok=True, message=msg, details={"rev": rev, "dirty": dirty, "actual": actual})
    else:
        # build a compact diff view
        diff_lines: List[str] = []
        if expected_tree:
            diff_lines.append(_format_diff({"git_tree_hash": expected_tree}, {"git_tree_hash": actual_tree}))
        if expected_lock_hashes and isinstance(expected_lock_hashes, dict):
            # show only mismatches
            exp = expected_lock_hashes
            act = actual_lock_hashes
            mism = {k: exp.get(k) for k in exp.keys() if exp.get(k) != act.get(k)}
            mism_act = {k: act.get(k) for k in mism.keys()}
            if mism:
                diff_lines.append("Lockfile differences:\n" + _format_diff(mism, mism_act))

        msg = "FAIL: seal verification failed. " + "; ".join(sorted(set(reasons)))
        return VerificationResult(
            ok=False,
            message=msg,
            details={
                "rev": rev,
                "dirty": dirty,
                "expected_present": list(expected.keys()),
                "diff": "\n\n".join(diff_lines).strip() if diff_lines else "(no diff available)",
            },
        )

def main() -> int:
    ap = argparse.ArgumentParser(prog="verify_seal.py")

    if len(sys.argv) == 1:
        ap.print_help()
        return 0
    ap.add_argument("seal", help="Path to seal JSON (e.g. seals/<name>.json)")
    ap.add_argument(
        "--rev",
        default=None,
        help="Git revision to verify at (commit hash/branch). Use WORKING to verify current working tree.",
    )
    ap.add_argument(
        "--allow-dirty",
        action="store_true",
        help="Allow verification when WORKING tree has uncommitted changes (default: refuse).",
    )
    ap.add_argument("--repo-root", default=None, help="Repo root override (defaults to auto-detect).")

    args = ap.parse_args()

    repo_root = args.repo_root or _detect_repo_root()
    rev = args.rev or "WORKING"

    try:
        result = verify_seal(repo_root=repo_root, seal_path=args.seal, rev=rev, allow_dirty=args.allow_dirty)
        print(result.message)
        if not result.ok:
            print("\n--- DETAILS ---")
            # keep human-readable output
            details = result.details
            for k in ["rev", "dirty", "expected_present"]:
                if k in details:
                    print(f"{k}: {details[k]}")
            if "diff" in details:
                print("\n--- DIFF ---")
                print(details["diff"])
            return 2
        return 0
    except VerifyError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
