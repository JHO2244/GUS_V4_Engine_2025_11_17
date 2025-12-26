#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import annotations

"""
GUS v4 — Anchor Verify (CI Spine v0.2)

- Finds latest epoch anchor tag (default: epoch_*_anchor_*)
- Resolves tag -> commit SHA
- Checks out anchor commit (detached)
- Runs: python -m scripts.verify_repo_seals --head --sig-relaxed
- Writes attestation JSON

Key rule:
- Seal verification refuses dirty trees. So we do verification BEFORE writing artifacts inside repo.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


def run(cmd: list[str], *, capture: bool = False) -> subprocess.CompletedProcess:
    if capture:
        return subprocess.run(cmd, check=True, text=True, capture_output=True)
    return subprocess.run(cmd, check=True, text=True)


def git_output(cmd: list[str]) -> str:
    cp = run(cmd, capture=True)
    return (cp.stdout or "").strip()


def find_latest_anchor_tag(tag_pattern: str) -> str:
    tags = git_output([
        "git", "for-each-ref",
        "--sort=-taggerdate",
        "--format=%(refname:short)",
        f"refs/tags/{tag_pattern}",
    ]).splitlines()
    tags = [t.strip() for t in tags if t.strip()]
    if tags:
        return tags[0]

    tags = git_output([
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
    return git_output(["git", "rev-list", "-n", "1", tag])


def short12(sha: str) -> str:
    return sha[:12]


def ensure_out_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag-pattern", default="epoch_*_anchor_*")
    ap.add_argument("--out", default="artifacts/anchor_attestation.json")
    args = ap.parse_args(argv)

    repo_root = Path(git_output(["git", "rev-parse", "--show-toplevel"]))
    os.chdir(repo_root)

    original_head = git_output(["git", "rev-parse", "HEAD"])
    original_head12 = short12(original_head)

    tag = find_latest_anchor_tag(args.tag_pattern)
    anchor_sha = resolve_tag_to_sha(tag)
    anchor_sha12 = short12(anchor_sha)

    print(f"[OK] Latest anchor tag: {tag}")
    print(f"[OK] Anchor commit:     {anchor_sha12}")

    run(["git", "checkout", "--detach", anchor_sha])

    verify_status = "PASS"
    try:
        run([sys.executable, "-m", "scripts.verify_repo_seals", "--head", "--sig-relaxed"])
    except subprocess.CalledProcessError:
        verify_status = "FAIL"

    att = {
        "utc": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
        "tag_pattern": args.tag_pattern,
        "latest_anchor_tag": tag,
        "anchor_sha": anchor_sha,
        "anchor_sha12": anchor_sha12,
        "verified": verify_status,
        "invocation": "python -m scripts.verify_repo_seals --head --sig-relaxed (on detached anchor checkout)",
        "original_head_sha12": original_head12,
    }

    # Write to temp first, then copy into repo (avoids tripping verification itself)
    with tempfile.TemporaryDirectory() as td:
        tmp_path = Path(td) / "anchor_attestation.json"
        tmp_path.write_text(json.dumps(att, indent=2) + "\n", encoding="utf-8")

        out_path = Path(args.out)
        ensure_out_dir(out_path)
        shutil.copy2(tmp_path, out_path)

    print(f"[OK] Wrote attestation: {Path(args.out).as_posix()}")
    return 0 if verify_status == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
