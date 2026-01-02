from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional
import json

from utils.canonical_json import write_canonical_json_file
from layer7_measurement.measurement_manifest_v0_1 import load_manifest
from layer7_measurement.score_aggregator_v0_1 import compute_composite_score

# IMPORTANT: do not write into repo tree by default.
DEFAULT_REPORT_PATH = Path("layer7_measurement") / "self_measurement_report_v0_1.json"


def build_self_measurement_report(
    scores: Dict[str, Any],
    *,
    manifest: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Pure function: builds a deterministic self-measurement report dict.
    No file I/O.
    """
    m = manifest or load_manifest(auto_write=False)
    agg = compute_composite_score(scores, manifest=m)

    report: Dict[str, Any] = {
        "schema": "gus_v4_self_measurement_report",
        "version": "0.1",
        "manifest_schema": m.get("schema"),
        "manifest_version": m.get("version"),
        "measurement_mode": (m.get("measurement", {}) or {}).get("mode", "strict"),
        "units": "score_out_of_10",
        "result": agg,
        "notes": "A4 self-measurement report (deterministic, no timestamps, no entropy).",
    }
    return report


def write_self_measurement_report(
    report: Dict[str, Any],
    *,
    path: Optional[Path] = None,
) -> Path:
    """
    Explicit writer only. Caller must choose to write.
    """
    target = path or DEFAULT_REPORT_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    write_canonical_json_file(target, report)
    return target


def read_self_measurement_report(path: Optional[Path] = None) -> Dict[str, Any]:
    target = path or DEFAULT_REPORT_PATH
    if not target.exists():
        return {}
    with target.open("r", encoding="utf-8") as f:
        return json.load(f)
