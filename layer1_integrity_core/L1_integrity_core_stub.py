# layer1_integrity_core/L1_integrity_core_stub.py
"""
GUS v4 – Layer 1 Integrity Core stub v0.1

This module provides a stable, test-friendly API for:
- Loading a simple "integrity status" object
- Verifying file hashes against gus_integrity.json (stubbed)
- Summarising integrity in a small dataclass

It is intentionally simple. We can deepen the internal behavior later
without breaking tests or gus_engine_health / PAS callers.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Sequence

import json
import hashlib

# ---------------------------------------------------------------------------
# Paths / constants
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = PROJECT_ROOT / "layer1_integrity_core" / "chain" / "gus_integrity.json"


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass
class FileIntegrityResult:
    """
    Result for a single file.
    """
    path: str
    expected_hash: str
    actual_hash: str
    ok: bool


@dataclass
class IntegritySummary:
    """
    High-level summary for a set of files.
    """
    engine_ok: bool
    reason: str
    checked_at: str
    files: List[FileIntegrityResult]

@dataclass
class IntegrityStatus:
    ok: bool
    reason: str
    errors: List[str]

    """
    Compact status representation used by tests and gus_engine_health.

    The tests do *not* need the whole file list; they just assert that we
    have a boolean and a human-readable reason string.
    """

# ---------------------------------------------------------------------------
# Manifest helpers (v0.1 stub)
# ---------------------------------------------------------------------------


def load_manifest(path: Path | None = None) -> Dict[str, Any]:
    """
    Load gus_integrity.json.

    Expected minimal structure:
    {
        "essence_hash": "...",
        "locked_at": "ISO timestamp",
        "note": "string",
        "files": {
            "relative/path.py": {"sha256": "..."},
            ...
        }
    }

    If the file is missing, we return a tiny stub manifest so that tests
    can still exercise the logic without crashing.
    """
    manifest_path = path or MANIFEST_PATH
    if not manifest_path.is_file():
        # Safe stub manifest when chain file does not yet exist.
        return {
            "essence_hash": "",
            "locked_at": _iso_now(),
            "note": "stub manifest – gus_integrity.json not present",
            "files": {},
        }

    with manifest_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_manifest(
    manifest: Dict[str, Any],
    project_root: Path | None = None,
) -> IntegritySummary:
    """
    Real-ish verification stub:

    - Walks manifest["files"]
    - Computes sha256 for each listed file
    - Compares with expected
    """
    root = project_root or PROJECT_ROOT
    files_meta = manifest.get("files", {})
    results: List[FileIntegrityResult] = []

    for rel_path, meta in files_meta.items():
        expected = str(meta.get("sha256") or "")
        file_path = root / rel_path

        if not file_path.is_file():
            results.append(
                FileIntegrityResult(
                    path=rel_path,
                    expected_hash=expected,
                    actual_hash="MISSING",
                    ok=False,
                )
            )
            continue

        actual = _sha256_file(file_path)
        results.append(
            FileIntegrityResult(
                path=rel_path,
                expected_hash=expected,
                actual_hash=actual,
                ok=(expected != "" and expected == actual),
            )
        )

    total = len(results)
    ok_count = sum(1 for r in results if r.ok)

    if total == 0:
        engine_ok = False
        reason = "Layer 1 integrity manifest has no files registered"
    else:
        engine_ok = (ok_count == total)
        reason = f"Layer 1 integrity: {ok_count}/{total} files match manifest"

    return IntegritySummary(
        engine_ok=engine_ok,
        reason=reason,
        checked_at=_iso_now(),
        files=results,
    )


# ---------------------------------------------------------------------------
# Public API expected by tests & engine_health
# ---------------------------------------------------------------------------


def verify_integrity() -> IntegritySummary:
    """
    Convenience wrapper expected by tests.

    - Loads manifest from the default path
    - Verifies all files in it
    - Returns IntegritySummary
    """
    manifest = load_manifest()
    return verify_manifest(manifest)


def summarize_integrity_status(
    results: Sequence[FileIntegrityResult],
) -> IntegrityStatus:
    """
    Collapse a list of per-file integrity results into a high-level status.

    This is a *pure* summariser: tests will mostly care about the
    boolean + message.
    """
    total = len(results)
    failed = [r for r in results if not r.ok]
    failed_count = len(failed)

    engine_ok = failed_count == 0

    if total == 0:
        reason = "no files checked"
    elif engine_ok:
        reason = f"{total} files checked; all passed"
    else:
        reason = f"{failed_count}/{total} files failed integrity"

    return IntegrityStatus(
        engine_ok=engine_ok,
        reason=reason,
        checked_at=_iso_now(),
    )


def load_integrity_status() -> IntegrityStatus:
    """
    Entry point expected by tests:

    - Loads manifest
    - Verifies it
    - Summarises to IntegrityStatus
    """
    manifest = load_manifest()
    summary = verify_manifest(manifest)
    return summarize_integrity_status(summary.files)


def run_integrity_check(manifest_path: Path | None = None) -> Dict[str, Any]:
    """
    Public dict-based API used by gus_engine_health & CLI.

    Returns a simple dict so higher layers don’t need dataclasses.
    """
    manifest = load_manifest(manifest_path)
    summary = verify_manifest(manifest)

    return {
        "engine_ok": summary.engine_ok,
        "reason": summary.reason,
        "checked_at": summary.checked_at,
        "files_checked": len(summary.files),
        "details": [
            {
                "path": r.path,
                "expected_hash": r.expected_hash,
                "actual_hash": r.actual_hash,
                "ok": r.ok,
            }
            for r in summary.files
        ],
    }

def load_integrity_status() -> IntegrityStatus:
    """
    Legacy-style API used by early tests.

    For now, we:
      - run the integrity check against the manifest (if present)
      - map it into a simple IntegrityStatus
      - errors[] is a simple list of human-readable strings for any failing files
    """
    summary_dict = run_integrity_check()

    engine_ok = bool(summary_dict.get("engine_ok", False))
    reason = summary_dict.get("reason", "no reason provided")

    errors: List[str] = []
    for item in summary_dict.get("details", []):
        if not item.get("ok", False):
            errors.append(
                f"{item.get('path', '?')} mismatch "
                f"(expected={item.get('expected_hash')}, actual={item.get('actual_hash')})"
            )

    return IntegrityStatus(ok=engine_ok, reason=reason, errors=errors)

def verify_integrity() -> bool:
    """
    Backwards-compatible stub for tests.

    Returns:
        True if integrity is OK (no failing files or manifest missing),
        False otherwise.
    """
    status = load_integrity_status()
    return bool(status.ok)

__all__ = [
    "FileIntegrityResult",
    "IntegritySummary",
    "IntegrityStatus",
    "run_integrity_check",
    "summarize_integrity_status",
    "load_integrity_status",
    "verify_integrity",
]

if __name__ == "__main__":
    # Optional local debug: python -m layer1_integrity_core.L1_integrity_core_stub
    result = run_integrity_check()
    print(json.dumps(result, indent=2))
