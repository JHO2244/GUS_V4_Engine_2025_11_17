from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, Union


# Canonical JSON rules (contract):
# - sort_keys=True
# - separators=(",", ":")   (minified, deterministic)
# - ensure_ascii=True       (portable across envs)
# - encoded as UTF-8
# - file output is SINGLE LINE + EXACTLY ONE trailing newline
# NOTE: Do NOT indent. Indent changes bytes/hashes and breaks determinism.


def canonical_dumps(obj: Any) -> str:
    """Return deterministic JSON string (no trailing newline)."""
    return json.dumps(
        obj,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )


def canonical_json_bytes(obj: Any) -> bytes:
    """Return deterministic UTF-8 bytes for hashing/storage."""
    return canonical_dumps(obj).encode("utf-8")


def canonical_json_line(obj: Any) -> str:
    """Return deterministic JSON line with one trailing newline."""
    return canonical_dumps(obj) + "\n"


def write_canonical_json_file(path: Union[str, Path], obj: Any) -> None:
    """
    Deterministic on-disk JSON artifact:
    - UTF-8
    - newline normalization to LF
    - atomic replace (same filesystem)
    - EXACTLY one trailing newline
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    payload = canonical_json_line(obj)

    fd, tmp_name = tempfile.mkstemp(prefix=path.name + ".", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            f.write(payload)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_name, path)
    finally:
        try:
            if os.path.exists(tmp_name):
                os.remove(tmp_name)
        except OSError:
            # fail-closed behavior: do not mask the original error
            pass


def to_jsonable_dict(obj: Any) -> Dict[str, Any]:
    """
    Fail-closed conversion:
    - If obj has to_dict() and it returns dict, use it.
    - If obj is dict, use it.
    - Otherwise raise.
    """
    to_dict = getattr(obj, "to_dict", None)
    if callable(to_dict):
        out = to_dict()
        if isinstance(out, dict):
            return out

    if isinstance(obj, dict):
        return obj

    raise TypeError(f"Object is not JSON-serializable dict: {type(obj)}")
