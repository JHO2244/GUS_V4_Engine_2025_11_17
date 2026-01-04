"""
GUS v4.0 — L8 Execution Layer
Execution Export v0.1

Purpose:
- Deterministic, JSON-safe export of ExecutionRecord for downstream audit/replication layers.
- Fail-closed: raises TypeError on non-serializable structures.

Contract v0.1:
- export_execution_record(record) returns only JSON-safe primitives:
  dict/list/str/int/float/bool/None
- Tuples are converted to lists (stable order preserved).
- Mappings are exported with lexicographically sorted string keys (deterministic).
"""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any, Dict, Mapping

from .execution_record_v0_1 import ExecutionRecord


_JSON_PRIMITIVE = (str, int, float, bool, type(None))


def _to_json_safe(obj: Any) -> Any:
    # primitives
    if isinstance(obj, _JSON_PRIMITIVE):
        return obj

    # dataclasses -> dict
    if is_dataclass(obj):
        return _to_json_safe(asdict(obj))

    # mappings (deterministic key order)
    if isinstance(obj, Mapping):
        out: Dict[str, Any] = {}
        for k in sorted(obj.keys()):
            if not isinstance(k, str):
                raise TypeError(f"Non-string key not allowed in export: {k!r}")
            out[k] = _to_json_safe(obj[k])
        return out

    # tuples/lists -> lists
    if isinstance(obj, (list, tuple)):
        return [_to_json_safe(x) for x in obj]

    raise TypeError(f"Non-JSON-safe type in export: {type(obj).__name__}")


def export_execution_record(record: ExecutionRecord) -> Dict[str, Any]:
    """
    Deterministic JSON-safe export of ExecutionRecord.

    Downstream canonical writer enforces stable serialization; we also sort mapping keys
    here to guarantee deterministic structure even before serialization.
    """
    if not isinstance(record, ExecutionRecord):
        raise TypeError("record must be an ExecutionRecord")

    payload: Dict[str, Any] = {
        "execution_id": record.execution_id,
        "decision_hash": record.decision_hash,
        "result": _to_json_safe(record.result),
        "audit_trace": _to_json_safe(record.audit_trace),
        "side_effect_events": _to_json_safe(record.side_effect_events),
        "policy_verdict": _to_json_safe(record.policy_verdict),
        "record_hash": record.record_hash,
    }
    return _to_json_safe(payload)
