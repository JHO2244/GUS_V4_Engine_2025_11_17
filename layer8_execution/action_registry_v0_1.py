"""
GUS v4.0 — L8 Execution Layer
Action Registry v0.1

Purpose:
- Deterministic allow-list of executable actions.
- Execution Layer must never execute actions not registered here.

Guardian constraints:
- No side effects in L8-2 (NOOP only).
- Deterministic constants only.
"""

from __future__ import annotations

from typing import Final, Mapping, Any


# Minimal deterministic registry (v0.1)
# Expand later under controlled milestones.
ACTION_REGISTRY: Final[Mapping[str, Mapping[str, Any]]] = {
    "NOOP": {
        "description": "No operation. Deterministic placeholder action.",
        "side_effects": False,
        "version": "0.1",
    },
}


def is_action_allowed(action: str) -> bool:
    """Return True iff action exists in the deterministic allow-list."""
    return isinstance(action, str) and action in ACTION_REGISTRY
