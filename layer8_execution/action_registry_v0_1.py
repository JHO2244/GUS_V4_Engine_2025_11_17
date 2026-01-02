"""
GUS v4.0 — L8 Execution Layer
Action Registry v0.1

Purpose:
- Deterministic allow-list of executable actions.
- Execution Layer must never execute actions not registered here.

Guardian constraints:
- L8-2 baseline: NOOP only.
- L8-4: Side effects are allowed ONLY via declared channels (Declared IO only).
"""

from __future__ import annotations

from typing import Final, Mapping, Any


# Minimal deterministic registry (v0.1)
# Expand later under controlled milestones.
ACTION_REGISTRY: Final[Mapping[str, Mapping[str, Any]]] = {
    "NOOP": {
        "description": "No operation. Deterministic placeholder action.",
        "version": "0.1",
        # L8-4: declared IO only. NOOP declares none.
        "declared_side_effect_channels": (),
    },
}


def is_action_allowed(action: str) -> bool:
    """Return True iff action exists in the deterministic allow-list."""
    return isinstance(action, str) and action in ACTION_REGISTRY


def get_declared_side_effect_channels(action: str) -> tuple[str, ...]:
    """Return declared side-effect channels for an allow-listed action."""
    if not is_action_allowed(action):
        return ()
    channels = ACTION_REGISTRY[action].get("declared_side_effect_channels", ())
    return tuple(channels) if isinstance(channels, (list, tuple)) else ()
