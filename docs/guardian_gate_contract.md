# Guardian Gate Contract (GUS v4) — v1.0

## Purpose
Guardian Gate is a hard-stop integrity checkpoint that prevents unsafe, inconsistent, or contaminated commits.

## Source of Truth
- Bash gate: `scripts/guardian_gate.sh`
- PowerShell gate: `scripts/guardian_gate.ps1`
- Hook template: `scripts/hooks/pre-commit`
- Installer: `scripts/install_hooks.sh`

## Required Gates (must PASS)
1. Branch: must be `main` (strict)
2. `python -m compileall .`
3. `python -m pytest -rs --basetemp .pytest_tmp`
4. `python -m scripts.pas_status` must include `Overall PAS status: OK`
5. Clean commit semantics:
   - no unstaged changes
   - no untracked files
   - staged changes allowed
6. No tracked `.zip` files

## Seal Entry (log record)
Timestamp (Cape Town, South Africa): 2025-12-12  
Gate: scripts/guardian_gate.ps1  
Result: ✅ PASS (compileall + pytest + PAS + clean tree + no tracked archives)
