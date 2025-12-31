import pytest

def test_run_decision_abort_on_bad_context_type():
    from layer3_decision_engine.L3_decision_matrix_stub import run_decision
    with pytest.raises(TypeError):
        run_decision("not-a-dict", "noop", 1)

def test_run_decision_denies_invalid_layer_origin():
    from layer3_decision_engine.L3_decision_matrix_stub import run_decision
    with pytest.raises(ValueError):
        run_decision({"ok": True}, "noop", 9)
