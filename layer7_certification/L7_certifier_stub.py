from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict

from utils import load_json_config, get_guardian_logger

logger = get_guardian_logger("GUSv4.Layer7")

L5_LOCK_PATH = "layer5_continuity/L5_lock_manifest.json"
L6_LOCK_PATH = "layer6_replication/L6_lock_manifest.json"


@dataclass
class CertificationResult:
    ok: bool
    certificate: Dict[str, Any] | None
    error: str | None


def _locked(path: str) -> bool:
    data = load_json_config(path)
    return bool(data and data.get("locked") is True)


def _stable_receipt_hash(payload: Dict[str, Any]) -> str:
    # Deterministic: JSON canonical sort + utf-8, then sha256 hex
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def issue_certificate(
    subject: Dict[str, Any],
    scores: Dict[str, Any],
    engine_version: str = "GUS_v4.dev",
    notes: str = "skeleton",
) -> CertificationResult:
    """
    Skeleton certifier:
    - Requires L5 + L6 locked.
    - Emits a minimal certificate record.
    """
    if not _locked(L5_LOCK_PATH) or not _locked(L6_LOCK_PATH):
        err = "Cannot certify: L5/L6 must be locked."
        logger.warning(err)
        return CertificationResult(ok=False, certificate=None, error=err)

    issued = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    base = {
        "schema_version": "0.1",
        "certificate_id": "L7-SKELETON-001",
        "issued_at_utc": issued,
        "engine_version": engine_version,
        "subject": subject,
        "scores": scores,
        "notes": notes,
    }
    base["receipt_hash"] = _stable_receipt_hash(base)

    logger.info("Issued certificate %s", base["certificate_id"])
    return CertificationResult(ok=True, certificate=base, error=None)
