from __future__ import annotations

import sys
from pathlib import Path
from utils.console_symbols import sym


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    seals_dir = repo_root / "seals"
    seals = sorted(seals_dir.glob("seal_*_*.json"))

    if not seals:
        print(f"{sym('fail')} No seals found in {seals_dir}")
        return 1

    latest = seals[-1]
    print(f"[VERIFY] Latest seal (content-only): {latest}")

    # Use existing verifier for content-only
    import subprocess

    rc = subprocess.run(
        [sys.executable, "-m", "scripts.verify_seal", str(latest), "--allow-dirty"],
        text=True,
    ).returncode

    if rc != 0:
        print(f"{sym('fail')} verify_seal failed for {latest.name}")
        return rc

    print(f"[OK] {latest.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
