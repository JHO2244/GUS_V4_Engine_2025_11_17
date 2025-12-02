import hashlib
from datetime import datetime
from typing import Any, Dict

class PASSeal:
    def __init__(self, version: str, scope: str, issuer: str, timestamp: str, payload_hash: str):
        self.version = version
        self.scope = scope
        self.issuer = issuer
        self.timestamp = timestamp
        self.payload_hash = payload_hash

def compute_hash(payload: dict) -> str:
    raw = str(payload).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()

def generate_seal_proto(scope: str, issuer: str = "JHO") -> PASSeal:
    timestamp = datetime.utcnow().isoformat()
    payload = {
        "scope": scope,
        "issuer": issuer,
        "timestamp": timestamp,
    }
    payload_hash = compute_hash(payload)
    return PASSeal(
        version="PAS.v1.0-proto",
        scope=scope,
        issuer=issuer,
        timestamp=timestamp,
        payload_hash=payload_hash
    )

from pathlib import Path
from typing import Dict, Any, List
import json

from utils import get_guardian_logger

logger = get_guardian_logger("GUSv4.PAS.Stage")

STAGE_LOG_PATH = Path("logs") / "gus_stage_log.json"


def build_phase2_continuity_payload(engine_summary: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build a canonical payload for:
    GUS v4 – Phase 2 Initialization (Continuity Layer Awakening).
    """
    return {
        "scope": "GUS_v4_Phase2_Continuity_Awakening",
        "stage": "Phase2_Continuity_Layer",
        "engine_overall_ok": bool(engine_summary.get("overall_ok", True)),
        "engine_layers": engine_summary.get("layers", {}),
        "meta": {
            "note": "First continuity-stage seal after L0–L9 skeleton + PAS proto online.",
        },
    }


def append_stage_seal_to_log(seal: PASSeal, log_path: Path = STAGE_LOG_PATH) -> None:
    """
    Append the PAS seal to logs/gus_stage_log.json in a simple list structure.
    Creates the file if it does not exist.
    """
    log_path.parent.mkdir(parents=True, exist_ok=True)

    if log_path.exists():
        try:
            existing: List[Dict[str, Any]] = json.loads(log_path.read_text(encoding="utf-8"))
            if not isinstance(existing, list):
                logger.warning("Stage log %s is not a list; resetting.", log_path)
                existing = []
        except Exception as exc:  # pragma: no cover (defensive)
            logger.error("Failed to read existing stage log at %s: %s", log_path, exc)
            existing = []
    else:
        existing = []

    entry = {
        "version": seal.version,
        "created_at": seal.created_at,
        "issuer": seal.issuer,
        "scope": seal.scope,
        "payload_hash": seal.payload_hash,
    }
    existing.append(entry)

    log_path.write_text(json.dumps(existing, indent=2), encoding="utf-8")
    logger.info("Appended PAS stage seal to %s (entries=%d).", log_path, len(existing))

def generate_pas_seal(payload: Dict[str, Any], issuer: str) -> Dict[str, Any]:
    """
    Tiny PAS seal stub for Phase 2.

    In the real engine this would:
      - normalize payload
      - attach cryptographic signatures
      - write to PAS ledger

    For now we just:
      - wrap the payload with issuer + UTC timestamp
      - mark this clearly as a stub object
    """
    return {
        "seal_version": "PAS_v4_phase2_stub",
        "issuer": issuer,
        "issued_at": datetime.utcnow().isoformat() + "Z",
        "payload": payload,
    }

def mint_phase2_continuity_seal() -> dict:
    """
    Produce a Phase 2 continuity seal based on current engine health.
    Safe stub: reads from gus_engine_health, returns a structured dict.
    """
    issuer = "GUS_v4_PAS_Phase2_stub"

    # Local import to avoid cycles
    from gus_engine_health import get_engine_health_summary

    engine_summary = get_engine_health_summary()

    payload = {
        "phase": "PAS_Phase2",
        "engine_health": engine_summary,
    }

    seal = generate_pas_seal(payload, issuer=issuer)
    return seal
