from __future__ import annotations

from pathlib import Path

from layer7_measurement.measurement_manifest_v0_1 import (
    MANIFEST_PATH,
    create_default_manifest,
    load_manifest,
)

def _read_bytes(p: Path) -> bytes:
    return p.read_bytes()


def test_a1_manifest_creates_and_loads_defaults(tmp_path, monkeypatch):
    p = tmp_path / "measurement_manifest_v0_1.json"
    monkeypatch.setattr("layer7_measurement.measurement_manifest_v0_1.MANIFEST_PATH", p)

    m = load_manifest()
    assert m.get("schema") == "gus_v4_measurement_manifest"
    assert m.get("version") == "0.1"
    assert m.get("measurement", {}).get("mode") == "strict"
    assert "dimensions" in m.get("measurement", {})


def test_a1_manifest_is_deterministic_bytes(tmp_path, monkeypatch):
    p = tmp_path / "measurement_manifest_v0_1.json"
    monkeypatch.setattr("layer7_measurement.measurement_manifest_v0_1.MANIFEST_PATH", p)

    create_default_manifest()
    b1 = _read_bytes(p)

    # Write again using the same deterministic creator
    create_default_manifest()
    b2 = _read_bytes(p)

    assert b1 == b2, "Measurement manifest output must be byte-stable across writes."


def test_a1_no_entropy_fields_present(tmp_path, monkeypatch):
    p = tmp_path / "measurement_manifest_v0_1.json"
    monkeypatch.setattr("layer7_measurement.measurement_manifest_v0_1.MANIFEST_PATH", p)

    m = load_manifest()

    # Hard forbid common entropy/timestamp fields at top-level.
    forbidden = {"timestamp", "created_at", "updated_at", "uuid", "random", "nonce"}
    assert forbidden.isdisjoint(set(m.keys()))
