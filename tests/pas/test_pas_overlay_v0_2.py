# GUS v4 – PAS v0.2 Overlay Tests (L5–L6 Continuity + Replication)
# Non-blocking, import-only tests

import pytest

from layer5_continuity.continuity_manifest_v0_1 import load_manifest as l5_load_manifest
from layer6_replication.replication_manifest_v0_1 import (
    load_manifest as l6_load_manifest,
    build_replication_plan_from_continuity,
)


def test_pas_010_continuity_manifest_importable():
    manifest = l5_load_manifest()
    assert manifest is not None, "L5 manifest must load and not be None."


def test_pas_011_continuity_manifest_has_entries():
    manifest = l5_load_manifest()
    entries = manifest.get("continuity_entries", [])
    assert isinstance(entries, list)
    assert len(entries) >= 1, "L5 continuity manifest must contain ≥ 1 entry."


def test_pas_013_replication_manifest_importable():
    manifest = l6_load_manifest()
    assert manifest is not None, "L6 manifest must load without error."


def test_pas_014_replication_plan_basic_generation():
    dummy_targets = ["D:\\GuardianReplicas"]
    plan = build_replication_plan_from_continuity(default_targets=dummy_targets)

    assert isinstance(plan, dict)
    assert "targets" in plan
    assert len(plan["targets"]) >= 1
    assert plan["targets"][0] == dummy_targets[0]


def test_pas_015_replication_policy_invariants():
    manifest = l6_load_manifest()

    assert manifest.get("frequency") == "on_demand"
    assert manifest.get("require_all_green") is True
    assert manifest.get("max_snapshots", 0) >= 1
