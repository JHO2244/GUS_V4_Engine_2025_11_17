from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any, Dict, Optional
import json

from utils.canonical_json import write_canonical_json_file
from layer7_measurement.measurement_manifest_v0_1 import load_manifest, AUTO_WRITE_DEFAULT

# Tests may monkeypatch this
SCORE_REPORT_PATH = Path("layer7_measurement") / "score_report_v0_1.json"

_DIMENSIONS_DEFAULT = (
    "truth_density",
    "activation_potential",
    "systemic_coherence",
    "resonance_longevity",
)

_Q = Decimal("0.0001")  # 4 dp fixed quantization for deterministic output


def _d(x: Any) -> Decimal:
    """
    Parse numeric-like input to Decimal deterministically.
    Accepts int/float/str/Decimal. Floats are stringified to reduce binary noise.
    """
    if isinstance(x, Decimal):
        return x
    if isinstance(x, (int,)):
        return Decimal(x)
    if isinstance(x, float):
        return Decimal(str(x))
    if isinstance(x, str):
        return Decimal(x.strip())
    raise TypeError(f"Unsupported numeric type: {type(x)}")


def _quantize(x: Decimal) -> Decimal:
    return x.quantize(_Q, rounding=ROUND_HALF_UP)


def validate_scores(scores: Dict[str, Any], *, dimensions: Optional[list[str]] = None) -> Dict[str, Decimal]:
    """
    Validate and normalize scores into Decimals in [0,10].
    """
    dims = dimensions or list(_DIMENSIONS_DEFAULT)
    out: Dict[str, Decimal] = {}

    for k in dims:
        if k not in scores:
            raise KeyError(f"Missing score for dimension: {k}")
        v = _d(scores[k])
        if v < 0 or v > 10:
            raise ValueError(f"Score out of range [0,10] for {k}: {v}")
        out[k] = _quantize(v)

    return out


def _load_weights_from_manifest(manifest: Dict[str, Any], dims: list[str]) -> Dict[str, Decimal]:
    agg = (manifest or {}).get("aggregation", {}) or {}
    weights_raw = agg.get("weights", {}) or {}

    if not weights_raw:
        # Equal weights default
        w = _quantize(Decimal("1") / Decimal(len(dims)))
        return {k: w for k in dims}

    weights: Dict[str, Decimal] = {}
    for k in dims:
        if k not in weights_raw:
            raise KeyError(f"Missing weight for dimension: {k}")
        weights[k] = _quantize(_d(weights_raw[k]))

    total = sum(weights.values(), Decimal("0"))
    if total == 0:
        raise ValueError("Weights sum to zero; invalid.")

    # Normalize to sum exactly 1.0000 deterministically.
    normed = {k: _quantize(weights[k] / total) for k in dims}

    # Fix any rounding drift by adjusting the last element.
    drift = _quantize(Decimal("1") - sum(normed.values(), Decimal("0")))
    if drift != 0:
        last = dims[-1]
        normed[last] = _quantize(normed[last] + drift)

    return normed


def compute_composite_score(scores: Dict[str, Any], *, manifest: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Deterministically compute a composite score from A1 dimensions + weights.

    Output is JSON-safe and deterministic:
    - composite_score_str: fixed 4dp string
    - composite_score_10k: int scaled by 10,000 (exact)
    - per_dimension: fixed 4dp strings
    - weights: fixed 4dp strings
    """
    m = manifest or load_manifest(auto_write=False)
    measurement = (m.get("measurement", {}) or {})
    dims = list(measurement.get("dimensions") or _DIMENSIONS_DEFAULT)

    clean_scores = validate_scores(scores, dimensions=dims)
    weights = _load_weights_from_manifest(m, dims)

    composite = Decimal("0")
    for k in dims:
        composite += clean_scores[k] * weights[k]

    composite = _quantize(composite)

    # Representations: string (stable) + scaled int (exact)
    scaled_10k = int((composite * Decimal("10000")).to_integral_value(rounding=ROUND_HALF_UP))

    return {
        "schema": "gus_v4_score_aggregator_result",
        "version": "0.1",
        "dimensions": dims,
        "per_dimension": {k: f"{clean_scores[k]:f}" for k in dims},
        "weights": {k: f"{weights[k]:f}" for k in dims},
        "composite_score_str": f"{composite:f}",
        "composite_score_10k": scaled_10k,
        "units": "score_out_of_10",
        "notes": "Deterministic A2 composite score (no timestamps, no entropy).",
    }


def write_score_report(report: Dict[str, Any], path: Optional[Path] = None) -> Path:
    target = path or SCORE_REPORT_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    write_canonical_json_file(target, report)
    return target


def read_score_report(path: Optional[Path] = None) -> Dict[str, Any]:
    target = path or SCORE_REPORT_PATH
    if not target.exists():
        return {}
    with target.open("r", encoding="utf-8") as f:
        return json.load(f)
