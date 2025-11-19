"""
hash_tools_stub.py
GUS v4 – simple hashing helpers (skeleton, but real SHA-256).
"""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import Any, Dict
import json


def compute_sha256(text: str) -> str:
    """Return the hex SHA-256 of the given text."""
    if not isinstance(text, str):
        text = str(text)
    return sha256(text.encode("utf-8")).hexdigest()


def compute_file_sha256(path: Path) -> str:
    """Return SHA-256 of file contents, or empty string if file doesn't exist."""
    if not path.exists() or not path.is_file():
        return ""
    h = sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def hash_payload(payload: Dict[str, Any]) -> str:
    """Stable hash for dict-like payloads (sorted keys)."""
    data = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    return compute_sha256(data)
