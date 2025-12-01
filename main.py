from __future__ import annotations

"""
GUS v4 – Skeleton Diagnostic Harness

This script runs a minimal health check for:
- Layer 0 (UAM v4 status)
- Layer 1 (Integrity Core status)

It is read-only and safe: it only reads local JSON and prints results.
"""

from layer2_governance_matrix.L2_governance_static_stub import load_governance_status

from layer3_decision_engine.L3_decision_matrix_stub import load_decision_engine_status

from layer4_execution.L4_executor_stub import load_execution_status

from pprint import pprint

from utils import get_guardian_logger
from layer0_uam_v4.L0_uam_core_stub import load_uam_status
from layer1_integrity_core.L1_integrity_core_stub import (
    load_integrity_status,
    verify_integrity,
)

logger = get_guardian_logger("GUSv4.Main")


def print_header(title: str) -> None:
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def main() -> None:
    print_header("GUS v4 – Skeleton Diagnostic (Layers 0 & 1)")

    # Layer 0 – UAM
    print_header("Layer 0 – UAM v4 Status")
    uam_status = load_uam_status()
    pprint(uam_status.__dict__)

    # Layer 1 – Integrity Core
    print_header("Layer 1 – Integrity Core Status")
    integrity_status = load_integrity_status()
    pprint(integrity_status)

    # Layer 1 – High-level verify call
    print_header("Layer 1 – Integrity Verification Result")
    result = verify_integrity()
    print(f"verify_integrity() => {result}")

    print("\nGUS v4 skeleton diagnostic complete.\n")

    # Layer 2 – Governance Matrix
    print_header("Layer 2 – Governance Matrix Status")
    governance_status = load_governance_status()
    pprint(governance_status.__dict__)

    # Layer 3 – Decision Engine
    print_header("Layer 3 – Decision Engine Status")
    decision_status = load_decision_engine_status()
    pprint(decision_status.__dict__)

    # Layer 4 – Execution Layer
    print_header("Layer 4 – Execution Layer Status")
    l4_status = load_execution_status()
    pprint(l4_status.__dict__)

from layer5_continuity.L5_continuity_stub import (
    load_continuity_status,
    verify_continuity,
)

# ... inside main diagnostic:

print("\n============================================================")
print("Layer 5 – Continuity Layer Status")
print("============================================================")
l5_status = load_continuity_status()
print(l5_status)
print("\nLayer 5 – Continuity Verification Result")
print("============================================================")
print(f"verify_continuity() => {verify_continuity()}")

if __name__ == "__main__":
    main()
