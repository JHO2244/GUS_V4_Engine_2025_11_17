from __future__ import annotations

import json
from pathlib import Path

def test_d6_world_facing_threat_sim_shape_is_strict() -> None:
    p = Path("gdvs/d6_world/world_facing_threat_sim_v0_1.json")
    assert p.exists(), "Missing canonical D6 artifact at gdvs/d6_world/world_facing_threat_sim_v0_1.json"

    data = json.loads(p.read_text(encoding="utf-8"))

    allowed_top = {"created_at_utc", "d6_version", "schema_version", "simulations"}
    assert set(data.keys()) == allowed_top, f"Top-level keys must be exactly {sorted(allowed_top)}"
    assert data["d6_version"] == "0.1"
    assert data["schema_version"] == "0.1"
    assert isinstance(data["created_at_utc"], str) and data["created_at_utc"].endswith("Z")

    sims = data["simulations"]
    assert isinstance(sims, list), "simulations must be a list"
    # scaffold may start empty; enforceable content comes next step
