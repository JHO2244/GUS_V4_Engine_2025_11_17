from pathlib import Path
import json

def test_d8_operational_misuse_failure_audit_shape() -> None:
    p = Path("gdvs/d8_ops/operational_misuse_failure_audit_v0_1.json")
    assert p.exists()

    data = json.loads(p.read_text(encoding="utf-8"))
    allowed_top = {"created_at_utc","d8_version","schema_version","scenarios"}
    assert set(data.keys()) == allowed_top

    assert data["d8_version"] == "0.1"
    assert data["schema_version"] == "0.1"
    assert isinstance(data["created_at_utc"], str) and data["created_at_utc"].endswith("Z")

    scenarios = data["scenarios"]
    assert isinstance(scenarios, list)

    # Scaffold can be empty; if present each scenario must be enforceable.
    for s in scenarios:
        assert set(s.keys()) == {
            "id","name","failure_mode","impact",
            "containment","detection","recovery"
        }
        assert isinstance(s["id"], str) and s["id"].strip()
        assert isinstance(s["name"], str) and s["name"].strip()
        assert isinstance(s["failure_mode"], str) and s["failure_mode"].strip()
        assert isinstance(s["impact"], str) and s["impact"].strip()

        for k in ("containment","detection","recovery"):
            assert isinstance(s[k], list) and len(s[k]) >= 2
            assert all(isinstance(x, str) and x.strip() for x in s[k])
