from __future__ import annotations

import json
from pathlib import Path


def test_d7_future_ai_adversarial_reasoning_shape() -> None:
    p = Path("gdvs/d7_future_ai/future_ai_adversarial_reasoning_v0_1.json")
    assert p.exists()

    data = json.loads(p.read_text(encoding="utf-8"))
    allowed_top = {"created_at_utc", "d7_version", "schema_version", "threats"}
    assert set(data.keys()) == allowed_top

    assert data["d7_version"] == "0.1"
    assert data["schema_version"] == "0.1"
    assert isinstance(data["created_at_utc"], str) and data["created_at_utc"].endswith("Z")

    threats = data["threats"]
    assert isinstance(threats, list)

    # For D7 scaffold: allow empty, but each entry must be enforceable if present.
    for t in threats:
        assert set(t.keys()) == {
            "id", "name", "description", "capability_assumption",
            "containment", "detection", "recovery"
        }
        assert isinstance(t["id"], str) and t["id"].strip()
        assert isinstance(t["name"], str) and t["name"].strip()
        assert isinstance(t["description"], str) and t["description"].strip()
        assert isinstance(t["capability_assumption"], str) and t["capability_assumption"].strip()

        for k in ("containment", "detection", "recovery"):
            v = t[k]
            assert isinstance(v, list) and len(v) >= 2
            assert all(isinstance(x, str) and x.strip() for x in v)
