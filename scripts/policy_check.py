from __future__ import annotations

import argparse
import json
from pathlib import Path

from layer8_safety.anti_weaponization_policy_v0_1 import evaluate_text, write_eval_report


def main() -> int:
    p = argparse.ArgumentParser(description="GUS v4 A5 Anti-Weaponization Policy Check (v0.1)")
    p.add_argument("--text", type=str, default="", help="Text to evaluate.")
    p.add_argument("--in", dest="infile", type=str, default="", help="Read text from a file.")
    p.add_argument("--out", type=str, default="", help="Write canonical verdict report to path (optional).")
    args = p.parse_args()

    text = args.text
    if args.infile.strip():
        text = Path(args.infile).read_text(encoding="utf-8")

    verdict = evaluate_text(text)

    if args.out.strip():
        out_path = Path(args.out)
        write_eval_report(verdict, path=out_path)
        print(str(out_path))
    else:
        print(json.dumps(verdict.to_dict(), indent=2, sort_keys=True))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
