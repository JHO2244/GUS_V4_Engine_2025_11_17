from pathlib import Path
import json

def test_d4_misuse_adversarial_analysis_is_enforceable_and_strict() -> None:
    path = Path("gdvs/d4_policy/misuse_adversarial_analysis_v0_1.json")
    assert path.exists(), "Missing canonical D4 misuse analysis at gdvs/d4_policy/misuse_adversarial_analysis_v0_1.json"

    data = json.loads(path.read_text(encoding="utf-8"))

    allowed_top = {"d4_version", "schema_version", "created_at_utc", "scenarios"}
    assert set(data.keys()) == allowed_top, f"Top-level keys must be exactly {sorted(allowed_top)}"

    assert data["d4_version"] == "0.1"
    assert data["schema_version"] == "0.1"
    assert isinstance(data["created_at_utc"], str) and data["created_at_utc"].endswith("Z")

    scenarios = data["scenarios"]
    assert isinstance(scenarios, list) and len(scenarios) == 4

    allowed_s = {"id", "name", "abuse_path", "detection", "containment", "recovery", "severity"}
    ids = set()
    for s in scenarios:
        assert set(s.keys()) == allowed_s, f"Scenario keys must be exactly {sorted(allowed_s)}"
        assert isinstance(s["id"], str) and s["id"].startswith("D4-S")
        assert s["id"] not in ids, "Scenario IDs must be unique"
        ids.add(s["id"])

        for field in ("name", "abuse_path", "severity"):
            assert isinstance(s[field], str) and s[field].strip()

        # LAW: no empty controls
        for field in ("detection", "containment", "recovery"):
            items = s[field]
            assert isinstance(items, list), f"{s['id']}:{field} must be a list"
            assert len(items) >= 2, f"{s['id']}:{field} must have >=2 controls (no placeholders)"
