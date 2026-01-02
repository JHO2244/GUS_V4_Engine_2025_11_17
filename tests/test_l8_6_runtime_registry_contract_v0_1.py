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


def test_runtime_fail_closed_if_noop_channels_not_tuple(monkeypatch):
    rt = ExecutionRuntimeV0_1()
    orig = registry.ACTION_REGISTRY
    bad = dict(orig)
    bad["NOOP"] = dict(bad["NOOP"])
    bad["NOOP"]["declared_channels"] = ["log"]  # invalid: must be tuple
    monkeypatch.setattr(registry, "ACTION_REGISTRY", bad, raising=True)

    rec = rt.execute(_decision(verdict="ALLOW", action="NOOP", decision_hash="HB-1"))
    assert rec.result.status == "BLOCKED"
    assert rec.result.note == "Registry metadata invalid"
    assert rec.side_effect_events == ()


def test_runtime_fail_closed_if_noop_side_effects_mismatch(monkeypatch):
    rt = ExecutionRuntimeV0_1()
    orig = registry.ACTION_REGISTRY
    bad = dict(orig)
    bad["NOOP"] = dict(bad["NOOP"])
    bad["NOOP"]["declared_channels"] = ()
    bad["NOOP"]["side_effects"] = True  # invalid: must match empty
    monkeypatch.setattr(registry, "ACTION_REGISTRY", bad, raising=True)

    rec = rt.execute(_decision(verdict="ALLOW", action="NOOP", decision_hash="HB-2"))
    assert rec.result.status == "BLOCKED"
    assert rec.result.note == "Registry metadata invalid"
    assert rec.side_effect_events == ()
