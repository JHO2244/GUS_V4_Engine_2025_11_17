from pathlib import Path

DOC = Path("docs/GUS_V4_COMPLETION_ROADMAP.md")

REQUIRED_HEADERS = [
    "# GUS v4 Completion Roadmap",
    "## Status Snapshot",
    "## Non-Negotiables",
    "## Build Phases",
    "## Definition of “GUS v4 Ready”",
]

def test_completion_roadmap_exists():
    assert DOC.exists(), "Missing docs/GUS_V4_COMPLETION_ROADMAP.md"

def test_completion_roadmap_has_required_sections():
    text = DOC.read_text(encoding="utf-8")
    for h in REQUIRED_HEADERS:
        assert h in text, f"Roadmap missing required header: {h}"
