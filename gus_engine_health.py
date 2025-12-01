"""
gus_engine_health.py
GUS v4 — Unified Engine Health Summary
"""

from dataclasses import dataclass, asdict
from typing import Any, Dict

# 🔹 Adjust these imports to match your actual file + function names

# Layer 0 – UAM
from layer0_uam.L0_uam_stub import load_uam_status

# Layer 1 – Integrity
from layer1_integrity_core.L1_integrity_core_stub import (
    load_integrity_status,
    verify_integrity,
)

# Layer 2 – Governance
from layer2_governance_matrix.L2_governance_stub import (
    load_governance_status,
    # if you have a verify function, import it here:
    # verify_governance,
)

# Layer 3 – Decision
from layer3_decision_engine.L3_decision_stub import (
    load_decision_schema_status,
)

# Layer 4 – Execution
from layer4_execution.L4_execution_stub import (
    load_execution_status,
)

# Layer 5 – Continuity
from layer5_continuity.L5_continuity_stub import (
    load_continuity_status,
    verify_continuity,
)

# Layer 6 – Replication
from layer6_replication.L6_replication_stub import (
    load_replication_status,
    verify_replication,
)

# Layer 7 – Ecosystem
from layer7_ecosystem.L7_ecosystem_stub import (
    load_ecosystem_status,
    verify_ecosystem,
)

# Layer 8 – Meta-Governance
from layer8_meta_governance.L8_meta_governance_stub import (
    load_meta_governance_status,
    verify_meta_governance,
)

# Layer 9 – Preservation
from layer9_preservation.L9_preservation_stub import (
    load_preservation_status,
    verify_preservation,
)


@dataclass
class LayerHealth:
    layer: int
    name: str
    status: Any
    verified: bool
    errors: list[str]


@dataclass
class EngineHealth:
    overall_ok: bool
    layers: Dict[int, LayerHealth]


def _extract_errors(status: Any) -> list[str]:
    """
    Helper that tries to pull an 'errors' attribute or key from status.
    Falls back to [] if not present.
    """
    if hasattr(status, "errors"):
        return list(getattr(status, "errors") or [])
    if isinstance(status, dict) and "errors" in status:
        return list(status.get("errors") or [])
    return []


def get_engine_health() -> EngineHealth:
    """
    Collects health from Layers 0–9 and returns a unified summary.
    This is the primary GUS v4 engine health interface.
    """

    layers: Dict[int, LayerHealth] = {}

    # 🔹 Layer 0 – UAM
    uam_status = load_uam_status()
    layers[0] = LayerHealth(
        layer=0,
        name="UAM v4",
        status=uam_status,
        verified=True,  # no verify function yet, but we mark it as loaded
        errors=_extract_errors(uam_status),
    )

    # 🔹 Layer 1 – Integrity
    l1_status = load_integrity_status()
    l1_verified = bool(verify_integrity())
    layers[1] = LayerHealth(
        layer=1,
        name="Integrity Core",
        status=l1_status,
        verified=l1_verified,
        errors=_extract_errors(l1_status),
    )

    # 🔹 Layer 2 – Governance
    l2_status = load_governance_status()
    # If you later add verify_governance(), change this:
    l2_verified = True
    layers[2] = LayerHealth(
        layer=2,
        name="Governance Matrix",
        status=l2_status,
        verified=l2_verified,
        errors=_extract_errors(l2_status),
    )

    # 🔹 Layer 3 – Decision
    l3_status = load_decision_schema_status()
    layers[3] = LayerHealth(
        layer=3,
        name="Decision Engine",
        status=l3_status,
        verified=True,
        errors=_extract_errors(l3_status),
    )

    # 🔹 Layer 4 – Execution
    l4_status = load_execution_status()
    layers[4] = LayerHealth(
        layer=4,
        name="Execution Layer",
        status=l4_status,
        verified=True,
        errors=_extract_errors(l4_status),
    )

    # 🔹 Layer 5 – Continuity
    l5_status = load_continuity_status()
    l5_verified = bool(verify_continuity())
    layers[5] = LayerHealth(
        layer=5,
        name="Continuity Layer",
        status=l5_status,
        verified=l5_verified,
        errors=_extract_errors(l5_status),
    )

    # 🔹 Layer 6 – Replication
    l6_status = load_replication_status()
    l6_verified = bool(verify_replication())
    layers[6] = LayerHealth(
        layer=6,
        name="Replication Layer",
        status=l6_status,
        verified=l6_verified,
        errors=_extract_errors(l6_status),
    )

    # 🔹 Layer 7 – Ecosystem
    l7_status = load_ecosystem_status()
    l7_verified = bool(verify_ecosystem())
    layers[7] = LayerHealth(
        layer=7,
        name="Ecosystem Layer",
        status=l7_status,
        verified=l7_verified,
        errors=_extract_errors(l7_status),
    )

    # 🔹 Layer 8 – Meta-Governance
    l8_status = load_meta_governance_status()
    l8_verified = bool(verify_meta_governance())
    layers[8] = LayerHealth(
        layer=8,
        name="Meta-Governance Layer",
        status=l8_status,
        verified=l8_verified,
        errors=_extract_errors(l8_status),
    )

    # 🔹 Layer 9 – Preservation
    l9_status = load_preservation_status()
    l9_verified = bool(verify_preservation())
    layers[9] = LayerHealth(
        layer=9,
        name="Preservation Layer",
        status=l9_status,
        verified=l9_verified,
        errors=_extract_errors(l9_status),
    )

    # Overall OK if:
    #  - every layer is verified=True
    #  - every errors list is empty
    overall_ok = all(
        lh.verified and not lh.errors for lh in layers.values()
    )

    return EngineHealth(overall_ok=overall_ok, layers=layers)


def get_engine_health_as_dict() -> Dict[str, Any]:
    """
    Convenience wrapper to convert EngineHealth into plain dicts
    (more friendly for JSON or logs).
    """
    health = get_engine_health()
    return {
        "overall_ok": health.overall_ok,
        "layers": {
            layer_id: {
                "layer": lh.layer,
                "name": lh.name,
                "verified": lh.verified,
                "errors": lh.errors,
                "status": (
                    asdict(lh.status) if hasattr(lh.status, "__dict__") else lh.status
                ),
            }
            for layer_id, lh in health.layers.items()
        },
    }
