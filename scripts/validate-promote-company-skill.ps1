param(
    [string]$SkillName = "promote-company"
)

$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$skillRoot = Join-Path $repoRoot "skills\$SkillName"
$skillPath = Join-Path $skillRoot "SKILL.md"
$yamlPath = Join-Path $skillRoot "skill.yaml"
$scriptPath = Join-Path $skillRoot "scripts\promote_company.py"
$failures = New-Object System.Collections.Generic.List[string]

function Require-Path {
    param([string]$Path, [string]$Message)
    if (-not (Test-Path -LiteralPath $Path)) {
        $script:failures.Add($Message)
    }
}

function Get-YamlScalar {
    param([string]$Text, [string]$Key)
    $match = [regex]::Match($Text, "(?m)^$([regex]::Escape($Key)):\s*['""]?([^'""\r\n]+)['""]?\s*$")
    if ($match.Success) { return $match.Groups[1].Value.Trim() }
    return $null
}

Require-Path $skillPath "Missing promote-company SKILL.md"
Require-Path $yamlPath "Missing promote-company skill.yaml"
Require-Path $scriptPath "Missing promote-company helper script"

if ((Test-Path -LiteralPath $skillPath) -and (Test-Path -LiteralPath $yamlPath)) {
    $skillText = Get-Content -Raw -Encoding UTF8 -LiteralPath $skillPath
    $yamlText = Get-Content -Raw -Encoding UTF8 -LiteralPath $yamlPath

    foreach ($phrase in @(
        "# Promote Company",
        "topics/company/<company-slug>/",
        "2026-05-18-rklb-stock-quickread.md",
        "2026-05-18-stock-quickread.md",
        "Backlink Only",
        "Dry Run",
        "integrate",
        "mixed peer / industry artifact",
        "conversation-only"
    )) {
        if (-not $skillText.Contains($phrase)) {
            $failures.Add("promote-company: SKILL.md missing required phrase '$phrase'")
        }
    }

    $expected = @{
        metadata_schema_version = "1"
        name = "promote-company"
        id = "promote-company"
        version = "1.0.0"
        system_generation = "3.8.0"
        category = "operations"
    }
    foreach ($key in $expected.Keys) {
        $actual = Get-YamlScalar $yamlText $key
        if ($actual -ne $expected[$key]) {
            $failures.Add("promote-company: skill.yaml $key '$actual' does not match expected '$($expected[$key])'")
        }
    }

    foreach ($phrase in @(
        "save_policy: 'none'",
        "company-promotion",
        "Promote Company",
        "Backlink Only",
        "Dry Run Move Plan",
        "do not replace integrate whole-topic merge behavior"
    )) {
        if (-not $yamlText.Contains($phrase)) {
            $failures.Add("promote-company: skill.yaml missing required phrase '$phrase'")
        }
    }

    if ($yamlText -match "(?m)^research_layer:") {
        $failures.Add("promote-company: operations skill must not define research_layer")
    }
}

if (Test-Path -LiteralPath $scriptPath) {
    $scriptText = Get-Content -Raw -Encoding UTF8 -LiteralPath $scriptPath
    foreach ($phrase in @(
        "--source-topic",
        "--company-slug",
        "--apply",
        "dry_run",
        "company-prefixed dated markdown",
        "cache source_path matched a promoted source file",
        "collision_safe"
    )) {
        if (-not $scriptText.Contains($phrase)) {
            $failures.Add("promote_company.py missing required phrase '$phrase'")
        }
    }
}

if ($failures.Count -gt 0) {
    Write-Host "Promote-company validation failed:" -ForegroundColor Red
    foreach ($failure in $failures) {
        Write-Host " - $failure" -ForegroundColor Red
    }
    exit 1
}

Write-Host "Promote-company validation passed." -ForegroundColor Green
