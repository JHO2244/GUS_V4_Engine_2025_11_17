from pathlib import Path

DOC = Path("docs/A1_4_CHARTER_GATE_CONTRACT.md")

REQUIRED_SNIPPETS = [
    "Fail-Closed",
    "GUS_PURPOSE_CHARTER_v4.json",
    "charter_version",
    "startswith(\"v4\")",
    "govern_action",
    "gus govern",
    "ledger append fails",
    "policy_id",
    "object_hash",
    "ledger_hash",
]

def test_a1_4_contract_doc_exists():
    assert DOC.exists(), "A1.4 contract doc missing"

def test_a1_4_contract_doc_contains_core_contract():
    txt = DOC.read_text(encoding="utf-8")
    for s in REQUIRED_SNIPPETS:
        assert s in txt, f"Missing required contract snippet: {s}"
