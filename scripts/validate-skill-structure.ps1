param(
    [int]$ExpectedActiveSkillCount = 17
)

$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$skillsRoot = Join-Path $repoRoot "skills"

$failures = New-Object System.Collections.Generic.List[string]

function New-UnicodeText {
    param([int[]]$CodePoints)

    return -join ($CodePoints | ForEach-Object { [char]$_ })
}

$mindset = New-UnicodeText @(0x5FC3, 0x6CD5)
$sourcePolicy = "Source " + (New-UnicodeText @(0x653F, 0x7B56))
$workflowLinkage = "Workflow " + (New-UnicodeText @(0x8054, 0x52A8))
$antiPattern = New-UnicodeText @(0x53CD, 0x6A21, 0x5F0F, 0x81EA, 0x67E5)
$lengthBenchmark = New-UnicodeText @(0x7BC7, 0x5E45, 0x57FA, 0x51C6)
$outputLengthBenchmark = (New-UnicodeText @(0x8F93, 0x51FA)) + $lengthBenchmark

$requiredSections = @(
    @{ Label = "Mindset"; Pattern = "(?m)^##\s*" + [regex]::Escape($mindset) },
    @{ Label = "Source Policy"; Pattern = "(?m)^##\s*" + [regex]::Escape($sourcePolicy) },
    @{ Label = "Workflow Linkage"; Pattern = "(?m)^##\s*" + [regex]::Escape($workflowLinkage) },
    @{ Label = "Anti-pattern Self-check"; Pattern = "(?m)^##\s*" + [regex]::Escape($antiPattern) },
    @{ Label = "Length Benchmark"; Pattern = "(?m)^##\s*(" + [regex]::Escape($lengthBenchmark) + "|" + [regex]::Escape($outputLengthBenchmark) + ")" }
)

$activeSkillDirs = Get-ChildItem -LiteralPath $skillsRoot -Directory |
    Where-Object { Test-Path -LiteralPath (Join-Path $_.FullName "SKILL.md") } |
    Sort-Object Name

if ($activeSkillDirs.Count -ne $ExpectedActiveSkillCount) {
    $failures.Add("Expected $ExpectedActiveSkillCount active skills with SKILL.md, found $($activeSkillDirs.Count): $($activeSkillDirs.Name -join ', ')")
}

foreach ($dir in $activeSkillDirs) {
    $skillPath = Join-Path $dir.FullName "SKILL.md"
    $text = Get-Content -Raw -Encoding UTF8 -LiteralPath $skillPath
    $h1 = [regex]::Match($text, "(?m)^# ")

    if (-not $h1.Success) {
        $failures.Add("$($dir.Name): missing first H1 heading; cannot isolate body from capsule")
        continue
    }

    # Only inspect content from the first H1 onward so the shared capsule cannot satisfy structure checks.
    $body = $text.Substring($h1.Index)

    foreach ($section in $requiredSections) {
        if ($body -notmatch $section.Pattern) {
            $failures.Add("$($dir.Name): body is missing required section '$($section.Label)'")
        }
    }
}

if ($failures.Count -gt 0) {
    Write-Host "Skill structure validation failed:" -ForegroundColor Red
    foreach ($failure in $failures) {
        Write-Host " - $failure" -ForegroundColor Red
    }
    exit 1
}

Write-Host "Skill structure validation passed for $($activeSkillDirs.Count) active skills." -ForegroundColor Green
