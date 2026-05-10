param(
    [string]$SkillName = "company-primer"
)

$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$skillRoot = Join-Path $repoRoot "skills\$SkillName"
$skillPath = Join-Path $skillRoot "SKILL.md"
$yamlPath = Join-Path $skillRoot "skill.yaml"
$failures = New-Object System.Collections.Generic.List[string]

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

foreach ($path in @($skillPath, $yamlPath)) {
    if (-not (Test-Path -LiteralPath $path)) {
        $failures.Add("Missing required company-primer file: $path")
    }
}

if (Test-Path -LiteralPath $skillPath) {
    $skillText = Get-Content -Raw -Encoding UTF8 -LiteralPath $skillPath

    $requiredSkillPhrases = @(
        "## Global Rules Capsule (v1)",
        "# Company Primer",
        "Foundation Primer",
        "Business Evolution Audit",
        "Disclosure Evolution Audit",
        "company-primer.md",
        "driver-map",
        "mechanism-map",
        "information-impact",
        "research-journal"
    )

    foreach ($phrase in $requiredSkillPhrases) {
        if (-not $skillText.Contains($phrase)) {
            $failures.Add("SKILL.md is missing required phrase: $phrase")
        }
    }
}

if (Test-Path -LiteralPath $yamlPath) {
    $yamlText = Get-Content -Raw -Encoding UTF8 -LiteralPath $yamlPath
    $expectedScalars = @{
        name = "company-primer"
        id = "company-primer"
        version = "1.0.0"
        system_generation = "3.4.0-dev"
        metadata_schema_version = "1"
    }

    foreach ($key in $expectedScalars.Keys) {
        $actual = Get-YamlScalar $yamlText $key
        if ($actual -ne $expectedScalars[$key]) {
            $failures.Add("skill.yaml $key '$actual' does not match expected '$($expectedScalars[$key])'")
        }
    }

    foreach ($phrase in @("Foundation Primer", "Business Evolution Audit", "Disclosure Evolution Audit", "optional_topic_session", "company-primer.md")) {
        if (-not $yamlText.Contains($phrase)) {
            $failures.Add("skill.yaml is missing required phrase: $phrase")
        }
    }
}

if ($failures.Count -gt 0) {
    Write-Host "Company primer validation failed:" -ForegroundColor Red
    foreach ($failure in $failures) {
        Write-Host " - $failure" -ForegroundColor Red
    }
    exit 1
}

Write-Host "Company primer validation passed." -ForegroundColor Green
