param(
    [int]$BackendPort = 8000,
    [int]$FrontendPort = 5173
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendDir = Join-Path $repoRoot "backend"
$frontendDir = Join-Path $repoRoot "frontend\my-react-app"
$activateScript = Join-Path $backendDir ".venv\Scripts\Activate.ps1"

if (-not (Test-Path $backendDir)) {
    throw "Backend directory not found: $backendDir"
}

if (-not (Test-Path $frontendDir)) {
    throw "Frontend directory not found: $frontendDir"
}

if (-not (Test-Path $activateScript)) {
    throw "Backend venv activation script not found: $activateScript"
}

$backendCmd = @"
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
& '$activateScript'
Set-Location '$backendDir'
uvicorn main:app --reload --port $BackendPort
"@

$frontendCmd = @"
Set-Location '$frontendDir'
npm run dev -- --host 127.0.0.1 --port $FrontendPort
"@

Start-Process -FilePath "powershell.exe" -ArgumentList @(
    "-NoExit",
    "-Command",
    $backendCmd
)

Start-Process -FilePath "powershell.exe" -ArgumentList @(
    "-NoExit",
    "-Command",
    $frontendCmd
)

Write-Host "Started backend on http://127.0.0.1:$BackendPort and frontend on http://127.0.0.1:$FrontendPort"