from layer8_execution.execution_runtime_v0_1 import ExecutionRuntimeV0_1


def _decision(verdict="ALLOW", action="NOOP", params=None, decision_hash="abc123", decision_id="d1"):
    return {
        "decision_id": decision_id,
        "verdict": verdict,
        "authorized_action": action,
        "parameters": params if params is not None else {},
        "decision_hash": decision_hash,
    }


def test_allow_noop_success_deterministic():
    rt = ExecutionRuntimeV0_1()
    d = _decision(verdict="ALLOW", action="NOOP", decision_hash="H1")
    rec1 = rt.execute(d)
    rec2 = rt.execute(d)
    assert rec1.result.status == "SUCCESS"
    assert rec1.record_hash == rec2.record_hash  # determinism


def test_non_allow_blocks():
    rt = ExecutionRuntimeV0_1()
    d = _decision(verdict="DENY", action="NOOP", decision_hash="H2")
    rec = rt.execute(d)
    assert rec.result.status == "BLOCKED"


def test_unknown_action_blocks():
    rt = ExecutionRuntimeV0_1()
    d = _decision(verdict="ALLOW", action="DO_SOMETHING", decision_hash="H3")
    rec = rt.execute(d)
    assert rec.result.status == "BLOCKED"


def test_missing_fields_fail_hard():
    rt = ExecutionRuntimeV0_1()
    d = _decision()
    d.pop("decision_hash")
    try:
        rt.execute(d)
        assert False, "Expected ValueError"
    except ValueError:
        assert True
