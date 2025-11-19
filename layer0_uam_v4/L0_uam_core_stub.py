# Placeholder for UAM logic wrapper
"""
GUS v4 – Layer 0 UAM core stub.

Responsibility (skeleton mode):
- Load the UAM schema and lock manifest JSON files.
- Return a simple status snapshot to higher layers.
- Log whether Layer 0 is structurally OK.

No UAM logic or rating rules are implemented here yet.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List

from utils import load_json_config, get_guardian_logger

# Base directory for this layer (layer0_uam_v4)
BASE_DIR = Path(__file__).resolve().parent

SCHEMA_PATH = BASE_DIR / "L0_uam_schema.json"
LOCK_MANIFEST_PATH = BASE_DIR / "L0_uam_lock_manifest.json"

logger = get_guardian_logger("GUSv4.Layer0")


@dataclass
class UAMStatus:
    """
    Minimal status snapshot for UAM Layer 0.

    This is intentionally small and conservative. More fields can be
    added later as the UAM v4 spec is fully wired in.
    """
    schema_loaded: bool
    lock_loaded: bool
    locked: bool
    lock_level: str
    errors: List[str]


def load_uam_status() -> UAMStatus:
    """
    Load the UAM schema + lock manifest and return a UAMStatus object.

    Skeleton behavior:
    - If a file cannot be read or parsed, we record an error but do not raise.
    - If the lock manifest is missing, we default to unlocked / 'none'.
    """
    errors: List[str] = []

    # Load schema
    schema = load_json_config(SCHEMA_PATH)
    if schema is None:
        schema_ok = False
        errors.append("Failed to load UAM schema JSON.")
    else:
        schema_ok = True

    # Load lock manifest
    lock = load_json_config(LOCK_MANIFEST_PATH)
    if lock is None:
        lock_ok = False
        locked = False
        lock_level = "none"
        errors.append("Failed to load UAM lock manifest JSON.")
    else:
        lock_ok = True
        locked = bool(lock.get("locked", False))
        lock_level = str(lock.get("lock_level", "none"))

    if errors:
        logger.warning("UAM Layer 0 status loaded with issues: %s", "; ".join(errors))
    else:
        logger.info("UAM Layer 0 status loaded successfully (schema + lock manifest).")

    return UAMStatus(
        schema_loaded=schema_ok,
        lock_loaded=lock_ok,
        locked=locked,
        lock_level=lock_level,
        errors=errors,
    )


def is_uam_locked() -> bool:
    """
    Convenience wrapper for higher layers.

    - Returns True if the lock manifest says locked=True.
    - Returns False if the lock manifest is missing or cannot be read.
    """
    status = load_uam_status()
    return status.locked
