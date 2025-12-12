# PAS v0.2 Posture — Option A (Observational)

PAS v0.2 is present as an overlay diagnostic layer.

## Rules (Option A)
- PAS v0.2 MUST NOT fail the build.
- PAS v0.2 test skips are treated as NOT ACTIVATED (not broken).
- No PYTHONPATH hacks / no packaging promotion in Option A.
- Continuity (L5) and Replication (L6) remain validated by their own unit tests.
- Promotion of PAS v0.2 to enforceable is deferred to Option B.

## Expected pytest posture
- 39 passed
- 2 skipped (expected): PAS v0.2 overlay tests
