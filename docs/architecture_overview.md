# GUS v4 – Architecture Overview

- **Repo:** `GUS_V4_Engine_2025_11_17`
- **Date:** 2025-11-17
- **Status:** Core skeleton online (Layers 0–4) + full test suite green (`pytest`)

---

## 1. What the Engine Is

GUS v4 is a **Guardian-aligned integrity and governance engine**.

It is structured as a **10-layer vertical spine (0–9)** where each layer has:

- A clear **purpose** in the overall system.
- A small, testable **status interface** (e.g. `load_*_status()`).
- Room to evolve internally without breaking the rest of the engine.

The current codebase provides a **running skeleton** for:

- **Layer 0 – Universal Alignment Mechanism (UAM v4)**
- **Layer 1 – Integrity Core & Hash Spine**
- **Layer 2 – Governance Matrix**
- **Layer 3 – Decision Engine**
- **Layer 4 – Execution Layer**

Higher layers (5–9) are present at the folder level and will be activated next.

---

## 2. Layer Stack Overview

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

**Layer 1 – Integrity Core (`layer1_integrity_core/`)**  
Purpose: Integrity hash spine + integrity status reporting.  
Artifacts:
- `L1_integrity_core_stub.py` (exposes `IntegrityStatus`, `load_integrity_status()`, `verify_integrity()`)
- `L1_hash_spine_stub.py`
- `L1_integrity_config.json`
- `chain/gus_chain_v4_stub.py`  
Status:
- `IntegrityStatus(code='ok', errors=[])`
- `verify_integrity() => True`  
Tests:
- `tests/test_layer1_integrity_stub.py` ✅

**Layer 2 – Governance Matrix (`layer2_governance_matrix/`)**  
Purpose: Static governance definitions (councils, pillars, laws).  
Artifacts:
- `L2_governance_static_stub.py`
- `L2_council_definitions.json`
- `L2_pillars_laws_map.json`
- `L2_lock_manifest.json`  
Status:
- `councils_loaded=True`, `laws_map_loaded=True`
- Counts: `councils=3`, `pillars=1`, `construction_laws=2`
- `locked=False`, `errors=[]`  
Tests:
- `tests/test_layer2_governance_stub.py` ✅

**Layer 3 – Decision Engine (`layer3_decision_engine/`)**  
Purpose: Context evaluation + decision matrix + authorization stubs.  
Artifacts:
- `L3_decision_matrix_stub.py`
- `L3_context_evaluator_stub.py`
- `L3_authorization_stub.py`
- `L3_schema.json`  
Status:
- `schema_loaded=True`, `schema_version='0.1'`, `fields_count=4`, `errors=[]`  
Tests:
- `tests/test_layer3_decision_stub.py` ✅

**Layer 4 – Execution Layer (`layer4_execution/`)**  
Purpose: Registry of executable actions + simple executor.  
Artifacts:
- `L4_executor_stub.py`
- `L4_action_registry.json`
- `L4_lock_manifest.json`
- `L4_modules/` (e.g. `L4_guardian_tools_stub.py`)  
Status:
- `registry_loaded=True`, `actions_count=2`
- `locked=False`, `lock_level='none'`, `errors=[]`  
Tests:
- `tests/test_layer4_execution_stub.py` ✅

**Planned Upper Layers (5–9)**  
Folders already present:

- `layer5_continuity/` – Continuity & long-term preservation logic.
- `layer6_replication/` – Replication, backup, and mirroring strategies.
- `layer7_ecosystem/` – External systems, integrations, and environments.
- `layer8_meta_governance/` – Self-governance and meta-rules of GUS.
- `layer9_preservation/` – Deep time preservation, archiving, and legacy.

These layers will gradually gain their own `*_status` models, loaders, and tests.

---

## 3. Runtime Flow (Current Skeleton)

1. **Tests**  
   - `pytest` runs all layer tests under `tests/`.
   - Current suite: 12 tests, all passing.

2. **Diagnostic Entry Point**  
   - `python main.py` runs a simple **GUS v4 Skeleton Diagnostic**:
     - Calls each layer’s `load_*_status()` (Layers 0–4).
     - Prints a human-readable report for each layer.

3. **Logging**  
   - Logging stubs live in `utils/guardian_logging_stub.py`.
   - Log directories exist under `logs/` for integrity, governance, and execution.

This gives a **fast feedback loop**: _“green tests + clear diagnostics = engine healthy”_.

---

## 4. Roadmap (Next Steps)

Short-term planned steps:

1. Add **high-level Architecture Diagram / notes** to this document as the upper layers come online.
2. Introduce a `scripts/run_diagnostics` helper to run `pytest` + `python main.py` in one go.
3. Deepen **Layer 2** governance logic and start wiring real decisions into L3.
4. Activate **Layer 5 – Continuity** with a real `ContinuityStatus` model and tests.

This document should always reflect the **actual running state** of the engine, not just the design intent.
