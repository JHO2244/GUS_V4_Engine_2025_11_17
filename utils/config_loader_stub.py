# Safe config loader (no secrets)
"""
GUS v4 STUB: Config loader placeholder.

Provides a minimal, safe JSON config loader.
No writing, no network calls, no side effects beyond reading a file.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional, Union


PathLike = Union[str, Path]


def load_json_config(path: PathLike) -> Optional[Dict[str, Any]]:
    """
    Best-effort JSON file loader.

    Returns:
        - dict on success
        - None if file is missing or JSON is invalid
    """
    p = Path(path)

    try:
        text = p.read_text(encoding="utf-8")
    except OSError:
        return None

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None
