"""
Basic smoke test for Layer 0 UAM stub.
"""

from layer0_uam_v4.L0_uam_core_stub import load_uam_status, is_uam_locked, UAMStatus


def test_load_uam_status_returns_object():
    status = load_uam_status()
    assert isinstance(status, UAMStatus)
    # lock_level should always be a string
    assert isinstance(status.lock_level, str)


def test_is_uam_locked_runs():
    # This should not raise, regardless of manifest contents
    locked = is_uam_locked()
    assert isinstance(locked, bool)
