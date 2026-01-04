import pytest

from layer8_execution.execution_runtime_v0_1 import ExecutionRuntimeV0_1


def _decision(*, verdict: str, action: str, params: dict, decision_id: str = "D1") -> dict:
    # decision_hash only needs to be a non-empty string for this layer
    return {
        "decision_id": decision_id,
        "verdict": verdict,
        "authorized_action": action,
        "parameters": params,
        "decision_hash": "H1",
        "actor_id": "X",
    }


def test_policy_deny_blocks_execution():
    rt = ExecutionRuntimeV0_1()
    rec = rt.execute(_decision(verdict="ALLOW", action="NOOP", params={"deny": True}))
    assert rec.result.status == "BLOCKED"
    assert rec.policy_verdict is not None
    assert rec.policy_verdict["code"] == "DENY"


def test_policy_allow_attaches_verdict_and_allows_noop():
    rt = ExecutionRuntimeV0_1()
    rec = rt.execute(_decision(verdict="ALLOW", action="NOOP", params={"action": "do", "target": "t"}))
    assert rec.result.status == "SUCCESS"
    assert rec.policy_verdict is not None
    assert rec.policy_verdict["code"] == "ALLOW"
