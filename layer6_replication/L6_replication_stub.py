"""
L6_replication_stub.py – Layer 6 Replication status stub (GUS v4)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class ReplicationStatus:
    """
    Layer 6 – Replication status stub.

    This is a minimal, static stub that will later be replaced by
    real replication topology + health data.
    """
    code: str = "ok"
    replicas_configured: int = 0
    last_replication_ok: bool = True
    errors: List[str] = field(default_factory=list)


def load_replication_status() -> ReplicationStatus:
    """
    Return a default 'OK' replication status.

    Future version will:
    - Load replication config / topology
    - Check last replication timestamps
    - Populate errors if any checks fail
    """
    return ReplicationStatus()


def verify_replication() -> bool:
    """
    Minimal verification hook for Layer 6.

    For now it only checks:
    - status.code == "ok"
    - no errors present

    This keeps the contract simple while allowing tests + diagnostics
    to treat replication as a first-class layer.
    """
    status = load_replication_status()
    return status.code == "ok" and not status.errors
