"""
GUS v4 – Layer 5 Continuity Manifest v0.1

Thin loader around continuity/gus_v4_continuity_manifest.json.
"""

from __future__ import annotations

from pathlib import Path
import json
from typing import Any, Dict


def _get_manifest_path() -> Path:
    """
    Resolve the continuity manifest JSON relative to the project root.
    """
    # layer5_continuity/continuity_manifest_v0_1.py -> project root
    root = Path(__file__).resolve().parents[1]
    return root / "continuity" / "gus_v4_continuity_manifest.json"


def load_manifest() -> Dict[str, Any]:
    """
    Load the L5 continuity manifest from JSON.

    Expected shape (minimal for tests):
    {
        "continuity_entries": [ ... ],
        ...
    }
    """
    path = _get_manifest_path()
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, dict):
        raise ValueError("Continuity manifest JSON must be a top-level object/dict.")

    return data
