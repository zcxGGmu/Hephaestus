param(
  [string]$FrontendDir = "..\\frontend"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Push-Location $FrontendDir
try {
  if (-not (Test-Path ".env.local") -and (Test-Path "env.example")) {
    Copy-Item env.example .env.local
  }
  npm run dev
}
finally {
  Pop-Location
}
