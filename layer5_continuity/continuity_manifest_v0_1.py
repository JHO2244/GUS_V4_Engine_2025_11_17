"""Layer 5 – Continuity Manifest v0.1

Gentle continuity manifest helper for GUS v4.

Goals in v0.1:
- Observe and record key "ALL GREEN" snapshots.
- Provide a minimal check_continuity() that *does not* block development.
- Avoid any hard dependency on git – presence + shape checks only.

This will be tightened in later versions once the continuity spine matures.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

import json

MANIFEST_PATH = Path("continuity") / "gus_v4_continuity_manifest.json"


@dataclass
class ContinuityStatus:
    ok: bool
    reason: str
    data: Dict[str, Any]


def read_manifest() -> Dict[str, Any]:
    """Read the continuity manifest JSON if it exists.

    Returns an empty dict if the file is missing or unreadable.
    """
    if not MANIFEST_PATH.exists():
        return {}

    try:
        with MANIFEST_PATH.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        # If the file is corrupted, we treat it as missing at this level.
        return {}


def write_manifest(data: Dict[str, Any]) -> None:
    """Write the continuity manifest JSON to disk.

    Parent folder is created if necessary. The write is atomic enough
    for our current single-process, dev-focused use case.
    """
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    with MANIFEST_PATH.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)


def create_default_manifest(
    *,
    engine_version: str,
    last_all_green_commit: str,
    last_all_green_timestamp: str,
    backup_paths: list[str],
    pas_version: str,
    test_summary: Dict[str, Any],
) -> Dict[str, Any]:
    """Create a default manifest dict for a known ALL_GREEN state.

    This does *not* write the file – caller must invoke write_manifest().
    """
    return {
        "engine_version": engine_version,
        "last_all_green_commit": last_all_green_commit,
        "last_all_green_timestamp": last_all_green_timestamp,
        "backup_paths": list(backup_paths),
        "pas_version": pas_version,
        "test_summary": dict(test_summary),
    }


def check_continuity() -> ContinuityStatus:
    """Perform a very gentle continuity check.

    In v0.1 we only assert that:
    - A manifest exists; and
    - The minimal required fields are present.

    We deliberately do *not* compare git commits or enforce anything.
    Later versions of Layer 5 will extend this.
    """
    data = read_manifest()
    if not data:
        return ContinuityStatus(
            ok=False,
            reason="manifest_missing",
            data={},
        )

    required = [
        "engine_version",
        "last_all_green_commit",
        "last_all_green_timestamp",
        "backup_paths",
        "pas_version",
        "test_summary",
    ]
    missing = [k for k in required if k not in data]
    if missing:
        return ContinuityStatus(
            ok=False,
            reason=f"fields_missing:{','.join(missing)}",
            data=data,
        )

    return ContinuityStatus(
        ok=True,
        reason="ok",
        data=data,
    )


__all__ = [
    "MANIFEST_PATH",
    "ContinuityStatus",
    "read_manifest",
    "write_manifest",
    "create_default_manifest",
    "check_continuity",
]
