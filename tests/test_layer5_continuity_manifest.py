import json
from pathlib import Path

from layer5_continuity.continuity_manifest_v0_1 import (
    MANIFEST_PATH,
    ContinuityStatus,
    read_manifest,
    write_manifest,
    create_default_manifest,
    check_continuity,
)


def _sample_manifest() -> dict:
    return create_default_manifest(
        engine_version="GUS_V4_Engine_2025_11_17",
        last_all_green_commit="3205b5e3972d8b4393d3a5d779675f67affedb78",
        last_all_green_timestamp="2025-12-10T11:19:00+02:00",
        backup_paths=[
            "Z:\\\\GuardianBackups\\\\GUS_V4\\\\GUS_V4_Engine_2025_11_17_ALL_GREEN_20251210.zip",
        ],
        pas_version="0.1",
        test_summary={"total": 31, "passed": 31, "failed": 0},
    )


def test_manifest_can_be_created_and_read_roundtrip(tmp_path, monkeypatch):
    """Manifest roundtrip should preserve key fields.

    We temporarily redirect MANIFEST_PATH into a temp folder to avoid
    interfering with any real continuity manifest.
    """
    fake_path = tmp_path / "gus_v4_continuity_manifest.json"

    # Monkeypatch the module-level MANIFEST_PATH
    from layer5_continuity import continuity_manifest_v0_1 as cm

    monkeypatch.setattr(cm, "MANIFEST_PATH", fake_path, raising=True)

    data = _sample_manifest()
    write_manifest(data)
    loaded = read_manifest()

    assert loaded["engine_version"] == data["engine_version"]
    assert loaded["last_all_green_commit"] == data["last_all_green_commit"]


def test_check_continuity_ok_when_manifest_valid(tmp_path, monkeypatch):
    """check_continuity() returns ok=True for a valid manifest."""
    fake_path = tmp_path / "gus_v4_continuity_manifest.json"

    from layer5_continuity import continuity_manifest_v0_1 as cm

    monkeypatch.setattr(cm, "MANIFEST_PATH", fake_path, raising=True)

    data = _sample_manifest()
    write_manifest(data)

    status = check_continuity()
    assert isinstance(status, ContinuityStatus)
    assert status.ok is True
    assert status.reason == "ok"
    assert status.data["engine_version"].startswith("GUS_V4_Engine")


def test_check_continuity_reports_missing_manifest(tmp_path, monkeypatch):
    """Missing manifest should be reported but not raise exceptions."""
    fake_path = tmp_path / "gus_v4_continuity_manifest.json"

    from layer5_continuity import continuity_manifest_v0_1 as cm

    monkeypatch.setattr(cm, "MANIFEST_PATH", fake_path, raising=True)

    status = check_continuity()
    assert isinstance(status, ContinuityStatus)
    assert status.ok is False
    assert status.reason == "manifest_missing"
    assert status.data == {}
