from __future__ import annotations

from pathlib import Path

from layer9_final_guardian_audit.final_guardian_audit_v0_1 import run_final_guardian_audit_v0_1


def test_a9_audit_report_has_required_shape_and_passes_seals():
    verdict = run_final_guardian_audit_v0_1(repo_root=Path.cwd(), require_seal_ok=True)

    # Shape checks (deterministic keys)
    assert "a9_version" in verdict.report
    assert verdict.report["a9_version"] == "0.1"
    assert "repo" in verdict.report
    assert "checks" in verdict.report
    assert "verdict" in verdict.report

    # Must not be missing core artifacts
    missing = verdict.report["checks"]["required_files_missing"]
    assert missing == [], f"Missing required files: {missing}"

    # Seal verify must be OK in this repo
    assert verdict.report["checks"]["seal_verify"]["ok"] is True
    assert verdict.ok is True
