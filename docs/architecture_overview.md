# GUS v4 – Architecture Overview

_Date:_ 2025-11-17  
_Repo:_ `GUS_V4_Engine_2025_11_17`  
_Status:_ Skeleton online (Layers 0–4) + full test suite green

---

## 1. What GUS v4 Is

GUS v4 is a **Guardian-aligned integrity and governance engine**.

It provides a layered spine for:
- describing systems,
- rating them against Guardian standards, and
- executing actions only when integrity conditions are met.

This repo currently contains a **running skeleton** for Layers **0 → 4**, with scaffolding in place for 5 → 9.

---

## 2. Layer Map (0 → 9)

**Layer 0 – UAM v4 (`layer0_uam_v4/`)**  
Purpose: Universal Alignment Mechanism – system-wide alignment & configuration baseline.  
Key artifacts:
- `L0_uam_core_stub.py`
- `L0_uam_schema.json`
- `L0_uam_lock_manifest.json`  
Runtime status (from `python main.py`):
- `schema_loaded=True`, `lock_loaded=True`, `locked=False`, `errors=[]`  
Tests:
- `tests/test_layer0_uam_stub.py` ✅

---

**Layer 1 – Integrity Core & Hash Spine (`layer1_integrity_core/`)**  
Purpose: Integrity hash spine + integrity status reporting.  
Key artifacts:
- `L1_integrity_core_stub.py` (exposes `IntegrityStatus`, `load_integrity_status()`, `verify_integrity()`)
- `L1_hash_spine_stub.py`
- `L1_integrity_config.json`
- `chain/gus_chain_v4_stub.py`  
Runtime status:
- `IntegrityStatus(code='ok', errors=[])`
- `verify_integrity() => True`  
Tests:
- `tests/test_layer1_integrity_stub.py` ✅

---

**Layer 2 – Governance Matrix (`layer2_governance_matrix/`)**  
Purpose: Static governance definitions – Pillars, Laws, Councils, lock manifest.  
Key artifacts:
- `L2_governance_static_stub.py`
- `L2_council_definitions.json`
- `L2_pillars_laws_map.json`
- `L2_lock_manifest.json`  
Runtime status:
- `councils_loaded=True`, `laws_map_loaded=True`, `lock_loaded=True`
- Counts: `councils=3`, `pillars=1`, `construction_laws=2`, `locked=False`, `errors=[]`  
Tests:
- `tests/test_layer2_governance_stub.py` ✅

---

**Layer 3 – Decision Engine (`layer3_decision_engine/`)**  
Purpose: Context evaluation + decision matrix + authorization stubs.  
Key artifacts:
- `L3_decision_matrix_stub.py`
- `L3_context_evaluator_stub.py`
- `L3_authorization_stub.py`
- `L3_schema.json`  
Runtime status:
- `schema_loaded=True`, `schema_version='0.1'`, `fields_count=4`, `errors=[]`  
Tests:
- `tests/test_layer3_decision_stub.py` ✅

---

**Layer 4 – Execution Layer (`layer4_execution/`)**  
Purpose: Registry of executable actions + basic executor wiring.  
Key artifacts:
- `L4_action_registry.json`
- `L4_executor_stub.py`
- `L4_lock_manifest.json`
- `L4_modules/L4_guardian_tools_stub.py`
- `L4_modules/L4_reserved_slot_01.py`  
Runtime status:
- `registry_loaded=True`, `actions_count=2`
- `lock_loaded=True`, `locked=False`, `lock_level='none'`, `errors=[]`  
Tests:
- `tests/test_layer4_execution_stub.py` ✅

---

**Layers 5–9 – Planned Spine (Scopes Only)**

These layers are currently **stubs / design targets** and will be implemented on top of the stable 0–4 skeleton:

- **Layer 5 – Continuity (`layer5_continuity/`)**  
  Continuity, epoch preservation, long-term system lifespan.

- **Layer 6 – Replication (`layer6_replication/`)**  
  Safe propagation, cloning, and deployment of GUS instances.

- **Layer 7 – Ecosystem (`layer7_ecosystem/`)**  
  Multi-system interactions, networks of GUS-aligned entities.

- **Layer 8 – Meta-Governance (`layer8_meta_governance/`)**  
  Governance of governance – rules for evolving Pillars, Laws, and councils.

- **Layer 9 – Preservation (`layer9_preservation/`)**  
  Archival, immutability guarantees, and high-fidelity history of the engine itself.

---

## 3. Runtime & Diagnostics

The main entry point for the current skeleton is:

```bash
python main.py
