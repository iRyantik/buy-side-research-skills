param()

$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$skillsRoot = Join-Path $repoRoot "skills"
$sharedRulesPath = Join-Path $skillsRoot "_shared\global-rules.md"
$mainAgent = [string]([char]0x4E3B) + " agent"
$noFinalConclusion = [string]([char]0x4E0D) + [char]0x5F97 + [char]0x5199 + [char]0x6700 + [char]0x7EC8 + [char]0x7ED3 + [char]0x8BBA
$subAgentRuntimeCap = "Runtime cap: no per-skill sub-agent count limit; max 6-8 active sub-agents globally; parallel within one skill but serial across skills; close sub-agents immediately after evidence cards or QA notes return."
$oldSubAgentRuntimeCap = "max 3-5 sub-agents" + " per skill"

$parallelEvidenceSkills = @(
    "peer-deep-dive",
    "driver-map",
    "company-primer",
    "candidate-screener",
    "cross-market-compare",
    "earnings-setup",
    "stock-quickread",
    "industry-quickread",
    "consensus-map",
    "mechanism-map",
    "information-impact",
    "alpha-thesis",
    "bear-pre-mortem",
    "pair-trade",
    "primary-research-plan",
    "next-step",
    "research-journal"
)

$skillRequiredPhrases = @(
    "## Parallel Evidence Pass",
    "evidence card",
    $mainAgent,
    $noFinalConclusion,
    "URL / claim",
    $subAgentRuntimeCap
)

$yamlRequiredPhrases = @(
    "parallel_evidence_spawn_default",
    "evidence_cards_only",
    "main_agent_synthesis_required",
    "url_claim_spot_check_required"
)

$failures = New-Object System.Collections.Generic.List[string]

$legacyScanTargets = @(
    (Join-Path $repoRoot "CLAUDE.md"),
    (Join-Path $repoRoot "README.md")
)
$legacyScanTargets += Get-ChildItem -LiteralPath (Join-Path $repoRoot "docs") -Recurse -File |
    Select-Object -ExpandProperty FullName
$legacyScanTargets += Get-ChildItem -LiteralPath $skillsRoot -Recurse -File |
    Select-Object -ExpandProperty FullName
$legacyScanTargets += Get-ChildItem -LiteralPath (Join-Path $repoRoot "scripts") -Recurse -File |
    Select-Object -ExpandProperty FullName

foreach ($path in $legacyScanTargets) {
    $text = Get-Content -Raw -Encoding UTF8 -LiteralPath $path
    if ($text.Contains($oldSubAgentRuntimeCap)) {
        $failures.Add("legacy sub-agent runtime cap phrase remains in: $path")
    }
}

if (-not (Test-Path -LiteralPath $sharedRulesPath)) {
    $failures.Add("Missing shared runtime rules file: $sharedRulesPath")
} else {
    $sharedText = Get-Content -Raw -Encoding UTF8 -LiteralPath $sharedRulesPath
    foreach ($phrase in @("## 5. Sub-Agent Evidence Protocol", "evidence card", $mainAgent, $noFinalConclusion, $subAgentRuntimeCap)) {
        if (-not $sharedText.Contains($phrase)) {
            $failures.Add("shared global rules missing sub-agent protocol phrase: $phrase")
        }
    }
}

foreach ($skillName in $parallelEvidenceSkills) {
    $skillPath = Join-Path $skillsRoot "$skillName\SKILL.md"
    $yamlPath = Join-Path $skillsRoot "$skillName\skill.yaml"

    if (-not (Test-Path -LiteralPath $skillPath)) {
        $failures.Add("${skillName}: missing SKILL.md")
        continue
    }
    if (-not (Test-Path -LiteralPath $yamlPath)) {
        $failures.Add("${skillName}: missing skill.yaml")
        continue
    }

    $skillText = Get-Content -Raw -Encoding UTF8 -LiteralPath $skillPath
    $yamlText = Get-Content -Raw -Encoding UTF8 -LiteralPath $yamlPath

    foreach ($phrase in $skillRequiredPhrases) {
        if (-not $skillText.Contains($phrase)) {
            $failures.Add("${skillName}: SKILL.md missing sub-agent protocol phrase: $phrase")
        }
    }

    foreach ($phrase in $yamlRequiredPhrases) {
        if (-not $yamlText.Contains($phrase)) {
            $failures.Add("${skillName}: skill.yaml missing sub-agent protocol phrase: $phrase")
        }
    }
}

$operationsDirs = Get-ChildItem -LiteralPath $skillsRoot -Directory |
    Where-Object {
        $yamlPath = Join-Path $_.FullName "skill.yaml"
        $skillPath = Join-Path $_.FullName "SKILL.md"
        (Test-Path -LiteralPath $yamlPath) -and (Test-Path -LiteralPath $skillPath) -and
            ((Get-Content -Raw -Encoding UTF8 -LiteralPath $yamlPath) -match "(?m)^category:\s*['""]?operations['""]?\s*$")
    }

foreach ($dir in $operationsDirs) {
    $skillText = Get-Content -Raw -Encoding UTF8 -LiteralPath (Join-Path $dir.FullName "SKILL.md")
    if ($skillText.Contains("## Parallel Evidence Pass")) {
        $failures.Add("$($dir.Name): operations skill must not contain Parallel Evidence Pass")
    }
}

if ($failures.Count -gt 0) {
    Write-Host "Sub-agent protocol validation failed:" -ForegroundColor Red
    foreach ($failure in $failures) {
        Write-Host " - $failure" -ForegroundColor Red
    }
    exit 1
}

Write-Host "Sub-agent protocol validation passed for $($parallelEvidenceSkills.Count) parallel-evidence research skills." -ForegroundColor Green
