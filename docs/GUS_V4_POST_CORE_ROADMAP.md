# GUS v4 — Post-Core Roadmap (C5)

**Status:** FINAL  
**Core Tag:** gus-v4.0.0-guardian-ready  
**Core Commit:** a2e5478668c4d000f13e9653e8bd0676e0de3214  
**Purpose:** Define what is DONE, what is NEXT, and what is OUT OF SCOPE after GUS v4 Core completion.

---

## 1. What Is DONE (Locked, Non-Negotiable)

The following is complete, sealed, and immutable under the release tag
`gus-v4.0.0-guardian-ready`.

- GUS v4 Core architecture (Layers 0–10)
- A1–A9 Measurement & Governance Phases
- Policy Verdict system (P2.x)
- Output Contract + A7 envelope emission
- A9 Final Guardian Audit with A7 proof chain
- Guardian Startup Gate (ALL SYSTEMS GREEN)
- CI spine, PAS grid, seals, epochs, and determinism guarantees

No further changes may be made to **Core behavior** without a new major version.

---

## 2. What Is NEXT (Explicitly Non-Core)

The following are allowed **future tracks**, but are NOT part of GUS v4 Core:

- Application layers built *on top of* GUS (apps, services, agents)
- External governance integrations (institutions, APIs, platforms)
- UI / visualization tooling
- Performance optimizations that do not alter guarantees
- Research extensions, simulations, or educational derivatives

These must reference GUS v4 Core as a **dependency**, not modify it.

---

## 3. What Is OUT OF SCOPE (Protected Boundary)

The following are explicitly prohibited within v4 Core:

- Changing A1–A9 definitions or semantics
- Weakening integrity, determinism, or fail-closed behavior
- Removing or bypassing policy verdict enforcement
- Introducing opaque or non-verifiable decision paths
- “Quick fixes” that compromise Guardian guarantees

Any such change requires a **v5 design cycle**.

---

## 4. Artifact Policy (Important)

Runtime-generated artifacts such as:

- `audits/a9_final_report_v0_1.json`
- `audits/a7_output_envelope_from_a9_v0_1.json`

are **certification outputs**, not source code.

They may be archived externally but are **not committed by default**.

---

## 5. Closure Statement

GUS v4 Core is complete, verified, sealed, and release-ready.

All future work proceeds from a position of **stability, clarity, and integrity**.

No ambiguity remains.
