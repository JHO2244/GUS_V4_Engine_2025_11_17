from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Dict, List

from layer1_integrity_core import verify_integrity


@dataclass
class LayerHealth:
    layer: str
    name: str
    engine_ok: bool
    reason: str
    files_checked: int | None = None


@dataclass
class EngineHealth:
    overall_ok: bool
    checked_at: str
    layers: Dict[str, LayerHealth]


def get_engine_health() -> EngineHealth:
    """Compute a minimal but structured engine-health snapshot.

    For PAS Phase 3 we only wire Layer 1, but the structure is future-proof:
    additional layers can be added to the mapping as they come online.
    """
    l1_ok, l1_issues = verify_integrity()

    if l1_issues:
        reason = "; ".join(issue.reason for issue in l1_issues)
    elif not l1_ok:
        # defensive fallback – should not normally happen
        reason = "unknown integrity failure"
    else:
        reason = "ok"

    checked_at = datetime.now(timezone.utc).isoformat()
    l1_health = LayerHealth(
        layer="L1",
        name="Integrity Core",
        engine_ok=l1_ok,
        reason=reason,
    )

    overall_ok = l1_ok
    return EngineHealth(
        overall_ok=overall_ok,
        checked_at=checked_at,
        layers={"L1_integrity_core": l1_health},
    )


def get_engine_health_as_dict() -> dict:
    """Return EngineHealth in a plain-dict form convenient for JSON dumping."""
    health = get_engine_health()
    return {
        "overall_ok": health.overall_ok,
        "checked_at": health.checked_at,
        "layers": {name: asdict(h) for name, h in health.layers.items()},
    }


def get_engine_health_summary() -> dict:
    """Thin alias kept for backwards compatibility with earlier PAS steps."""
    return get_engine_health_as_dict()


if __name__ == "__main__":  # pragma: no cover
    import json

    print(json.dumps(get_engine_health_summary(), indent=2))
