# Epoch Lock Cadence (Canonical)

Goal: keep `main` **ALL GREEN** with minimal friction and no seal/anchor loops.

## Definitions
- **Sealed ancestor**: nearest commit on first-parent history that has `seals/seal_<hash12>_*.json` committed.
- **Drift distance**: first-parent commit count from `HEAD` back to the sealed ancestor.
- **Default drift limit**: `GUS_MAX_UNSEALED_COMMITS` (default = **1**).

## Cadence Rule (Micro)
1) **Normal work (default)**  
   - `GUS_MAX_UNSEALED_COMMITS=1` means: `main` may be **1 commit ahead** of the last sealed ancestor.  
   - This “+1” exists because PR merges often create a merge commit after the sealed commit.

2) **When to lock a new epoch**
   Lock a new epoch (anchor + seal PR) when ANY of these is true:
   - Drift distance would become **> 1** (Guardian Gate will block).
   - You are about to start a new major build phase.
   - You want a clean “checkpoint” before risky changes.
   - You want strict verification (`GUS_MAX_UNSEALED_COMMITS=0` for audits).

3) **Minimal epoch lock flow**
   - Create an annotated tag on `main`: `epoch_YYYYMMDD_anchor_main`
   - Generate a seal for the anchored commit.
   - Commit ONLY `seals/seal_<hash12>_*.json` via a PR and merge to `main`.
   - Verify: `bash scripts/guardian_gate.sh` (should pass at default drift=1)

## Daily/Session Habit (30 seconds)
- Start: `git switch main && git pull --ff-only && bash scripts/guardian_gate.sh`
- End (if drift would exceed 1): run epoch lock flow before continuing tomorrow.

## Non-negotiables
- Never edit `seals/` except via the approved lock/seal PR flow.
- Keep drift small; epoch anchors are your integrity checkpoints.
