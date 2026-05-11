param(
    [int]$ExpectedActiveSkillCount = 20
)

$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$skillsRoot = Join-Path $repoRoot "skills"
$exampleWorkspace = Join-Path $repoRoot "examples\workspaces\ai-data-center-power"
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

Require-Path (Join-Path $repoRoot ".claude-plugin\plugin.json") "Missing Claude plugin manifest: .claude-plugin/plugin.json"
Require-Path (Join-Path $repoRoot ".codex-plugin\plugin.json") "Missing Codex plugin manifest: .codex-plugin/plugin.json"
Require-Path $exampleWorkspace "Missing example workspace: examples/workspaces/ai-data-center-power"
Require-Path (Join-Path $repoRoot "docs\install.md") "Missing install docs: docs/install.md"

foreach ($rootResearchDir in @("topics", "screens", "peers", "quickreads")) {
    if (Test-Path -LiteralPath (Join-Path $repoRoot $rootResearchDir)) {
        $failures.Add("Root research artifact directory should live under examples/workspaces/ai-data-center-power: $rootResearchDir")
    }

    if (-not (Test-Path -LiteralPath (Join-Path $exampleWorkspace $rootResearchDir))) {
        $failures.Add("Example workspace missing migrated directory: $rootResearchDir")
    }
}

$activeSkillDirs = Get-ChildItem -LiteralPath $skillsRoot -Directory |
    Where-Object { Test-Path -LiteralPath (Join-Path $_.FullName "SKILL.md") } |
    Sort-Object Name

if ($activeSkillDirs.Count -ne $ExpectedActiveSkillCount) {
    $failures.Add("Expected $ExpectedActiveSkillCount active skills with SKILL.md, found $($activeSkillDirs.Count): $($activeSkillDirs.Name -join ', ')")
}

if (Test-Path -LiteralPath (Join-Path $skillsRoot "_shared\SKILL.md")) {
    $failures.Add("_shared must not contain SKILL.md; it should not be an active skill")
}

$installDoc = Join-Path $repoRoot "docs\install.md"
if (Test-Path -LiteralPath $installDoc) {
    $installText = Get-Content -Raw -Encoding UTF8 -LiteralPath $installDoc
    if (-not $installText.Contains("iRyantik/buy-side-research-skills")) {
        $failures.Add("docs/install.md must reference iRyantik/buy-side-research-skills")
    }
}

$releaseDoc = Join-Path $repoRoot "docs\release.md"
if (Test-Path -LiteralPath $releaseDoc) {
    $releaseText = Get-Content -Raw -Encoding UTF8 -LiteralPath $releaseDoc
    foreach ($excluded in @('.claude/', 'RTK.md', '.git/', 'root `CLAUDE.md`', 'root `AGENTS.md`', 'root `scripts/`', '`docs/`', '`examples/`')) {
        if (-not $releaseText.Contains($excluded)) {
            $failures.Add("docs/release.md must document release exclusion: $excluded")
        }
    }
}

if ($failures.Count -gt 0) {
    Write-Host "Plugin tree validation failed:" -ForegroundColor Red
    foreach ($failure in $failures) {
        Write-Host " - $failure" -ForegroundColor Red
    }
    exit 1
}

Write-Host "Plugin tree validation passed for $($activeSkillDirs.Count) active skills." -ForegroundColor Green
