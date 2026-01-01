from __future__ import annotations

import hashlib
import json

from utils.canonical_json import canonical_json_bytes, canonical_json_line, canonical_dumps
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from utils.guardian_logging_stub import get_guardian_logger

logger = get_guardian_logger("GUSv4.Layer8")

BASE_DIR = Path(__file__).resolve().parent


def _resolve_ledger_path() -> Path:
    """
    Portability guarantee:
    - If GUS_V4_LEDGER_PATH is unset → default under BASE_DIR.
    - If set to a relative path → resolve under BASE_DIR (NOT CWD).
    - If set to an absolute path → use as-is.
    """
    raw = os.environ.get("GUS_V4_LEDGER_PATH")
    if not raw:
        return (BASE_DIR / "gus_v4_audit_ledger.json").resolve()

    p = Path(raw)
    if p.is_absolute():
        return p
    return (BASE_DIR / p).resolve()


LEDGER_PATH = _resolve_ledger_path()


@dataclass
class LedgerResult:
    ok: bool
    entry: Dict[str, Any] | None
    error: str | None


def _utc_now() -> str:
    # Deterministic timestamp format (no microseconds, Z suffix)
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _canonical_json(obj: Any) -> str:
    # Canonical JSON for determinism (stable hashing + stable on-disk format)
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _stable_hash(payload: Dict[str, Any]) -> str:
    blob = canonical_json_bytes(payload)
    return hashlib.sha256(blob).hexdigest()


def _load_ledger() -> Dict[str, Any]:
    if not LEDGER_PATH.exists():
        return {
            "schema_version": "0.1",
            "created_at_utc": _utc_now(),
            "entries": [],
        }
    return json.loads(LEDGER_PATH.read_text(encoding="utf-8"))


def _save_ledger(ledger: Dict[str, Any]) -> None:
    # Canonical file content (single-line JSON + trailing newline)
    LEDGER_PATH.write_text(_canonical_json(ledger) + "\n", encoding="utf-8")


def last_entry_hash() -> str:
    ledger = _load_ledger()
    entries: List[Dict[str, Any]] = ledger.get("entries", [])
    if not entries:
        return "GENESIS"
    return str(entries[-1].get("entry_hash", "GENESIS"))


def append_entry(
    decision: Dict[str, Any],
    execution: Dict[str, Any],
    certificate: Dict[str, Any],
    entry_id: str = "L8-SKELETON-001",
) -> LedgerResult:
    """
    Append-only ledger contract:
    - Loads JSON ledger file (creates if missing)
    - Appends a new entry with prev_hash and entry_hash
    - Saves back to disk
    - Fail-closed: returns ok=False + error OR raises via callers upstream
    """
    try:
        ledger = _load_ledger()
        prev = last_entry_hash()

        entry: Dict[str, Any] = {
            "schema_version": "0.1",
            "entry_id": entry_id,
            "created_at_utc": _utc_now(),
            "decision": decision,
            "execution": execution,
            "certificate": certificate,
            "prev_hash": prev,
        }

        # Hash must be computed over the entry WITHOUT entry_hash included.
        entry["entry_hash"] = _stable_hash(entry)

        ledger.setdefault("entries", []).append(entry)
        _save_ledger(ledger)

        logger.info("Ledger append ok: %s", entry_id)
        return LedgerResult(ok=True, entry=entry, error=None)
    except Exception as e:
        err = f"Ledger append failed: {e}"
        logger.warning(err)
        return LedgerResult(ok=False, entry=None, error=err)
