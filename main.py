from __future__ import annotations

from pprint import pprint

from gus_engine_health import get_engine_health_as_dict
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

try:
    from pas.pas_seal_engine_stub import generate_seal_proto  # optional stub
except Exception:
    generate_seal_proto = None

from utils import get_guardian_logger

if __name__ == "__main__":
    if generate_seal_proto is None:
        print("Proto Seal Generated: SKIPPED (generate_seal_proto not available)")
    else:
        seal = generate_seal_proto(scope="PAS_L5_L9")
        print("Proto Seal Generated:")
        print(vars(seal))

logger = get_guardian_logger("GUSv4.Main")


def print_header(title: str) -> None:
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def main() -> None:
    print_header("GUS v4 – Skeleton Diagnostic (Layers 0–9)")

    # ---------------------------------------------------------
    # Layer 0 – UAM v4
    # ---------------------------------------------------------
    print_header("Layer 0 – UAM v4 Status")
    uam_status = load_uam_status()
    pprint(uam_status.__dict__)

    # ---------------------------------------------------------
    # Layer 1 – Integrity Core
    # ---------------------------------------------------------
    print_header("Layer 1 – Integrity Core Status")
    integrity_status = load_integrity_status()
    pprint(integrity_status)

    print_header("Layer 1 – Integrity Verification Result")
    print(f"verify_integrity() => {verify_integrity()}")

    # ---------------------------------------------------------
    # Layer 2 – Governance Matrix
    # ---------------------------------------------------------
    print_header("Layer 2 – Governance Matrix Status")
    governance_status = load_governance_status()
    pprint(governance_status.__dict__)

    # ---------------------------------------------------------
    # Layer 3 – Decision Engine
    # ---------------------------------------------------------
    print_header("Layer 3 – Decision Engine Status")
    decision_status = load_decision_engine_status()
    pprint(decision_status.__dict__)

    # ---------------------------------------------------------
    # Layer 4 – Execution Layer
    # ---------------------------------------------------------
    print_header("Layer 4 – Execution Layer Status")
    l4_status = load_execution_status()
    pprint(l4_status.__dict__)

    # ---------------------------------------------------------
    # Layer 5 – Continuity
    # ---------------------------------------------------------
    print_header("Layer 5 – Continuity Layer Status")
    l5_status = load_continuity_status()
    print(l5_status)

    print_header("Layer 5 – Continuity Verification Result")
    print(f"verify_continuity() => {verify_continuity()}")

    # ---------------------------------------------------------
    # Layer 6 – Replication
    # ---------------------------------------------------------
    print_header("Layer 6 – Replication Status")
    l6_status = load_replication_status()
    print(l6_status)

    print_header("Layer 6 – Replication Verification Result")
    print(f"verify_replication() => {verify_replication()}")

    # ---------------------------------------------------------
    # Layer 7 – Ecosystem
    # ---------------------------------------------------------
    print_header("Layer 7 – Ecosystem Status")
    l7_status = load_ecosystem_status()
    print(l7_status)

    print_header("Layer 7 – Ecosystem Verification Result")
    print(f"verify_ecosystem() => {verify_ecosystem()}")

    # ---------------------------------------------------------
    # Layer 8 – Meta-Governance
    # ---------------------------------------------------------
    print_header("Layer 8 – Meta-Governance Status")
    l8_status = load_meta_governance_status()
    print(l8_status)

    print_header("Layer 8 – Meta-Governance Verification Result")
    print(f"verify_meta_governance() => {verify_meta_governance()}")

    # ---------------------------------------------------------
    # Layer 9 – Preservation
    # ---------------------------------------------------------
    print_header("Layer 9 – Preservation Status")
    l9_status = load_preservation_status()
    print(l9_status)

    print_header("Layer 9 – Preservation Verification Result")
    print(f"verify_preservation() => {verify_preservation()}")

    # ------------------------------------------------------------
    # Unified Engine Health Summary
    # ------------------------------------------------------------
    print("\n============================================================")
    print("GUS v4 – Unified Engine Health Summary")
    print("============================================================")

    engine_health = get_engine_health_as_dict()
    print(f"overall_ok => {engine_health['overall_ok']}")

    for layer_id, lh in engine_health["layers"].items():
        print(
            f"Layer {lh['layer']} ({lh['name']}): "
            f"verified={lh['verified']}, errors={len(lh['errors'])}"
        )

    print("\n[GUS v4] Diagnostics run complete.")


if __name__ == "__main__":
    main()
