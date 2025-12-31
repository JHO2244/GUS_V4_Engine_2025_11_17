from pathlib import Path

from layer9_policy_verdict.src.governance_api import govern_action


def test_govern_action_happy_path(tmp_path: Path, monkeypatch):
    # CI-safe ledger path
    ledger_tmp = tmp_path / "gus_v4_audit_ledger.json"
    monkeypatch.setenv("GUS_V4_LEDGER_PATH", str(ledger_tmp))

    action = {"type": "merge_pr", "target": "main"}
    context = {"actor": "JHO", "checks": "green"}
    out = govern_action(
        action=action,
        context=context,
        policy_filename="L9_MERGE_MAIN.json",
        epoch_ref="epoch_test",
        chain_head="head_test"
    )

    assert out["ok"] is True
    assert out["level"] in {"allow", "warn", "block"}
    assert 0.0 <= out["score"] <= 10.0
    assert out["ledger_hash"] is not None
