param(
  [switch]$CheckOnly,
  [switch]$Yes
)

$ErrorActionPreference = "Stop"

$SkillRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$Requirements = Join-Path $SkillRoot "assets\requirements-reddit-sentiment.txt"

function Test-CommandAvailable {
  param([string]$Name)
  return [bool](Get-Command $Name -ErrorAction SilentlyContinue)
}

Write-Host "== reddit-sentiment dependency check =="

if (-not (Test-CommandAvailable "python")) {
  throw "python is not available on PATH. Install Python 3.12+ or activate the intended environment first."
}

$PythonVersion = python -c "import sys; print('.'.join(map(str, sys.version_info[:3])))"
Write-Host "python: $PythonVersion"

$ScrapiAvailable = Test-CommandAvailable "scrapi-reddit"
if ($ScrapiAvailable) {
  Write-Host "scrapi-reddit: available"
} else {
  Write-Host "scrapi-reddit: missing"
}

if ($CheckOnly) {
  if (-not $ScrapiAvailable) {
    exit 2
  }
  exit 0
}

if (-not $Yes) {
  throw "Pass -Yes to install reddit-sentiment dependencies from $Requirements."
}

python -m pip install -r $Requirements

if (-not (Test-CommandAvailable "scrapi-reddit")) {
  throw "Install completed, but scrapi-reddit is still not available on PATH. Restart the shell or check the Python Scripts directory."
}

Write-Host "reddit-sentiment dependencies are ready."
