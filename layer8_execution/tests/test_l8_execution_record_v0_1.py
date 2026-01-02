from layer8_execution.execution_runtime_v0_1 import ExecutionRuntimeV0_1


def _decision(verdict="ALLOW", action="NOOP", params=None, decision_hash="abc123", decision_id="d1"):
    return {
        "decision_id": decision_id,
        "verdict": verdict,
        "authorized_action": action,
        "parameters": params if params is not None else {},
        "decision_hash": decision_hash,
    }


def test_execute_always_returns_record():
    rt = ExecutionRuntimeV0_1()
    rec = rt.execute(_decision(verdict="DENY", action="NOOP", decision_hash="H-deny"))
    assert rec.result.status == "BLOCKED"
    assert isinstance(rec.record_hash, str) and len(rec.record_hash) == 64


def test_record_hash_deterministic_same_input():
    rt = ExecutionRuntimeV0_1()
    d = _decision(verdict="ALLOW", action="NOOP", decision_hash="H1")
    r1 = rt.execute(d)
    r2 = rt.execute(d)
    assert r1.record_hash == r2.record_hash
    assert r1.execution_id == r2.execution_id
    assert r1.result.execution_hash == r2.result.execution_hash


def test_record_hash_changes_if_decision_hash_changes():
    rt = ExecutionRuntimeV0_1()
    d1 = _decision(verdict="ALLOW", action="NOOP", decision_hash="H1")
    d2 = _decision(verdict="ALLOW", action="NOOP", decision_hash="H2")
    r1 = rt.execute(d1)
    r2 = rt.execute(d2)
    assert r1.record_hash != r2.record_hash
