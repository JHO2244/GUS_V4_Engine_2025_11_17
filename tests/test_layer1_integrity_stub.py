from layer1_integrity_core.L1_integrity_core_stub import verify_integrity, L1_MANIFEST_PATH
from pathlib import Path
import json

def test_l1_integrity_empty_manifest(tmp_path, monkeypatch):
    # Point manifest to a non-existing temp file
    fake_manifest = tmp_path / "L1_manifest_empty.json"
    monkeypatch.setattr("layer1_integrity_core.L1_integrity_core_stub.L1_MANIFEST_PATH", fake_manifest)

    ok, issues = verify_integrity()
    assert ok is False
    assert any("no files registered" in i.reason for i in issues)

def test_l1_integrity_populated_manifest(tmp_path, monkeypatch):
    # Create a temp file and manifest that matches
    test_file = tmp_path / "dummy.txt"
    test_file.write_text("hello", encoding="utf-8")

    from hashlib import sha256
    h = sha256(test_file.read_bytes()).hexdigest()

    manifest = {
        "version": "test",
        "generated_at": "2025-12-03T00:00:00Z",
        "note": "test manifest",
        "files": [
            {"path": str(test_file), "role": "test", "required": True, "sha256": h},
        ],
    }

    manifest_path = tmp_path / "L1_manifest_test.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    monkeypatch.setattr("layer1_integrity_core.L1_integrity_core_stub.L1_MANIFEST_PATH", manifest_path)

    ok, issues = verify_integrity()
    assert ok is True
    assert issues == []

