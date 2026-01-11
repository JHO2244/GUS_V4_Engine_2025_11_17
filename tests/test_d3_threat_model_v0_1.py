from __future__ import annotations

import json
from pathlib import Path


def test_d3_threat_model_exists_and_is_strict() -> None:
    path = Path("gdvs/d3_security/threat_model_v0_1.json")
    assert path.exists(), "Missing canonical D3 threat model at gdvs/d3_security/threat_model_v0_1.json"

    raw = path.read_text(encoding="utf-8")
    data = json.loads(raw)

    # ---- strict top-level keys (no drift) ----
    allowed_top = {"d3_version", "schema_version", "created_at_utc", "threats"}
    assert set(data.keys()) == allowed_top, f"Top-level keys must be exactly {sorted(allowed_top)}"

    assert data["d3_version"] == "0.1"
    assert data["schema_version"] == "0.1"
    assert isinstance(data["created_at_utc"], str) and data["created_at_utc"].endswith("Z")

    threats = data["threats"]
    assert isinstance(threats, list) and len(threats) == 4

    allowed_threat = {"id", "name", "description", "detection", "containment", "recovery"}

    ids = set()
    for t in threats:
        assert set(t.keys()) == allowed_threat, f"Threat keys must be exactly {sorted(allowed_threat)}"
        assert isinstance(t["id"], str) and t["id"].startswith("D3-T")
        assert t["id"] not in ids, "Threat IDs must be unique"
        ids.add(t["id"])

        for field in ("name", "description"):
            assert isinstance(t[field], str) and t[field].strip()

        # ---- LAW: no empty controls ----
        for field in ("detection", "containment", "recovery"):
            items = t[field]
            assert isinstance(items, list), f"{t['id']}:{field} must be a list"
            assert len(items) >= 2, f"{t['id']}:{field} must have >=2 controls (no placeholders)"
            for item in items:
                assert isinstance(item, str) and item.strip(), f"{t['id']}:{field} contains empty control"
