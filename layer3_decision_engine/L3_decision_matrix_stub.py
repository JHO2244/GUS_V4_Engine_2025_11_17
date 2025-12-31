# Placeholder for decision selection logic
from __future__ import annotations

"""
GUS v4 – Layer 3 Decision Engine stub.

Skeleton responsibilities:
- Load the L3 decision schema JSON.
- Expose a DecisionEngineStatus snapshot.
- Provide no real decision logic yet (safe, read-only).
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from utils import load_json_config, get_guardian_logger

BASE_DIR = Path(__file__).resolve().parent
SCHEMA_PATH = BASE_DIR / "L3_schema.json"

logger = get_guardian_logger("GUSv4.Layer3")


@dataclass
class DecisionEngineStatus:
    schema_loaded: bool
    schema_version: str
    fields_count: int
    errors: List[str]


def load_decision_engine_status() -> DecisionEngineStatus:
    errors: List[str] = []

    data: Optional[Dict] = load_json_config(SCHEMA_PATH)
    if data is None:
        errors.append("Failed to load L3_schema.json.")
        logger.warning("Decision Engine status loaded with issues: %s", "; ".join(errors))
        return DecisionEngineStatus(
            schema_loaded=False,
            schema_version="unknown",
            fields_count=0,
            errors=errors,
        )

    schema_version = str(data.get("schema_version", "unknown"))
    fields = data.get("fields", {})
    fields_count = len(fields) if isinstance(fields, dict) else 0

    logger.info("Decision Engine schema loaded successfully (version=%s, fields=%s).",
                schema_version, fields_count)

    return DecisionEngineStatus(
        schema_loaded=True,
        schema_version=schema_version,
        fields_count=fields_count,
        errors=errors,
    )

def run_decision(context: Dict, requested_action: str, layer_origin: int) -> Dict:
    """
    Minimal working Layer 3 pipeline (safe, deterministic).
    Flow: Context Evaluator -> Decision Object -> Authorization -> Status.
    """
    # Local imports to avoid circular imports during skeleton phase
    from layer3_decision_engine.L3_context_evaluator_stub import evaluate_context
    from layer3_decision_engine.L3_authorization_stub import authorize_decision

    # Basic input validation (schema-aligned, minimal)
    if not isinstance(context, dict):
        raise TypeError("context must be a dict")
    if not isinstance(requested_action, str) or not requested_action.strip():
        raise ValueError("requested_action must be a non-empty string")
    if not isinstance(layer_origin, int) or layer_origin < 0 or layer_origin > 4:
        raise ValueError("layer_origin must be an int in range 0–4")

    # Context gate
    context_ok = evaluate_context(context)

    decision: Dict = {
        "decision_id": "L3-SKELETON-001",
        "requested_action": requested_action.strip(),
        "layer_origin": layer_origin,
        "status": "pending",
    }

    if not context_ok:
        decision["status"] = "aborted"
        logger.warning("Decision aborted: context evaluator rejected context.")
        return decision

    # Authorization gate
    authorized = authorize_decision(decision)
    decision["status"] = "approved" if authorized else "denied"

    logger.info(
        "run_decision(): status=%s action=%s origin=%s",
        decision["status"],
        decision["requested_action"],
        decision["layer_origin"],
    )
    return decision
