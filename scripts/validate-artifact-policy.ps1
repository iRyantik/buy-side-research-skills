param(
    [int]$ExpectedActiveSkillCount = 23
)

$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$skillsRoot = Join-Path $repoRoot "skills"
$failures = New-Object System.Collections.Generic.List[string]

$allowedSavePolicies = @(
    "none",
    "optional_topic_session",
    "default_topic_session",
    "earned_memory",
    "external_workbook",
    "workspace_scaffold",
    "cache_artifact",
    "topic_session_scaffold"
)

$expectedPolicies = @{
    "alpha-thesis" = @{
        save_policy = "optional_topic_session"
        default_artifact = "alpha-thesis.md"
        canonical_location = "topics/[topic-slug]/[YYYY-MM-DD]-[session-slug]/alpha-thesis.md"
    }
    "bear-pre-mortem" = @{
        save_policy = "optional_topic_session"
        default_artifact = "bear-pre-mortem.md"
        canonical_location = "topics/[topic-slug]/[YYYY-MM-DD]-[session-slug]/bear-pre-mortem.md"
    }
    "candidate-screener" = @{
        save_policy = "default_topic_session"
        default_artifact = "candidate-screener.md"
        canonical_location = "topics/[topic-slug]/[YYYY-MM-DD]-[session-slug]/candidate-screener.md"
    }
    "cross-market-compare" = @{
        save_policy = "optional_topic_session"
        default_artifact = "cross-market-compare.md"
        canonical_location = "topics/[topic-slug]/[YYYY-MM-DD]-[session-slug]/cross-market-compare.md"
    }
    "company-primer" = @{
        save_policy = "optional_topic_session"
        default_artifact = "company-primer.md"
        canonical_location = "topics/[topic-slug]/[YYYY-MM-DD]-[session-slug]/company-primer.md"
    }
    "consensus-map" = @{
        save_policy = "optional_topic_session"
        default_artifact = "consensus-map.md"
        canonical_location = "topics/[topic-slug]/[YYYY-MM-DD]-[session-slug]/consensus-map.md"
    }
    "driver-map" = @{
        save_policy = "optional_topic_session"
        default_artifact = "driver-map.md"
        canonical_location = "topics/[topic-slug]/[YYYY-MM-DD]-[session-slug]/driver-map.md"
    }
    "earnings-setup" = @{
        save_policy = "optional_topic_session"
        default_artifact = "earnings-setup.md"
        canonical_location = "topics/[topic-slug]/[YYYY-MM-DD]-[session-slug]/earnings-setup.md"
    }
    "financial-model" = @{
        save_policy = "external_workbook"
        default_artifact = "model.xlsx"
        canonical_location = "user-provided workbook or topics/[topic]/_models/model.xlsx"
    }
    "information-impact" = @{
        save_policy = "none"
        default_artifact = "conversation-only"
        canonical_location = "conversation-only"
    }
    "init-workspace" = @{
        save_policy = "workspace_scaffold"
        default_artifact = "workspace scaffold"
        canonical_location = "user-provided research workspace"
    }
    "ingest" = @{
        save_policy = "cache_artifact"
        default_artifact = "[source-filename].md"
        canonical_location = "topics/[topic]/_cache/[source-filename].md"
    }
    "industry-quickread" = @{
        save_policy = "optional_topic_session"
        default_artifact = "industry-quickread.md"
        canonical_location = "topics/[topic-slug]/[YYYY-MM-DD]-[session-slug]/industry-quickread.md"
    }
    "integrate" = @{
        save_policy = "none"
        default_artifact = "conversation-only"
        canonical_location = "conversation-only"
    }
    "mechanism-map" = @{
        save_policy = "optional_topic_session"
        default_artifact = "mechanism-map.md"
        canonical_location = "topics/[topic-slug]/[YYYY-MM-DD]-[session-slug]/mechanism-map.md"
    }
    "meta-skill" = @{
        save_policy = "none"
        default_artifact = "conversation-only"
        canonical_location = "conversation-only"
    }
    "new-session" = @{
        save_policy = "topic_session_scaffold"
        default_artifact = "topic session folder + index.md"
        canonical_location = "topics/[topic-slug]/[YYYY-MM-DD]-[session-slug]/"
    }
    "next-step" = @{
        save_policy = "none"
        default_artifact = "conversation-only"
        canonical_location = "conversation-only"
    }
    "pair-trade" = @{
        save_policy = "default_topic_session"
        default_artifact = "pair-note.md"
        canonical_location = "topics/[topic-slug]/[YYYY-MM-DD]-[session-slug]/pair-note.md"
    }
    "peer-deep-dive" = @{
        save_policy = "optional_topic_session"
        default_artifact = "peer-deep-dive.md"
        canonical_location = "topics/[topic-slug]/[YYYY-MM-DD]-[session-slug]/peer-deep-dive.md"
    }
    "primary-research-plan" = @{
        save_policy = "optional_topic_session"
        default_artifact = "primary-research-plan.md"
        canonical_location = "topics/[topic-slug]/[YYYY-MM-DD]-[session-slug]/primary-research-plan.md"
    }
    "research-journal" = @{
        save_policy = "earned_memory"
        default_artifact = "research-journal.md | boss-brief.md | index.md"
        canonical_location = "topics/[topic-slug]/[YYYY-MM-DD]-[session-slug]/research-journal.md or boss-brief.md; topic index at topics/[topic-slug]/index.md"
    }
    "stock-quickread" = @{
        save_policy = "optional_topic_session"
        default_artifact = "stock-quickread.md"
        canonical_location = "topics/[topic-slug]/[YYYY-MM-DD]-[session-slug]/stock-quickread.md"
    }
}

