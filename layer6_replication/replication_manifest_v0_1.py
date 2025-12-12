"""
GUS v4 – Layer 6 Replication Manifest v0.1

This module defines a simple, test-aligned API:

- MANIFEST_PATH: JSON location (monkeypatchable by tests)
- read_manifest() / write_manifest(): raw JSON helpers
- load_manifest(): returns a *normalized* manifest dict with top-level keys:
    - "frequency"          → e.g. "on_demand"
    - "require_all_green"  → bool
    - "max_snapshots"      → int
- create_default_manifest(): writes a canonical v0.1 manifest to disk
- build_replication_plan_from_continuity(): builds a dict-based plan using L5

Tests expect:
- from layer6_replication.replication_manifest_v0_1 import load_manifest as l6_load_manifest
- l6_load_manifest().get("frequency") == "on_demand"
- build_replication_plan_from_continuity(...) returns a dict
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence
import json

from layer5_continuity.continuity_manifest_v0_1 import (
    ContinuityStatus,
    load_continuity_status,
)

# Default replication manifest location (tests may monkeypatch this)
MANIFEST_PATH = Path("layer6_replication") / "replication_manifest_v0_1.json"


# ---------------------------------------------------------------------------
# Raw JSON helpers
# ---------------------------------------------------------------------------

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
    with target.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)


# ---------------------------------------------------------------------------
# Manifest creation + normalization
# ---------------------------------------------------------------------------

def create_default_manifest(
    path: Optional[Path] = None,
    *,
    default_targets: Optional[Sequence[str]] = None,
) -> Dict[str, Any]:
    """
    Create a canonical replication manifest that satisfies PAS v0.2 + tests.

    Top-level invariants (used by tests):
      - frequency == "on_demand"
      - require_all_green == True
      - max_snapshots == 7 (arbitrary but > 0)
    """
    target = _resolve_path(path)

    manifest: Dict[str, Any] = {
        "version": "0.1",
        "schema": "gus_v4_replication_manifest",
        "description": "GUS v4 – default Layer 6 replication policy.",
        # Top-level fields the tests look at:
        "frequency": "on_demand",
        "require_all_green": True,
        "max_snapshots": 7,
        # Targets & policy details are used by PAS and future layers:
        "targets": list(default_targets or []),
        "policy": {
            "min_targets": 1,
            "max_targets": 3,
            "allow_network_paths": True,
            "require_airgap": False,
        },
        "continuity": {
            "require_green_status": True,
            "allow_warning_status": False,
        },
    }

    write_manifest(manifest, target)
    return manifest


def _normalize_manifest(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ensure the manifest dict exposes the keys the tests expect.
    If essential keys are missing, we "upgrade" it in-memory.
    """
    if not data:
        return create_default_manifest()

    # If it's an older / nested schema, promote key fields to top-level
    policy = data.get("policy", {})
    data.setdefault("frequency", policy.get("frequency", "on_demand"))
    data.setdefault("require_all_green", policy.get("require_all_green", True))

    # max_snapshots invariant: > 0
    max_snaps = data.get("max_snapshots", policy.get("max_snapshots", 7))
    if not isinstance(max_snaps, int) or max_snaps <= 0:
        max_snaps = 7
    data["max_snapshots"] = max_snaps

    return data


def load_manifest(path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Public loader used by tests (aliased as l6_load_manifest).

    It always returns a normalized dict with:
      - "frequency"
      - "require_all_green"
      - "max_snapshots"
    present at the top level.
    """
    target = _resolve_path(path)
    raw = read_manifest(target)

    if not raw:
        return create_default_manifest(path=target)

    return _normalize_manifest(raw)


# ---------------------------------------------------------------------------
# Replication plan builder
# ---------------------------------------------------------------------------

def build_replication_plan_from_continuity(
    default_targets: Optional[Sequence[str]] = None,
) -> Dict[str, Any]:
    """
    Construct a simple dict-based replication plan from the continuity spine.

    tests_pas_014 only asserts that the return type is `dict`, but we provide
    a clean, structured payload for future use.

    Shape:

        {
            "continuity_status": "ok" | "error" | "manifest_missing" | ...,
            "continuity_ok": bool,
            "continuity_reason": str,
            "targets": [...],
            "frequency": "on_demand",
            "require_all_green": True,
            "max_snapshots": 7,
            "manifest": {...},   # full L6 manifest
        }
    """
    continuity_status: ContinuityStatus = load_continuity_status()
    manifest = load_manifest()

    targets: List[str] = list(default_targets or manifest.get("targets", []))

    plan: Dict[str, Any] = {
        "continuity_status": continuity_status.code,
        "continuity_ok": continuity_status.ok,
        "continuity_reason": continuity_status.reason,
        "targets": targets,
        "frequency": manifest.get("frequency"),
        "require_all_green": manifest.get("require_all_green"),
        "max_snapshots": manifest.get("max_snapshots"),
        "manifest": manifest,
    }

    return plan
