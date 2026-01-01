import importlib
import os
from pathlib import Path

def _reload_l8(monkeypatch, rel_path: str):
    # Set env BEFORE reload so module reads it.
    monkeypatch.setenv("GUS_V4_LEDGER_PATH", rel_path)
    import layer8_audit_ledger.L8_ledger_stub as L8
    return importlib.reload(L8)

def test_ledger_path_relative_env_resolves_under_base_dir(monkeypatch):
    L8 = _reload_l8(monkeypatch, "tmp_ledger_rel.json")
    # must resolve under module BASE_DIR, not CWD
    assert str(L8.LEDGER_PATH).endswith(str(Path("layer8_audit_ledger") / "tmp_ledger_rel.json").replace("/", "\\")) or \
           str(L8.LEDGER_PATH).endswith(str(Path("layer8_audit_ledger") / "tmp_ledger_rel.json"))

def test_entry_hash_is_stable_with_frozen_time(monkeypatch, tmp_path):
    # Use an absolute temp ledger path to avoid polluting repo ledger during test
    ledger_file = tmp_path / "ledger.json"
    monkeypatch.setenv("GUS_V4_LEDGER_PATH", str(ledger_file))

    import layer8_audit_ledger.L8_ledger_stub as L8
    L8 = importlib.reload(L8)

    # Freeze time deterministically
    monkeypatch.setattr(L8, "_utc_now", lambda: "2026-01-01T00:00:00Z")

    r1 = L8.append_entry(
        decision={"a": 1},
        execution={"b": 2},
        certificate={"c": 3},
        entry_id="E1",
    )
    assert r1.ok and r1.entry
    h1 = r1.entry["entry_hash"]

    # Reload ledger and confirm stable chain behavior with same frozen time for a NEW entry
    r2 = L8.append_entry(
        decision={"a": 1},
        execution={"b": 2},
        certificate={"c": 3},
        entry_id="E2",
    )
    assert r2.ok and r2.entry
    h2 = r2.entry["entry_hash"]

    assert h1 != h2  # because prev_hash changes
    assert r2.entry["prev_hash"] == h1

    # On-disk must be canonical: single-line JSON + trailing newline
    txt = ledger_file.read_text(encoding="utf-8")
    assert txt.endswith("\n")
    assert txt.count("\n") == 1
