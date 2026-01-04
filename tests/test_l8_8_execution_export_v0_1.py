from __future__ import annotations

from layer8_execution.execution_export_v0_1 import export_execution_record
from layer8_execution.execution_runtime_v0_1 import ExecutionRuntimeV0_1


def _decision(*, verdict: str, action: str, decision_hash: str = "H1"):
    return {
        "decision_id": "d1",
        "verdict": verdict,
        "authorized_action": action,
        "parameters": {},
        "decision_hash": decision_hash,
    }


def test_export_execution_record_json_safe_and_has_contract_fields() -> None:
    rt = ExecutionRuntimeV0_1()
    rec = rt.execute(_decision(verdict="ALLOW", action="NOOP", decision_hash="HEX-1"))

    out = export_execution_record(rec)

    assert set(out.keys()) == {
        "execution_id",
        "decision_hash",
        "result",
        "audit_trace",
        "side_effect_events",
        "policy_verdict",
        "record_hash",
    }

    # JSON-safe primitives only (recursive)
    def _is_json_safe(x):
        if x is None or isinstance(x, (str, int, float, bool)):
            return True
        if isinstance(x, list):
            return all(_is_json_safe(i) for i in x)
        if isinstance(x, dict):
            return all(isinstance(k, str) and _is_json_safe(v) for k, v in x.items())
        return False

    assert _is_json_safe(out)
