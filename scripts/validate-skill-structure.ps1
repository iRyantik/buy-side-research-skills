param(
    [int]$ExpectedActiveSkillCount = 28
)

$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$skillsRoot = Join-Path $repoRoot "skills"

$failures = New-Object System.Collections.Generic.List[string]

function New-UnicodeText {
    param([int[]]$CodePoints)

    return -join ($CodePoints | ForEach-Object { [char]$_ })
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

$mindset = New-UnicodeText @(0x5FC3, 0x6CD5)
$sourcePolicy = "Source " + (New-UnicodeText @(0x653F, 0x7B56))
$workflowLinkage = "Workflow " + (New-UnicodeText @(0x8054, 0x52A8))
$antiPattern = New-UnicodeText @(0x53CD, 0x6A21, 0x5F0F, 0x81EA, 0x67E5)
$lengthBenchmark = New-UnicodeText @(0x7BC7, 0x5E45, 0x57FA, 0x51C6)
$outputLengthBenchmark = (New-UnicodeText @(0x8F93, 0x51FA)) + $lengthBenchmark

$responsibilityBoundary = New-UnicodeText @(0x804C, 0x8D23, 0x8FB9, 0x754C)
$triggerAndInput = New-UnicodeText @(0x89E6, 0x53D1, 0x4E0E, 0x8F93, 0x5165)
$executionModes = New-UnicodeText @(0x6267, 0x884C, 0x6A21, 0x5F0F)
$toolResources = New-UnicodeText @(0x5DE5, 0x5177, 0x8D44, 0x6E90)
$fileSafety = New-UnicodeText @(0x6587, 0x4EF6, 0x5B89, 0x5168)
$runtimeContract = New-UnicodeText @(0x8FD0, 0x884C, 0x8F93, 0x51FA, 0x5951, 0x7EA6)
$failureHandling = New-UnicodeText @(0x5931, 0x8D25, 0x5904, 0x7406)
$safetyCheck = New-UnicodeText @(0x5B89, 0x5168, 0x81EA, 0x67E5)

$researchSections = @(
    @{ Label = "Mindset"; Pattern = "(?m)^##\s*" + [regex]::Escape($mindset) },
    @{ Label = "Source Policy"; Pattern = "(?m)^##\s*" + [regex]::Escape($sourcePolicy) },
    @{ Label = "Workflow Linkage"; Pattern = "(?m)^##\s*" + [regex]::Escape($workflowLinkage) },
    @{ Label = "Anti-pattern Self-check"; Pattern = "(?m)^##\s*" + [regex]::Escape($antiPattern) },
    @{ Label = "Length Benchmark"; Pattern = "(?m)^##\s*(" + [regex]::Escape($lengthBenchmark) + "|" + [regex]::Escape($outputLengthBenchmark) + ")" }
)

$operationsSections = @(
    @{ Label = "Mindset"; Pattern = "(?m)^##\s*" + [regex]::Escape($mindset) },
    @{ Label = "Responsibility Boundary"; Pattern = "(?m)^##\s*" + [regex]::Escape($responsibilityBoundary) },
    @{ Label = "Trigger and Input"; Pattern = "(?m)^##\s*" + [regex]::Escape($triggerAndInput) },
    @{ Label = "Execution Modes"; Pattern = "(?m)^##\s*" + [regex]::Escape($executionModes) },
    @{ Label = "Tool Resources"; Pattern = "(?m)^##\s*" + [regex]::Escape($toolResources) },
    @{ Label = "File Safety"; Pattern = "(?m)^##\s*" + [regex]::Escape($fileSafety) },
    @{ Label = "Runtime Output Contract"; Pattern = "(?m)^##\s*" + [regex]::Escape($runtimeContract) },
    @{ Label = "Failure Handling"; Pattern = "(?m)^##\s*" + [regex]::Escape($failureHandling) },
    @{ Label = "Workflow Linkage"; Pattern = "(?m)^##\s*" + [regex]::Escape($workflowLinkage) },
    @{ Label = "Safety Self-check"; Pattern = "(?m)^##\s*" + [regex]::Escape($safetyCheck) }
)

$importedModelingSkills = @(
    "3-statement-model",
    "dcf-model",
    "comps-analysis",
    "model-update"
)

$activeSkillDirs = Get-ChildItem -LiteralPath $skillsRoot -Directory |
    Where-Object { Test-Path -LiteralPath (Join-Path $_.FullName "SKILL.md") } |
    Sort-Object Name

if ($activeSkillDirs.Count -ne $ExpectedActiveSkillCount) {
    $failures.Add("Expected $ExpectedActiveSkillCount active skills with SKILL.md, found $($activeSkillDirs.Count): $($activeSkillDirs.Name -join ', ')")
}

foreach ($dir in $activeSkillDirs) {
    $skillPath = Join-Path $dir.FullName "SKILL.md"
    $yamlPath = Join-Path $dir.FullName "skill.yaml"

    if (-not (Test-Path -LiteralPath $yamlPath)) {
        $failures.Add("$($dir.Name): missing skill.yaml; cannot decide structure contract")
        continue
    }

    $yamlText = Get-Content -Raw -Encoding UTF8 -LiteralPath $yamlPath
    $category = Get-YamlScalar $yamlText "category"
    $text = Get-Content -Raw -Encoding UTF8 -LiteralPath $skillPath
    $h1 = [regex]::Match($text, "(?m)^# ")

    if (-not $h1.Success) {
        $failures.Add("$($dir.Name): missing first H1 heading; cannot isolate body from capsule")
        continue
    }

    # Only inspect content from the first H1 onward so the shared capsule cannot satisfy structure checks.
    $body = $text.Substring($h1.Index)

    if ($importedModelingSkills -contains $dir.Name) {
        if ($text -notmatch "(?m)^##\s*Research Workspace Adapter") {
            $failures.Add("$($dir.Name): imported modeling skill must include a short Research Workspace Adapter section")
        }
        foreach ($requiredInput in @(
            "_cache/financial-data/financial-data-summary.md",
            "_cache/financial-data/internal/actuals-resolved.json",
            "_cache/financial-data/internal/evidence-pack.json",
            "_cache/driver-map/driver-map.md",
            "_cache/driver-map/internal/driver-map.json"
        )) {
            if (-not $text.Contains($requiredInput)) {
                $failures.Add("$($dir.Name): Research Workspace Adapter missing preferred input '$requiredInput'")
            }
        }
        continue
    }

    $requiredSections = $null
    if ($category -eq "research") {
        $requiredSections = $researchSections
    } elseif ($category -eq "operations") {
        $requiredSections = $operationsSections
    } else {
        $failures.Add("$($dir.Name): unknown category '$category'; expected research or operations")
        continue
    }

    foreach ($section in $requiredSections) {
        if ($body -notmatch $section.Pattern) {
            $failures.Add("$($dir.Name): $category body is missing required section '$($section.Label)'")
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
