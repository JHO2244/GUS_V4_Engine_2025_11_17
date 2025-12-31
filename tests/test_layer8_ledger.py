import json
from pathlib import Path

from layer8_audit_ledger.L8_ledger_stub import append_entry, last_entry_hash, LEDGER_PATH

def test_ledger_append_creates_file_and_hash_chain(tmp_path, monkeypatch):
    # Redirect ledger path to tmp for test isolation
    from layer8_audit_ledger import L8_ledger_stub as l8
    test_ledger = tmp_path / "ledger.json"
    monkeypatch.setattr(l8, "LEDGER_PATH", test_ledger)

    h0 = l8.last_entry_hash()
    assert h0 == "GENESIS"

    r1 = l8.append_entry({"d":1}, {"e":1}, {"c":1}, entry_id="E1")
    assert r1.ok is True
    assert test_ledger.exists()
    assert len(r1.entry["entry_hash"]) == 64
    assert r1.entry["prev_hash"] == "GENESIS"

    r2 = l8.append_entry({"d":2}, {"e":2}, {"c":2}, entry_id="E2")
    assert r2.ok is True
    assert r2.entry["prev_hash"] == r1.entry["entry_hash"]

    data = json.loads(test_ledger.read_text(encoding="utf-8"))
    assert len(data["entries"]) == 2
