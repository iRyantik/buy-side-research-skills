param(
    [int]$ExpectedActiveSkillCount = 27
)

$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$skillsRoot = Join-Path $repoRoot "skills"
$sharedRulesPath = Join-Path $skillsRoot "_shared\global-rules.md"
$marker = "## Global Rules Capsule (v1)"
$needsVerification = "[" + [char]0x9700 + [char]0x67E5 + [char]0x8BC1 + "]"
$sourcePending = "[" + [char]0x6765 + [char]0x6E90 + [char]0x5F85 + [char]0x8865 + "]"
$linkPending = "[link " + [char]0x5F85 + [char]0x8865 + "]"
$noFabrication = [string]([char]0x7EDD) + [char]0x5BF9 + [char]0x4E0D + [char]0x80FD + [char]0x7F16 + [char]0x9020
$mainAgent = [string]([char]0x4E3B) + " agent"
$noFinalConclusion = [string]([char]0x4E0D) + [char]0x5F97 + [char]0x5199 + [char]0x6700 + [char]0x7EC8 + [char]0x7ED3 + [char]0x8BBA
$requiredPhrases = @(
    $needsVerification,
    $sourcePending,
    $linkPending,
    "Senior Analyst Radar",
    "mechanism-map",
    "driver-map",
    $noFabrication,
    "Sub-Agent Evidence Protocol",
    "evidence card",
    $mainAgent,
    $noFinalConclusion
)
$forbiddenSharedTerms = @(
    "coverage/",
    "pairs/",
    "portfolio/",
    "health_status",
    "decision-journal",
    "thesis-tracker"
)

$importedModelingSkills = @(
    "3-statement-model",
    "dcf-model",
    "comps-analysis",
    "model-update"
)

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

if (-not (Test-Path -LiteralPath $sharedRulesPath)) {
    $failures.Add("Missing shared runtime rules file: $sharedRulesPath")
} else {
    $sharedText = Get-Content -Raw -Encoding UTF8 -LiteralPath $sharedRulesPath
    foreach ($term in $forbiddenSharedTerms) {
        if ($sharedText.Contains($term)) {
            $failures.Add("Shared runtime rules contain non-runtime migration term: $term")
        }
    }
}

$activeSkillDirs = Get-ChildItem -LiteralPath $skillsRoot -Directory |
    Where-Object { Test-Path -LiteralPath (Join-Path $_.FullName "SKILL.md") } |
    Sort-Object Name

if ($activeSkillDirs.Count -ne $ExpectedActiveSkillCount) {
    $failures.Add("Expected $ExpectedActiveSkillCount active skills with SKILL.md, found $($activeSkillDirs.Count): $($activeSkillDirs.Name -join ', ')")
}

$researchSkillCount = 0
foreach ($dir in $activeSkillDirs) {
    $skillPath = Join-Path $dir.FullName "SKILL.md"
    $yamlPath = Join-Path $dir.FullName "skill.yaml"

    if (-not (Test-Path -LiteralPath $yamlPath)) {
        $failures.Add("$($dir.Name): missing skill.yaml; cannot decide whether Global Rules Capsule is required")
        continue
    }

    $yamlText = Get-Content -Raw -Encoding UTF8 -LiteralPath $yamlPath
    $category = Get-YamlScalar $yamlText "category"
    $text = Get-Content -Raw -Encoding UTF8 -LiteralPath $skillPath
    $markerCount = ([regex]::Matches($text, [regex]::Escape($marker))).Count

    if ($category -eq "research") {
        $researchSkillCount += 1
        if ($importedModelingSkills -contains $dir.Name) {
            if ($text -notmatch "(?m)^##\s*Research Workspace Adapter") {
                $failures.Add("$($dir.Name): imported modeling skill must include Research Workspace Adapter")
            }
            continue
        }
        if ($markerCount -ne 1) {
            $failures.Add("$($dir.Name): research skill expected exactly one '$marker', found $markerCount")
            continue
        }

        foreach ($phrase in $requiredPhrases) {
            if (-not $text.Contains($phrase)) {
                $failures.Add("$($dir.Name): capsule is missing required phrase '$phrase'")
            }
        }
    } elseif ($category -eq "operations") {
        if ($markerCount -gt 1) {
            $failures.Add("$($dir.Name): operations skill has duplicate '$marker' sections")
        }
    } else {
        $failures.Add("$($dir.Name): unknown category '$category'; expected research or operations")
    }
}

$sharedSkillPath = Join-Path $skillsRoot "_shared\SKILL.md"
if (Test-Path -LiteralPath $sharedSkillPath) {
    $failures.Add("_shared must not contain SKILL.md; it should not be an active skill")
}

if ($failures.Count -gt 0) {
    Write-Host "Global rules validation failed:" -ForegroundColor Red
    foreach ($failure in $failures) {
        Write-Host " - $failure" -ForegroundColor Red
    }
    exit 1
}

Write-Host "Global rules validation passed for $researchSkillCount research skills across $($activeSkillDirs.Count) active skills." -ForegroundColor Green
