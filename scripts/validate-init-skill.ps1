param(
    [string]$SkillName = "init"
)

$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$skillRoot = Join-Path $repoRoot "skills\$SkillName"
$skillPath = Join-Path $skillRoot "SKILL.md"
$yamlPath = Join-Path $skillRoot "skill.yaml"
$scriptPath = Join-Path $skillRoot "scripts\init-research-workspace.ps1"
$assetPaths = @(
    "assets\CLAUDE.md.template",
    "assets\gitignore.template",
    "assets\edge-radar.md"
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

Require-Path $skillPath "Missing init SKILL.md"
Require-Path $yamlPath "Missing init skill.yaml"
Require-Path $scriptPath "Missing init helper script"

foreach ($asset in $assetPaths) {
    Require-Path (Join-Path $skillRoot $asset) "Missing init asset: $asset"
}

if ((Test-Path -LiteralPath $skillPath) -and (Test-Path -LiteralPath $yamlPath)) {
    $skillText = Get-Content -Raw -Encoding UTF8 -LiteralPath $skillPath
    $yamlText = Get-Content -Raw -Encoding UTF8 -LiteralPath $yamlPath

    $capsuleCount = ([regex]::Matches($skillText, "## Global Rules Capsule \(v1\)")).Count
    if ($capsuleCount -ne 1) {
        $failures.Add("init: expected exactly one Global Rules Capsule, found $capsuleCount")
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
            $failures.Add("init: missing required section '$($section.Label)'")
        }
    }

    $notText = New-UnicodeText @(0x4E0D)
    foreach ($phrase in @(
        "workspace scaffold",
        "_inbox",
        "_raw",
        "_cache",
        "_models",
        "topics/_meta/edge-radar.md",
        "bootstrap-ingest-deps.ps1",
        "requirements-ingest.txt",
        "Docling",
        "Tesseract",
        ($notText + " git init"),
        ($notText + " ingest")
    )) {
        if (-not $skillText.Contains($phrase)) {
            $failures.Add("init: SKILL.md missing required phrase '$phrase'")
        }
    }

    foreach ($phrase in @(
        "workspace_scaffold",
        "workspace scaffold",
        "user-provided research workspace",
        "3.4.0-dev"
    )) {
        if (-not $yamlText.Contains($phrase)) {
            $failures.Add("init: skill.yaml missing required phrase '$phrase'")
        }
    }

    $yamlName = Get-YamlScalar $yamlText "name"
    $yamlVersion = Get-YamlScalar $yamlText "version"
    $systemGeneration = Get-YamlScalar $yamlText "system_generation"

    if ($yamlName -ne "init") {
        $failures.Add("init: skill.yaml name '$yamlName' does not match init")
    }
    if ($yamlVersion -ne "1.2.0") {
        $failures.Add("init: expected skill version 1.2.0, found '$yamlVersion'")
    }
    if ($systemGeneration -ne "3.4.0-dev") {
        $failures.Add("init: expected system_generation 3.4.0-dev, found '$systemGeneration'")
    }
}

if (Test-Path -LiteralPath $scriptPath) {
    $scriptText = Get-Content -Raw -Encoding UTF8 -LiteralPath $scriptPath
    foreach ($phrase in @(
        "WorkspacePath",
        "Refusing to initialize research workspace inside a plugin repo",
        ".claude-plugin\plugin.json",
        ".codex-plugin\plugin.json",
        "ingest.py",
        "ingest_xlsx.py",
        "ingest_table_crosscheck.py",
        "bootstrap-ingest-deps.ps1",
        "requirements-ingest.txt",
        "init-assets",
        "No git init, no dependency install, and no ingest execution were performed."
    )) {
        if (-not $scriptText.Contains($phrase)) {
            $failures.Add("init helper script missing required phrase '$phrase'")
        }
    }
}

if ($failures.Count -gt 0) {
    Write-Host "Init skill validation failed:" -ForegroundColor Red
    foreach ($failure in $failures) {
        Write-Host " - $failure" -ForegroundColor Red
    }
    exit 1
}

Write-Host "Init skill validation passed." -ForegroundColor Green
