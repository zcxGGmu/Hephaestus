param(
  [string]$RepoRoot = ".."
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$resolvedRoot = Resolve-Path $RepoRoot
$backendScript = Join-Path $resolvedRoot "scripts\dev-backend.ps1"
$workerScript = Join-Path $resolvedRoot "scripts\dev-worker.ps1"
$frontendScript = Join-Path $resolvedRoot "scripts\dev-frontend.ps1"
$checkScript = Join-Path $resolvedRoot "scripts\check-prereqs.ps1"

if (Test-Path $checkScript) {
  & $checkScript
}

Write-Host "Starting backend API, worker, and frontend in separate PowerShell windows..."

Start-Process powershell -ArgumentList "-NoExit", "-ExecutionPolicy", "Bypass", "-File", $backendScript
Start-Process powershell -ArgumentList "-NoExit", "-ExecutionPolicy", "Bypass", "-File", $workerScript
Start-Process powershell -ArgumentList "-NoExit", "-ExecutionPolicy", "Bypass", "-File", $frontendScript

Write-Host "Launch commands sent."
