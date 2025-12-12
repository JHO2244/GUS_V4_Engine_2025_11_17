# scripts/deps_lock_check.py
from __future__ import annotations

import hashlib
import os
import subprocess
import sys
from pathlib import Path

LOCK_FILE = Path("requirements.lock.txt")

def _run(cmd: list[str]) -> tuple[int, str]:
    p = subprocess.run(cmd, capture_output=True, text=True)
    out = (p.stdout or "") + (p.stderr or "")
    return p.returncode, out

def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()

def main() -> int:
    if not LOCK_FILE.exists():
        print(f"FAIL: missing {LOCK_FILE}. Create it with: python -m pip freeze > requirements.lock.txt")
        return 1

    # freeze using the *current interpreter*
    rc, out = _run([sys.executable, "-m", "pip", "freeze"])
    if rc != 0:
        print("FAIL: pip freeze failed.")
        print(out)
        return 1

    live = out.replace("\r\n", "\n").strip() + "\n"
    locked = LOCK_FILE.read_text(encoding="utf-8", errors="replace").replace("\r\n", "\n").strip() + "\n"

    if live == locked:
        print("OK: dependency lock matches current environment.")
        return 0

    # strict by default; allow override for controlled workflows
    allow_drift = os.getenv("GUS_ALLOW_DEPS_DRIFT", "").strip().lower() in {"1", "true", "yes"}

    print("FAIL: dependency lock drift detected.")
    print(f"LOCK_SHA256={_sha256(locked)}")
    print(f"LIVE_SHA256={_sha256(live)}")
    print("")
    print("Fix options:")
    print("  A) Update lock: python -m pip freeze > requirements.lock.txt && git add requirements.lock.txt")
    print("  B) Recreate env to match lock (recommended for strict reproducibility)")
    print("")
    if allow_drift:
        print("WARN: GUS_ALLOW_DEPS_DRIFT is set; allowing drift for this run.")
        return 0

    return 2

if __name__ == "__main__":
    raise SystemExit(main())
