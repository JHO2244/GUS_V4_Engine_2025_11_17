# GUS v4 — PR Labels (Canonical)

## Purpose
Labels are used as **enforcement switches** in CI + Guardian policy.

Use labels intentionally. If you’re unsure, ask before applying.

---

## Enforcement Labels

### `epoch-lock-required`
**Meaning:** This PR must satisfy strict integrity checks.  
**CI Effect:** Enables strict tier (exact HEAD seal required).

Use for:
- phase completion PRs
- epoch lock / anchor PRs
- anything that must be historically declared

---

### `milestone`
**Meaning:** This PR is a milestone checkpoint.  
**CI Effect:** Enables strict tier (exact HEAD seal required).

Use for:
- end-of-layer / end-of-phase merges
- release preparation
- “ready to seal” merges

---

## Normal Labels (Optional, informative)
These do not change enforcement behavior.

- `docs` — documentation-only changes
- `ci` — CI workflow changes
- `security` — integrity/security posture changes
- `refactor` — internal restructuring without behavior change
- `feature` — new capability
- `fix` — bug fix

---

## Rule of Thumb (ELI5)
If it’s a “big moment” → label it `milestone` or `epoch-lock-required`.
If it’s normal work → don’t.
