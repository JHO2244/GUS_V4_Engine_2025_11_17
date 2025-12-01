from layer2_governance_matrix.L2_governance_core_stub import (
    GovernanceStatus,
    load_governance_status,
    verify_governance,
)


def test_load_governance_status_returns_status_object():
    status = load_governance_status()
    assert isinstance(status, GovernanceStatus)

    # basic structural expectations
    assert isinstance(status.councils_count, int)
    assert isinstance(status.pillars_count, int)
    assert isinstance(status.construction_laws_count, int)
    assert isinstance(status.errors, list)


def test_verify_governance_returns_bool_and_is_true_for_default_config():
    result = verify_governance()
    assert isinstance(result, bool)
    # With the shipped config, this should be True
    assert result is True

def verify_governance() -> bool:
    """
    Minimal verification stub for Layer 2.
    Returns True if there are no errors in the governance status.
    """
    status = load_governance_status()
    return bool(status.errors == [])