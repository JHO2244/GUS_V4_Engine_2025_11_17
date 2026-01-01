# GUS v4 Completion Roadmap (Authoritative, Test-Gated)

## Status Snapshot (as of this doc)
- Purpose Charter v4: ✅ present + test-gated (A1.2)
- Charter Gate enforcement: ✅ fail-closed across L9 + CLI (A2)
- Charter Gate Contract: ✅ authoritative + test-gated (A1.4)
- Epoch anchors: ✅ sealed and current

## Non-Negotiables (Hard Gates)
1. Fail-closed posture is mandatory
2. Charter gate must run before governance evaluation
3. Ledger append must be mandatory and fail-closed
4. Outputs must be JSON-serializable at CLI boundary
5. All changes must be test-gated and epoch-sealed

## Build Phases (Next)
### Phase R1 — Roadmap Lock (this doc)
- Goal: Establish the single source of truth for build order and “done” definition.
- Output: This roadmap + a test that enforces section presence.

### Phase R2 — Governance Surface Hardening
- Verify CLI/governance API contracts match docs and tests.
- Add negative tests (missing charter, invalid charter, ledger fail) if not already complete.

### Phase R3 — Measurement Engine Consolidation
- Ensure scoring semantics and “hard fail rules” are enforced consistently across layers.
- Lock scoring interfaces and determinism invariants.

### Phase R4 — System Packaging / Distribution
- Define minimal runtime entrypoints + versioning.
- Ensure reproducible execution and documented invocation paths.

## Definition of “GUS v4 Ready”
- All Phase R2–R4 tests pass
- Docs are authoritative + test-gated
- Epoch seal exists after every accepted phase
- No drift beyond allowed sealed distance
