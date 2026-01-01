import json
from pathlib import Path

CHARTER_PATH = Path("GUS_PURPOSE_CHARTER_v4.json")


def load_charter():
    assert CHARTER_PATH.exists(), "Purpose Charter missing"
    return json.loads(CHARTER_PATH.read_text(encoding="utf-8"))


def test_charter_metadata_and_target_rating():
    c = load_charter()
    assert c["charter_version"].startswith("v4")
    assert c["guardian_rating_target"] == 10.0


def test_core_purpose_is_non_negotiable():
    c = load_charter()
    core = c["core_purpose"]
    assert core["non_negotiable"] is True
    assert "measure integrity" in core["statement"].lower()
    assert "execute actions" in core["statement"].lower() or "does not optimize" in core["statement"].lower()


def test_no_weaponization_constraints_are_explicit_and_testable():
    c = load_charter()
    nw = c["foundational_constraints"]["no_weaponization"]
    assert nw["testable"] is True
    for req in ["no_execution_layer", "no_reward_optimization", "no_autonomous_actuation"]:
        assert req in nw["enforcement"]


def test_human_sovereignty_is_mandatory():
    c = load_charter()
    hs = c["foundational_constraints"]["human_sovereignty"]
    assert hs["testable"] is True
    for req in ["verdicts_are_non_binding", "explicit_human_ack_required", "no_auto_execute_flag"]:
        assert req in hs["requirements"]


def test_mandatory_auditability_requirements():
    c = load_charter()
    ma = c["foundational_constraints"]["mandatory_auditability"]
    assert ma["testable"] is True
    for req in ["hash_anchored_verdict", "append_only_ledger_entry", "epoch_reference_required"]:
        assert req in ma["requirements"]


def test_measurement_axioms_are_absolute_and_non_normalized():
    c = load_charter()
    ss = c["measurement_axioms"]["score_semantics"]
    assert ss["type"] == "absolute"
    assert ss["range"] == [0.0, 10.0]
    assert ss["normalization"] == "forbidden"


def test_hard_fail_rules_are_non_averagable():
    c = load_charter()
    hfr = c["measurement_axioms"]["hard_fail_rules"]
    assert hfr["averagable"] is False
    for example in ["audit_missing", "policy_invalid", "sovereignty_bypass_attempt"]:
        assert example in hfr["examples"]


def test_determinism_requirements_present():
    c = load_charter()
    det = c["measurement_axioms"]["determinism"]
    for req in ["stable_hashing", "pure_functions_only", "no_time_entropy_in_scoring"]:
        assert req in det["requirements"]


def test_governance_policy_first_and_verdict_contract():
    c = load_charter()
    gov = c["governance_requirements"]
    assert gov["policy_first"]["enforced_at"] == "L9"
    vc = gov["verdict_contract"]["required_fields"]
    for field in ["level", "score", "reasons", "policy_id", "epoch_ref", "object_hash"]:
        assert field in vc


def test_forbidden_capabilities_are_explicit():
    c = load_charter()
    forbidden = c["forbidden_capabilities"]
    for cap in [
        "autonomous_execution",
        "behavioral_manipulation",
        "hidden_scoring_logic",
        "unverifiable_outputs",
        "silent_mutation",
    ]:
        assert cap in forbidden


def test_failure_posture_is_fail_closed():
    c = load_charter()
    fp = c["failure_posture"]
    assert fp["principle"].lower().startswith("fail")
    assert fp["on_uncertainty"] in ["WARN", "BLOCK"]
    assert fp["on_integrity_violation"] == "BLOCK"


def test_evolution_clause_minimum_rating():
    c = load_charter()
    evo = c["evolution_clause"]
    assert evo["minimum_rating_to_merge"] >= 9.7
