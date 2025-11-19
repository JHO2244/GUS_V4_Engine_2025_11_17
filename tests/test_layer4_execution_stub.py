"""
Basic smoke tests for Layer 4 Execution stub.
"""

from layer4_execution.L4_executor_stub import (
    L4ExecutionStatus,
    load_execution_status,
    execute_action,
)


def test_load_execution_status_returns_object():
    status = load_execution_status()
    assert isinstance(status, L4ExecutionStatus)
    assert isinstance(status.errors, list)


def test_execute_action_ping_runs():
    ok = execute_action("PING", {"example": "payload"})
    assert isinstance(ok, bool)
