from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict

from layer9_interpretability.explainability_trace_v0_1 import (
    build_explainability_trace,
    write_explainability_trace,
)

DEFAULT_SCORES: Dict[str, Any] = {
    "truth_density": "9.5",
    "activation_potential": "8.25",
    "systemic_coherence": "9.0",
    "resonance_longevity": "7.75",
}


def main() -> int:
    p = argparse.ArgumentParser(description="GUS v4 A6 Explain Score (Explainability Trace v0.1)")
    p.add_argument("--scores", type=str, default="", help="JSON string of scores.")
    p.add_argument("--out", type=str, default="", help="Write canonical trace to this path (optional).")
    args = p.parse_args()

    scores = DEFAULT_SCORES
    if args.scores.strip():
        scores = json.loads(args.scores)

    trace = build_explainability_trace(scores)

    if args.out.strip():
        out_path = Path(args.out)
        write_explainability_trace(trace, path=out_path)
        print(str(out_path))
    else:
        print(json.dumps(trace.to_dict(), indent=2, sort_keys=True))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
