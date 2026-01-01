from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Tuple


CHARTER_PATH = Path("GUS_PURPOSE_CHARTER_v4.json")


class CharterError(RuntimeError):
    pass


@dataclass(frozen=True)
class CharterLoadResult:
    ok: bool
    charter: Dict[str, Any] | None
    error: str | None


def load_charter_v4(path: Path = CHARTER_PATH) -> CharterLoadResult:
    if not path.exists():
        return CharterLoadResult(ok=False, charter=None, error="Purpose Charter missing")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        return CharterLoadResult(ok=False, charter=None, error=f"Purpose Charter unreadable: {e}")

    # Minimal fail-closed validation aligned to test contract expectations
    try:
        if data.get("charter_version") != "v4":
            raise CharterError("charter_version must be v4")
        if float(data.get("target_rating", 0.0)) < 10.0:
            raise CharterError("target_rating must be >= 10.0")

        fp = data.get("failure_posture", {})
        on_uncertainty = fp.get("on_uncertainty")
        if on_uncertainty not in ("WARN", "BLOCK"):
            raise CharterError("failure_posture.on_uncertainty must be WARN or BLOCK")
    except Exception as e:
        return CharterLoadResult(ok=False, charter=None, error=str(e))

    return CharterLoadResult(ok=True, charter=data, error=None)


def require_charter_v4() -> Dict[str, Any]:
    r = load_charter_v4()
    if not r.ok or r.charter is None:
        raise CharterError(r.error or "Purpose Charter invalid")
    return r.charter
