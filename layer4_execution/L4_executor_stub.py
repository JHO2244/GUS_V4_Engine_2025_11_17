# Placeholder: invokes allowed actions
from __future__ import annotations

"""
GUS v4 – Layer 4 Execution stub.

Skeleton responsibilities:
- Load the L4 action registry.
- Load the L4 lock manifest.
- Expose an L4ExecutionStatus snapshot.
- Provide a safe execute_action() that logs only and does NOT perform real execution.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from utils import load_json_config, get_guardian_logger

BASE_DIR = Path(__file__).resolve().parent
REGISTRY_PATH = BASE_DIR / "L4_action_registry.json"
LOCK_MANIFEST_PATH = BASE_DIR / "L4_lock_manifest.json"

logger = get_guardian_logger("GUSv4.Layer4")


@dataclass
class L4ExecutionStatus:
    """
    Minimal status snapshot for Layer 4 – Execution.
    """
    registry_loaded: bool
    actions_count: int
    lock_loaded: bool
    locked: bool
    lock_level: str
    errors: List[str]


def load_execution_status() -> L4ExecutionStatus:
    """
    Load the action registry and lock manifest, returning an L4ExecutionStatus.
    """
    errors: List[str] = []

    # Registry
    registry_data: Optional[Dict[str, Any]] = load_json_config(REGISTRY_PATH)
    if registry_data is None:
        registry_loaded = False
        actions_count = 0
        errors.append("Failed to load L4_action_registry.json.")
    else:
        registry_loaded = True
        actions = registry_data.get("actions", {})
        actions_count = len(actions) if isinstance(actions, dict) else 0

    # Lock manifest
    lock_data: Optional[Dict[str, Any]] = load_json_config(LOCK_MANIFEST_PATH)
    if lock_data is None:
        lock_loaded = False
        locked = False
        lock_level = "none"
        errors.append("Failed to load L4_lock_manifest.json.")
    else:
        lock_loaded = True
        locked = bool(lock_data.get("locked", False))
        lock_level = str(lock_data.get("lock_level", "none"))

    if errors:
        logger.warning("Execution Layer status loaded with issues: %s", "; ".join(errors))
    else:
        logger.info(
            "Execution Layer status loaded successfully (actions=%s, locked=%s, lock_level=%s).",
            actions_count,
            locked,
            lock_level,
        )

    return L4ExecutionStatus(
        registry_loaded=registry_loaded,
        actions_count=actions_count,
        lock_loaded=lock_loaded,
        locked=locked,
        lock_level=lock_level,
        errors=errors,
    )


def execute_action(action_id: str, payload: Dict[str, Any]) -> bool:
    """
    Skeleton executor.

    Behavior in skeleton mode:
    - If Layer 4 is locked → log & return False.
    - If action_id is unknown → log & return False.
    - Otherwise → log that we *would* execute and return True (no real side effects).
    """
    status = load_execution_status()

    if not status.registry_loaded:
        logger.warning("execute_action(%s) aborted: registry not loaded.", action_id)
        return False

    if status.locked:
        logger.warning(
            "execute_action(%s) blocked: Layer 4 is locked (lock_level=%s).",
            action_id,
            status.lock_level,
        )
        return False

    registry_data: Optional[Dict[str, Any]] = load_json_config(REGISTRY_PATH)
    if registry_data is None:
        logger.warning("execute_action(%s) aborted: registry reload failed.", action_id)
        return False

    actions = registry_data.get("actions", {})
    if action_id not in actions:
        logger.warning("execute_action(%s) aborted: unknown action_id.", action_id)
        return False

    logger.info(
        "execute_action(%s) called in skeleton mode with payload_keys=%s (no real execution).",
        action_id,
        list(payload.keys()),
    )
    return True
