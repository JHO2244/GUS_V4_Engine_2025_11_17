from __future__ import annotations
import pytest

from layer9_policy_verdict.src.policy_schema import validate_policy_v1, require_policy_v1, PolicySchemaError

def test_policy_v1_valid_ok():
    policy = {"policy_id": "L9_BASE", "thresholds": {"allow": 9.7, "warn": 8.5}, "base_score": 9.8}
    ok, errors = validate_policy_v1(policy)
    assert ok is True
    assert errors == []
    require_policy_v1(policy)  # no raise

def test_policy_v1_missing_policy_id_fails():
    policy = {"thresholds": {"allow": 9.7, "warn": 8.5}}
    ok, errors = validate_policy_v1(policy)
    assert ok is False
    assert any("policy_id" in e for e in errors)
    with pytest.raises(PolicySchemaError):
        require_policy_v1(policy)

def test_policy_v1_threshold_bounds_fails():
    policy = {"policy_id": "X", "thresholds": {"allow": 11.0, "warn": -1.0}}
    ok, errors = validate_policy_v1(policy)
    assert ok is False
    assert any("thresholds.allow" in e for e in errors)
    assert any("thresholds.warn" in e for e in errors)

def test_policy_v1_allow_less_than_warn_fails():
    policy = {"policy_id": "X", "thresholds": {"allow": 8.0, "warn": 8.5}}
    ok, errors = validate_policy_v1(policy)
    assert ok is False
    assert any("allow must be >=" in e for e in errors)
