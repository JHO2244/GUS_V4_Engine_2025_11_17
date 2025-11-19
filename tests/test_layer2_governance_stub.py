"""
Basic smoke test for Layer 2 Governance Matrix stub.
"""

from layer2_governance_matrix.L2_governance_static_stub import (
    GovernanceStatus,
    load_governance_status,
    is_governance_locked,
)


def test_load_governance_status_returns_object():
    status = load_governance_status()
    assert isinstance(status, GovernanceStatus)
    assert isinstance(status.errors, list)


def test_is_governance_locked_runs():
    locked = is_governance_locked()
    assert isinstance(locked, bool)
