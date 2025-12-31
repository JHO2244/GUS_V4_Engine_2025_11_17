import json
from pathlib import Path

from cli.gus_cli import main


def test_cli_govern_outputs_json(tmp_path: Path, monkeypatch, capsys):
    # CI-safe ledger path
    ledger_tmp = tmp_path / "gus_v4_audit_ledger.json"
    monkeypatch.setenv("GUS_V4_LEDGER_PATH", str(ledger_tmp))

    rc = main([
        "govern",
        "--policy", "L9_MERGE_MAIN.json",
        "--epoch", "epoch_test",
        "--head", "head_test",
        "--action", json.dumps({"type": "merge_pr", "target": "main"}),
        "--context", json.dumps({"actor": "JHO", "checks": "green"}),
    ])

    assert rc == 0
    out = capsys.readouterr().out.strip()
    payload = json.loads(out)

    assert payload["ok"] is True
    assert payload["level"] in {"allow", "warn", "block"}
    assert 0.0 <= float(payload["score"]) <= 10.0
    assert payload["ledger_hash"] is not None
    assert payload["policy_id"] == "L9_MERGE_MAIN"
    assert "object_hash" in payload
