from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional
import json

from utils.canonical_json import write_canonical_json_file

# Tests may monkeypatch this
MANIFEST_PATH = Path("layer7_measurement") / "measurement_manifest_v0_1.json"

# Strict mode default: DO NOT write to repo unless explicitly requested
AUTO_WRITE_DEFAULT = False


def _resolve_path(path: Optional[Path]) -> Path:
    return path or MANIFEST_PATH


def read_manifest(path: Optional[Path] = None) -> Dict[str, Any]:
    target = _resolve_path(path)
    if not target.exists():
        return {}
    with target.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_manifest(data: Dict[str, Any], path: Optional[Path] = None) -> None:
    target = _resolve_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    write_canonical_json_file(target, data)


def _default_manifest_dict() -> Dict[str, Any]:
    """
    Pure in-memory default manifest dict. NO file I/O.
    """
    return {
        "version": "0.1",
        "schema": "gus_v4_measurement_manifest",
        "description": "GUS v4 – A1 Measurement Manifest (Strict Deterministic v0.1).",
        "measurement": {
            "mode": "strict",
            "units": "score_out_of_10",
            "dimensions": ["truth_density", "activation_potential", "systemic_coherence", "resonance_longevity"],
            "dimension_aliases": {
                "truth_density": "TD",
                "activation_potential": "AP",
                "systemic_coherence": "SC",
                "resonance_longevity": "RL",
            },
        },
        "aggregation": {
            "enabled": False,
            "strategy": "placeholder_for_A2",
            "composite_field": "composite_score",
            "weights": {
                "truth_density": 0.25,
                "activation_potential": 0.25,
                "systemic_coherence": 0.25,
                "resonance_longevity": 0.25,
            },
        },
        "invariants": {
            "no_entropy_fields": True,
            "no_timestamps": True,
            "canonical_json": True,
            "stable_key_order": True,
        },
        "upgrade_path": {
            "next": "A2_score_aggregator",
            "notes": "A2 computes composite_score deterministically; enable aggregation there if desired.",
        },
    }


def create_default_manifest(path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Explicit writer: creates and WRITES the canonical default to disk.
    Only call this when you truly want a file on disk.
    """
    target = _resolve_path(path)
    manifest = _default_manifest_dict()
    write_manifest(manifest, target)
    return manifest


def _normalize_manifest(data: Dict[str, Any]) -> Dict[str, Any]:
    if not data:
        data = _default_manifest_dict()

    data.setdefault("version", "0.1")
    data.setdefault("schema", "gus_v4_measurement_manifest")
    data.setdefault("measurement", {})
    data.setdefault("aggregation", {})
    data.setdefault("invariants", {})
    data.setdefault("upgrade_path", {})

    measurement = data["measurement"]
    measurement.setdefault("mode", "strict")
    measurement.setdefault("units", "score_out_of_10")
    measurement.setdefault(
        "dimensions",
        ["truth_density", "activation_potential", "systemic_coherence", "resonance_longevity"],
    )
    measurement.setdefault(
        "dimension_aliases",
        {"truth_density": "TD", "activation_potential": "AP", "systemic_coherence": "SC", "resonance_longevity": "RL"},
    )

    aggregation = data["aggregation"]
    aggregation.setdefault("enabled", False)
    aggregation.setdefault("strategy", "placeholder_for_A2")
    aggregation.setdefault("composite_field", "composite_score")
    aggregation.setdefault(
        "weights",
        {"truth_density": 0.25, "activation_potential": 0.25, "systemic_coherence": 0.25, "resonance_longevity": 0.25},
    )

    invariants = data["invariants"]
    invariants.setdefault("no_entropy_fields", True)
    invariants.setdefault("no_timestamps", True)
    invariants.setdefault("canonical_json", True)
    invariants.setdefault("stable_key_order", True)

    upgrade_path = data["upgrade_path"]
    upgrade_path.setdefault("next", "A2_score_aggregator")

    return data


def load_manifest(path: Optional[Path] = None, *, auto_write: bool = AUTO_WRITE_DEFAULT) -> Dict[str, Any]:
    """
    Strict default: SIDE-EFFECT FREE.

    - If missing: return in-memory default (normalized).
    - Only writes if auto_write=True explicitly.
    """
    target = _resolve_path(path)
    raw = read_manifest(target)

    if not raw:
        if auto_write:
            return create_default_manifest(path=target)
        return _normalize_manifest(_default_manifest_dict())

    return _normalize_manifest(raw)


@dataclass(frozen=True)
class MeasurementManifest:
    raw: Dict[str, Any]

    @property
    def schema(self) -> str:
        return str(self.raw.get("schema", ""))

    @property
    def version(self) -> str:
        return str(self.raw.get("version", ""))


def load_manifest_typed(path: Optional[Path] = None) -> MeasurementManifest:
    return MeasurementManifest(load_manifest(path))
