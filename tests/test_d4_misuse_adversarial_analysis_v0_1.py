from pathlib import Path
import json

def test_d4_misuse_adversarial_analysis_exists_and_shape_is_strict() -> None:
    path = Path("gdvs/d4_policy/misuse_adversarial_analysis_v0_1.json")
    assert path.exists(), "Missing canonical D4 misuse analysis at gdvs/d4_policy/misuse_adversarial_analysis_v0_1.json"

    raw = path.read_text(encoding="utf-8")
    data = json.loads(raw)

    allowed_top = {"d4_version", "schema_version", "created_at_utc", "scenarios"}
    assert set(data.keys()) == allowed_top, f"Top-level keys must be exactly {sorted(allowed_top)}"

    assert data["d4_version"] == "0.1"
    assert data["schema_version"] == "0.1"
    assert isinstance(data["created_at_utc"], str) and data["created_at_utc"].endswith("Z")

    scenarios = data["scenarios"]
    assert isinstance(scenarios, list), "scenarios must be a list"
