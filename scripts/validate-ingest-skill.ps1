param(
    [string]$SkillName = "ingest"
)

$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$skillRoot = Join-Path $repoRoot "skills\$SkillName"
$skillPath = Join-Path $skillRoot "SKILL.md"
$yamlPath = Join-Path $skillRoot "skill.yaml"
$scriptPaths = @(
    "scripts\ingest.py",
    "scripts\ingest_xlsx.py",
    "scripts\ingest_table_crosscheck.py",
    "scripts\bootstrap-ingest-deps.ps1",
    "assets\requirements-ingest.txt"
)

$failures = New-Object System.Collections.Generic.List[string]

function New-UnicodeText {
    param([int[]]$CodePoints)

    return -join ($CodePoints | ForEach-Object { [char]$_ })
}

function Require-Path {
    param(
        [string]$Path,
        [string]$Message
    )

    if (-not (Test-Path -LiteralPath $Path)) {
        $script:failures.Add($Message)
    }
}

function Get-YamlScalar {
    param(
        [string]$Text,
        [string]$Key
    )

    $match = [regex]::Match($Text, "(?m)^$([regex]::Escape($Key)):\s*['""]?([^'""\r\n]+)['""]?\s*$")
    if ($match.Success) {
        return $match.Groups[1].Value.Trim()
    }
    return $null
}

Require-Path $skillPath "Missing ingest SKILL.md"
Require-Path $yamlPath "Missing ingest skill.yaml"
foreach ($script in $scriptPaths) {
    Require-Path (Join-Path $skillRoot $script) "Missing ingest script: $script"
}

if ((Test-Path -LiteralPath $skillPath) -and (Test-Path -LiteralPath $yamlPath)) {
    $skillText = Get-Content -Raw -Encoding UTF8 -LiteralPath $skillPath
    $yamlText = Get-Content -Raw -Encoding UTF8 -LiteralPath $yamlPath

    $capsuleCount = ([regex]::Matches($skillText, "## Global Rules Capsule \(v1\)")).Count
    if ($capsuleCount -ne 1) {
        $failures.Add("ingest: expected exactly one Global Rules Capsule, found $capsuleCount")
    }

    $requiredSections = @(
        @{ Label = "Mindset"; Text = New-UnicodeText @(0x5FC3, 0x6CD5) },
        @{ Label = "Source Policy"; Text = "Source " + (New-UnicodeText @(0x653F, 0x7B56)) },
        @{ Label = "Workflow Linkage"; Text = "Workflow " + (New-UnicodeText @(0x8054, 0x52A8)) },
        @{ Label = "Anti-pattern Self-check"; Text = New-UnicodeText @(0x53CD, 0x6A21, 0x5F0F, 0x81EA, 0x67E5) },
        @{ Label = "Length Benchmark"; Text = New-UnicodeText @(0x7BC7, 0x5E45, 0x57FA, 0x51C6) }
    )

    foreach ($section in $requiredSections) {
        if ($skillText -notmatch "(?m)^##\s*$([regex]::Escape($section.Text))") {
            $failures.Add("ingest: missing required section '$($section.Label)'")
        }
    }

    foreach ($phrase in @(
        "_cache/",
        "source_sha256",
        "source_modified_utc",
        "converted_at_utc",
        "precision",
        "ingest.py",
        "ingest_xlsx.py",
        "ingest_table_crosscheck.py",
        "bootstrap-ingest-deps.ps1",
        "requirements-ingest.txt",
        "Docling",
        "EdgarTools",
        "Tesseract",
        "MarkItDown",
        "PDFPlumber",
        "--check-deps",
        "EDGAR_IDENTITY",
        "information-impact",
        "company-primer",
        "research-journal"
    )) {
        if (-not $skillText.Contains($phrase)) {
            $failures.Add("ingest: SKILL.md missing required phrase '$phrase'")
        }
    }

    foreach ($phrase in @(
        "cache_artifact",
        "[source-filename].md",
        "_cache/[bucket]/[source-filename].md",
        "Dependency Bootstrap / Check",
        "precision_level",
        "document_type",
        "route",
        "3.4.0"
    )) {
        if (-not $yamlText.Contains($phrase)) {
            $failures.Add("ingest: skill.yaml missing required phrase '$phrase'")
        }
    }

    $yamlName = Get-YamlScalar $yamlText "name"
    $yamlVersion = Get-YamlScalar $yamlText "version"
    $systemGeneration = Get-YamlScalar $yamlText "system_generation"

    if ($yamlName -ne "ingest") {
        $failures.Add("ingest: skill.yaml name '$yamlName' does not match ingest")
    }
    if ($yamlVersion -ne "1.1.0") {
        $failures.Add("ingest: expected skill version 1.1.0, found '$yamlVersion'")
    }
    if ($systemGeneration -ne "3.4.0") {
        $failures.Add("ingest: expected system_generation 3.4.0, found '$systemGeneration'")
    }
}

$ingestScript = Join-Path $skillRoot "scripts\ingest.py"
if (Test-Path -LiteralPath $ingestScript) {
    $scriptText = Get-Content -Raw -Encoding UTF8 -LiteralPath $ingestScript
    foreach ($phrase in @(
        "source_sha256",
        "source_modified_utc",
        "converted_at_utc",
        "precision",
        "precision_level",
        "document_type",
        "route",
        "page_count",
        "table_count",
        "ocr_required",
        "dependency_status",
        "detect_format",
        "route_converter",
        "def cache",
        "--check-deps",
        "Docling",
        "EdgarTools",
        "TesseractCliOcrOptions",
        "MarkItDown",
        "Could not discover research workspace",
        "Missing optional dependency",
        "--recursive",
        "--force"
    )) {
        if (-not $scriptText.Contains($phrase)) {
            $failures.Add("ingest.py missing required phrase '$phrase'")
        }
    }
}

$bootstrapScript = Join-Path $skillRoot "scripts\bootstrap-ingest-deps.ps1"
if (Test-Path -LiteralPath $bootstrapScript) {
    $bootstrapText = Get-Content -Raw -Encoding UTF8 -LiteralPath $bootstrapScript
    foreach ($phrase in @(
        "CheckOnly",
        "Yes",
        "PythonScope",
        "EdgarIdentity",
        "requirements-ingest.txt",
        "python -m pip",
        "EDGAR_IDENTITY",
        "winget",
        "UB-Mannheim",
        "Tesseract"
    )) {
        if (-not $bootstrapText.Contains($phrase)) {
            $failures.Add("bootstrap-ingest-deps.ps1 missing required phrase '$phrase'")
        }
    }
}

$requirementsPath = Join-Path $skillRoot "assets\requirements-ingest.txt"
if (Test-Path -LiteralPath $requirementsPath) {
    $requirementsText = Get-Content -Raw -Encoding UTF8 -LiteralPath $requirementsPath
    foreach ($package in @(
        "docling",
        "edgartools",
        "markitdown[all]",
        "openpyxl",
        "python-pptx",
        "python-docx",
        "pdfplumber",
        "pypdf",
        "pytesseract",
        "Pillow"
    )) {
        if (-not $requirementsText.Contains($package)) {
            $failures.Add("requirements-ingest.txt missing package '$package'")
        }
    }
}

if ($failures.Count -gt 0) {
    Write-Host "Ingest skill validation failed:" -ForegroundColor Red
    foreach ($failure in $failures) {
        Write-Host " - $failure" -ForegroundColor Red
    }
    exit 1
}

Write-Host "Ingest skill validation passed." -ForegroundColor Green
