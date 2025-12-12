<#
GUS v4 — Guardian Gate (PowerShell)
Purpose: hard-stop if integrity gates fail (compile, tests, PAS status, cleanliness, no tracked archives)
Usage:   .\scripts\guardian_gate.ps1
#>

$ErrorActionPreference = "Stop"

function Fail($msg) {
    Write-Host "✖ GUARDIAN GATE FAIL: $msg" -ForegroundColor Red
    exit 1
}
function Ok($msg) { Write-Host "✔ $msg" -ForegroundColor Green }
function Warn($msg) { Write-Host "⚠ $msg" -ForegroundColor Yellow }

# Ensure inside git repo
try { $repoRoot = (git rev-parse --show-toplevel).Trim() }
catch { Fail "Not inside a git repository." }

Set-Location $repoRoot

Write-Host "🛡  GUS v4 — Guardian Gate (PowerShell)"
Write-Host "Repo: $repoRoot"
Write-Host ""

# Prefer venv python if present; else fallback to python in PATH
$py = Join-Path $repoRoot "venv\Scripts\python.exe"
if (-not (Test-Path $py)) {
    $py = "python"
    Warn "venv\Scripts\python.exe not found; using 'python' from PATH."
} else {
    Ok "Using venv python: $py"
}

# 1) Branch check (warn only)
$branch = (git rev-parse --abbrev-ref HEAD).Trim()
if ($branch -ne "main") { Warn "You are on branch '$branch' (expected 'main')." }
else { Ok "Branch is main" }

# 2) compileall
Ok "Running: python -m compileall ."
& $py -m compileall . | Out-Null
Ok "compileall OK"

# 3) pytest (use python -m so PATH doesn't matter)
Ok "Running: python -m pytest -rs"
& $py -m pytest -rs
Ok "pytest OK"

# 4) PAS status must be OK and exit 0
Ok "Running: python -m scripts.pas_status"

$pasRaw = & $py -m scripts.pas_status 2>&1
$pasOut = ($pasRaw | Out-String)

if ($LASTEXITCODE -ne 0) {
    Fail "PAS status command failed (exit $LASTEXITCODE). Output:`n$pasOut"
}

# Normalize whitespace/line breaks to survive encoding + single-line squashing
$norm = ($pasOut -replace "`r","`n")
$norm = ($norm -replace '\s+', ' ')

if ($norm -notmatch "Overall PAS status:\s*OK") {
    Fail "PAS status not OK. Output:`n$pasOut"
}

Ok "PAS status OK"

# 5) Clean tree
Ok "Checking: git status --porcelain"
$status = (git status --porcelain)
if ($status -and $status.Trim().Length -gt 0) {
    Write-Host ""
    Write-Host $status
    Write-Host ""
    Fail "Working tree not clean. Commit or stash changes."
}
Ok "Working tree clean"

# 6) No tracked zips
Ok "Checking: no tracked .zip files"
$zips = (git ls-files) | Select-String -Pattern '\.zip$' -CaseSensitive:$false
if ($zips) {
    Write-Host ""
    $zips | ForEach-Object { Write-Host $_.Line }
    Write-Host ""
    Fail "Tracked .zip files detected. Remove from index + keep ignored."
}
Ok "No tracked zips"

Write-Host ""
Write-Host "✅ GUARDIAN GATE PASS: compileall + pytest + PAS + clean tree + no tracked archives" -ForegroundColor Green
