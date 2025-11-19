"""
Basic smoke test for Layer 1 Integrity Core stub.
"""

from layer1_integrity_core.L1_integrity_core_stub import (
    IntegrityStatus,
    load_integrity_status,
    verify_integrity,
)
from layer1_integrity_core.L1_hash_spine_stub import get_chain_log_path, append_chain_event_stub


def test_load_integrity_status_returns_object():
    status = load_integrity_status()
    assert isinstance(status, IntegrityStatus)
    assert isinstance(status.errors, list)


def test_verify_integrity_runs():
    result = verify_integrity()
    assert isinstance(result, bool)


def test_hash_spine_stub_paths():
    log_path = get_chain_log_path()
    assert log_path.name.endswith(".txt")
    returned = append_chain_event_stub("TEST_EVENT")
    assert returned == log_path
