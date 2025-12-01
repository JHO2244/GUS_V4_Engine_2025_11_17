"""
L2_governance_core_stub.py
Guardian-aligned bridge for Layer 2 governance.

For v4.0 this simply re-exports the static governance stub so that
tests and future code can import from `L2_governance_core_stub`
without caring about the underlying implementation.
"""

from .L2_governance_static_stub import (
    GovernanceStatus,
    load_governance_status,
    verify_governance,
)

__all__ = ["GovernanceStatus", "load_governance_status", "verify_governance"]
