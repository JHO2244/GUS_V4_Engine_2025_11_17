# scripts/seal_snapshot.py
from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

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
    # You already run full tests in gate; here we store the discovered count (no execution).
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

    # filename includes commit prefix
    out_path = OUT_DIR / f"seal_{commit[:12]}_{now_utc.replace(':','').replace('-','')}.json"
    out_path.write_text(json.dumps(snapshot, indent=2, sort_keys=True), encoding="utf-8")

    print(f"OK: wrote {out_path.as_posix()}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
