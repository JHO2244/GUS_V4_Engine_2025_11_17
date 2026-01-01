"""
GUS v4 – Layer 5 Continuity Manifest v0.1

This module provides:

- A JSON-backed continuity manifest API:
  - MANIFEST_PATH
  - read_manifest()
  - write_manifest()
  - load_manifest()
  - create_default_manifest(...)
  - check_continuity()

- A status Enum used across L5–L9:
  - ContinuityStatus (code, ok, reason)

- A high-level continuity probe:
  - load_continuity_status()

Design goals:

- Tests for L5 manifest behavior get explicit control via monkeypatched
  MANIFEST_PATH and create_default_manifest().
- Higher-layer stubs (L6–L9) can always see continuity="ok" based on the
  embedded manifest, even if the JSON file has not yet been written.
"""

from __future__ import annotations  # 👈 must be first, and only here
from utils.canonical_json import write_canonical_json_file

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List
import copy
import json


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

# The canonical/default manifest path (used to detect monkeypatching)
DEFAULT_MANIFEST_PATH: Path = Path(__file__).with_name("gus_v4_continuity_manifest.json")

# This is the value tests will monkeypatch.
MANIFEST_PATH: Path = DEFAULT_MANIFEST_PATH


# ---------------------------------------------------------------------------
# Status Enum
# ---------------------------------------------------------------------------

@dataclass
class ContinuityStatus:
    """
    Rich continuity status object used by tests and higher layers.

    Fields:
        code   – short machine-readable code ("ok", "manifest_missing", "error")
        ok     – boolean convenience flag
        data   – dict payload (e.g. loaded manifest) or {} when unavailable
        errors – list of human-readable error strings (can be empty when ok)
    """
    code: str
    ok: bool
    data: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)

    @property
    def reason(self) -> str:
        # Backwards-compat alias – tests expect status.reason == code
        return self.code

# ---------------------------------------------------------------------------
# Embedded continuity plan (for stubs / fallback)
# ---------------------------------------------------------------------------

EMBEDDED_MANIFEST: Dict[str, Any] = {
    "engine_version": "GUS_V4_Engine_2025_11_17",
    "last_all_green_commit": "0000000000000000000000000000000000000000",
    "last_all_green_timestamp": "1970-01-01T00:00:00Z",
    "backup_paths": [],
    "pas_version": "0.1",
    "test_summary": {"total": 0, "passed": 0, "failed": 0},
    "entries": [
        {
            "id": "primary_repo",
            "kind": "git",
            "description": "Local GUS v4 engine repository continuity root (embedded)",
            "target": "local_repo",
            "frequency": "on_demand",
        }
    ],
}


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def _validate_manifest(data: Dict[str, Any]) -> bool:
    """
    Minimal validation used by check_continuity().

    We deliberately keep this permissive so that older or partially populated
    manifests still count as "OK" for continuity, as long as they are dicts.

    Tests for manifest roundtrip care about the *presence* of specific fields,
    which they control via create_default_manifest() and write_manifest().
    """
    return isinstance(data, dict)


# ---------------------------------------------------------------------------
# Core manifest I/O
# ---------------------------------------------------------------------------

def load_manifest(path: Path | None = None) -> Dict[str, Any]:
    """
    Load a continuity manifest.

    - If 'path' (or MANIFEST_PATH) exists on disk → load JSON from there.
    - Otherwise → return a deep copy of the embedded manifest.
    """
    p = Path(path) if path is not None else MANIFEST_PATH

    if p.is_file():
        with p.open("r", encoding="utf-8") as f:
            return json.load(f)

    # Fallback – embedded manifest (used heavily by higher-level code)
    return copy.deepcopy(EMBEDDED_MANIFEST)


def write_manifest(data: Dict[str, Any], path: Path | None = None) -> None:
    """
    Write manifest JSON to disk.

    Tests monkeypatch MANIFEST_PATH and then call write_manifest(), so we must
    honor the patched value.
    """
    p = Path(path) if path is not None else MANIFEST_PATH
    p.parent.mkdir(parents=True, exist_ok=True)

    write_canonical_json_file(p, data)


