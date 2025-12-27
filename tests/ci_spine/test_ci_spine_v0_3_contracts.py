from __future__ import annotations

import json
from pathlib import Path

from ci_spine.v0_3.capabilities.capabilities_v0_3 import CISpineV03Capabilities
from ci_spine.v0_3.policy.non_retroactivity_guard import NonRetroactivityGuard
from ci_spine.v0_3.replay.replay_plan_v0_3 import ReplayPlanV03
from ci_spine.v0_3.attestation.attestation_bundle_v0_3 import AttestationBundleV03


def test_capabilities_are_deterministic_and_boolean():
    caps = CISpineV03Capabilities().as_dict()
    assert caps
    assert all(isinstance(v, bool) for v in caps.values())


def test_non_retroactivity_guard_blocks_pass_to_fail():
    g = NonRetroactivityGuard()
    g.enforce("PASS", "PASS")  # ok
    try:
        g.enforce("PASS", "FAIL")
        assert False, "Expected guard to raise"
    except RuntimeError as e:
        assert "NonRetroactivityGuard" in str(e)


def test_replay_plan_no_duplicates():
    p = ReplayPlanV03(["epoch_a", "epoch_b"])
    p.validate()
    try:
        ReplayPlanV03(["epoch_a", "epoch_a"]).validate()
        assert False, "Expected duplicate check to raise"
    except ValueError:
        pass


def test_attestation_bundle_writes_deterministic_json(tmp_path: Path):
    b = AttestationBundleV03()
    out = tmp_path / "a.json"
    b.write_json(out, {"z": 1, "a": 2})
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["schema_version"] == "ci_spine_attestation_v0_3"
    assert data["a"] == 2
    assert data["z"] == 1
