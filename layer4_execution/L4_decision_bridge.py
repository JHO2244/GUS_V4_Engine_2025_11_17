from __future__ import annotations

"""
GUS v4 – Layer 4 Decision Bridge.

Purpose:
- Accept a Layer 3 decision object.
- Enforce: only APPROVED decisions may proceed.
- Map decision.requested_action -> L4 action_id (skeleton mapping).
- Call execute_action() safely (no real side effects).
"""

from typing import Any, Dict

from utils import get_guardian_logger
from layer4_execution.L4_executor_stub import execute_action

logger = get_guardian_logger("GUSv4.Layer4.Bridge")


_ACTION_MAP = {
    "noop": "PING",
    "ping": "PING",
}


def execute_decision(decision: Dict[str, Any], payload: Dict[str, Any] | None = None) -> bool:
    """
    Execute an approved decision via Layer 4.

    Returns True if skeleton execution accepted; False otherwise.
    """
    if payload is None:
        payload = {}

    if not isinstance(decision, dict):
        raise TypeError("decision must be a dict")

    status = str(decision.get("status", "")).lower()
    if status != "approved":
        logger.warning("execute_decision blocked: decision status is %s (must be approved).", status)
        return False

    requested_action = str(decision.get("requested_action", "")).strip().lower()
    action_id = _ACTION_MAP.get(requested_action)

    if not action_id:
        logger.warning("execute_decision blocked: no action mapping for requested_action=%s", requested_action)
        return False

    logger.info("execute_decision: mapped requested_action=%s to action_id=%s", requested_action, action_id)
    return execute_action(action_id, payload)
