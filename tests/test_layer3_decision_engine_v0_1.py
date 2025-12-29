from layer3_decision_engine.L3_decision_engine_v0_1 import run_decision


def test_l3_decision_engine_minimal_happy_path():
    context = {
        "decision_id": "TEST-001",
        "requested_action": "noop",
        "layer_origin": 1,
    }

    result = run_decision(context)

    assert result.ok is True
    assert result.status == "approved"
    assert result.decision is not None
    assert result.decision["decision_id"] == "TEST-001"
    assert result.decision["status"] == "approved"
