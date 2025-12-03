from __future__ import annotations

import json
import hashlib
from pathlib import Path

from layer1_integrity_core import (
    L1_MANIFEST_PATH,
    L1_STATUS_PATH,
)
from layer1_integrity_core.L1_integrity_core_stub import (
    verify_integrity,
    load_integrity_status,
)


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def test_verify_integrity_empty_manifest(tmp_path, monkeypatch):
    # Point the manifest to a non-existent file to simulate "no manifest yet".
    fake_manifest = tmp_path / "no_manifest_yet.json"
    monkeypatch.setattr("layer1_integrity_core.L1_integrity_core_stub.L1_MANIFEST_PATH", fake_manifest)

    ok, issues = verify_integrity()
    assert ok is False
    assert issues, "Expected at least one issue for empty manifest"
    assert "no files registered" in issues[0].reason


def test_verify_integrity_with_real_file(tmp_path, monkeypatch):
    # Create a real file and a matching manifest entry.
    target = tmp_path / "sample.txt"
    target.write_text("guardian-test", encoding="utf-8")

    manifest = {
        "version": "L1_manifest_test",
        "files": [
            {
                "path": str(target),
                "sha256": _sha256(target),
            }
        ],
    }

    manifest_path = tmp_path / "L1_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    monkeypatch.setattr("layer1_integrity_core.L1_integrity_core_stub.L1_MANIFEST_PATH", manifest_path)

    ok, issues = verify_integrity()
    assert ok is True
    assert issues == []


def test_load_integrity_status_persists_snapshot(tmp_path, monkeypatch):
    # Prepare a healthy one-file manifest.
    target = tmp_path / "file.txt"
    target.write_text("snap-test", encoding="utf-8")
    manifest = {
        "version": "L1_manifest_test",
        "files": [
            {
                "path": str(target),
                "sha256": _sha256(target),
            }
        ],
    }
    manifest_path = tmp_path / "L1_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    monkeypatch.setattr("layer1_integrity_core.L1_integrity_core_stub.L1_MANIFEST_PATH", manifest_path)

    status_path = tmp_path / "L1_status.json"
    monkeypatch.setattr("layer1_integrity_core.L1_integrity_core_stub.L1_STATUS_PATH", status_path)

    status = load_integrity_status()
    assert status.overall_ok is True

    # The helper should have written a JSON snapshot to disk.
    assert status_path.exists()
    snapshot = json.loads(status_path.read_text(encoding="utf-8"))
    assert snapshot["overall_ok"] is True
    assert snapshot["files"], "snapshot should contain at least one file entry"
