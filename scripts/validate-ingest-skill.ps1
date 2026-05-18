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

    foreach ($phrase in @(
        "topics/<namespace>/<topic-slug>/_cache/",
        "topics/<namespace>/<topic-slug>/index.md",
        "_raw/<category>/",
        "_cache/",
        "industry/space-launch",
        "company/rklb",
        "source_sha256",
        "source_modified_utc",
        "converted_at_utc",
        "precision_level",
        "document_type",
        "route",
        "Docling",
        "EdgarTools",
        "PyMuPDF4LLM",
        "PDFPlumber",
        "--check-deps",
        "financial-data",
        "promote-company"
    )) {
        if (-not $skillText.Contains($phrase)) {
            $failures.Add("ingest: SKILL.md missing required phrase '$phrase'")
        }
    }

    foreach ($phrase in @(
        "category: 'operations'",
        "cache_artifact",
        "topics/[topic-namespace]/[topic-slug]/_cache/[source-filename].md",
        "1.4.0",
        "strict topic root check",
        "support namespaced topics",
        "create _cache/ and _raw/<category>/ on first conversion"
    )) {
        if (-not $yamlText.Contains($phrase)) {
            $failures.Add("ingest: skill.yaml missing required phrase '$phrase'")
        }
    }

    if ($yamlText -match "(?m)^research_layer:") {
        $failures.Add("ingest: operations skill must not define research_layer")
    }

    if ((Get-YamlScalar $yamlText "name") -ne "ingest") {
        $failures.Add("ingest: skill.yaml name does not match ingest")
    }
    if ((Get-YamlScalar $yamlText "version") -ne "1.4.0") {
        $failures.Add("ingest: expected skill version 1.4.0")
    }
    if ((Get-YamlScalar $yamlText "system_generation") -ne "3.8.0") {
        $failures.Add("ingest: expected system_generation 3.8.0")
    }
}

$ingestScript = Join-Path $skillRoot "scripts\ingest.py"
if (Test-Path -LiteralPath $ingestScript) {
    $scriptText = Get-Content -Raw -Encoding UTF8 -LiteralPath $ingestScript
    foreach ($phrase in @(
        "TOPIC_NAMESPACES",
        "normalize_topic_arg",
        "industry/space-launch",
        "company/rklb",
        "source_sha256",
        "source_modified_utc",
        "converted_at_utc",
        "precision_level",
        "document_type",
        "route",
        "def cache",
        "--check-deps",
        "Missing optional dependency",
        "--recursive",
        "--force"
    )) {
        if (-not $scriptText.Contains($phrase)) {
            $failures.Add("ingest.py missing required phrase '$phrase'")
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
