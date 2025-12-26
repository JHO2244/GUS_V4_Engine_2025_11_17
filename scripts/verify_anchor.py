#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import annotations

"""
GUS v4 — Anchor Verify (CI Spine v0.2)

What this does (SAFE):
- Finds latest epoch anchor tag (pattern: epoch_*_anchor_*)
- Resolves tag -> anchor commit SHA
- Verifies that a seal JSON exists for that anchor SHA in the CURRENT checkout
  (IMPORTANT: we DO NOT detach/checkout to the anchor commit)
- Writes attestation JSON
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


def run_capture(cmd: list[str]) -> str:
    cp = subprocess.run(cmd, check=True, text=True, capture_output=True)
    return (cp.stdout or "").strip()


def find_latest_anchor_tag(tag_pattern: str) -> str:
    # Prefer annotated tags by taggerdate; fallback to creatordate
    tags = run_capture([
        "git", "for-each-ref",
        "--sort=-taggerdate",
        "--format=%(refname:short)",
        f"refs/tags/{tag_pattern}",
    ]).splitlines()
    tags = [t.strip() for t in tags if t.strip()]
    if tags:
        return tags[0]

    tags = run_capture([
        "git", "for-each-ref",
        "--sort=-creatordate",
        "--format=%(refname:short)",
        f"refs/tags/{tag_pattern}",
    ]).splitlines()
    tags = [t.strip() for t in tags if t.strip()]
    if not tags:
        raise SystemExit(f"[FAIL] No tags found matching pattern: {tag_pattern}")
    return tags[0]


def resolve_tag_to_sha(tag: str) -> str:
    return run_capture(["git", "rev-list", "-n", "1", tag])


def short12(sha: str) -> str:
    return sha[:12]


def write_attestation(att: dict, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(att, indent=2), encoding="utf-8")
    print(f"[OK] Wrote attestation: {out_path}")


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag-pattern", default="epoch_*_anchor_*")
    ap.add_argument("--out", default="artifacts/anchor_attestation.json")
    args = ap.parse_args(argv)

    repo_root = Path(run_capture(["git", "rev-parse", "--show-toplevel"]))
    os.chdir(repo_root)

    original_head = run_capture(["git", "rev-parse", "HEAD"])
    original_head12 = short12(original_head)

    tag = find_latest_anchor_tag(args.tag_pattern)
    anchor_sha = resolve_tag_to_sha(tag)
    anchor_sha12 = short12(anchor_sha)

    print(f"[OK] Latest anchor tag: {tag}")
    print(f"[OK] Anchor commit:     {anchor_sha12}")

    # ✅ CRITICAL RULE: never detach/checkout here.
    # Seal files for older commits are stored in newer history. Detaching would hide them.

    # 1) Verify that the seal JSON exists for the anchor SHA (content-only ok here)
    cmd = [
        sys.executable, "-m", "scripts.verify_repo_seals",
        "--sha", anchor_sha12,
        "--no-sig",
        "--sig-strict",
        "--ci",
    ]
    rc = subprocess.call(cmd)
    verified = (rc == 0)

    # 2) Decide where to write the attestation
    if os.environ.get("GITHUB_ACTIONS") == "true":
        # Write outside repo in CI
        out_dir = Path(os.environ.get("RUNNER_TEMP", "/tmp")) / "gus_artifacts"
        out_path = out_dir / "anchor_attestation.json"
    else:
        # Local: write to requested path in repo (default artifacts/)
        out_path = Path(args.out)

    att = {
        "utc": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
        "tag_pattern": args.tag_pattern,
        "latest_anchor_tag": tag,
        "anchor_sha": anchor_sha,
        "anchor_sha12": anchor_sha12,
        "verified": "PASS" if verified else "FAIL",
        "verification_cmd": "python -m scripts.verify_repo_seals --sha <ANCHOR_SHA12> --no-sig --sig-strict --ci",
        "original_head_sha12": original_head12,
    }

    write_attestation(att, out_path)

    return 0 if verified else 2


if __name__ == "__main__":
    raise SystemExit(main())
