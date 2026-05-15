param()

$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$skillsRoot = Join-Path $repoRoot "skills"
$runtimeCap = "Runtime cap: no per-skill sub-agent count limit; max 6-8 active sub-agents globally; parallel within one skill but serial across skills; close sub-agents immediately after evidence cards or QA notes return."

$modelingSkills = @(
    "3-statement-model",
    "dcf-model",
    "comps-analysis",
    "model-update"
)

$skillRequiredPhrases = @(
    "## Model Sub-Agent Protocol",
    "model QA notes",
    "work-packet findings",
    "main agent owns the final workbook",
    $runtimeCap,
    "actuals-resolved.json",
    "evidence-pack.json",
    "source-map",
    "completeness",
    "missing or unmapped actuals",
    "zero"
)

$yamlRequiredPhrases = @(
    "model_sub_agent_protocol",
    "main_agent_workbook_ownership_required",
    "source_map_and_completeness_check_required",
    "no_final_valuation_or_workbook_delivery_by_sub-agent",
    "no_missing_or_unmapped_actuals_as_zero"
)

$governancePaths = @(
    (Join-Path $repoRoot "CLAUDE.md"),
    (Join-Path $repoRoot "README.md"),
    (Join-Path $repoRoot "docs\architecture.md"),
    (Join-Path $skillsRoot "_shared\global-rules.md"),
    (Join-Path $skillsRoot "init-workspace\assets\CLAUDE.md.template")
)

$governanceRequiredPhrases = @(
    "Model Sub-Agent Protocol",
    "model QA notes",
    $runtimeCap,
    "actuals-resolved.json",
    "evidence-pack.json",
    "source-map",
    "completeness",
    "missing or unmapped actuals"
)

$failures = New-Object System.Collections.Generic.List[string]

foreach ($path in $governancePaths) {
    if (-not (Test-Path -LiteralPath $path)) {
        $failures.Add("Missing governance file: $path")
        continue
    }
    $text = Get-Content -Raw -Encoding UTF8 -LiteralPath $path
    foreach ($phrase in $governanceRequiredPhrases) {
        if (-not $text.Contains($phrase)) {
            $failures.Add("${path}: missing model sub-agent governance phrase: $phrase")
        }
    }
}

foreach ($skillName in $modelingSkills) {
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
            $failures.Add("${skillName}: SKILL.md missing model sub-agent phrase: $phrase")
        }
    }

    foreach ($phrase in $yamlRequiredPhrases) {
        if (-not $yamlText.Contains($phrase)) {
            $failures.Add("${skillName}: skill.yaml missing model sub-agent phrase: $phrase")
        }
    }

    if ($skillText.Contains("evidence_cards_only") -or $yamlText.Contains("evidence_cards_only")) {
        $failures.Add("${skillName}: modeling skill must not use research evidence_cards_only gate")
    }
}

if ($failures.Count -gt 0) {
    Write-Host "Model sub-agent protocol validation failed:" -ForegroundColor Red
    foreach ($failure in $failures) {
        Write-Host " - $failure" -ForegroundColor Red
    }
    exit 1
}

Write-Host "Model sub-agent protocol validation passed for $($modelingSkills.Count) modeling skills." -ForegroundColor Green
