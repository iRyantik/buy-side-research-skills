param(
    [switch]$CheckOnly,
    [switch]$Yes,
    [ValidateSet("User", "System")]
    [string]$PythonScope = "User",
    [string]$EdgarIdentity
)

$ErrorActionPreference = "Stop"

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$requirementCandidates = @(
    (Join-Path $scriptRoot "requirements-ingest.txt"),
    (Join-Path $scriptRoot "..\assets\requirements-ingest.txt")
)
$requirementsPath = $null
foreach ($candidate in $requirementCandidates) {
    if (Test-Path -LiteralPath $candidate) {
        $requirementsPath = Resolve-Path $candidate
        break
    }
}

function Test-CommandAvailable {
    param([string]$Name)
    return $null -ne (Get-Command $Name -ErrorAction SilentlyContinue)
}

function Test-PythonModule {
    param([string]$ModuleName)

    if (-not (Test-CommandAvailable "python")) {
        return $false
    }

    $code = "import importlib.util, sys; sys.exit(0 if importlib.util.find_spec('$ModuleName') else 1)"
    & python -c $code *> $null
    return $LASTEXITCODE -eq 0
}

function Get-DependencyStatus {
    $packages = [ordered]@{
        docling = Test-PythonModule "docling"
        edgartools = Test-PythonModule "edgar"
        markitdown = Test-PythonModule "markitdown"
        openpyxl = Test-PythonModule "openpyxl"
        "python-pptx" = Test-PythonModule "pptx"
        "python-docx" = Test-PythonModule "docx"
        pdfplumber = Test-PythonModule "pdfplumber"
        pypdf = Test-PythonModule "pypdf"
        pytesseract = Test-PythonModule "pytesseract"
        Pillow = Test-PythonModule "PIL"
    }

    return [ordered]@{
        python = [ordered]@{
            available = Test-CommandAvailable "python"
            path = if (Test-CommandAvailable "python") { (Get-Command python).Source } else { $null }
        }
        pip = [ordered]@{
            available = Test-CommandAvailable "python"
            install_scope = $PythonScope
        }
        packages = $packages
        binaries = [ordered]@{
            tesseract = [ordered]@{
                available = Test-CommandAvailable "tesseract"
                path = if (Test-CommandAvailable "tesseract") { (Get-Command tesseract).Source } else { $null }
            }
            winget = [ordered]@{
                available = Test-CommandAvailable "winget"
                path = if (Test-CommandAvailable "winget") { (Get-Command winget).Source } else { $null }
            }
            choco = [ordered]@{
                available = Test-CommandAvailable "choco"
                path = if (Test-CommandAvailable "choco") { (Get-Command choco).Source } else { $null }
            }
        }
        env = [ordered]@{
            EDGAR_IDENTITY = [ordered]@{
                configured = -not [string]::IsNullOrWhiteSpace($env:EDGAR_IDENTITY)
                value = if ([string]::IsNullOrWhiteSpace($env:EDGAR_IDENTITY)) { $null } else { $env:EDGAR_IDENTITY }
            }
        }
        requirements_path = if ($requirementsPath) { "$requirementsPath" } else { $null }
    }
}

function Write-StatusJson {
    param([hashtable]$Extra)

    $status = Get-DependencyStatus
    if ($Extra) {
        foreach ($key in $Extra.Keys) {
            $status[$key] = $Extra[$key]
        }
    }
    $status | ConvertTo-Json -Depth 8
}

if ($CheckOnly) {
    Write-StatusJson
    exit 0
}

if (-not $requirementsPath) {
    throw "Cannot find requirements-ingest.txt next to this script or under ../assets."
}

if (-not (Test-CommandAvailable "python")) {
    throw "python is required before ingest dependencies can be installed."
}

if (-not $Yes) {
    Write-Host "This will install Python ingest dependencies from $requirementsPath using python -m pip." -ForegroundColor Yellow
    Write-Host "Default scope is current user only. Pass -Yes to skip this confirmation." -ForegroundColor Yellow
    $answer = Read-Host "Proceed? [y/N]"
    if ($answer -notin @("y", "Y", "yes", "YES")) {
        Write-StatusJson @{ status = "cancelled" }
        exit 1
    }
}

$pipArgs = @("-m", "pip", "install", "--upgrade", "-r", "$requirementsPath")
if ($PythonScope -eq "User") {
    $pipArgs = @("-m", "pip", "install", "--user", "--upgrade", "-r", "$requirementsPath")
}

& python @pipArgs
if ($LASTEXITCODE -ne 0) {
    throw "pip install failed with exit code $LASTEXITCODE"
}

if (-not [string]::IsNullOrWhiteSpace($EdgarIdentity)) {
    $env:EDGAR_IDENTITY = $EdgarIdentity
    & setx EDGAR_IDENTITY "$EdgarIdentity" | Out-Null
}

$tesseractInstallNote = $null
if (-not (Test-CommandAvailable "tesseract")) {
    if (Test-CommandAvailable "winget") {
        Write-Host "tesseract.exe not found. Trying winget install UB-Mannheim.TesseractOCR..." -ForegroundColor Yellow
        & winget install --id UB-Mannheim.TesseractOCR -e --accept-source-agreements --accept-package-agreements
        if ($LASTEXITCODE -ne 0) {
            $tesseractInstallNote = "winget install failed. Try Chocolatey (`choco install tesseract`) or UB Mannheim installer: https://ub-mannheim.github.io/Tesseract_Dokumentation/Tesseract_Doku_Windows.html"
        }
    } else {
        $tesseractInstallNote = "winget is unavailable. Try Chocolatey (`choco install tesseract`) or UB Mannheim installer: https://ub-mannheim.github.io/Tesseract_Dokumentation/Tesseract_Doku_Windows.html"
    }
}

$warnings = New-Object System.Collections.Generic.List[string]
if ([string]::IsNullOrWhiteSpace($env:EDGAR_IDENTITY)) {
    [void]$warnings.Add("EDGAR_IDENTITY is not configured. Non-SEC ingest still works; SEC / EdgarTools routes need -EdgarIdentity `"Name email@domain.com`".")
}
if ($tesseractInstallNote) {
    [void]$warnings.Add($tesseractInstallNote)
}

Write-StatusJson @{
    status = "completed"
    warnings = @($warnings)
}
