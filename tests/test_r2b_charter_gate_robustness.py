import json
from pathlib import Path

import pytest

from gus_purpose_charter_gate import load_charter_v4

CHARTER = Path("GUS_PURPOSE_CHARTER_v4.json")


def _write(tmp_path: Path, obj):
    p = tmp_path / "charter.json"
    p.write_text(json.dumps(obj), encoding="utf-8")
    return p


def test_missing_file_is_fail_closed(tmp_path):
    p = tmp_path / "nope.json"
    r = load_charter_v4(p)
    assert not r.ok
    assert "missing" in (r.error or "").lower()


def test_invalid_json_is_fail_closed(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text("{not-json", encoding="utf-8")
    r = load_charter_v4(p)
    assert not r.ok
    assert "unreadable" in (r.error or "").lower()


@pytest.mark.parametrize("ver", ["v3", "V2", "", None, "version4"])
def test_wrong_version_is_rejected(tmp_path, ver):
    obj = {"charter_version": ver, "failure_posture": {"on_uncertainty": "BLOCK"}}
    p = _write(tmp_path, obj)
    r = load_charter_v4(p)
    assert not r.ok
    assert "v4" in (r.error or "").lower()


@pytest.mark.parametrize("val", ["ALLOW", "", None, 123])
def test_on_uncertainty_must_be_warn_or_block(tmp_path, val):
    obj = {"charter_version": "v4", "failure_posture": {"on_uncertainty": val}}
    p = _write(tmp_path, obj)
    r = load_charter_v4(p)
    assert not r.ok
    msg = (r.error or "").lower()
    assert "on_uncertainty" in msg and ("warn" in msg and "block" in msg)


def test_requires_failure_posture_object(tmp_path):
    obj = {"charter_version": "v4", "failure_posture": "BLOCK"}
    p = _write(tmp_path, obj)
    r = load_charter_v4(p)
    assert not r.ok
    assert "failure_posture" in (r.error or "").lower()


def test_load_real_charter_is_ok():
    r = load_charter_v4(CHARTER)
    assert r.ok and r.charter is not None


def test_on_uncertainty_is_case_insensitive(tmp_path):
    obj = {"charter_version": "v4", "failure_posture": {"on_uncertainty": "warn"}}
    p = _write(tmp_path, obj)
    r = load_charter_v4(p)
    assert r.ok and r.charter is not None
