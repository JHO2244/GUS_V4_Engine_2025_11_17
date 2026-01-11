from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from utils.canonical_json import write_canonical_json_file

def main() -> int:
    if len(sys.argv) != 2:
        print("[FAIL] usage: python scripts/gdvs_stamp_created_at.py <path/to/gdvs_artifact.json>")
        return 2

    p = Path(sys.argv[1])
    if not p.is_file():
        print(f"[FAIL] missing file: {p}")
        return 2

    data = json.loads(p.read_text(encoding="utf-8"))
    if "created_at_utc" not in data:
        print("[FAIL] JSON missing required key: created_at_utc")
        return 2

    data["created_at_utc"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    write_canonical_json_file(p, data)
    print("OK: stamped created_at_utc (canonical)")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
