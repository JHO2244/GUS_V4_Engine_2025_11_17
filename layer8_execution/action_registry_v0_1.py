""""
GUS v4.0 — L8 Execution Layer
Action Registry v0.1

Purpose:
- Deterministic allow-list of executable actions.
- Execution Layer must never execute actions not registered here.

Guardian constraints:
- No side effects in L8-2 (non-IO NOOP only).
- Deterministic constants only.
- L8-5: Declared IOO contract (channels must be declared and validated).
"""

from __future__ import annotations

from typing import Final, Mapping, Any, Tuple


# Minimal deterministic registry (v0.1)
# Expand later under controlled milestones.
ACTION_REGISTRY: Final[Mapping[str, Mapping[str, Any]]] = {
    "NOOP": {
        "description": "No operation. Deterministic placeholder action.",
        "declared_channels": (),
        "side_effects": False,
        "version": "0.1",
    },
}


def is_action_allowed(action: str) -> bool:
    """Return True iff action exists in the deterministic allow-list."""
    return isinstance(action, str) and action in ACTION_REGISTRY



def get_declared_side_effect_channels(action: str) -> Tuple[str, ...]:
    """
    Return validated declared side-effect channels for an action.

    Fail-close: raises ValueError if the registry metadata is invalid.
    """
    if not is_action_allowed(action):
        raise ValueError(f"Action not allowed: {action}")

    meta = ACTION_REGISTRY[action]
    channels = meta.get("declared_channels")
    if not isinstance(channels, tuple):
        raise ValueError(f"Action {action} declared_channels must be a tuple")

    for ch in channels:
        if not isinstance(ch, str) or not ch.strip():
            raise ValueError(f"Action {action} has invalid channel entry: {ch!r}")

    side_effects = meta.get("side_effects")
    if not isinstance(side_effects, bool):
        raise ValueError(f"Action {action} side_effects must be bool")

    if side_effects != (len(channels) > 0):
        raise ValueError(f"Action {action} side_effects must match declared_channels emptiness")

    return channels
