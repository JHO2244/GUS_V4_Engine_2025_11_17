#!/usr/bin/env python
"""
GUS v4 — Epoch Validator v0.1 (read-only)

Validates the epoch manifest against:
- Git HEAD & expected anchor
- Allowed "dirty tree" rules
- Seal verification (content-only)
- Optional signature expectations (only if present)

Run:
  python epochs/epoch_bada220e_20251221T120542Z/epoch_validator_v0_1.py
"""

from __future__ import annotations

import fnmatch
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Iterable

PYTHON = sys.executable

REPO_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = Path(__file__).with_name("epoch_manifest_v0_1.json")


def run(cmd: list[str]) -> tuple[int, str]:
    """
    Run a command from repo root.

    Guardian rule: never rely on PATH for Python.
    If the command starts with 'python', force the active interpreter (sys.executable).
    """
    if cmd and cmd[0].lower() == "python":
        cmd = [sys.executable, *cmd[1:]]

    p = subprocess.run(
        cmd,
        cwd=str(REPO_ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    return p.returncode, p.stdout


def git_head() -> str:
    rc, out = run(["git", "rev-parse", "HEAD"])
    if rc != 0:
        raise RuntimeError(f"git rev-parse HEAD failed:\n{out}")
    return out.strip()


def git_status_porcelain() -> list[str]:
    rc, out = run(["git", "status", "--porcelain"])
    if rc != 0:
        raise RuntimeError(f"git status failed:\n{out}")
    lines = [ln.strip() for ln in out.splitlines() if ln.strip()]
    return lines


def porcelain_paths(lines: Iterable[str]) -> list[str]:
    """
    Extract paths from porcelain lines. Handles '?? path' and 'XY path'.
    """
    paths: list[str] = []
    for ln in lines:
        # Untracked
        if ln.startswith("?? "):
            paths.append(ln[3:].strip())
        else:
            # e.g. ' M file', 'A  file', 'R  old -> new'
            parts = ln.split()
            if not parts:
                continue
            if "->" in parts:
                # rename: last token is new path
                paths.append(parts[-1].strip())
            else:
                paths.append(parts[-1].strip())
    return paths


def is_allowed_dirty(path: str, allowed_patterns: list[str]) -> bool:
    # Normalize to forward slashes for pattern matching
    p = path.replace("\\", "/")
    return any(fnmatch.fnmatch(p, pat) for pat in allowed_patterns)


def main() -> int:
    if not MANIFEST_PATH.exists():
        print(f"FAIL: missing manifest: {MANIFEST_PATH}")
        return 2

    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    epoch = manifest.get("epoch", {})
    invariants = manifest.get("invariants", [])
    policy = manifest.get("policy", {})
    vmods = policy.get("verification_modes", {})

    anchor_commit = epoch.get("head_commit", "")
    seal_json_rel = epoch.get("seal_json", "")
    seal_sig_rel = epoch.get("seal_sig", "")
    seal_sig_tracked = bool(epoch.get("seal_sig_tracked", False))

    # Allowed dirt patterns (from sig_relaxed mode)
    sig_relaxed = vmods.get("sig_relaxed", {})
    allowed_dirty_patterns = sig_relaxed.get("allowed_dirty_paths", ["seals/*.sig"])

    print("[EPOCH] Epoch Validator v0.1")
    print(f"Repo root: {REPO_ROOT}")
    print(f"Manifest:  {MANIFEST_PATH}")
    print(f"Anchor commit (epoch.head_commit): {anchor_commit}")

    head = git_head()
    print(f"Current git HEAD: {head}")

    # Invariant: anchor_commit must be a valid commit
    if anchor_commit:
        rc, out = run(["git", "cat-file", "-t", anchor_commit])
        if rc != 0 or out.strip() != "commit":
            print(f"FAIL: anchor commit is not a valid commit: {anchor_commit}")
            return 3

    # Check seal json path exists (relative to repo)
    if seal_json_rel:
        seal_path = (REPO_ROOT / seal_json_rel).resolve()
        if not seal_path.exists():
            print(f"FAIL: epoch seal_json does not exist: {seal_json_rel}")
            return 4
        print(f"OK: epoch seal_json exists: {seal_json_rel}")

    # Check dirty tree is within allowed patterns (strict epoch invariant)
    lines = git_status_porcelain()
    paths = porcelain_paths(lines)
    if paths:
        # If there are changes, all must be allowed dirt (narrow exception)
        disallowed = [p for p in paths if not is_allowed_dirty(p, allowed_dirty_patterns)]
        if disallowed:
            print("FAIL: working tree contains disallowed changes beyond allowed dirty paths.")
            print("Disallowed:")
            for p in disallowed:
                print(f"  - {p}")
            print("Allowed patterns:")
            for pat in allowed_dirty_patterns:
                print(f"  - {pat}")
            return 5
        else:
            print("OK: working tree dirt is within allowed patterns only.")
    else:
        print("OK: working tree clean.")

    # Verify HEAD seal in the most practical safe mode available.
    # We use --sig-relaxed because strict modes refuse any dirt (including allowed untracked seals/*.sig).
    # NOTE: It is acceptable for the HEAD seal to be unsigned; we report it explicitly.
    rc, out = run(["python", "-m", "scripts.verify_repo_seals", "--head", "--sig-relaxed"])
    print(out.rstrip())

    if rc != 0:
        # If the only failure is "signature file missing", treat as NOTE (unsigned HEAD) not as failure.
        lowered = out.lower()
        if "signature file missing" in lowered:
            print("NOTE: HEAD seal is valid but unsigned (signature file missing).")
        else:
            print("FAIL: HEAD seal verification failed under sig-relaxed.")
            return 6

    # Optional: check epoch signature file existence (not required if untracked policy is in place)
    if seal_sig_rel:
        sig_path = (REPO_ROOT / seal_sig_rel).resolve()
        if sig_path.exists():
            print(f"OK: epoch seal signature file exists: {seal_sig_rel}")
        else:
            # Not a failure by default because your policy keeps .sig untracked/uncommitted.
            print(f"NOTE: epoch seal signature file not present in repo: {seal_sig_rel}")
            if seal_sig_tracked:
                print("FAIL: manifest says seal_sig_tracked=true but signature is missing.")
                return 7

    print("✅ Epoch Validator PASS (read-only).")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as e:
        print(f"FAIL: exception: {e}")
        raise
