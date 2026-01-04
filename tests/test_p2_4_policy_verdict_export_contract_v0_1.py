from __future__ import annotations

from layer8_execution.execution_runtime_v0_1 import ExecutionRuntimeV0_1
from layer8_execution.execution_export_v0_1 import export_execution_record


def _decision(*, verdict: str = "ALLOW", action: str = "NOOP", decision_hash: str = "H1", params=None):
    return {
        "decision_id": "D1",
        "verdict": verdict,
        "authorized_action": action,
        "parameters": params or {},
        "decision_hash": decision_hash,
        "actor_id": "A1",
    }


def test_export_includes_policy_verdict_and_is_json_safe():
    rt = ExecutionRuntimeV0_1()
    rec = rt.execute(_decision(params={"action": "do", "target": "t"}))
    out = export_execution_record(rec)

    assert "policy_verdict" in out
    pv = out["policy_verdict"]
    assert isinstance(pv, dict)

    # Minimal shape contract (fail-closed but not over-specified)
    for k in ("code", "summary"):
        assert k in pv


def test_export_deterministic_same_record_same_output():
    rt = ExecutionRuntimeV0_1()
    rec = rt.execute(_decision(decision_hash="HEX-D1", params={"x": 1, "y": 2}))
    out1 = export_execution_record(rec)
    out2 = export_execution_record(rec)
    assert out1 == out2


def test_policy_verdict_deny_blocks_and_exports_policy_verdict():
    rt = ExecutionRuntimeV0_1()
    rec = rt.execute(_decision(params={"deny": True}))
    out = export_execution_record(rec)

    assert out["result"]["status"] == "BLOCKED"
    assert isinstance(out.get("policy_verdict"), dict)
    assert out["policy_verdict"].get("code") == "DENY"
