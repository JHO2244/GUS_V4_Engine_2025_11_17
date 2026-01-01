from __future__ import annotations

import json
from typing import Any, Dict

# Canonical JSON rules (contract):
# - sort_keys=True
# - separators=(",", ":")  (minified, deterministic)
# - ensure_ascii=True      (portable across envs)
# - output ends with ONE trailing newline
# NOTE: Do NOT indent. Indent changes hashes and breaks determinism.

def canonical_dumps(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)

def canonical_json_bytes(obj: Any) -> bytes:
    return canonical_dumps(obj).encode("utf-8")

def canonical_json_line(obj: Any) -> str:
    return canonical_dumps(obj) + "\n"

def to_jsonable_dict(obj: Any) -> Dict[str, Any]:
    to_dict = getattr(obj, "to_dict", None)
    if callable(to_dict):
        out = to_dict()
        if isinstance(out, dict):
            return out
    if isinstance(obj, dict):
        return obj
    raise TypeError(f"Object is not JSON-serializable dict: {type(obj)}")
