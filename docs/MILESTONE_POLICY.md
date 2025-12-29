# GUS v4 — Milestone Seal Policy

## Purpose
Provide a **hard integrity switch** for GUS v4.  
When enabled, the system requires an **exact HEAD seal** (no fallback).  
When disabled, development flow remains smooth with ancestor fallback allowed.

---

## Default Mode (Dev)
**State:** Milestone flag NOT present

- Guardian Gate allows nearest sealed ancestor fallback
- Fast iteration, low friction
- No requirement to seal every commit on `main`

This is the **default** operating mode.

---

## Milestone Mode (Strict)
**State:** File present → `.gus/milestone_required`

- Guardian Gate **requires exact HEAD seal**
- No ancestor or parent fallback
- Verification fails if HEAD is not sealed
- Used for:
  - Phase completion
  - Before starting a new layer
  - Releases / public artifacts
  - Integrity-sensitive merges

---

## How to Enable Milestone Mode
Create the file (tracked):

```bash
mkdir -p .gus
type nul > .gus/milestone_required
git add .gus/milestone_required
git commit -m "chore: enable milestone strictness"
