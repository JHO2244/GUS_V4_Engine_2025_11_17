from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional
import json

from utils.canonical_json import write_canonical_json_file

# Tests may monkeypatch this
MANIFEST_PATH = Path("layer7_measurement") / "measurement_manifest_v0_1.json"


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


def create_default_manifest(path: Optional[Path] = None) -> Dict[str, Any]:
    """
    A1 Strict 10/10 requirements:
    - Deterministic (no timestamps, no random IDs, no env-dependent fields)
    - Canonical JSON writer
    - Explicit upgrade hooks for A2 (score aggregator) without implementing A2
    """
    target = _resolve_path(path)

    manifest: Dict[str, Any] = {
        "version": "0.1",
        "schema": "gus_v4_measurement_manifest",
        "description": "GUS v4 – A1 Measurement Manifest (Strict Deterministic v0.1).",

        # A1 core contract: what gets measured, at what granularity
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

        # Upgrade hook for A2: aggregator will consume these fields later
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

        # Deterministic invariants for A1:
        "invariants": {
            "no_entropy_fields": True,
            "no_timestamps": True,
            "canonical_json": True,
            "stable_key_order": True,
        },

        # Upgrade path marker (document-only)
        "upgrade_path": {
            "next": "A2_score_aggregator",
            "notes": "A2 will implement aggregation.enabled=True and compute composite_score deterministically.",
        },
    }

    write_manifest(manifest, target)
    return manifest


def _normalize_manifest(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize minimal fields to keep tests stable and upgrades safe.
    """
    if not data:
        return create_default_manifest()

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


def load_manifest(path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Always returns a normalized manifest dict.
    If missing, creates deterministic default and writes canonically.
    """
    target = _resolve_path(path)
    raw = read_manifest(target)
    if not raw:
        return create_default_manifest(path=target)
    return _normalize_manifest(raw)


# Optional typed view (non-essential, but helpful for future layers)
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
