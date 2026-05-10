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
    "assets\AGENTS.md.template",
    "assets\gitignore.template",
    "assets\edge-radar.md"
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

Require-Path $skillPath "Missing init SKILL.md"
Require-Path $yamlPath "Missing init skill.yaml"
Require-Path $scriptPath "Missing init helper script"

foreach ($asset in $assetPaths) {
    Require-Path (Join-Path $skillRoot $asset) "Missing init asset: $asset"
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
            $failures.Add("init: missing operations section '$section'")
        }
    }

    foreach ($phrase in @(
        "workspace scaffold",
        "AGENTS.md",
        "AGENTS.md.template",
        "_inbox",
        "_raw",
        "_cache",
        "_models",
        "topics/_meta/edge-radar.md",
        "bootstrap-ingest-deps.ps1",
        "requirements-ingest.txt",
        "Docling",
        "Tesseract",
        "git init",
        "ingest"
    )) {
        if (-not $skillText.Contains($phrase)) {
            $failures.Add("init: SKILL.md missing required phrase '$phrase'")
        }
    }

    foreach ($phrase in @(
        "category: 'operations'",
        "workspace_scaffold",
        "workspace scaffold",
        "user-provided research workspace",
        "3.5.0-dev"
    )) {
        if (-not $yamlText.Contains($phrase)) {
            $failures.Add("init: skill.yaml missing required phrase '$phrase'")
        }
    }

    if ($yamlText -match "(?m)^research_layer:") {
        $failures.Add("init: operations skill must not define research_layer")
    }

    $yamlName = Get-YamlScalar $yamlText "name"
    $yamlVersion = Get-YamlScalar $yamlText "version"
    $systemGeneration = Get-YamlScalar $yamlText "system_generation"

    if ($yamlName -ne "init") {
        $failures.Add("init: skill.yaml name '$yamlName' does not match init")
    }
    if ($yamlVersion -ne "1.3.0") {
        $failures.Add("init: expected skill version 1.3.0, found '$yamlVersion'")
    }
    if ($systemGeneration -ne "3.5.0-dev") {
        $failures.Add("init: expected system_generation 3.5.0-dev, found '$systemGeneration'")
    }
}

if (Test-Path -LiteralPath $scriptPath) {
    $scriptText = Get-Content -Raw -Encoding UTF8 -LiteralPath $scriptPath
    foreach ($phrase in @(
        "WorkspacePath",
        "AGENTS.md.template",
        "AGENTS.md",
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

$claudeTemplatePath = Join-Path $skillRoot "assets\CLAUDE.md.template"
if (Test-Path -LiteralPath $claudeTemplatePath) {
    $claudeTemplate = Get-Content -Raw -Encoding UTF8 -LiteralPath $claudeTemplatePath
    foreach ($phrase in @(
        "Buy-Side Research Workspace Constitution",
        "Buy-side equity researcher",
        "LANG-default = zh",
        "Source Policy",
        "Anti-Hallucination",
        "Anti Sell-Side Rules",
        "Cross-Cut Bias",
        "new-session",
        "ingest",
        "research-journal.md",
        "topics/[company|theme|event]",
        "_cache/",
        "AGENTS.md"
    )) {
        if (-not $claudeTemplate.Contains($phrase)) {
            $failures.Add("workspace CLAUDE.md.template missing required phrase '$phrase'")
        }
    }

    foreach ($forbidden in @("decision-journal", "thesis-tracker", "coverage/", "portfolio/", "pairs/")) {
        if ($claudeTemplate.Contains($forbidden)) {
            $failures.Add("workspace CLAUDE.md.template contains forbidden stale phrase '$forbidden'")
        }
    }
}

$agentsTemplatePath = Join-Path $skillRoot "assets\AGENTS.md.template"
if (Test-Path -LiteralPath $agentsTemplatePath) {
    $agentsTemplate = Get-Content -Raw -Encoding UTF8 -LiteralPath $agentsTemplatePath
    foreach ($phrase in @(
        "Research Workspace Agent Entry Point",
        "CLAUDE.md",
        "AGENTS.md",
        "source of truth",
        "Required Workflow",
        "source policy"
    )) {
        if (-not $agentsTemplate.Contains($phrase)) {
            $failures.Add("workspace AGENTS.md.template missing required phrase '$phrase'")
        }
    }

    foreach ($forbidden in @("decision-journal", "thesis-tracker", "coverage/", "portfolio/", "pairs/")) {
        if ($agentsTemplate.Contains($forbidden)) {
            $failures.Add("workspace AGENTS.md.template contains forbidden stale phrase '$forbidden'")
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
