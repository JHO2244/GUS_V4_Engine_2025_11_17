# GUS v4 — ENGINE-ONLY DECLARATION

## Status
FINAL — IMMUTABLE

## Definition
GUS v4 is a **non-interactive, non-configurable Integrity Engine**.

It exposes **evaluation, refusal, certification, and explanation only**.

## Explicitly Disallowed
- User interfaces (UI)
- APIs or service layers
- Adapters or connectors
- Runtime configuration
- Overrides, flags, or escape hatches
- Market- or client-specific behavior

## Rationale
- Prevents UI pressure from weakening logic
- Eliminates “just one override” creep
- Preserves deterministic integrity
- Makes v4 defensible as a permanent reference engine

## Version Discipline
- GUS v4 semantics are **frozen**
- Only **v5+** may introduce semantic changes
- v4 exists solely as a reference integrity engine

## Enforcement
Any attempt to wrap, configure, or extend v4 behavior
**outside evaluation, refusal, certification, or explanation**
constitutes a protocol violation.

— Guardian Universal Standard (GUS)
