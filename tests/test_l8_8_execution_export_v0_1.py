from __future__ import annotations

from typing import Any, Mapping

from layer8_execution.execution_export_v0_1 import export_execution_record
from layer8_execution.execution_runtime_v0_1 import ExecutionRuntimeV0_1


def _decision(*, verdict: str, action: str, decision_hash: str) -> Mapping[str, Any]:
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
        "record_hash",
    }

    # JSON-safe expectations
    assert isinstance(out["execution_id"], str)
    assert isinstance(out["decision_hash"], str)
    assert isinstance(out["record_hash"], str)

    assert isinstance(out["result"], dict)
    assert isinstance(out["audit_trace"], dict)
    assert isinstance(out["side_effect_events"], list)

    # Ensure tuples have become lists (declared_channels is a tuple in runtime)
    if "declared_channels" in out["audit_trace"]:
        assert isinstance(out["audit_trace"]["declared_channels"], list)
