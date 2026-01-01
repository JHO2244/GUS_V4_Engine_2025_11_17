# layer9_policy_verdict/src/verdict_ledger_bridge.py

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict

from layer9_policy_verdict.src.verdict_types import PolicyVerdict
from layer8_audit_ledger.L8_ledger_stub import append_entry


class VerdictLedgerError(RuntimeError):
    pass


def append_verdict_to_ledger(verdict: PolicyVerdict) -> Dict[str, Any]:
    """
    Contract:
    - Appends verdict hash into L8 append-only ledger using L8_ledger_stub.append_entry
    - Returns the appended ledger entry dict
    - Raises VerdictLedgerError on failure (fail-closed)
    """

    decision = {
        "type": "policy_verdict",
        "verdict_hash": verdict.object_hash,
        "policy_id": verdict.policy_id,
        "level": verdict.level.value,
        "score": verdict.score,
        "epoch_ref": verdict.epoch_ref,
        "chain_head": verdict.chain_head,
    }

    execution = {
        "timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_layer": "L9",
        "target_layer": "L8",
    }

    certificate = {
        "reasons": verdict.reasons,
    }

    result = append_entry(
        decision=decision,
        execution=execution,
        certificate=certificate,
        entry_id=f"L9-VERDICT-{verdict.policy_id}"
    )

    if not result.ok or result.entry is None:
        raise VerdictLedgerError(result.error or "Ledger append failed (unknown).")

    return {
        "hash": result.entry.get("entry_hash"),
        "entry": result.entry
    }
