from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Union


PathLike = Union[str, Path]


def sha256_hex(data: bytes) -> str:
    """
    Return the SHA-256 hex digest for the given bytes.
    """
    h = hashlib.sha256()
    h.update(data)
    return h.hexdigest()


def hash_text(text: str, *, encoding: str = "utf-8") -> str:
    """
    Convenience helper: hash a text string using UTF-8 by default.
    """
    return sha256_hex(text.encode(encoding))


def hash_file(path: PathLike, *, chunk_size: int = 65536) -> str:
    """
    Stream a file and return its SHA-256 hex digest.
    """
    p = Path(path)
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()
