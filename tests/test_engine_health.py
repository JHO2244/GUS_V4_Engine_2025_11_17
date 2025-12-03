from __future__ import annotations

from types import SimpleNamespace

import gus_engine_health


def test_engine_health_ok(monkeypatch):
    # Simulate a clean Layer-1 run.
    monkeypatch.setattr("gus_engine_health.verify_integrity", lambda: (True, []))

    data = gus_engine_health.get_engine_health_as_dict()
    assert data["overall_ok"] is True
    assert "L1_integrity_core" in data["layers"]
    l1 = data["layers"]["L1_integrity_core"]
    assert l1["engine_ok"] is True
    assert l1["reason"] == "ok"


def test_engine_health_failure(monkeypatch):
    # Simulate a manifest/hash failure with a custom reason.
    fake_issue = SimpleNamespace(reason="hash mismatch in L1")
    monkeypatch.setattr(
        "gus_engine_health.verify_integrity",
        lambda: (False, [fake_issue]),
    )

    data = gus_engine_health.get_engine_health_summary()
    assert data["overall_ok"] is False
    l1 = data["layers"]["L1_integrity_core"]
    assert l1["engine_ok"] is False
    assert "hash mismatch" in l1["reason"]
