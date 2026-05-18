param(
    [string]$SkillName = "new-session"
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
        $failures.Add("Missing required new-session file: $path")
    }
}

if (Test-Path -LiteralPath $skillPath) {
    $skillText = Get-Content -Raw -Encoding UTF8 -LiteralPath $skillPath

    foreach ($phrase in @(
        "# New Session",
        "New Topic Root",
        "Resolve Dated Result Path",
        "Index Touch",
        "index.md",
        "_inbox/",
        "Do not create `_raw/`, `_cache/`, or `_models/`",
        "topics/<topic-namespace>/<topic-slug>/",
        "topics/industry/space-launch/2026-05-18-rklb-stock-quickread.md",
        "topics/company/rklb/2026-05-18-stock-quickread.md",
        "YYYY-MM-DD-<company-slug>-<artifact>.md",
        "promote-company",
        "ingest",
        "topic_scaffold",
        "topic root + inbox + dated result file"
    )) {
        if (-not $skillText.Contains($phrase)) {
            $failures.Add("new-session: SKILL.md missing required phrase '$phrase'")
        }
    }

    foreach ($forbiddenPhrase in @(
        ("create full topic " + "scaffold"),
        ("_raw/{filings," + "transcripts,sellside,industry,irdecks,datasets}"),
        "完整 scaffold",
        ("session" + "_slug")
    )) {
        if ($skillText.Contains($forbiddenPhrase)) {
            $failures.Add("new-session: SKILL.md still contains deprecated phrase '$forbiddenPhrase'")
        }
    }
}

if (Test-Path -LiteralPath $yamlPath) {
    $yamlText = Get-Content -Raw -Encoding UTF8 -LiteralPath $yamlPath
    $expectedScalars = @{
        metadata_schema_version = "1"
        name = "new-session"
        id = "new-session"
        version = "2.1.0"
        system_generation = "3.8.0"
        category = "operations"
    }

    foreach ($key in $expectedScalars.Keys) {
        $actual = Get-YamlScalar $yamlText $key
        if ($actual -ne $expectedScalars[$key]) {
            $failures.Add("new-session: skill.yaml $key '$actual' does not match expected '$($expectedScalars[$key])'")
        }
    }

    if ($yamlText -match "(?m)^research_layer:") {
        $failures.Add("new-session: operations skill must not define research_layer")
    }

    foreach ($phrase in @(
        "topic_scaffold",
        "topic root + inbox + dated result file",
        "topics/[topic-namespace]/[topic-slug]/_inbox/",
        "do not create _raw/, _cache/, or _models/",
        "use [YYYY-MM-DD]-[company-slug]-[artifact].md",
        "promote-company",
        "ingest"
    )) {
        if (-not $yamlText.Contains($phrase)) {
            $failures.Add("new-session: skill.yaml missing required phrase '$phrase'")
        }
    }

    foreach ($forbiddenPhrase in @(
        ("create full topic " + "scaffold"),
        ("_raw/{filings," + "transcripts,sellside,industry,irdecks,datasets}")
    )) {
        if ($yamlText.Contains($forbiddenPhrase)) {
            $failures.Add("new-session: skill.yaml still contains deprecated phrase '$forbiddenPhrase'")
        }
    }
}

if ($failures.Count -gt 0) {
    Write-Host "New-session validation failed:" -ForegroundColor Red
    foreach ($failure in $failures) {
        Write-Host " - $failure" -ForegroundColor Red
    }
    exit 1
}

Write-Host "New-session validation passed." -ForegroundColor Green
