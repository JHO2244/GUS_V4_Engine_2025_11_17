# Generic hash helpers (stub)
"""
GUS v4 STUB: Hash tools placeholder.

Provides tiny, generic helpers for computing SHA-256 hashes.
Safe to use in skeleton mode (no external dependencies, no side effects).
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Optional, Union


PathLike = Union[str, Path]


def compute_sha256(text: str) -> str:
    """
    Compute a SHA-256 hash of the given text and return the hex digest.

    In skeleton mode this is a simple wrapper around hashlib.sha256.
    """
    if text is None:
        text = ""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def compute_file_sha256(path: PathLike) -> Optional[str]:
    """
    Best-effort SHA-256 hash of a file.

    Returns:
        - hex digest string on success
        - None if the file cannot be read (skeleton mode: no exceptions raised)
    """
    try:
        data = Path(path).read_bytes()
    except OSError:
        return None
    return hashlib.sha256(data).hexdigest()
