"""
GUS v4 – Layer 1 Integrity Core stub

This module provides a minimal, test-aligned stub for the L1 integrity layer.
It is intentionally simple: the real implementation can later plug in JSON-
backed state, hash-chain verification, etc., without changing the public API.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class IntegrityStatus:
    """
    Lightweight container used by the L1 integrity core to report status.

    Attributes
    ----------
    code:
        Short status code, e.g. "ok" or "error".
    errors:
        List of human-readable error messages. Empty list means "no errors".
    """
    code: str = "ok"
    errors: List[str] = field(default_factory=list)


def load_integrity_status() -> IntegrityStatus:
    """
    Stub loader for the current integrity status.

    For the v4 skeleton this simply returns an "all good" status object.
    Later this can be extended to read from a lock manifest, chain log, etc.
    """
    # Skeleton behaviour: system starts in an OK state with no recorded errors.
    return IntegrityStatus(code="ok", errors=[])


def verify_integrity() -> bool:
    """
    Run a minimal integrity check and return a boolean result.

    The tests only require that:
      * verify_integrity() returns a bool
      * it can be called without raising exceptions

    In this stub we delegate to `load_integrity_status()` and treat "no errors"
    as True and any recorded errors as False.
    """
    status = load_integrity_status()

    # Ensure we always have a list for `.errors`, even if someone mis-constructs
    # IntegrityStatus elsewhere.
    if status.errors is None:
        status.errors = []

    return len(status.errors) == 0
