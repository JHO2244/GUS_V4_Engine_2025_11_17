# Placeholder for action authorization gates
from __future__ import annotations

"""
GUS v4 – Authorization stub.

Skeleton logic only: always "allow" decisions.
"""

from typing import Dict, Any

from utils import get_guardian_logger

logger = get_guardian_logger("GUSv4.Layer3.Auth")


def authorize_decision(decision: Dict[str, Any]) -> bool:
    """
    Placeholder authorization check.

    For now:
    - Logs that it was called.
    - Always returns True (authorized).
    """
    logger.info("authorize_decision() called in skeleton mode with keys=%s", list(decision.keys()))
    return True
