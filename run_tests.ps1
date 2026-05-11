param(
    [switch]$All,        # run all test files (existing + new)
    [switch]$CasesOnly   # run only test_all_cases.py
)

$ErrorActionPreference = "Stop"
$backendDir = Join-Path $PSScriptRoot "backend"
$activateScript = Join-Path $backendDir ".venv\Scripts\Activate.ps1"

if (-not (Test-Path $activateScript)) {
    Write-Error "No .venv found. Run 'uv sync' inside the backend/ directory first."
    exit 1
}

& $activateScript
Set-Location $backendDir

if ($CasesOnly) {
    Write-Host "`nRunning testcases.md test suite only...`n" -ForegroundColor Cyan
    uv run pytest tests/test_all_cases.py -v --tb=short
} elseif ($All) {
    Write-Host "`nRunning ALL tests...`n" -ForegroundColor Cyan
    uv run pytest -v --tb=short
} else {
    Write-Host "`nRunning testcases.md test suite (default)...`n" -ForegroundColor Cyan
    uv run pytest tests/test_all_cases.py -v --tb=short
}
