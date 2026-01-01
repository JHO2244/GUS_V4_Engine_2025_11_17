import json
from pathlib import Path

def _load_schema():
    schema_path = Path("layer9_policy_verdict/schemas/governance_v1.schema.json")
    return json.loads(schema_path.read_text(encoding="utf-8"))

def _basic_schema_asserts(schema: dict):
    assert schema["type"] == "object"
    assert schema["properties"]["contract_version"]["const"] == "governance.v1"
    for key in ["contract_version","ok","decision","timestamp_utc","inputs_hash","ledger"]:
        assert key in schema["required"]

def test_governance_schema_exists_and_has_core_requirements():
    schema = _load_schema()
    _basic_schema_asserts(schema)

def test_canonical_json_rules_are_documented_in_contract_doc():
    doc = Path("docs/A1_4_CHARTER_GATE_CONTRACT.md").read_text(encoding="utf-8")
    # hard requirement: stable JSON output for portability + determinism
    assert "sort_keys" in doc or "canonical" in doc.lower()
    assert "separators" in doc or "minified" in doc.lower()
