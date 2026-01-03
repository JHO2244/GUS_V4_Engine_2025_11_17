from __future__ import annotations

from layer8_execution.execution_runtime_v0_1 import ExecutionRuntimeV0_1
from layer8_execution.execution_packet_v0_1 import build_execution_packet_v0_1
from dataclasses import replace


def _decision(*, verdict: str, action: str, decision_hash: str):
    return {
        "decision_id": "d1",
        "verdict": verdict,
        "authorized_action": action,
        "parameters": {},
        "decision_hash": decision_hash,
    }


def test_packet_deterministic_same_record_same_packet_hash():
    rt = ExecutionRuntimeV0_1()
    rec = rt.execute(_decision(verdict="ALLOW", action="NOOP", decision_hash="HP-1"))

    p1 = build_execution_packet_v0_1(rec)
    p2 = build_execution_packet_v0_1(rec)

    assert p1 == p2
    assert p1["packet_hash"] == p2["packet_hash"]
    assert p1["record_hash"] == rec.record_hash


def test_packet_hash_changes_if_record_hash_changes(monkeypatch):
    rt = ExecutionRuntimeV0_1()
    rec = rt.execute(_decision(verdict="ALLOW", action="NOOP", decision_hash="HP-2"))

    p1 = build_execution_packet_v0_1(rec)

    # simulate tamper: clone with modified record_hash
    rec2 = replace(rec, record_hash=rec.record_hash + "X")

    p2 = build_execution_packet_v0_1(rec2)

    assert p1["packet_hash"] != p2["packet_hash"]
    assert p2["record_hash"] != p1["record_hash"]
