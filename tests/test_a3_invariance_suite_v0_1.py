from __future__ import annotations

from pathlib import Path

from utils.canonical_json import write_canonical_json_file

from layer6_replication.replication_manifest_v0_1 import create_default_manifest as l6_create_manifest
from layer7_measurement.measurement_manifest_v0_1 import load_manifest as a1_load_manifest
from layer7_measurement.score_aggregator_v0_1 import compute_composite_score, write_score_report


def _read_bytes(p: Path) -> bytes:
    return p.read_bytes()


def test_a3_canonical_json_writer_byte_stable(tmp_path: Path):
    """
    If the same semantic dict is written twice, bytes must match exactly.
    Also checks that key insertion order does not change output.
    """
    p1 = tmp_path / "a.json"
    p2 = tmp_path / "b.json"

    d1 = {"b": 2, "a": 1, "z": {"y": 2, "x": 1}}
    d2 = {"a": 1, "b": 2, "z": {"x": 1, "y": 2}}  # different insertion order

    write_canonical_json_file(p1, d1)
    write_canonical_json_file(p2, d2)

    assert _read_bytes(p1) == _read_bytes(p2), "Canonical writer must be order-invariant and byte-stable."


def test_a3_l6_replication_manifest_deterministic(tmp_path: Path, monkeypatch):
    """
    L6 manifest must be byte-stable across repeated creation.
    """
    p = tmp_path / "replication_manifest_v0_1.json"
    monkeypatch.setattr("layer6_replication.replication_manifest_v0_1.MANIFEST_PATH", p)

    l6_create_manifest()
    b1 = _read_bytes(p)

    l6_create_manifest()
    b2 = _read_bytes(p)

    assert b1 == b2, "L6 replication manifest must be byte-stable across writes."


def test_a3_a1_load_manifest_is_side_effect_free_by_default():
    """
    A1 load_manifest must NOT generate layer7_measurement/measurement_manifest_v0_1.json in the repo tree.
    (We already guard this with a dedicated guardrail test; this confirms behavior at the API level.)
    """
    p = Path("layer7_measurement") / "measurement_manifest_v0_1.json"
    if p.exists():
        # If it exists, tests must fail; this would violate epoch cleanliness.
        raise AssertionError("Repo contains generated measurement_manifest_v0_1.json; must not exist.")

    m = a1_load_manifest()  # default auto_write=False
    assert m.get("schema") == "gus_v4_measurement_manifest"
    assert (Path("layer7_measurement") / "measurement_manifest_v0_1.json").exists() is False


def test_a3_a2_score_report_byte_stable(tmp_path: Path, monkeypatch):
    """
    A2 report must be byte-stable across identical runs.
    Also ensures no repo-side effect by writing to tmp_path only.
    """
    p = tmp_path / "score_report_v0_1.json"
    monkeypatch.setattr("layer7_measurement.score_aggregator_v0_1.SCORE_REPORT_PATH", p)

    scores = {
        "truth_density": "9.5",
        "activation_potential": "8.25",
        "systemic_coherence": "9.0",
        "resonance_longevity": "7.75",
    }

    r1 = compute_composite_score(scores)
    write_score_report(r1)
    b1 = _read_bytes(p)

    r2 = compute_composite_score(scores)
    write_score_report(r2)
    b2 = _read_bytes(p)

    assert b1 == b2, "A2 score report must be byte-stable across identical runs."


def test_a3_no_repo_generated_score_report():
    """
    Guard against accidental creation of score_report_v0_1.json in the repo tree.
    """
    p = Path("layer7_measurement") / "score_report_v0_1.json"
    assert not p.exists(), "Generated score_report_v0_1.json must not appear in repo tree."
