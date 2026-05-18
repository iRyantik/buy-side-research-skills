param(
    [switch]$CheckOnly,
    [switch]$Yes,
    [switch]$China,
    [ValidateSet("User", "System")]
    [string]$PythonScope = "User"
)

$ErrorActionPreference = "Stop"

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$requirementCandidates = @(
    (Join-Path $scriptRoot "requirements-financial-data.txt"),
    (Join-Path $scriptRoot "..\assets\requirements-financial-data.txt")
)
$requirementsPath = $null
foreach ($candidate in $requirementCandidates) {
    if (Test-Path -LiteralPath $candidate) {
        $requirementsPath = Resolve-Path $candidate
        break
    }
}

function Test-CommandAvailable { param([string]$Name); return $null -ne (Get-Command $Name -ErrorAction SilentlyContinue) }

function Test-PythonModule { param([string]$ModuleName)
    if (-not (Test-CommandAvailable "python")) { return $false }
    $code = "import importlib.util, sys; sys.exit(0 if importlib.util.find_spec('$ModuleName') else 1)"
    & python -c $code *> $null
    return $LASTEXITCODE -eq 0
}

function Get-DependencyStatus {
    $packages = [ordered]@{
        edgartools = Test-PythonModule "edgar"
        akshare = Test-PythonModule "akshare"
        "edinet-tools" = Test-PythonModule "edinet_tools"
        "dart-fss" = Test-PythonModule "dart_fss"
        openesef = Test-PythonModule "openesef"
    }
    return [ordered]@{
        python = [ordered]@{ available = (Test-CommandAvailable "python") }
        packages = $packages
        env = [ordered]@{
            EDGAR_IDENTITY = [ordered]@{ configured = -not [string]::IsNullOrWhiteSpace($env:EDGAR_IDENTITY) }
            DART_API_KEY = [ordered]@{ configured = -not [string]::IsNullOrWhiteSpace($env:DART_API_KEY) }
        }
        requirements_path = if ($requirementsPath) { "$requirementsPath" } else { $null }
    }
}

if ($CheckOnly) {
    Get-DependencyStatus | ConvertTo-Json -Depth 8
    exit 0
}

if (-not (Test-CommandAvailable "python")) {
    Write-Host "Python not found. Install Python 3.10+ first." -ForegroundColor Red
    exit 1
}

if (-not $requirementsPath) {
    throw "requirements-financial-data.txt not found"
}

if (-not $Yes) {
    Write-Host "Will install financial-data dependencies from $requirementsPath" -ForegroundColor Yellow
    Write-Host "Install scope: $PythonScope" -ForegroundColor Yellow
    if ($China) { Write-Host "Using China PyPI mirror" -ForegroundColor Yellow }
    $answer = Read-Host "Continue? [y/N]"
    if ($answer -notin @("y", "Y", "yes", "YES")) {
        [ordered]@{ status = "cancelled" } | ConvertTo-Json
        exit 1
    }
}

$pipArgs = @("-m", "pip", "install", "--user", "-r", "$requirementsPath")
if ($China) {
    $pipArgs = @("-m", "pip", "install", "--user", "-i", "https://pypi.tuna.tsinghua.edu.cn/simple", "-r", "$requirementsPath")
}

& python @pipArgs
if ($LASTEXITCODE -ne 0) {
    Write-Host "pip install failed" -ForegroundColor Red
    exit 1
}

Get-DependencyStatus | ConvertTo-Json -Depth 8
