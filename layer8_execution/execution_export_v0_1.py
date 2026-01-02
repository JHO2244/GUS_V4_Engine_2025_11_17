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
"""

from __future__ import annotations

from dataclasses import is_dataclass, asdict
from typing import Any, Mapping, Dict, List

from .execution_record_v0_1 import ExecutionRecord


_JSON_PRIMITIVE = (str, int, float, bool, type(None))


def _to_json_safe(obj: Any) -> Any:
    # primitives
    if isinstance(obj, _JSON_PRIMITIVE):
        return obj

    # dataclasses -> dict
    if is_dataclass(obj):
        return _to_json_safe(asdict(obj))

    # mappings
    if isinstance(obj, Mapping):
        out: Dict[str, Any] = {}
        for k, v in obj.items():
            if not isinstance(k, str):
                raise TypeError(f"Non-string key not allowed in export: {k!r}")
            out[k] = _to_json_safe(v)
        return out

    # tuples/lists -> lists
    if isinstance(obj, (list, tuple)):
        return [_to_json_safe(x) for x in obj]

    raise TypeError(f"Non-JSON-safe type in export: {type(obj).__name__}")


def export_execution_record(record: ExecutionRecord) -> Dict[str, Any]:
    """
    Deterministic JSON-safe export of ExecutionRecord.

    Note: Dict insertion order in Python is deterministic; downstream canonical writer
    will enforce stable serialization.
    """
    if not isinstance(record, ExecutionRecord):
        raise TypeError("record must be an ExecutionRecord")

    payload: Dict[str, Any] = {
        "execution_id": record.execution_id,
        "decision_hash": record.decision_hash,
        "result": _to_json_safe(record.result),
        "audit_trace": _to_json_safe(record.audit_trace),
        "side_effect_events": _to_json_safe(record.side_effect_events),
        "record_hash": record.record_hash,
    }
    return _to_json_safe(payload)
