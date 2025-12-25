#!/usr/bin/env python
"""
GUS v4 — Epoch Validator v0.1 (read-only)

Validates the epoch manifest against:
- Git HEAD & expected anchor
- Allowed "dirty tree" rules
- Epoch seal JSON existence
- Optional epoch signature expectations
- (Option A) CI skips HEAD seal verification entirely

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


def is_ci() -> bool:
    gus_ci = os.getenv("GUS_CI", "")
    ci = os.getenv("CI", "")
    gha = os.getenv("GITHUB_ACTIONS", "")

    truthy = {"1", "true", "yes", "on", "y"}

    result = (
        gus_ci.strip().lower() in truthy
        or ci.strip().lower() in truthy
        or gha.strip().lower() in truthy
    )

    # Keep this print ASCII-safe for Windows runners
    print(f"CI flags: GUS_CI={gus_ci} CI={ci} GITHUB_ACTIONS={gha}")
    return result


# Force UTF-8 stdout/stderr where supported (prevents Windows cp1252 crashes)
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


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


def any_seal_json_present() -> bool:
    seals_dir = REPO_ROOT / "seals"
    if not seals_dir.is_dir():
        return False
    return any(seals_dir.glob("seal_*.json"))


def git_head() -> str:
    rc, out = run(["git", "rev-parse", "HEAD"])
    if rc != 0:
        raise RuntimeError(f"git rev-parse HEAD failed:\n{out}")
    return out.strip()


def git_status_porcelain() -> list[str]:
    rc, out = run(["git", "status", "--porcelain"])
    if rc != 0:
        raise RuntimeError(f"git status failed:\n{out}")
    return [ln.strip() for ln in out.splitlines() if ln.strip()]


def porcelain_paths(lines: Iterable[str]) -> list[str]:
    """
    Extract paths from porcelain lines. Handles '?? path' and 'XY path'.
    """
    paths: list[str] = []
    for ln in lines:
        if ln.startswith("?? "):
            paths.append(ln[3:].strip())
        else:
            parts = ln.split()
            if not parts:
                continue
            if "->" in parts:
                paths.append(parts[-1].strip())
            else:
                paths.append(parts[-1].strip())
    return paths


def is_allowed_dirty(path: str, allowed_patterns: list[str]) -> bool:
    p = path.replace("\\", "/")
    return any(fnmatch.fnmatch(p, pat) for pat in allowed_patterns)


def verify_head_seal_sig_relaxed() -> int:
    """
    Local-only HEAD seal verification.
    Option A: CI skips this entirely.
    Uses sig-relaxed because head seals are allowed to be unsigned.
    """
    rc, out = run(["python", "-m", "scripts.verify_repo_seals", "--head", "--sig-relaxed"])
    if rc != 0:
        print(out.strip())
        return rc
    # Print tool output to keep logs consistent
    print(out.strip())
    return 0


def main() -> int:
    if not MANIFEST_PATH.exists():
        print(f"FAIL: missing manifest: {MANIFEST_PATH}")
        return 2

    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    epoch = manifest.get("epoch", {})
    policy = manifest.get("policy", {})
    vmods = policy.get("verification_modes", {})

    anchor_commit = epoch.get("head_commit", "")
    seal_json_rel = epoch.get("seal_json", "")
    seal_sig_rel = epoch.get("seal_sig", "")
    seal_sig_tracked = bool(epoch.get("seal_sig_tracked", False))

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

    # Check epoch seal JSON exists (relative to repo)
    if seal_json_rel:
        seal_path = (REPO_ROOT / seal_json_rel).resolve()
        if not seal_path.exists():
            if is_ci():
                print(f"[WARN] epoch seal_json missing in CI verify-only mode: {seal_json_rel} — skipping.")
            else:
                print(f"FAIL: epoch seal_json does not exist: {seal_json_rel}")
                return 4
        else:
            print(f"OK: epoch seal_json exists: {seal_json_rel}")

    # Check dirty tree is within allowed patterns
    lines = git_status_porcelain()
    paths = porcelain_paths(lines)
    if paths:
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
        print("OK: working tree dirt is within allowed patterns only.")
    else:
        print("OK: working tree clean.")

    # Option A: CI skips HEAD seal verification (CI doesn't generate head seals)
    if is_ci():
        print("[EPOCH] CI mode: skipping HEAD seal verification (Option A).")
    else:
        # Local mode: only attempt if seals exist at all
        if any_seal_json_present():
            rc = verify_head_seal_sig_relaxed()
            if rc != 0:
                print("FAIL: HEAD seal verification failed under sig-relaxed.")
                return 6
        else:
            print("[WARN] No seals present locally — skipping HEAD seal verification.")

    # Optional: epoch signature file existence (strict only if manifest says tracked)
    if seal_sig_rel:
        sig_path = (REPO_ROOT / seal_sig_rel).resolve()
        if sig_path.exists():
            print(f"OK: epoch seal signature file exists: {seal_sig_rel}")
        else:
            print(f"NOTE: epoch seal signature file not present in repo: {seal_sig_rel}")
            if seal_sig_tracked:
                print("FAIL: manifest says seal_sig_tracked=true but signature is missing.")
                return 7

    print("[OK] Epoch Validator PASS (read-only).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
