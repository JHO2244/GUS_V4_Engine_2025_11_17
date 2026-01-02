from __future__ import annotations

from pathlib import Path

from layer7_measurement.self_measurement_v0_1 import (
    build_self_measurement_report,
    write_self_measurement_report,
)


def _read_bytes(p: Path) -> bytes:
    return p.read_bytes()


def test_a4_self_measure_report_is_pure_and_deterministic():
    scores = {
        "truth_density": "9.5",
        "activation_potential": "8.25",
        "systemic_coherence": "9.0",
        "resonance_longevity": "7.75",
    }
    r1 = build_self_measurement_report(scores)
    r2 = build_self_measurement_report(scores)

    assert r1 == r2
    assert r1.get("schema") == "gus_v4_self_measurement_report"
    assert r1.get("version") == "0.1"
    assert "result" in r1
    assert r1["result"]["schema"] == "gus_v4_score_aggregator_result"


def test_a4_self_measure_report_byte_stable(tmp_path):
    scores = {
        "truth_density": "9.5",
        "activation_potential": "8.25",
        "systemic_coherence": "9.0",
        "resonance_longevity": "7.75",
    }

    p = tmp_path / "self_measurement_report_v0_1.json"

    r1 = build_self_measurement_report(scores)
    write_self_measurement_report(r1, path=p)
    b1 = _read_bytes(p)

    r2 = build_self_measurement_report(scores)
    write_self_measurement_report(r2, path=p)
    b2 = _read_bytes(p)

    assert b1 == b2, "Self-measurement report must be byte-stable across identical writes."


def test_a4_no_repo_default_report_written():
    """
    Guardrail: default repo path must not appear unless explicitly written.
    """
    p = Path("layer7_measurement") / "self_measurement_report_v0_1.json"
    assert not p.exists(), "Repo must not contain generated self_measurement_report_v0_1.json by default."


def test_a4_forbids_entropy_fields():
    scores = {
        "truth_density": 9,
        "activation_potential": 9,
        "systemic_coherence": 9,
        "resonance_longevity": 9,
    }
    r = build_self_measurement_report(scores)
    forbidden = {"timestamp", "created_at", "updated_at", "uuid", "nonce", "random"}
    assert forbidden.isdisjoint(set(r.keys()))
