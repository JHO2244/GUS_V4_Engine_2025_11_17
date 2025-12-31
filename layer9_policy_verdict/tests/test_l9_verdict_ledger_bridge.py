import os
from pathlib import Path

from layer9_policy_verdict.src.verdict_ledger_bridge import append_verdict_to_ledger
from layer9_policy_verdict.src.verdict_types import PolicyVerdict, VerdictLevel


def test_verdict_appended_to_ledger(tmp_path: Path, monkeypatch):
    # Force ledger writes into pytest temp dir (keeps repo clean for epoch validation)
    ledger_tmp = tmp_path / "gus_v4_audit_ledger.json"
    monkeypatch.setenv("GUS_V4_LEDGER_PATH", str(ledger_tmp))

    verdict = PolicyVerdict(
        level=VerdictLevel.ALLOW,
        score=9.9,
        reasons=["test"],
        evidence={},
        policy_id="P_TEST",
        epoch_ref="epoch_test",
        chain_head="head_test",
        object_hash="abc123" * 10
    )

    result = append_verdict_to_ledger(verdict)

    assert "hash" in result
    assert result["hash"] is not None
    assert result["entry"]["decision"]["verdict_hash"] == verdict.object_hash
    assert result["entry"]["decision"]["policy_id"] == "P_TEST"

