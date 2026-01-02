from __future__ import annotations

from pathlib import Path

from layer7_measurement.score_aggregator_v0_1 import (
    compute_composite_score,
    write_score_report,
)

def _read_bytes(p: Path) -> bytes:
    return p.read_bytes()


def test_a2_composite_deterministic_exact_default_weights(tmp_path, monkeypatch):
    # Ensure report path is sandboxed
    p = tmp_path / "score_report_v0_1.json"
    monkeypatch.setattr("layer7_measurement.score_aggregator_v0_1.SCORE_REPORT_PATH", p)

    scores = {
        "truth_density": 10,
        "activation_potential": 10,
        "systemic_coherence": 10,
        "resonance_longevity": 10,
    }
    r = compute_composite_score(scores)
    assert r["composite_score_str"] == "10.0000"
    assert r["composite_score_10k"] == 100000


def test_a2_report_byte_stable(tmp_path, monkeypatch):
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

    # Write again from same inputs
    r2 = compute_composite_score(scores)
    write_score_report(r2)
    b2 = _read_bytes(p)

    assert b1 == b2, "Score report must be byte-stable across identical writes."


def test_a2_forbids_entropy_fields(tmp_path, monkeypatch):
    p = tmp_path / "score_report_v0_1.json"
    monkeypatch.setattr("layer7_measurement.score_aggregator_v0_1.SCORE_REPORT_PATH", p)

    scores = {
        "truth_density": 9,
        "activation_potential": 9,
        "systemic_coherence": 9,
        "resonance_longevity": 9,
    }
    r = compute_composite_score(scores)
    forbidden = {"timestamp", "created_at", "updated_at", "uuid", "nonce", "random"}
    assert forbidden.isdisjoint(set(r.keys()))
