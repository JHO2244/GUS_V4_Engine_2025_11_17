from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict

from layer7_measurement.self_measurement_v0_1 import (
    build_self_measurement_report,
    write_self_measurement_report,
)

DEFAULT_SCORES: Dict[str, Any] = {
    "truth_density": "10.0",
    "activation_potential": "10.0",
    "systemic_coherence": "10.0",
    "resonance_longevity": "10.0",
}


def main() -> int:
    p = argparse.ArgumentParser(description="GUS v4 A4 Self-Measurement (v0.1)")
    p.add_argument("--scores", type=str, default="", help="JSON string of scores (TD/AP/SC/RL).")
    p.add_argument("--out", type=str, default="", help="Write canonical report to this path (optional).")
    args = p.parse_args()

    scores = DEFAULT_SCORES
    if args.scores.strip():
        scores = json.loads(args.scores)

    report = build_self_measurement_report(scores)

    if args.out.strip():
        out_path = Path(args.out)
        write_self_measurement_report(report, path=out_path)
        print(str(out_path))
    else:
        # Side-effect free default: print JSON to stdout (no file writes)
        print(json.dumps(report, indent=2, sort_keys=True))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

