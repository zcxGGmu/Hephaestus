param(
  [string]$BackendDir = "..\\backend"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Push-Location $BackendDir
try {
  if (-not (Test-Path ".venv")) {
    python -m venv .venv
  }

  . .\.venv\Scripts\Activate.ps1
  pip install -r requirements.txt

  if (-not (Test-Path ".env")) {
    Copy-Item .env.example .env
  }

  python scripts/01_setup_database.py
  python scripts/02_setup_redis.py
  python scripts/03_init_hephaestus_table.py
}
finally {
  Pop-Location
}


