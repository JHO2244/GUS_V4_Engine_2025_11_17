# GUS v4 — CORE FREEZE BOUNDARY (IMMUTABLE)

## Status
FINAL — v4 CORE SEMANTICS FROZEN

## Rule
GUS v4 is a reference integrity engine.
Only v5+ may change semantics.

## Included in GUS v4 Core (Immutable)
- GDVS (Guardian Diamond Verification Standard)
- Sealing & verification (seal generation, verification policy, CI verify-only rules)
- Integrity invariants (structural constraints, determinism requirements)
- Policy spine (policy evaluation boundaries, refusal semantics, misuse resistance rules)
- Deterministic evaluation logic (canonicalization, hashing, stable ordering, reproducible outputs)
- Refusal semantics (fail-closed defaults, explicit refusal reasons, non-bypassability)

## Explicitly Excluded from GUS v4 Core (Never in v4)
- UI (any interface layer)
- APIs / service wrappers
- Adapters / connectors / integrations
- Presentation logic (formatting layers beyond the output contract)
- Business rules
- Market-specific behavior
- Runtime configuration or overrides ("just one flag")

## Enforcement Definition
Any change that alters outputs, meaning, policy verdict semantics, refusal thresholds,
or determinism guarantees is a semantic change and is forbidden in v4.

Such changes require v5+.

## Purpose
- Prevent UI pressure from weakening core logic
- Stop "just one override" creep
- Make v4 permanently defensible as a reference engine
- Ensure v5 evolution does not contaminate v4 trust anchors

— Guardian Universal Standard (GUS)
