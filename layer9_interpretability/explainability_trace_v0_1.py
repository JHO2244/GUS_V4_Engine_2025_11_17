from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
import json

from utils.canonical_json import write_canonical_json_file
from layer7_measurement.measurement_manifest_v0_1 import load_manifest
from layer7_measurement.score_aggregator_v0_1 import compute_composite_score

# Explicit writer only; never auto-write into repo tree.
DEFAULT_TRACE_PATH = Path("layer9_interpretability") / "explainability_trace_v0_1.json"

def _extract_composite_score(agg: Dict[str, Any]) -> float:
    """
    A2 compatibility: extract composite score from aggregator result dict.

    Current A2 contract observed in tests:
      - composite_score_10k: int scaled by 10,000 (preferred)
      - composite_score_str: string formatted to 4 decimals

    We prefer composite_score_10k for maximum determinism; fall back to _str.
    """
    v10k = agg.get("composite_score_10k")
    if v10k is not None:
        return float(v10k) / 10000.0

    vstr = agg.get("composite_score_str")
    if vstr is not None:
        return float(vstr)

    # Back-compat: common keys (if A2 evolves)
    for k in ("composite_score", "composite", "score"):
        v = agg.get(k)
        if v is not None:
            return float(v)

    # Nested patterns (defensive)
    for parent_key in ("result", "data", "payload"):
        parent = agg.get(parent_key)
        if isinstance(parent, dict):
            v10k = parent.get("composite_score_10k")
            if v10k is not None:
                return float(v10k) / 10000.0
            vstr = parent.get("composite_score_str")
            if vstr is not None:
                return float(vstr)
            for k in ("composite_score", "composite", "score"):
                v = parent.get(k)
                if v is not None:
                    return float(v)

    raise ValueError(
        "A6 cannot extract composite score from A2 aggregator result. "
        f"Available keys: {sorted(list(agg.keys()))}"
    )


def _to_float(x: Any) -> float:
    """
    Deterministic numeric coercion used for trace transparency.
    Raises ValueError for unsupported input.
    """
    if isinstance(x, bool):
        raise ValueError("bool is not a valid score")
    if isinstance(x, (int, float)):
        return float(x)
    if isinstance(x, str):
        s = x.strip()
        return float(s)
    raise ValueError(f"unsupported score type: {type(x)!r}")


def _stable_dim_order(manifest: Dict[str, Any]) -> Tuple[str, ...]:
    dims = ((manifest.get("measurement", {}) or {}).get("dimensions") or [])
    if not dims:
        dims = ["truth_density", "activation_potential", "systemic_coherence", "resonance_longevity"]
    # Preserve manifest order; cast to tuple for immutability.
    return tuple([str(d) for d in dims])


def _weights(manifest: Dict[str, Any]) -> Dict[str, float]:
    w = ((manifest.get("aggregation", {}) or {}).get("weights") or {})
    # Normalize weights to float deterministically
    out: Dict[str, float] = {}
    for k, v in w.items():
        out[str(k)] = float(v)
    return out


@dataclass(frozen=True)
class ExplainabilityTrace:
    """
    Deterministic explainability contract.
    No timestamps, UUIDs, randomness, or environment-dependent fields.
    """
    schema: str
    version: str
    manifest_schema: str
    manifest_version: str
    measurement_mode: str
    units: str
    input_scores_raw: Dict[str, Any]
    input_scores_parsed: Dict[str, float]
    weights: Dict[str, float]
    per_dimension_weighted: Dict[str, float]
    composite_score: float
    aggregator_result: Dict[str, Any]
    notes: str

    def to_dict(self) -> Dict[str, Any]:
        # Ensure stable ordering by building a regular dict with fixed keys.
        return {
            "schema": self.schema,
            "version": self.version,
            "manifest_schema": self.manifest_schema,
            "manifest_version": self.manifest_version,
            "measurement_mode": self.measurement_mode,
            "units": self.units,
            "input_scores_raw": self.input_scores_raw,
            "input_scores_parsed": self.input_scores_parsed,
            "weights": self.weights,
            "per_dimension_weighted": self.per_dimension_weighted,
            "composite_score": self.composite_score,
            "aggregator_result": self.aggregator_result,
            "notes": self.notes,
        }


def build_explainability_trace(
    scores: Dict[str, Any],
    *,
    manifest: Optional[Dict[str, Any]] = None,
) -> ExplainabilityTrace:
    """
    Pure function: produces a deterministic explainability trace.
    No file I/O.
    """
    m = manifest or load_manifest(auto_write=False)

    dims = _stable_dim_order(m)
    w = _weights(m)

    # Parse inputs deterministically per dimension order.
    parsed: Dict[str, float] = {}
    weighted: Dict[str, float] = {}

    for d in dims:
        raw = scores.get(d)
        val = _to_float(raw)
        parsed[d] = val
        weighted[d] = val * float(w.get(d, 0.0))

    # Use the authoritative aggregator for the official result
    agg = compute_composite_score(scores, manifest=m)

    composite = _extract_composite_score(agg)
    trace = ExplainabilityTrace(
        schema="gus_v4_explainability_trace",
        version="0.1",
        manifest_schema=str(m.get("schema", "")),
        manifest_version=str(m.get("version", "")),
        measurement_mode=str((m.get("measurement", {}) or {}).get("mode", "strict")),
        units="score_out_of_10",
        input_scores_raw=dict(scores),
        input_scores_parsed=parsed,
        weights=w,
        per_dimension_weighted=weighted,
        composite_score=composite,
        aggregator_result=agg,
        notes="A6 explainability trace (deterministic, no timestamps, no entropy).",
    )
    return trace


def write_explainability_trace(trace: ExplainabilityTrace, *, path: Optional[Path] = None) -> Path:
    """
    Explicit writer only. Canonical JSON.
    """
    target = path or DEFAULT_TRACE_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    write_canonical_json_file(target, trace.to_dict())
    return target


def read_explainability_trace(path: Optional[Path] = None) -> Dict[str, Any]:
    target = path or DEFAULT_TRACE_PATH
    if not target.exists():
        return {}
    with target.open("r", encoding="utf-8") as f:
        return json.load(f)
