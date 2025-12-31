from pathlib import Path


def test_l8_l9_integration_spec_exists_and_has_headings():
    p = Path("docs/L8_L9_INTEGRATION_SPEC.md")
    assert p.exists()

    s = p.read_text(encoding="utf-8")

    required = [
        "# GUS v4 — L8 ↔ L9 Integration Specification (Authoritative)",
        "## Scope",
        "## Components",
        "## Data Contracts",
        "## Execution Pipeline (Canonical)",
        "## CI Safety / Dirty Tree Protection",
    ]
    for r in required:
        assert r in s
