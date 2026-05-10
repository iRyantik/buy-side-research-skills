param(
    [string]$SkillName = "meta-skill"
)

$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$skillRoot = Join-Path $repoRoot "skills\$SkillName"
$skillPath = Join-Path $skillRoot "SKILL.md"
$yamlPath = Join-Path $skillRoot "skill.yaml"
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
        $failures.Add("Missing required meta-skill file: $path")
    }
}

if (Test-Path -LiteralPath $skillPath) {
    $skillText = Get-Content -Raw -Encoding UTF8 -LiteralPath $skillPath

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
            $failures.Add("meta-skill: missing operations section '$section'")
        }
    }

    foreach ($phrase in @(
        "# Meta Skill",
        "Buy-side equity researcher",
        "LS",
        "v3 Journal-First",
        "Senior Analyst Radar -> Better AI Question -> Research -> Journal -> Boss Brief",
        "Research Skill",
        "Research SKILL.md",
        "Operations SKILL.md",
        "Source",
        "Catalog",
        "Final Workflow",
        "Checklist",
        "category",
        "research_layer",
        "research",
        "operations",
        "new-session",
        "topic_session_scaffold",
        "artifact policy",
        "skill.yaml",
        "validate-skill-metadata.ps1",
        "validate-skill-structure.ps1",
        "meta.json",
        "v2 state",
        "skills/[skill-name]/SKILL.md"
    )) {
        if (-not $skillText.Contains($phrase)) {
            $failures.Add("meta-skill: SKILL.md missing required phrase '$phrase'")
        }
    }

    $forbiddenPhrases = @(
        "system_generation: 3.4.0-dev",
        ("FRAMEWORK" + ".md"),
        ("META-SKILL" + ".md")
    )
    foreach ($forbiddenPhrase in $forbiddenPhrases) {
        if ($skillText.Contains($forbiddenPhrase)) {
            $failures.Add("meta-skill: SKILL.md contains stale version phrase '$forbiddenPhrase'")
        }
    }
}

if (Test-Path -LiteralPath $yamlPath) {
    $yamlText = Get-Content -Raw -Encoding UTF8 -LiteralPath $yamlPath
    $expectedScalars = @{
        name = "meta-skill"
        id = "meta-skill"
        version = "1.1.1"
        system_generation = "3.5.0"
        metadata_schema_version = "1"
        category = "operations"
    }

    foreach ($key in $expectedScalars.Keys) {
        $actual = Get-YamlScalar $yamlText $key
        if ($actual -ne $expectedScalars[$key]) {
            $failures.Add("skill.yaml $key '$actual' does not match expected '$($expectedScalars[$key])'")
        }
    }

    if ($yamlText -match "(?m)^research_layer:") {
        $failures.Add("meta-skill: operations skill must not define research_layer")
    }

    foreach ($phrase in @("skill-authoring", "none", "conversation-only", "research_layer_for_research_only")) {
        if (-not $yamlText.Contains($phrase)) {
            $failures.Add("skill.yaml is missing required phrase: $phrase")
        }
    }
}

if ($failures.Count -gt 0) {
    Write-Host "Meta-skill validation failed:" -ForegroundColor Red
    foreach ($failure in $failures) {
        Write-Host " - $failure" -ForegroundColor Red
    }
    exit 1
}

Write-Host "Meta-skill validation passed." -ForegroundColor Green
