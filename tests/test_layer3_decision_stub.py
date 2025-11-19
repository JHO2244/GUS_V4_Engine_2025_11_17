"""
Basic smoke test for Layer 3 Decision Engine stub.
"""

from layer3_decision_engine.L3_decision_matrix_stub import (
    DecisionEngineStatus,
    load_decision_engine_status,
)
from layer3_decision_engine.L3_context_evaluator_stub import evaluate_context
from layer3_decision_engine.L3_authorization_stub import authorize_decision


def test_load_decision_engine_status_returns_object():
    status = load_decision_engine_status()
    assert isinstance(status, DecisionEngineStatus)
    assert isinstance(status.errors, list)


def test_context_evaluator_runs():
    ok = evaluate_context({"sample": "value"})
    assert isinstance(ok, bool)


def test_authorization_stub_runs():
    ok = authorize_decision({"id": "D-TEST"})
    assert isinstance(ok, bool)
