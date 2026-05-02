param(
  [string]$BackendDir = "..\\backend"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Push-Location $BackendDir
try {
  if (Test-Path ".venv\\Scripts\\Activate.ps1") {
    . .\.venv\Scripts\Activate.ps1
  }
  python api.py
}
finally {
  Pop-Location
}

