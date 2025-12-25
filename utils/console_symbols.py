# utils/console_symbols.py
from __future__ import annotations

import os
import sys


def _truthy(v: str) -> bool:
    return v.strip().lower() in {"1", "true", "yes", "on", "y"}


def ascii_mode() -> bool:
    """
    ASCII mode is ON when:
      - GUS_ASCII=1 (manual force), OR
      - running in CI, OR
      - on Windows (safer defaults for cp1252 consoles)
    """
    if _truthy(os.getenv("GUS_ASCII", "")):
        return True

    ci = _truthy(os.getenv("CI", "")) or _truthy(os.getenv("GITHUB_ACTIONS", "")) or _truthy(os.getenv("GUS_CI", ""))
    if ci:
        return True

    return os.name == "nt"


def sym(name: str) -> str:
    """
    Return a safe symbol for console output.
    """
    if ascii_mode():
        return {
            "arrow": "->",
            "ok": "OK:",
            "check": "[OK]",
            "warn": "[WARN]",
            "fail": "[FAIL]",
            "seal": "[SEAL]",
        }.get(name, "")
    else:
        return {
            "arrow": "→",
            "ok": "OK:",
            "check": "✔",
            "warn": "⚠",
            "fail": "✖",
            "seal": "🧷",
        }.get(name, "")
