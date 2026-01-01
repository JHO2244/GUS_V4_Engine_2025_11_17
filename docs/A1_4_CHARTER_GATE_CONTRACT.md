# A1.4 — Purpose Charter Gate Contract (Authoritative)

Status: Authoritative • Test-Gated  
Applies To: GUS v4 • Governance API (L9) • Operator CLI (L10)  
Last Updated: 2026-01-01

## 1) Non-Negotiable Principle (Fail-Closed)
If the Purpose Charter is missing or invalid, governance MUST NOT proceed.

**Fail-Closed Contract**
- Missing charter → BLOCK (raise CharterError)
- Invalid charter → BLOCK (raise CharterError)
- Any uncertainty about charter validity → treat as invalid → BLOCK

This protects:
- no weaponization pathways
- human sovereignty gating
- auditability requirements
- deterministic, inspectable measurement

## 2) Canonical Charter Location
The Purpose Charter MUST exist at repository root:

- `GUS_PURPOSE_CHARTER_v4.json`

No alternate paths are allowed unless explicitly approved by test-gated change.

## 3) Charter Version Normalization (v4)
The charter gate accepts version strings that normalize to v4:
- `"v4"`
- `"v4.0"`
- Any string where `charter_version.lower().startswith("v4") == True`

Anything else MUST fail closed.

## 4) Minimum Required Fields (Contract Surface)
The charter must include at least:

- `charter_version` (normalized v4)
- `failure_posture`
  - `principle` starts with `"Fail"` (case-insensitive acceptable)
  - `on_uncertainty` ∈ {"WARN", "BLOCK"}  
  - `on_integrity_violation` (recommended; if missing, gate still fails closed on other invalidity)

## 5) Enforcement Points (Must Be Called Before Governance)
The charter gate MUST be invoked before:
- any L9 policy evaluation begins
- any verdict is returned
- any ledger append is attempted

**Enforced At**
- `layer9_policy_verdict/src/governance_api.py` (entrypoint: `govern_action`)
- `cli/gus_cli.py` (command: `govern`)

## 6) Ledger Posture Alignment (Fail-Closed)
Even if policy evaluation succeeds:
- If ledger append fails OR returns no hash → BLOCK (raise RuntimeError)

This guarantees auditability (L8) as mandatory, not optional.

## 7) Output Contract (CLI)
The `gus govern` CLI output MUST be JSON-serializable and include:
- `ok` (bool)
- `level` ∈ {"allow","warn","block"}
- `score` (0.0–10.0)
- `policy_id` (e.g., `"L9_MERGE_MAIN"`)
- `object_hash` (verdict object hash)
- `ledger_hash` (ledger entry hash)

No non-serializable objects may be printed.

## 8) Change Control (Anti-Drift)
Any change to this contract requires:
- tests updated first (or alongside)
- CI passing
- PR reviewed and merged via the standard epoch/lock discipline

If the contract doc is removed or its core guarantees are weakened, tests must fail.

## Canonical JSON Output (Determinism Guarantee)
All governance outputs that claim conformance to the authoritative interface MUST be emitted as canonical JSON:
- json.dumps(..., sort_keys=True, separators=(",", ":"), ensure_ascii=True)
- Output MUST end with a single trailing newline ("\n")
Rationale: stable hashes, portable diffs, and deterministic ledger verification across OS/environments.

