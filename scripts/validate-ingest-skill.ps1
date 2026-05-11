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
    param([object[]]$CodePoints)

    return -join ($CodePoints | ForEach-Object {
        if ($_ -is [System.Array]) {
            $_ | ForEach-Object { [char][int]$_ }
        } else {
            [char][int]$_
        }
    })
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

    foreach ($section in @(
        (New-UnicodeText @(0x5FC3, 0x6CD5)),
        (New-UnicodeText @(0x804C, 0x8D23, 0x8FB9, 0x754C)),
        (New-UnicodeText @(0x89E6, 0x53D1, 0x4E0E, 0x8F93, 0x5165)),
        (New-UnicodeText @(0x6267, 0x884C, 0x6A21, 0x5F0F)),
        (New-UnicodeText @(0x5DE5, 0x5177, 0x8D44, 0x6E90)),
        (New-UnicodeText @(0x6587, 0x4EF6, 0x5B89, 0x5168)),
        (New-UnicodeText @(0x8FD0, 0x884C, 0x8F93, 0x51FA, 0x5951, 0x7EA6)),
        (New-UnicodeText @(0x5931, 0x8D25, 0x5904, 0x7406)),
        ("Workflow " + (New-UnicodeText @(0x8054, 0x52A8))),
        (New-UnicodeText @(0x5B89, 0x5168, 0x81EA, 0x67E5))
    )) {
        if ($skillText -notmatch "(?m)^##\s*$([regex]::Escape($section))") {
            $failures.Add("ingest: missing operations section '$section'")
        }
    }

    foreach ($phrase in @(
        "topics/<topic>/_cache/",
        "source_sha256",
        "source_modified_utc",
        "converted_at_utc",
        "precision",
        "precision_level",
        "document_type",
        "route",
        "ingest.py",
        "ingest_xlsx.py",
        "ingest_table_crosscheck.py",
        "bootstrap-ingest-deps.ps1",
        "requirements-ingest.txt",
        "Docling",
        "EdgarTools",
        "PyMuPDF4LLM",
        "AKShare",
        "dart-fss",
        "openesef",
        "PDFPlumber",
        "--check-deps",
        "EDGAR_IDENTITY",
        "information-impact",
        "company-primer",
        "research-journal",
        "--category",
        "filings",
        "transcripts",
        "sellside",
        "industry",
        "irdecks",
        "datasets",
        "unclassified"
    )) {
        if (-not $skillText.Contains($phrase)) {
            $failures.Add("ingest: SKILL.md missing required phrase '$phrase'")
        }
    }

    foreach ($phrase in @(
        "category: 'operations'",
        "cache_artifact",
        "[source-filename].md",
        "topics/[topic]/_cache/[source-filename].md",
        "Dependency Bootstrap / Check",
        "precision_level",
        "document_type",
        "route",
        "3.7.0",
        "--category",
        "auto-infer document category",
        "strict topic check"
    )) {
        if (-not $yamlText.Contains($phrase)) {
            $failures.Add("ingest: skill.yaml missing required phrase '$phrase'")
        }
    }

    if ($yamlText -match "(?m)^research_layer:") {
        $failures.Add("ingest: operations skill must not define research_layer")
    }

    $yamlName = Get-YamlScalar $yamlText "name"
    $yamlVersion = Get-YamlScalar $yamlText "version"
    $systemGeneration = Get-YamlScalar $yamlText "system_generation"

    if ($yamlName -ne "ingest") {
        $failures.Add("ingest: skill.yaml name '$yamlName' does not match ingest")
    }
    if ($yamlVersion -ne "1.2.0") {
        $failures.Add("ingest: expected skill version 1.2.0, found '$yamlVersion'")
    }
    if ($systemGeneration -ne "3.7.0") {
        $failures.Add("ingest: expected system_generation 3.7.0, found '$systemGeneration'")
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
        "PyMuPDF4LLM",
        "akshare",
        "dart-fss",
        "openesef",
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
        "China",
        "PythonScope",
        "EdgarIdentity",
        "requirements-ingest.txt",
        "EDGAR_IDENTITY",
        "winget",
        "docling",
        "pymupdf4llm",
        "hf-mirror"
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
        "pymupdf4llm",
        "openesef",
        "akshare",
        "edinet-tools",
        "dart-fss",
        "openpyxl",
        "python-pptx",
        "python-docx",
        "pdfplumber",
        "pypdf",
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
