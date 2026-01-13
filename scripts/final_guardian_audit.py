from __future__ import annotations

import sys
from pathlib import Path

import argparse

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from layer9_final_guardian_audit.final_guardian_audit_v0_1 import write_a9_report_v0_1


def main() -> int:
    ap = argparse.ArgumentParser(description="GUS v4 — A9 Final Guardian Audit (v0.1)")
    ap.add_argument(
        "--out",
        default="audits/a9_final_guardian_audit_v0_1.json",
        help="Output JSON path (default: audits/a9_final_guardian_audit_v0_1.json)",
    )
    ap.add_argument(
        "--no-require-seal-ok",
        action="store_true",
        help="Do not fail verdict if seal verification fails (not recommended)",
    )
    args = ap.parse_args()

    out_path = Path(args.out)
    verdict = write_a9_report_v0_1(out_path=out_path, require_seal_ok=(not args.no_require_seal_ok))
    print(f"[A9] wrote: {out_path.as_posix()}")
    print(f"[A9] verdict.ok={verdict.ok}")
    return 0 if verdict.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
