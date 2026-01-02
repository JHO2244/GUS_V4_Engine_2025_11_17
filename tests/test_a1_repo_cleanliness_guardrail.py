from __future__ import annotations

from pathlib import Path

def test_repo_has_no_generated_measurement_manifest_json():
    """
    Guardrail: A1 must not generate a manifest JSON into the repo working tree.
    CI epoch verification requires a clean tree (except allowed seal sig paths).
    """
    p = Path("layer7_measurement") / "measurement_manifest_v0_1.json"
    assert not p.exists(), (
        "Generated file detected: layer7_measurement/measurement_manifest_v0_1.json\n"
        "This must not be created in the repo tree. Use monkeypatched MANIFEST_PATH in tests."
    )
