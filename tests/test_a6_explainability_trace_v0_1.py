from __future__ import annotations

from pathlib import Path

from layer9_interpretability.explainability_trace_v0_1 import (
    build_explainability_trace,
    write_explainability_trace,
)


def _read_bytes(p: Path) -> bytes:
    return p.read_bytes()


def test_a6_trace_is_pure_and_deterministic():
    scores = {
        "truth_density": "9.5",
        "activation_potential": "8.25",
        "systemic_coherence": "9.0",
        "resonance_longevity": "7.75",
    }
    t1 = build_explainability_trace(scores)
    t2 = build_explainability_trace(scores)
    assert t1.to_dict() == t2.to_dict()
    assert t1.schema == "gus_v4_explainability_trace"
    assert t1.version == "0.1"
    assert isinstance(t1.composite_score, float)


def test_a6_trace_byte_stable(tmp_path):
    scores = {
        "truth_density": "9.5",
        "activation_potential": "8.25",
        "systemic_coherence": "9.0",
        "resonance_longevity": "7.75",
    }
    p = tmp_path / "trace.json"

    t1 = build_explainability_trace(scores)
    write_explainability_trace(t1, path=p)
    b1 = _read_bytes(p)

    t2 = build_explainability_trace(scores)
    write_explainability_trace(t2, path=p)
    b2 = _read_bytes(p)

    assert b1 == b2, "Explainability trace must be byte-stable across identical runs."


def test_a6_no_repo_default_trace_written():
    p = Path("layer9_interpretability") / "explainability_trace_v0_1.json"
    assert not p.exists(), "Repo must not contain generated explainability trace by default."


def test_a6_forbids_entropy_fields():
    scores = {
        "truth_density": 9,
        "activation_potential": 9,
        "systemic_coherence": 9,
        "resonance_longevity": 9,
    }
    t = build_explainability_trace(scores).to_dict()
    forbidden = {"timestamp", "created_at", "updated_at", "uuid", "nonce", "random"}
    assert forbidden.isdisjoint(set(t.keys()))
