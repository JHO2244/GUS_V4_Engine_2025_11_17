# GUS v4 — L8 ↔ L9 Integration Specification (Authoritative)

## Scope
This document defines the canonical integration between:
- **L9 Policy / Governance Verdict Layer** (policy → verdict)
- **L8 Audit Ledger** (append-only, hash-chained persistence)

It is designed to be:
- deterministic
- test-backed
- CI-safe
- fail-closed (no silent pass)

## Components

### L9 Core Modules
- `layer9_policy_verdict/src/policy_schema.py`
  - Validates Policy v1 structure (strict; rejects invalid input).
- `layer9_policy_verdict/schemas/policy_v1.schema.json`
  - JSON Schema reference for Policy v1.
- `layer9_policy_verdict/src/policy_loader.py`
  - Loads + validates policies from `layer9_policy_verdict/policies/`.
- `layer9_policy_verdict/src/ruleset.py`
  - Deterministic ruleset v1 producing score deltas + reasons.
- `layer9_policy_verdict/src/policy_engine.py`
  - `evaluate_policy()` returns a `PolicyVerdict` (hash-stable).
- `layer9_policy_verdict/src/verdict_ledger_bridge.py`
  - Bridges verdicts into L8 ledger append.
- `layer9_policy_verdict/src/governance_api.py`
  - Stable entrypoint: `govern_action()`.

### L8 Core Modules
- `layer8_audit_ledger/L8_ledger_stub.py`
  - Append-only JSON ledger with `prev_hash` + `entry_hash`
  - Path controlled by env: `GUS_V4_LEDGER_PATH` (CI-safe)

### L10 Operator Interface
- `cli/gus_cli.py`
  - CLI wrapper for `govern_action()`.

## Data Contracts

### Policy (v1) — Minimum Required
Required:
- `policy_id: string`
- `thresholds.allow: number (0..10)`
- `thresholds.warn: number (0..10)`

Optional:
- `policy_version: string` (default: v1)
- `base_score: number (0..10)`

Validation:
- Strict. Invalid values must raise and fail the run.

### PolicyVerdict — Required Fields
- `level`: allow | warn | block
- `score`: float in [0..10]
- `reasons`: non-empty list of strings
- `evidence`: dict (currently `{}` reserved)
- `policy_id`: string
- `epoch_ref`: string
- `chain_head`: string
- `object_hash`: sha256 of stable object core

Determinism:
- Same inputs → same verdict + same `object_hash`

## Execution Pipeline (Canonical)

### 1) Load Policy
`load_policy(policy_filename)`:
- reads JSON from policy pack
- validates via `require_policy_v1()`

### 2) Evaluate Verdict
`evaluate_policy(action, context, policy, epoch_ref, chain_head)`:
- applies ruleset v1
- computes score from base + deltas (clamped)
- assigns level from thresholds
- hashes object_core → object_hash

### 3) Append Verdict to L8 (Mandatory)
`append_verdict_to_ledger(verdict)`:
- maps verdict into L8 `append_entry()` payload
- writes append-only entry to JSON ledger
- returns ledger entry hash for downstream audit

Fail-closed rule:
- If ledger append fails → raise → operation fails.

### 4) Governance API Return
`govern_action(...)` returns:
- ok: True
- level: "allow|warn|block"
- score: float
- verdict: PolicyVerdict
- ledger_hash: str

### 5) CLI (Operator Path)
`python -m cli.gus_cli govern ...`:
- accepts action/context JSON
- calls `govern_action`
- prints compact JSON payload

## CI Safety / Dirty Tree Protection
- Ledger JSON is excluded from commit via `.gitignore`.
- CI requires clean working tree during epoch validation.
- Use `GUS_V4_LEDGER_PATH` to redirect ledger writes to temp.

## Security / Integrity Notes
- L8 ledger is append-only with hash chaining; tamper attempts break continuity.
- Verdict hash anchors policy decision inputs into the audit trail.
- Epoch seals gate drift; PR-only to main is enforced via your workflow.

## Required Headings (Test-Gated)
This file must retain these headings:
- Scope
- Components
- Data Contracts
- Execution Pipeline (Canonical)
- CI Safety / Dirty Tree Protection
