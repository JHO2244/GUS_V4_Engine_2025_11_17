# GUS v4 – Architecture Overview

**Repo:** `GUS_V4_Engine_2025_11_17`
**Date:** 2025-11-17
**Scope:** Layers 0–4 online + test suite + diagnostics

---

## 1. Core Idea

GUS v4 is a **Guardian-aligned integrity and governance engine**.

At its core, the engine is a **layered spine** that can evaluate systems, projects, or decisions using Guardian standards of integrity, truth density, and coherence. Each layer has a single responsibility, its own config/schema, and a test-backed status report.

The current codebase implements a **running skeleton** for:

- **Layer 0 – Universal Alignment Mechanism (UAM v4)**
- **Layer 1 – Integrity Core & Hash Spine**
- **Layer 2 – Governance Matrix**
- **Layer 3 – Decision Engine**
- **Layer 4 – Execution Layer**

Higher layers (5–9) are already scaffolded as folders and will extend this spine.

---

## 2. Layer Stack (0–9)

**Layer 0 – UAM v4 (`layer0_uam_v4/`)**
Purpose: System-wide alignment & configuration baseline.
Artifacts:
- `L0_uam_core_stub.py`
- `L0_uam_schema.json`
- `L0_uam_lock_manifest.json`
Status (from `python main.py`):
- `schema_loaded=True`, `lock_loaded=True`, `locked=False`, `errors=[]`
Tests:
- `tests/test_layer0_uam_stub.py` ✅

---

**Layer 1 – Integrity Core (`layer1_integrity_core/`)**
Purpose: Integrity hash spine + integrity status reporting.
Artifacts:
- `L1_integrity_core_stub.py` (exposes `IntegrityStatus`, `load_integrity_status()`, `verify_integrity()`)
- `L1_hash_spine_stub.py`
- `L1_integrity_config.json`
Status:
- `IntegrityStatus(code='ok', errors=[])`
- `verify_integrity() => True`
Tests:
- `tests/test_layer1_integrity_stub.py` ✅

---

**Layer 2 – Governance Matrix (`layer2_governance_matrix/`)**
Purpose: Councils, laws, and governance configuration.
Artifacts:
- `L2_governance_core_stub.py`
- `L2_councils_map.json`
- `L2_construction_laws.json`
- `L2_lock_manifest.json`
Status:
- `councils_loaded=True`, `laws_map_loaded=True`, `lock_loaded=True`
- `councils_count`, `pillars_count`, `construction_laws_count` reported
Tests:
- `tests/test_layer2_governance_stub.py` ✅

---

**Layer 3 – Decision Engine (`layer3_decision_engine/`)**
Purpose: Evaluate context and select actions (decision matrix).
Artifacts:
- `L3_decision_core_stub.py`
- `L3_decision_schema.json`
Status:
- `schema_loaded=True`, `schema_version='0.1'`, `fields_count=4`, `errors=[]`
Tests:
- `tests/test_layer3_decision_stub.py` ✅

---

**Layer 4 – Execution Layer (`layer4_execution/`)**
Purpose: Register and describe executable actions.
Artifacts:
- `L4_execution_core_stub.py`
- `L4_actions_registry.json`
- `L4_lock_manifest.json`
Status:
- `registry_loaded=True`, `actions_count`, `locked=False`, `lock_level='none'`, `errors=[]`
Tests:
- `tests/test_layer4_execution_stub.py` ✅

---

**Layer 5 – Continuity (`layer5_continuity/`)**
Purpose: Long-term continuity, preservation, and epoch/backup policies.
Status:
- Folder + stub file present (`L5_continuity_stub.py`).
- Detailed status model + tests **planned** (next major step).

---

**Layer 6 – Replication (`layer6_replication/`)**
Purpose: Safe duplication/propagation of GUS instances and configs.
Status:
- Folder scaffolded, logic **TBD**.

---

**Layer 7 – Ecosystem (`layer7_ecosystem/`)**
Purpose: Multi-node / multi-system interactions (GUS within a wider network).
Status:
- Folder scaffolded, logic **TBD**.

---

**Layer 8 – Meta-Governance (`layer8_meta_governance/`)**
Purpose: Governance of governance (how rules themselves evolve).
Status:
- Folder scaffolded, logic **TBD**.

---

**Layer 9 – Preservation (`layer9_preservation/`)**
Purpose: Immortality / long-horizon preservation of GUS identity and history.
Status:
- Folder scaffolded, logic **TBD**.

---

## 3. Runtime Flow & Diagnostics

**Primary entrypoints:**

1. **Test suite**

   ```bash
   pytest