function Get-ArtifactPolicyBlock {
    param([string]$Text)

    $match = [regex]::Match($Text, "(?ms)^artifact_policy:\s*\r?\n(?<block>(?:  [^\r\n]*(?:\r?\n|$))+)")
    if ($match.Success) {
        return $match.Groups["block"].Value
    }
    return $null
}

function Get-YamlScalarFromBlock {
    param(
        [string]$Block,
        [string]$Key
    )

    if ([string]::IsNullOrWhiteSpace($Block)) {
        return $null
    }

    $match = [regex]::Match($Block, "(?m)^\s+$([regex]::Escape($Key)):\s*['""]?([^'""\r\n]+)['""]?\s*$")
    if ($match.Success) {
        return $match.Groups[1].Value.Trim()
    }
    return $null
}

$activeSkillDirs = Get-ChildItem -LiteralPath $skillsRoot -Directory |
    Where-Object { Test-Path -LiteralPath (Join-Path $_.FullName "SKILL.md") } |
    Sort-Object Name

if ($activeSkillDirs.Count -ne $ExpectedActiveSkillCount) {
    $failures.Add("Expected $ExpectedActiveSkillCount active skills with SKILL.md, found $($activeSkillDirs.Count): $($activeSkillDirs.Name -join ', ')")
}

$legacyRootPatterns = @(
    "screens/[",
    "peers/[",
    "quickreads/[",
    "cross-market/["
)

foreach ($dir in $activeSkillDirs) {
    $skillName = $dir.Name
    $skillPath = Join-Path $dir.FullName "SKILL.md"
    $yamlPath = Join-Path $dir.FullName "skill.yaml"

    if (-not (Test-Path -LiteralPath $yamlPath)) {
        $failures.Add("${skillName}: missing skill.yaml")
        continue
    }

    if (-not $expectedPolicies.ContainsKey($skillName)) {
        $failures.Add("${skillName}: missing expected artifact policy entry in validator")
        continue
    }

    $yamlText = Get-Content -Raw -Encoding UTF8 -LiteralPath $yamlPath
    $skillText = Get-Content -Raw -Encoding UTF8 -LiteralPath $skillPath

    foreach ($pattern in $legacyRootPatterns) {
        if ($yamlText.Contains($pattern)) {
            $failures.Add("${skillName}: skill.yaml references legacy root artifact path '$pattern'")
        }
        if ($skillText.Contains($pattern)) {
            $failures.Add("${skillName}: SKILL.md references legacy root artifact path '$pattern'")
        }
    }

    $policyBlock = Get-ArtifactPolicyBlock $yamlText
    if ([string]::IsNullOrWhiteSpace($policyBlock)) {
        $failures.Add("${skillName}: missing artifact_policy block")
        continue
    }

    $savePolicy = Get-YamlScalarFromBlock $policyBlock "save_policy"
    $defaultArtifact = Get-YamlScalarFromBlock $policyBlock "default_artifact"
    $canonicalLocation = Get-YamlScalarFromBlock $policyBlock "canonical_location"
    $saveTrigger = Get-YamlScalarFromBlock $policyBlock "save_trigger"
    $expected = $expectedPolicies[$skillName]

    if ($allowedSavePolicies -notcontains $savePolicy) {
        $failures.Add("${skillName}: save_policy '$savePolicy' is not allowed")
    }

    foreach ($field in @("save_policy", "default_artifact", "canonical_location")) {
        $actual = switch ($field) {
            "save_policy" { $savePolicy }
            "default_artifact" { $defaultArtifact }
            "canonical_location" { $canonicalLocation }
        }
        if ($actual -ne $expected[$field]) {
            $failures.Add("${skillName}: artifact_policy.$field '$actual' does not match expected '$($expected[$field])'")
        }
    }

    if ([string]::IsNullOrWhiteSpace($saveTrigger)) {
        $failures.Add("${skillName}: artifact_policy.save_trigger is required")
    }
}

if ($failures.Count -gt 0) {
    Write-Host "Artifact policy validation failed:" -ForegroundColor Red
    foreach ($failure in $failures) {
        Write-Host " - $failure" -ForegroundColor Red
    }
    exit 1
}

Write-Host "Artifact policy validation passed for $($activeSkillDirs.Count) active skills." -ForegroundColor Green
