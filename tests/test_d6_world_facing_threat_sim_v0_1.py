from __future__ import annotations

import json
from pathlib import Path

def test_d6_world_facing_threat_sim_shape_and_minimum() -> None:
    p = Path("gdvs/d6_world/world_facing_threat_sim_v0_1.json")
    assert p.exists()

    data = json.loads(p.read_text(encoding="utf-8"))

    allowed_top = {"created_at_utc","d6_version","schema_version","simulations"}
    assert set(data.keys()) == allowed_top
    assert data["d6_version"] == "0.1"
    assert data["schema_version"] == "0.1"
    assert isinstance(data["created_at_utc"], str) and data["created_at_utc"].endswith("Z")

    sims = data["simulations"]
    assert isinstance(sims, list) and len(sims) >= 4

    allowed_sim = {"id","name","vector","expected_behavior","telemetry","containment","recovery"}
    ids = set()
    for s in sims:
        assert set(s.keys()) == allowed_sim
        assert isinstance(s["id"], str) and s["id"].startswith("D6-S")
        assert s["id"] not in ids
        ids.add(s["id"])

        for k in ("name","vector"):
            assert isinstance(s[k], str) and s[k].strip()

        for k in ("expected_behavior","telemetry","containment","recovery"):
            items = s[k]
            assert isinstance(items, list)
            assert len(items) >= 2
