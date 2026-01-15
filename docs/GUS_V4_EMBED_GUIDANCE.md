# GUS v4 - Embed / Installation Guidance (REFERENCE ENGINE)

Status: FINAL
Scope: v4 is ENGINE-ONLY, non-interactive, non-configurable, immutable by design.
Rule: v4 is embed-only. All evolution continues in v5+ containers.

## What GUS v4 is
GUS v4 is a reference integrity engine. It provides:
- evaluation
- refusal
- certification
- explanation

It does NOT provide:
- UI
- APIs
- adapters/connectors
- presentation layers beyond the output contract
- business rules
- market-specific behavior
- runtime configuration or overrides

## How to embed v4 safely (recommended)
1) Pin v4 to a known commit on main (or a tagged release if present).
2) Vendor or submodule the repo into your v5 container (preferred).
3) Treat v4 as read-only. Do not patch v4.

## Verification protocol (local)
Run these from the repo root:
- python -m scripts.verify_repo_seals --head --require-head --no-sig
- python -m pytest -q

Notes:
- On PR branches, strict head seal is required.
- On merged main, GitHub produces an unsealed merge commit. In that case, use merge-safe verification:
  - python -m scripts.verify_repo_seals --head --require-head --no-sig --ci

## Verification protocol (CI)
CI is verify-only:
- CI must not generate new seal files
- CI must not sign seals (private keys remain offline)
- Required checks on main: attestation, gus-ci-spine

## Operational rules
- v4 has frozen semantics. Only v5+ may change semantics.
- Any change that alters outputs, meaning, policy verdict semantics, refusal thresholds,
  or determinism guarantees is a semantic change and is forbidden in v4.
- All new features belong in v5 containers that embed v4.

## Embed patterns
Option A (vendor copy into v5):
- Copy the v4 engine into a v5 container and pin to the v4 commit hash.
- Keep v4 code unmodified. Wrap it externally.

Option B (git submodule):
- Add v4 as a submodule at a pinned commit.
- Verify seals and tests in CI for the pinned commit.

Option C (package/import):
- If packaging is required, do it in v5. Do not add packaging layers to v4.

