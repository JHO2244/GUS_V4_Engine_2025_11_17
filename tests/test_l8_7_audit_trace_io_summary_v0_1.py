from __future__ import annotations

from layer8_execution.execution_runtime_v0_1 import ExecutionRuntimeV0_1
import layer8_execution.action_registry_v0_1 as registry


def _decision(verdict: str, action: str, decision_hash: str):
    return {
        "decision_id": "d1",
        "verdict": verdict,
        "authorized_action": action,
        "parameters": {},
        "decision_hash": decision_hash,
    }


def test_audit_trace_declared_emitted_summary_noop_success() -> None:
    rt = ExecutionRuntimeV0_1()
    rec = rt.execute(_decision(verdict="ALLOW", action="NOOP", decision_hash="H-AUD-1"))

    assert rec.result.status == "SUCCESS"
    at = rec.audit_trace
    assert at["declared_channels"] == ()
    assert at["emitted_channels"] == ()
    assert at["emitted_count"] == 0


def test_audit_trace_declared_emitted_summary_registry_invalid_blocks(monkeypatch) -> None:
    rt = ExecutionRuntimeV0_1()

    bad = dict(registry.ACTION_REGISTRY)
    bad["NOOP"] = dict(bad["NOOP"])
    bad["NOOP"]["declared_channels"] = ["log"]  # invalid: must be tuple
    monkeypatch.setattr(registry, "ACTION_REGISTRY", bad, raising=True)

    rec = rt.execute(_decision(verdict="ALLOW", action="NOOP", decision_hash="H-AUD-2"))

    assert rec.result.status == "BLOCKED"
    assert rec.result.note == "Registry metadata invalid"
    at = rec.audit_trace
    assert at["declared_channels"] == ()
    assert at["emitted_channels"] == ()
    assert at["emitted_count"] == 0