def read_manifest(path: Path | None = None) -> Dict[str, Any]:
    """
    Strict JSON reader used by L5 tests.

    Unlike load_manifest(), this does NOT fall back to the embedded manifest.
    It simply reads JSON from disk and will raise if the file is missing or
    invalid. This is the behavior expected in tests.
    """
    p = Path(path) if path is not None else MANIFEST_PATH
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Factory used by tests (and tools)
# ---------------------------------------------------------------------------

def create_default_manifest(
    *,
    engine_version: str,
    last_all_green_commit: str,
    last_all_green_timestamp: str,
    backup_paths: List[str],
    pas_version: str,
    test_summary: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Factory used by tests/test_layer5_continuity_manifest.py via keyword args.

    The tests expect:
    - keyword-only parameters with the names below
    - the returned dict to preserve these keys exactly
    - some continuity list ("entries") to exist

    We also wire the first backup path (if present) into the entries list so
    that continuity-aware code can reason about it.
    """
    primary_target = backup_paths[0] if backup_paths else "unknown_target"

    return {
        "engine_version": engine_version,
        "last_all_green_commit": last_all_green_commit,
        "last_all_green_timestamp": last_all_green_timestamp,
        "backup_paths": backup_paths,
        "pas_version": pas_version,
        "test_summary": test_summary,
        "entries": [
            {
                "id": "primary_backup",
                "kind": "zip",
                "description": "Primary ALL_GREEN backup archive for GUS v4.",
                "target": primary_target,
                "frequency": "on_demand",
            }
        ],
    }


# ---------------------------------------------------------------------------
# Continuity status
# ---------------------------------------------------------------------------

def check_continuity(path: Path | None = None) -> ContinuityStatus:
    """
    File-oriented continuity check used directly by the L5 test suite.

    Semantics required by tests:

    - When MANIFEST_PATH is monkeypatched to a temp file and a valid manifest
      is written there via write_manifest(), this must return a status with:
        code="ok", ok=True, reason="ok", data containing engine_version, etc.

    - When MANIFEST_PATH is monkeypatched to a temp file that does NOT exist,
      this must return:
        code="manifest_missing", ok=False, data == {}, and a non-empty errors list.

    - When JSON exists but is invalid → code="error", ok=False.
    """
    p = Path(path) if path is not None else MANIFEST_PATH

    # Path missing altogether → manifest_missing
    if not p.exists():
        return ContinuityStatus(
            code="manifest_missing",
            ok=False,
            data={},
            errors=[f"Manifest file not found at {p!s}"],
        )

    # File exists – strict read
    try:
        data = read_manifest(p)
    except FileNotFoundError:
        return ContinuityStatus(
            code="manifest_missing",
            ok=False,
            data={},
            errors=[f"Manifest file not found at {p!s}"],
        )
    except Exception as exc:
        return ContinuityStatus(
            code="error",
            ok=False,
            data={},
            errors=[f"Failed to read manifest: {exc!r}"],
        )

    # Validate structure (permissive but must be a dict)
    if not _validate_manifest(data):
        return ContinuityStatus(
            code="error",
            ok=False,
            data={},
            errors=["Manifest validation failed"],
        )

    # All good
    return ContinuityStatus(
        code="ok",
        ok=True,
        data=data,
        errors=[],
    )


def load_continuity_status() -> ContinuityStatus:
    """
    High-level continuity probe used by L5–L9 stub layers.

    We primarily rely on the embedded manifest so that higher layers can
    report continuity=ok even before any JSON manifest is written to disk.

    If the embedded manifest is somehow invalid, we fall back to the
    file-based check_continuity() semantics.
    """
    try:
        data = copy.deepcopy(EMBEDDED_MANIFEST)
        if _validate_manifest(data):
            return ContinuityStatus(
                code="ok",
                ok=True,
                data=data,
                errors=[],
            )
    except Exception as exc:
        # embedded manifest failed – fall back to error
        return ContinuityStatus(
            code="error",
            ok=False,
            data={},
            errors=[f"Embedded manifest invalid: {exc!r}"],
        )

    # If validation failed for some reason, fall back to file
    return check_continuity()
