param(
    [string]$SkillName = "new-session"
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
        $failures.Add("Missing required new-session file: $path")
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
            $failures.Add("new-session: missing operations section '$section'")
        }
    }

    foreach ($phrase in @(
        "# New Session",
        "New Topic Session",
        "Resolve Save Path",
        "Index Touch",
        "topic_session_scaffold",
        "topics/[topic-slug]",
        "index.md",
        "Canonical Save Paths",
        "company-primer.md",
        "driver-map.md",
        "research-journal",
        "init-workspace",
        "earned insight",
        "Next Step",
        "_raw/",
        "topic scaffold",
        "_inbox/"
    )) {
        if (-not $skillText.Contains($phrase)) {
            $failures.Add("new-session: SKILL.md missing required phrase '$phrase'")
        }
    }

}

if (Test-Path -LiteralPath $yamlPath) {
    $yamlText = Get-Content -Raw -Encoding UTF8 -LiteralPath $yamlPath
    $expectedScalars = @{
        metadata_schema_version = "1"
        name = "new-session"
        id = "new-session"
        version = "1.0.0"
        system_generation = "3.7.0"
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
        "topic_session_scaffold",
        "topic session folder + index.md",
        "topics/[topic-slug]/[YYYY-MM-DD]-[session-slug]/",
        "New Topic Session",
        "Resolve Save Path",
        "Index Touch",
        "do not write research conclusions or earned insight",
        "do not recommend next research skill",
        "create full topic scaffold"
    )) {
        if (-not $yamlText.Contains($phrase)) {
            $failures.Add("new-session: skill.yaml missing required phrase '$phrase'")
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
