<# 
GUS v4 - Guardian Gate (PowerShell)
Gates: compileall + pytest + PAS status + clean working tree (no unstaged/untracked) + no tracked archives
#>

$ErrorActionPreference = "Stop"

function Fail([string]$msg) { Write-Host "FAIL: $msg" -ForegroundColor Red; exit 1 }
function Ok([string]$msg)   { Write-Host "OK:   $msg" -ForegroundColor Green }

try { $repoRoot = (git rev-parse --show-toplevel).Trim() } catch { Fail "Not inside a git repository." }
Set-Location $repoRoot

Write-Host "GUS v4 - Guardian Gate (PowerShell)"
Write-Host "Repo: $repoRoot"
Write-Host ""

# Prefer venv python if present
$venvPy = Join-Path $repoRoot "venv\Scripts\python.exe"
$py = if (Test-Path $venvPy) { $venvPy } else { "python" }
Ok "Using python: $py"

# Branch strict
$branch = (git rev-parse --abbrev-ref HEAD).Trim()
if ($branch -ne "main") { Fail "Branch is '$branch' (expected 'main')." }
Ok "Branch is main"

# compileall
Ok "Running: python -m compileall ."
& $py -m compileall . | Out-Null
Ok "compileall OK"

# pytest (basetemp inside repo, avoids WinError 5 in temp)
Ok "Running: python -m pytest -rs --basetemp .pytest_tmp"
& $py -m pytest -rs --basetemp .pytest_tmp
Ok "pytest OK"

# PAS status
Ok "Running: python -m scripts.pas_status"
$pasOut = & $py -m scripts.pas_status 2>&1
if ($LASTEXITCODE -ne 0) { Fail "PAS status command failed (exit $LASTEXITCODE). Output:`n$pasOut" }
if ($pasOut -notmatch "Overall PAS status:\s*OK") { Fail "PAS status not OK. Output:`n$pasOut" }
Ok "PAS status OK"

# Clean working tree rules for commits:
# - allow staged changes
# - block unstaged changes
# - block untracked files
Ok "Checking: no unstaged changes"
& git diff --quiet
if ($LASTEXITCODE -ne 0) { Fail "Unstaged changes detected. Stage or stash them." }
Ok "No unstaged changes"

Ok "Checking: no untracked files"
$untracked = & git ls-files --others --exclude-standard
if ($untracked -and $untracked.Trim().Length -gt 0) {
  Write-Host $untracked
  Fail "Untracked files detected. Add/ignore/stash them."
}
Ok "No untracked files"

# No tracked archives
Ok "Checking: no tracked .zip files"
$zips = (git ls-files) | Select-String -Pattern '\.zip$' -CaseSensitive:$false
if ($zips) {
  $zips | ForEach-Object { Write-Host $_.Line }
  Fail "Tracked .zip files detected. Remove from index: git rm --cached <file> and ensure .gitignore blocks it."
}
Ok "No tracked zips"

Write-Host ""
Write-Host "PASS: compileall + pytest + PAS + clean working tree + no tracked archives" -ForegroundColor Green
