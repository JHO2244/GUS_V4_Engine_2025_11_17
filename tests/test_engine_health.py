# gus_engine_health.py

from __future__ import annotations

from dataclasses import dataclass, asdict


@dataclass
class LayerHealth:
  name: str
  verified: bool
  errors: int


@dataclass
class EngineHealth:
  overall_ok: bool
  layers: list[LayerHealth]


def get_engine_health() -> EngineHealth:
  """
  Guardian-style programmatic health snapshot for tests.
  This is the structured version of what main.py prints.
  """

  # --- Layer 0: UAM v4 ---
  from layer0_uam_v4.L0_uam_core_stub import load_uam_status
  l0 = load_uam_status()
  l0_ok = bool(l0.get("schema_loaded") and l0.get("lock_loaded") and not l0.get("errors"))

  # --- Layer 1: Integrity Core ---
  from layer1_integrity_core.L1_integrity_core_stub import (
      load_integrity_status,
      verify_integrity,
  )
  l1_status = load_integrity_status()
  l1_ok = bool(verify_integrity() and not l1_status.errors)

  # --- Layer 2: Governance Matrix ---
  from layer2_governance_matrix.L2_governance_core_stub import load_governance_status
  l2 = load_governance_status()
  l2_ok = not l2.get("errors")

  # --- Layer 3: Decision Engine ---
  from layer3_decision_engine.L3_decision_core_stub import load_decision_status
  l3 = load_decision_status()
  l3_ok = not l3.get("errors")

  # --- Layer 4: Execution Layer ---
  from layer4_execution.L4_execution_core_stub import load_execution_status
  l4 = load_execution_status()
  l4_ok = not l4.get("errors")

  # --- Layer 5: Continuity ---
  from layer5_continuity.L5_continuity_stub import (
      load_continuity_status,
      verify_continuity,
  )
  l5_status = load_continuity_status()
  l5_ok = bool(verify_continuity() and not l5_status.errors)

  # --- Layer 6: Replication ---
  from layer6_replication.L6_replication_stub import (
      load_replication_status,
      verify_replication,
  )
  l6_status = load_replication_status()
  l6_ok = bool(verify_replication() and not l6_status.errors)

  # --- Layer 7: Ecosystem ---
  from layer7_ecosystem.L7_ecosystem_stub import (
      load_ecosystem_status,
      verify_ecosystem,
  )
  l7_status = load_ecosystem_status()
  l7_ok = bool(verify_ecosystem() and not l7_status.errors)

  # --- Layer 8: Meta-Governance ---
  from layer8_meta_governance.L8_meta_governance_stub import (
      load_meta_governance_status,
      verify_meta_governance,
  )
  l8_status = load_meta_governance_status()
  l8_ok = bool(verify_meta_governance() and not l8_status.errors)

  # --- Layer 9: Preservation ---
  from layer9_preservation.L9_preservation_stub import (
      load_preservation_status,
      verify_preservation,
  )
  l9_status = load_preservation_status()
  l9_ok = bool(verify_preservation() and not l9_status.errors)

  layers = [
      LayerHealth("Layer 0 (UAM v4)", l0_ok, len(l0.get("errors", []))),
      LayerHealth("Layer 1 (Integrity Core)", l1_ok, len(l1_status.errors)),
      LayerHealth("Layer 2 (Governance Matrix)", l2_ok, len(l2.get("errors", []))),
      LayerHealth("Layer 3 (Decision Engine)", l3_ok, len(l3.get("errors", []))),
      LayerHealth("Layer 4 (Execution Layer)", l4_ok, len(l4.get("errors", []))),
      LayerHealth("Layer 5 (Continuity)", l5_ok, len(l5_status.errors)),
      LayerHealth("Layer 6 (Replication)", l6_ok, len(l6_status.errors)),
      LayerHealth("Layer 7 (Ecosystem)", l7_ok, len(l7_status.errors)),
      LayerHealth("Layer 8 (Meta-Governance)", l8_ok, len(l8_status.errors)),
      LayerHealth("Layer 9 (Preservation)", l9_ok, len(l9_status.errors)),
  ]

  overall_ok = all(layer.verified for layer in layers)

  return EngineHealth(
      overall_ok=overall_ok,
      layers=layers,
  )


def get_engine_health_as_dict() -> dict:
  """
  Convenience wrapper for tests that want a pure dict.
  """
  health = get_engine_health()
  return {
      "overall_ok": health.overall_ok,
      "layers": [asdict(l) for l in health.layers],
  }
