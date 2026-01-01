#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import annotations
from utils.canonical_json import write_canonical_json_file

"""
GUS v4 - Anchor Verify (CI Spine v0.2)

What this does (SAFE):
- Finds latest epoch anchor tag (pattern: epoch_*_anchor_*)
- Resolves tag -> anchor commit SHA
- Verifies that a seal JSON exists for that anchor SHA in the CURRENT checkout
  (IMPORTANT: we DO NOT detach/checkout to the anchor commit)
- Writes an attestation JSON

Default behavior:
- Writes attestation OUTSIDE the repo by default (system temp folder)
- You can override with --out (e.g. --out artifacts/anchor_attestation.json)
"""

import argparse
import os
import subprocess
import sys
import tempfile
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


def default_attestation_path() -> Path:
    # Always write OUTSIDE the repo by default.
    # CI: RUNNER_TEMP; Local: system temp
    if os.environ.get("GITHUB_ACTIONS") == "true":
        base = Path(os.environ.get("RUNNER_TEMP", "/tmp")) / "gus_artifacts"
    else:
        base = Path(tempfile.gettempdir()) / "gus_artifacts"
    return base / "anchor_attestation.json"


def write_json(path: Path, payload: dict) -> None:
    write_canonical_json_file(path, payload)


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag-pattern", default="epoch_*_anchor_*")
    ap.add_argument("--out", default=str(default_attestation_path()))
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

    # CRITICAL RULE: never detach/checkout here.
    # Seal files for older commits are stored in newer history. Detaching would hide them.

    # Verify that the seal JSON exists for the anchor SHA (content-only is enough for CI,
    # because .sig is not committed by design).
    cmd = [
        sys.executable, "-m", "scripts.verify_repo_seals",
        "--sha", anchor_sha12,
        "--no-sig",
        "--sig-strict",
        "--ci",
    ]
    rc = subprocess.call(cmd)
    verified = (rc == 0)

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

    out_path = Path(args.out)
    write_json(out_path, att)
    print(f"[OK] Wrote attestation: {out_path}")

    return 0 if verified else 2


if __name__ == "__main__":
    raise SystemExit(main())
