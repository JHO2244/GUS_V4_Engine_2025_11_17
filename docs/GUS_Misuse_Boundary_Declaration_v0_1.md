# GUS v4 Misuse Boundary Declaration (World-Facing) — v0.1

**Document purpose:** Define clear misuse boundaries for the Guardian Universal Standard (GUS) v4 so it cannot be credibly framed, deployed, or marketed as a weapon, coercion tool, surveillance system, or harm-optimizing engine.

**Scope:** This declaration governs GUS v4 as published in this repository, including its auditing (A1–A9), sealing (PAS/seals), and governance/policy layers.

---

## 1) What GUS v4 is (and is not)

**GUS v4 is:**  
A deterministic measurement and audit framework that produces structured, inspectable “verdicts” about artifacts, processes, or configurations according to explicitly defined rules and invariants.

**GUS v4 is not:**  
- A targeting system.
- A surveillance product.
- A command-and-control platform.
- An enforcement mechanism.
- A substitute for law, due process, or human accountability.

GUS provides **measurement outputs**, not authority.

---

## 2) Prohibited uses (hard boundaries)

GUS v4 must not be used, integrated, or adapted to:

1. **Enable violence or physical harm**
   - Selecting targets, planning attacks, optimizing weapons, or escalating conflict.
2. **Enable coercion, extortion, or intimidation**
   - Scoring people or groups to justify threats, forced compliance, or deprivation.
3. **Facilitate surveillance or privacy invasion**
   - Identifying individuals, de-anonymizing datasets, tracking behavior, or building dossiers.
4. **Discriminate in high-stakes human decisions**
   - Employment, housing, education, medical access, insurance, legal outcomes, or policing decisions based on GUS outputs.
5. **Automate punitive enforcement**
   - Triggering penalties or restricting rights automatically based on a score/verdict.
6. **Manipulate populations**
   - Propaganda optimization, psychological operations, or “influence scoring” for control.
7. **Operate as a secrecy wrapper**
   - Using GUS branding to disguise malicious logic inside “audit” or “governance” language.

If an intended deployment falls into any category above, it is **out of bounds**.

---

## 3) Allowed uses (safe lanes)

GUS v4 is appropriate for:
- **Integrity verification** (tamper detection, sealed artifact chains, deterministic auditing).
- **Quality and compliance measurement** where the subject is **software, documents, configs, or systems**, not human beings.
- **Reproducibility checks** (cold-clone verification, deterministic outputs).
- **Transparency tooling** (traceable, reviewable decision criteria with explicit logs and schemas).
- **Safety gating** (refusing to generate or execute disallowed categories of actions).

---

## 4) Human accountability requirement

GUS outputs must be treated as **decision-support evidence**, not final authority.

Any real-world action taken after a GUS verdict requires:
- A named human accountable party,
- A documented rationale beyond “the system said so,”
- An appeal/review path where feasible.

---

## 5) Privacy posture

GUS v4 is designed to minimize leakage by:
- Avoiding hidden network calls in core verification paths,
- Emitting structured outputs intended for inspection,
- Treating sensitive content as out-of-scope unless explicitly provided and permitted.

Operators must not feed private personal data into GUS to “score” people. GUS is for **artifact integrity**, not human profiling.

---

## 6) Anti-weaponization stance

This repository includes an **anti-weaponization verdict layer** (A5) intended to refuse or flag weaponization-aligned intent.

Any fork or downstream system that removes or bypasses anti-weaponization controls must not represent itself as “Guardian-aligned” or “GUS compliant.”

---

## 7) Reporting misuse

If you discover a misuse pattern, downstream weaponization, or deceptive marketing that claims alignment while violating these boundaries:
- Document the evidence and context,
- Report it through the repository’s issue tracker or the project’s stated contact channel (if provided).

---

## 8) Versioning and change control

This is **v0.1**. Updates must:
- Preserve the “prohibited uses” section unless strengthening,
- Remain clear, specific, and enforceable,
- Be reviewed as a world-facing safety document.

**End of declaration.**
