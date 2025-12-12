"""
GUS v4 – Layer 5 Continuity Facade

This module exposes a simple, stable API that the rest of the engine and the
tests can rely on:

- ContinuityStatus Enum
- load_continuity_status() → ContinuityStatus
- verify_continuity()      → bool
"""

from __future__ import annotations

from .continuity_manifest_v0_1 import (
    ContinuityStatus,
    check_continuity,
    load_manifest,
    write_manifest,
)

__all__ = [
    "ContinuityStatus",
    "load_manifest",
    "write_manifest",
    "load_continuity_status",
    "verify_continuity",
]


def load_continuity_status() -> ContinuityStatus:
    """
    Lightweight continuity check used by L5–L9 stub tests.

    Default behavior (when no JSON manifest is present on disk):
    - Use the embedded continuity plan.
    - Return ContinuityStatus.OK if it validates.

    This keeps the higher layers green as long as the embedded plan is sane.
    """
    return check_continuity()


def verify_continuity() -> bool:
    """
    Convenience wrapper used by various stubs:

        if not verify_continuity():
            raise RuntimeError("Continuity chain not healthy")

    The tests expect this to return True in the baseline, all-green state.
    """
    return load_continuity_status().ok
