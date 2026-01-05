#!/usr/bin/env python
# scripts/seal_snapshot.py
from __future__ import annotations

import hashlib
import os
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# ------------------------------------------------------------
# Invocation hardening (GDVS)
# ------------------------------------------------------------
# Support BOTH:
#   1) python -m scripts.seal_snapshot   (preferred)
#   2) python scripts/seal_snapshot.py  (allowed; we repair sys.path)
#
# Also helps Git Bash exec via shebang when possible.
if __package__ is None or __package__ == "":
    # Running as a file path; ensure repo root is on sys.path so "utils" resolves.
    this_file = Path(__file__).resolve()
    repo_root = this_file.parents[1]  # scripts/ -> repo root
    sys.path.insert(0, str(repo_root))

from utils.canonical_json import write_canonical_json_file  # noqa: E402

# CI safety rail: attestation is verify-only; do not generate new seal artifacts in CI.
if os.environ.get("GUS_CI", "").strip() == "1":
    raise SystemExit("CI mode (GUS_CI=1): seal snapshot generation disabled (verify-only policy).")

OUT_DIR = Path("seals")
LOCK_FILE = Path("requirements.lock.txt")


def to_posix(s: str) -> str:
    bs = chr(92)  # backslash
    return s.replace(bs, "/")


def run(cmd: list[str]) -> str:
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\n{p.stdout}\n{p.stderr}")
    return (p.stdout or "").strip()


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    repo_root = run(["git", "rev-parse", "--show-toplevel"])
    os.chdir(repo_root)

    commit = run(["git", "rev-parse", "HEAD"])
    branch = run(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    status = run(["git", "status", "--porcelain"])
    clean = (status.strip() == "")

    # keep it deterministic + portable
    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # pip freeze hash (from current interpreter)
    freeze = subprocess.run([sys.executable, "-m", "pip", "freeze"], capture_output=True, text=True)
    freeze_txt = ((freeze.stdout or "") + (freeze.stderr or "")).replace("\r\n", "\n")
    freeze_sha = hashlib.sha256(freeze_txt.encode("utf-8", errors="replace")).hexdigest()

    lock_sha = sha256_file(LOCK_FILE)

    # test count (best-effort; keep quick)
    test_collect = subprocess.run([sys.executable, "-m", "pytest", "--collect-only", "-q"], capture_output=True, text=True)
    collected_lines = (test_collect.stdout or "").splitlines()
    collected_count = sum(1 for line in collected_lines if line.strip() and " " not in line.strip())

    snapshot = {
        "gus": {"version": "v4", "artifact": "repo_seal_snapshot"},
        "timestamp_utc": now_utc,
        "git": {
            "repo_root": to_posix(repo_root),
            "branch": branch,
            "commit": commit,
            "working_tree_clean": clean,
        },
        "python": {
            "executable": to_posix(sys.executable),
            "version": sys.version.split()[0],
            "platform": platform.platform(),
        },
        "deps": {
            "pip_freeze_sha256": freeze_sha,
            "requirements_lock_sha256": lock_sha,
            "lock_file_present": LOCK_FILE.exists(),
        },
        "tests": {
            "collect_only_exit": test_collect.returncode,
            "approx_collected_items": collected_count,
        },
    }

    out_path = OUT_DIR / f"seal_{commit[:12]}_{now_utc.replace(':','').replace('-','')}.json"
    write_canonical_json_file(out_path, snapshot)

    print(f"OK: wrote {out_path.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
