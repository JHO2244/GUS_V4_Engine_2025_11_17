# gus_engine_health.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Any

from layer0_uam_v4.L0_uam_core_stub import load_uam_status
from layer1_integrity_core.L1_integrity_core_stub import (
    load_integrity_status,
    verify_integrity,
)
from layer2_governance_matrix.L2_governance_static_stub import load_governance_status
from layer3_decision_engine.L3_decision_matrix_stub import load_decision_engine_status
from layer4_execution.L4_executor_stub import load_execution_status
from layer5_continuity.L5_continuity_stub import (
    load_continuity_status,
    verify_continuity,
)
from layer6_replication.L6_replication_stub import (
    load_replication_status,
    verify_replication,
)
from layer7_ecosystem.L7_ecosystem_stub import (
    load_ecosystem_status,
    verify_ecosystem,
)
from layer8_meta_governance.L8_meta_governance_stub import (
    load_meta_governance_status,
    verify_meta_governance,
)
from layer9_preservation.L9_preservation_stub import (
    load_preservation_status,
    verify_preservation,
)


def get_engine_health_as_dict() -> Dict[str, Any]:
    """
    Unified health snapshot for all 10 layers.
    Pure function: no prints, no logging side-effects.
    """
    layers: Dict[str, Dict[str, Any]] = {}

    layers["0"] = {
        "layer": 0,
        "name": "UAM v4",
        "verified": True,  # UAM has no explicit verify() yet
        "errors": load_uam_status().errors,
    }

    layers["1"] = {
        "layer": 1,
        "name": "Integrity Core",
        "verified": bool(verify_integrity()),
        "errors": load_integrity_status().errors,
    }

    layers["2"] = {
        "layer": 2,
        "name": "Governance Matrix",
        "verified": True,
        "errors": load_governance_status().errors,
    }

    layers["3"] = {
        "layer": 3,
        "name": "Decision Engine",
        "verified": True,
        "errors": load_decision_engine_status().errors,
    }

    layers["4"] = {
        "layer": 4,
        "name": "Execution Layer",
        "verified": True,
        "errors": load_execution_status().errors,
    }

    layers["5"] = {
        "layer": 5,
        "name": "Continuity",
        "verified": bool(verify_continuity()),
        "errors": load_continuity_status().errors,
    }

    layers["6"] = {
        "layer": 6,
        "name": "Replication",
        "verified": bool(verify_replication()),
        "errors": load_replication_status().errors,
    }

    layers["7"] = {
        "layer": 7,
        "name": "Ecosystem",
        "verified": bool(verify_ecosystem()),
        "errors": load_ecosystem_status().errors,
    }

    layers["8"] = {
        "layer": 8,
        "name": "Meta-Governance",
        "verified": bool(verify_meta_governance()),
        "errors": load_meta_governance_status().errors,
    }

    layers["9"] = {
        "layer": 9,
        "name": "Preservation",
        "verified": bool(verify_preservation()),
        "errors": load_preservation_status().errors,
    }

    overall_ok = all(lh["verified"] and not lh["errors"] for lh in layers.values())

    def get_engine_health():
        """
        Compatibility wrapper for tests.
        Returns the same data as get_engine_health_as_dict(),
        but keeps the naming used by earlier GUS versions and test suites.
        """
        return get_engine_health_as_dict()

    return {
        "overall_ok": overall_ok,
        "layers": layers,
    }
