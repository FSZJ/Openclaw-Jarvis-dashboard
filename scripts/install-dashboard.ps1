$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$rootDir = Resolve-Path (Join-Path $scriptDir "..")
Set-Location $rootDir

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
  Write-Error "Python not found. Install Python 3.11+ first."
}
if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
  Write-Error "Node.js not found. Install Node.js 18+ first."
}

python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt

Set-Location "$rootDir\frontend"
npm install
npm run build
Set-Location $rootDir

if (-not (Test-Path .env)) {
  Copy-Item .env.example .env
}

Write-Host "Install done. Run: .\.venv\Scripts\Activate.ps1; .\start.sh"
