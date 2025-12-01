from layer5_continuity.L5_continuity_stub import (
    ContinuityStatus,
    load_continuity_status,
    verify_continuity,
)


def test_load_continuity_status_returns_object():
    status = load_continuity_status()
    assert isinstance(status, ContinuityStatus)
    assert isinstance(status.errors, list)
    assert isinstance(status.checkpoints_count, int)
    assert isinstance(status.policies_count, int)


def test_verify_continuity_returns_bool_and_true_by_default():
    result = verify_continuity()
    assert isinstance(result, bool)
    assert result is True
