"""
GDVS State Machine v0.1
Authoritative integrity/security spine for GUS.

Rules:
- Fail-closed
- Deterministic
- No implicit transitions
"""

from enum import Enum, auto
from dataclasses import dataclass


class GDVSState(Enum):
    INIT = auto()
    D1_STRUCTURAL = auto()
    D2_DETERMINISM = auto()
    D3_SECURITY = auto()
    D4_POLICY = auto()
    D5_PRIVACY = auto()
    D6_WORLD = auto()
    D7_FUTURE_AI = auto()
    D8_OPERATIONAL = auto()
    SEALED = auto()
    LOCKED = auto()


@dataclass(frozen=True)
class GDVSContext:
    state: GDVSState
    head_commit: str
    head_sealed: bool


class GDVSViolation(Exception):
    pass


def assert_transition(current: GDVSState, target: GDVSState) -> None:
    """Enforce strict forward-only GDVS transitions."""
    allowed = {
        GDVSState.INIT: GDVSState.D1_STRUCTURAL,
        GDVSState.D1_STRUCTURAL: GDVSState.D2_DETERMINISM,
        GDVSState.D2_DETERMINISM: GDVSState.D3_SECURITY,
        GDVSState.D3_SECURITY: GDVSState.D4_POLICY,
        GDVSState.D4_POLICY: GDVSState.D5_PRIVACY,
        GDVSState.D5_PRIVACY: GDVSState.D6_WORLD,
        GDVSState.D6_WORLD: GDVSState.D7_FUTURE_AI,
        GDVSState.D7_FUTURE_AI: GDVSState.D8_OPERATIONAL,
        GDVSState.D8_OPERATIONAL: GDVSState.SEALED,
        GDVSState.SEALED: GDVSState.LOCKED,
    }
    if allowed.get(current) != target:
        raise GDVSViolation(f"Invalid GDVS transition: {current.name} -> {target.name}")
