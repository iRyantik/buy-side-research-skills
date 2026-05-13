param(
    [string]$SkillName = "financial-data"
)

$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$skillRoot = Join-Path $repoRoot "skills\$SkillName"
$skillPath = Join-Path $skillRoot "SKILL.md"
$yamlPath = Join-Path $skillRoot "skill.yaml"
$handoffPath = Join-Path $repoRoot "HANDOFF.md"
$scriptPaths = @(
    "scripts\financial_data.py",
    "scripts\bootstrap-financial-data-deps.ps1",
    "assets\requirements-financial-data.txt",
    "scripts\providers\sec_provider.py",
    "scripts\providers\akshare_provider.py",
    "scripts\providers\edinet_provider.py",
    "scripts\providers\dart_provider.py",
    "scripts\providers\openesef_provider.py"
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

Require-Path $skillPath "Missing financial-data SKILL.md"
Require-Path $yamlPath "Missing financial-data skill.yaml"
Require-Path $handoffPath "Missing repo HANDOFF.md"
foreach ($script in $scriptPaths) {
    Require-Path (Join-Path $skillRoot $script) "Missing financial-data runtime file: $script"
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
            $failures.Add("financial-data: missing operations section '$section'")
        }
    }

    $noUndisclosedRevenueSplit = (New-UnicodeText @(0x4E0D, 0x63A8, 0x65AD, 0x672A, 0x62AB, 0x9732)) + " revenue split"

    foreach ($phrase in @(
        "output_scope",
        "canonical_company",
        "current_topic_snapshot",
        "company_slug",
        "identifier_type",
        "financial_data_pack_path",
        "topics/company/<company-slug>/",
        "_cache/datasets/financial-data/",
        "_raw/datasets/financial-data/",
        "manifest.json",
        "financials.md",
        "financials.normalized.json",
        "financial-data-summary.md",
        "internal/",
        "internal/evidence-pack.json",
        "internal/actuals-resolved.json",
        "identity-source.json",
        "source-metadata.json",
        "source.sha256",
        "completeness.json",
        "source-map.json",
        "available / partial / unavailable / provider-gap",
        "openesef",
        "ESEF",
        "ticker-only",
        "experimental",
        $noUndisclosedRevenueSplit,
        "3-statement-model",
        "dcf-model",
        "comps-analysis",
        "model-update"
    )) {
        if (-not $skillText.Contains($phrase)) {
            $failures.Add("financial-data: SKILL.md missing required phrase '$phrase'")
        }
    }

    foreach ($phrase in @(
        "category: 'operations'",
        "cache_artifact",
        "financial-data-summary.md",
        "topics/company/[company-slug]/_cache/datasets/financial-data/[market]/[canonical-id]/[run-id]/",
        "Dependency Bootstrap / Check",
        "Canonical Company Fetch",
        "Current Topic Snapshot",
        "3.7.0"
    )) {
        if (-not $yamlText.Contains($phrase)) {
            $failures.Add("financial-data: skill.yaml missing required phrase '$phrase'")
        }
    }

    if ($yamlText -match "(?m)^research_layer:") {
        $failures.Add("financial-data: operations skill must not define research_layer")
    }

    $yamlName = Get-YamlScalar $yamlText "name"
    $yamlVersion = Get-YamlScalar $yamlText "version"
    $systemGeneration = Get-YamlScalar $yamlText "system_generation"

    if ($yamlName -ne "financial-data") {
        $failures.Add("financial-data: skill.yaml name '$yamlName' does not match financial-data")
    }
    if ($yamlVersion -ne "1.0.0") {
        $failures.Add("financial-data: expected skill version 1.0.0, found '$yamlVersion'")
    }
    if ($systemGeneration -ne "3.7.0") {
        $failures.Add("financial-data: expected system_generation 3.7.0, found '$systemGeneration'")
    }
}

$mainScript = Join-Path $skillRoot "scripts\financial_data.py"
if (Test-Path -LiteralPath $mainScript) {
    $scriptText = Get-Content -Raw -Encoding UTF8 -LiteralPath $mainScript
    foreach ($phrase in @(
        "--check-deps",
        "--market",
        "--identifier",
        "--identifier-type",
        "--company-slug",
        "--output-scope",
        "canonical_company",
        "current_topic_snapshot",
        "completeness.json",
        "source-map.json",
        "financials.normalized.json",
        "identity-source.json",
        "source-metadata.json",
        "source.sha256",
        "financial-data-summary.md",
        "internal/evidence-pack.json",
        "internal/actuals-resolved.json",
        "provider-normalized-review",
        "evidence-ready",
        "model-ready",
        "available",
        "partial",
        "unavailable",
        "provider-gap",
        "EDGAR_IDENTITY",
        "DART_API_KEY",
        "openesef",
        "provider_gap",
        "fail honestly",
        "write_raw_evidence_pack",
        "write_modeling_input_aliases",
        "derive_pack_status"
    )) {
        if (-not $scriptText.Contains($phrase)) {
            $failures.Add("financial_data.py missing required phrase '$phrase'")
        }
    }
}

if (Test-Path -LiteralPath $handoffPath) {
    $handoffText = Get-Content -Raw -Encoding UTF8 -LiteralPath $handoffPath
    foreach ($phrase in @(
        '# HANDOFF - Financial-Data Provider Repair Execution',
        'Sphere `347700`',
        'Toray `3402`',
        '`3750`',
        'RKLB',
        '_raw/` currently only had `provider_payload.json`',
        '`edinet_provider`',
        '`dart_provider`',
        '`_raw/` evidence files'
    )) {
        if (-not $handoffText.Contains($phrase)) {
            $failures.Add("HANDOFF.md missing required repair-context phrase '$phrase'")
        }
    }
}

$requirementsPath = Join-Path $skillRoot "assets\requirements-financial-data.txt"
if (Test-Path -LiteralPath $requirementsPath) {
    $requirementsText = Get-Content -Raw -Encoding UTF8 -LiteralPath $requirementsPath
    foreach ($package in @(
        "edgartools",
        "akshare",
        "edinet-tools",
        "dart-fss",
        "openesef"
    )) {
        if (-not $requirementsText.Contains($package)) {
            $failures.Add("requirements-financial-data.txt missing package '$package'")
        }
    }
}

if ($failures.Count -gt 0) {
    Write-Host "Financial-data skill validation failed:" -ForegroundColor Red
    foreach ($failure in $failures) {
        Write-Host " - $failure" -ForegroundColor Red
    }
    exit 1
}

Write-Host "Financial-data skill validation passed." -ForegroundColor Green
