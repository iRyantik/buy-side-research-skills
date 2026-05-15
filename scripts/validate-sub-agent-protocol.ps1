param()

$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$skillsRoot = Join-Path $repoRoot "skills"
$sharedRulesPath = Join-Path $skillsRoot "_shared\global-rules.md"
$mainAgent = [string]([char]0x4E3B) + " agent"
$noFinalConclusion = [string]([char]0x4E0D) + [char]0x5F97 + [char]0x5199 + [char]0x6700 + [char]0x7EC8 + [char]0x7ED3 + [char]0x8BBA

$firstBatchSkills = @(
    "peer-deep-dive",
    "driver-map",
    "company-primer",
    "candidate-screener",
    "cross-market-compare",
    "earnings-setup"
)

$skillRequiredPhrases = @(
    "## Parallel Evidence Pass",
    "evidence card",
    $mainAgent,
    $noFinalConclusion,
    "URL / claim"
)

$yamlRequiredPhrases = @(
    "parallel_evidence_gathering",
    "evidence_cards_only",
    "main_agent_synthesis_required",
    "url_claim_spot_check_required"
)

$failures = New-Object System.Collections.Generic.List[string]

if (-not (Test-Path -LiteralPath $sharedRulesPath)) {
    $failures.Add("Missing shared runtime rules file: $sharedRulesPath")
} else {
    $sharedText = Get-Content -Raw -Encoding UTF8 -LiteralPath $sharedRulesPath
    foreach ($phrase in @("## 5. Sub-Agent Evidence Protocol", "evidence card", $mainAgent, $noFinalConclusion)) {
        if (-not $sharedText.Contains($phrase)) {
            $failures.Add("shared global rules missing sub-agent protocol phrase: $phrase")
        }
    }
}

foreach ($skillName in $firstBatchSkills) {
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

Write-Host "Sub-agent protocol validation passed for $($firstBatchSkills.Count) first-batch research skills." -ForegroundColor Green
