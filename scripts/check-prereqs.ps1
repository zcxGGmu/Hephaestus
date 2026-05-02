Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Test-Command {
  param(
    [Parameter(Mandatory = $true)]
    [string]$Name
  )

  $cmd = Get-Command $Name -ErrorAction SilentlyContinue
  if ($null -eq $cmd) {
    Write-Host "[missing] $Name" -ForegroundColor Red
    return $false
  }

  Write-Host "[ok] $Name -> $($cmd.Source)" -ForegroundColor Green
  return $true
}

$allOk = $true

foreach ($name in @("python", "node", "npm")) {
  if (-not (Test-Command -Name $name)) {
    $allOk = $false
  }
}

Write-Host ""
Write-Host "Also make sure these services are available:" -ForegroundColor Yellow
Write-Host "- PostgreSQL"
Write-Host "- Redis"
Write-Host ""

if (-not $allOk) {
  Write-Host "One or more required commands are missing." -ForegroundColor Red
  exit 1
}

Write-Host "Basic local prerequisites look good." -ForegroundColor Green

