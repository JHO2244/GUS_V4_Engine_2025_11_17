# Placeholder for integrity checks
"""
GUS v4 – Layer 1 Hash Spine stub.

Skeleton behavior:
- Provide stable access to the chain log path used by the integrity layer.
- Reserve function names for future hash-chain operations.

No real chain logic is implemented here yet.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from utils import get_guardian_logger

logger = get_guardian_logger("GUSv4.Layer1.HashSpine")

BASE_DIR = Path(__file__).resolve().parent
CHAIN_DIR = BASE_DIR / "chain"
CHAIN_LOG_FILE = CHAIN_DIR / "gus_chain_log_placeholder.txt"


def get_chain_log_path() -> Path:
    """
    Return the path to the chain log placeholder.

    Higher layers can rely on this path being stable, even before
    real chain logic is implemented.
    """
    return CHAIN_LOG_FILE


def append_chain_event_stub(event: str) -> Optional[Path]:
    """
    Placeholder for future hash-chain append function.

    In skeleton mode:
    - It logs that an event would be written.
    - It does NOT write anything to disk.
    - It returns the log path for informational purposes.
    """
    logger.info("Hash spine stub received event (not persisted): %s", event)
    return CHAIN_LOG_FILE
