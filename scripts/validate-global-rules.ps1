param(
    [int]$ExpectedActiveSkillCount = 14
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
$requiredPhrases = @(
    $needsVerification,
    $sourcePending,
    $linkPending,
    "Senior Analyst Radar",
    "mechanism-map",
    "driver-map",
    $noFabrication
)
$forbiddenSharedTerms = @(
    "coverage/",
    "pairs/",
    "portfolio/",
    "health_status",
    "decision-journal",
    "thesis-tracker"
)

$failures = New-Object System.Collections.Generic.List[string]

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

foreach ($dir in $activeSkillDirs) {
    $skillPath = Join-Path $dir.FullName "SKILL.md"
    $text = Get-Content -Raw -Encoding UTF8 -LiteralPath $skillPath
    $markerCount = ([regex]::Matches($text, [regex]::Escape($marker))).Count

    if ($markerCount -ne 1) {
        $failures.Add("$($dir.Name): expected exactly one '$marker', found $markerCount")
        continue
    }

    foreach ($phrase in $requiredPhrases) {
        if (-not $text.Contains($phrase)) {
            $failures.Add("$($dir.Name): capsule is missing required phrase '$phrase'")
        }
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

Write-Host "Global rules validation passed for $($activeSkillDirs.Count) active skills." -ForegroundColor Green
