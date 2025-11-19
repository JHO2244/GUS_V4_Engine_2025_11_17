# Placeholder for static rules
"""
GUS v4 – Layer 2 Governance Matrix stub.

Responsibility (skeleton mode):
- Load council definitions JSON.
- Load pillars/laws map JSON.
- Load lock manifest JSON.
- Provide a simple GovernanceStatus snapshot.

No real decision policies or rule evaluation are implemented here yet.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from utils import load_json_config, get_guardian_logger

BASE_DIR = Path(__file__).resolve().parent

COUNCIL_DEFS_PATH = BASE_DIR / "L2_council_definitions.json"
PILLARS_LAWS_MAP_PATH = BASE_DIR / "L2_pillars_laws_map.json"
LOCK_MANIFEST_PATH = BASE_DIR / "L2_lock_manifest.json"

logger = get_guardian_logger("GUSv4.Layer2")


@dataclass
class GovernanceStatus:
    """
    Minimal status snapshot for Layer 2 – Governance Matrix.
    """
    councils_loaded: bool
    laws_map_loaded: bool
    lock_loaded: bool
    locked: bool
    lock_level: str
    councils_count: int
    construction_laws_count: int
    pillars_count: int
    errors: List[str]


def load_governance_status() -> GovernanceStatus:
    """
    Load governance JSON artifacts and return a GovernanceStatus object.

    Skeleton checks:
    - Can we read council definitions?
    - Can we read pillars/laws map?
    - Can we read lock manifest?
    """
    errors: List[str] = []

    # Councils
    council_data: Optional[Dict] = load_json_config(COUNCIL_DEFS_PATH)
    if council_data is None:
        councils_loaded = False
        councils_count = 0
        errors.append("Failed to load L2_council_definitions.json.")
    else:
        councils_loaded = True
        councils = council_data.get("councils", [])
        councils_count = len(councils) if isinstance(councils, list) else 0

    # Laws / pillars map
    map_data: Optional[Dict] = load_json_config(PILLARS_LAWS_MAP_PATH)
    if map_data is None:
        laws_map_loaded = False
        construction_laws_count = 0
        pillars_count = 0
        errors.append("Failed to load L2_pillars_laws_map.json.")
    else:
        laws_map_loaded = True
        construction_laws = map_data.get("construction_laws", {})
        pillars = map_data.get("pillars", {})
        construction_laws_count = len(construction_laws) if isinstance(construction_laws, dict) else 0
        pillars_count = len(pillars) if isinstance(pillars, dict) else 0

    # Lock manifest
    lock_data: Optional[Dict] = load_json_config(LOCK_MANIFEST_PATH)
    if lock_data is None:
        lock_loaded = False
        locked = False
        lock_level = "none"
        errors.append("Failed to load L2_lock_manifest.json.")
    else:
        lock_loaded = True
        locked = bool(lock_data.get("locked", False))
        lock_level = str(lock_data.get("lock_level", "none"))

    if errors:
        logger.warning("Governance Layer status loaded with issues: %s", "; ".join(errors))
    else:
        logger.info("Governance Layer status loaded successfully (councils + map + lock).")

    return GovernanceStatus(
        councils_loaded=councils_loaded,
        laws_map_loaded=laws_map_loaded,
        lock_loaded=lock_loaded,
        locked=locked,
        lock_level=lock_level,
        councils_count=councils_count,
        construction_laws_count=construction_laws_count,
        pillars_count=pillars_count,
        errors=errors,
    )


def is_governance_locked() -> bool:
    """
    Convenience wrapper for higher layers.

    - Returns True if the governance lock manifest says locked=True.
    - Returns False if lock data is missing or cannot be read.
    """
    status = load_governance_status()
    return status.locked
