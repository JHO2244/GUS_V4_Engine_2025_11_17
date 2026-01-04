from __future__ import annotations

import json
from pathlib import Path

from layer9_final_guardian_audit.final_guardian_audit_v0_1 import write_a9_report_v0_1


def test_p3_4_a9_report_includes_a7_envelope_section_v0_1(tmp_path: Path) -> None:
    out_report = tmp_path / "a9_report_v0_1.json"
    out_env = tmp_path / "a7_output_envelope_from_a9_v0_1.json"

    verdict = write_a9_report_v0_1(
        out_path=out_report,
        require_seal_ok=False,
        envelope_out_path=out_env,
    )

    assert out_report.is_file()
    data = json.loads(out_report.read_text(encoding="utf-8"))

    assert "a7_output_envelope" in data
    sec = data["a7_output_envelope"]

    assert sec["path"].endswith("a7_output_envelope_from_a9_v0_1.json")
    assert sec["exists"] is True
    assert sec["integrity_ok"] is True

    assert isinstance(sec["schema_version"], str)
    assert len(sec["schema_version"]) > 0

    assert isinstance(sec["policy_verdict_ref"], str)
    assert sec["policy_verdict_ref"] == "policy_verdict:a9_unavailable_v0_1"

    # Also ensure the Python-level verdict is consistent (should be ok when require_seal_ok=False).
    assert verdict.ok is True
