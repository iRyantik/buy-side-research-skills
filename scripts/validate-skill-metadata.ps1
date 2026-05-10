param(
    [int]$ExpectedActiveSkillCount = 15
)

$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$skillsRoot = Join-Path $repoRoot "skills"
$expectedSystemGeneration = "3.3.0"
$expectedMetadataSchemaVersion = "1"
$semverPattern = "^\d+\.\d+\.\d+$"

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

function Get-SkillFrontmatterName {
    param([string]$Text)

    $frontmatter = [regex]::Match($Text, "(?s)^---\s*(.*?)\s*---")
    if (-not $frontmatter.Success) {
        return $null
    }

    $name = [regex]::Match($frontmatter.Groups[1].Value, "(?m)^name:\s*['""]?([^'""\r\n]+)['""]?\s*$")
    if ($name.Success) {
        return $name.Groups[1].Value.Trim()
    }
    return $null
}

$activeSkillDirs = Get-ChildItem -LiteralPath $skillsRoot -Directory |
    Where-Object { Test-Path -LiteralPath (Join-Path $_.FullName "SKILL.md") } |
    Sort-Object Name

if ($activeSkillDirs.Count -ne $ExpectedActiveSkillCount) {
    $failures.Add("Expected $ExpectedActiveSkillCount active skills with SKILL.md, found $($activeSkillDirs.Count): $($activeSkillDirs.Name -join ', ')")
}

foreach ($dir in $activeSkillDirs) {
    $skillName = $dir.Name
    $skillPath = Join-Path $dir.FullName "SKILL.md"
    $yamlPath = Join-Path $dir.FullName "skill.yaml"
    $metaPath = Join-Path $dir.FullName "meta.json"

    if (Test-Path -LiteralPath $metaPath) {
        $failures.Add("${skillName}: meta.json is retired; move metadata into skill.yaml")
    }

    if (-not (Test-Path -LiteralPath $yamlPath)) {
        $failures.Add("${skillName}: missing canonical skill.yaml")
        continue
    }

    $skillText = Get-Content -Raw -Encoding UTF8 -LiteralPath $skillPath
    $yamlText = Get-Content -Raw -Encoding UTF8 -LiteralPath $yamlPath

    $frontmatterName = Get-SkillFrontmatterName $skillText
    $yamlName = Get-YamlScalar $yamlText "name"
    $yamlVersion = Get-YamlScalar $yamlText "version"
    $systemGeneration = Get-YamlScalar $yamlText "system_generation"
    $metadataSchemaVersion = Get-YamlScalar $yamlText "metadata_schema_version"

    if ($frontmatterName -ne $skillName) {
        $failures.Add("${skillName}: SKILL.md frontmatter name '$frontmatterName' does not match directory name")
    }

    if ($yamlName -ne $skillName) {
        $failures.Add("${skillName}: skill.yaml name '$yamlName' does not match directory name")
    }

    if ($yamlName -ne $frontmatterName) {
        $failures.Add("${skillName}: skill.yaml name '$yamlName' does not match SKILL.md frontmatter name '$frontmatterName'")
    }

    if ([string]::IsNullOrWhiteSpace($yamlVersion) -or $yamlVersion -notmatch $semverPattern) {
        $failures.Add("${skillName}: skill.yaml version '$yamlVersion' is not valid semver")
    }

    if ([string]::IsNullOrWhiteSpace($systemGeneration)) {
        $failures.Add("${skillName}: missing system_generation")
    } elseif ($systemGeneration -ne $expectedSystemGeneration) {
        $failures.Add("${skillName}: system_generation '$systemGeneration' does not match expected '$expectedSystemGeneration'")
    }

    if ([string]::IsNullOrWhiteSpace($metadataSchemaVersion)) {
        $failures.Add("${skillName}: missing metadata_schema_version")
    } elseif ($metadataSchemaVersion -ne $expectedMetadataSchemaVersion) {
        $failures.Add("${skillName}: metadata_schema_version '$metadataSchemaVersion' does not match expected '$expectedMetadataSchemaVersion'")
    }

    if ($yamlVersion -eq $systemGeneration) {
        $failures.Add("${skillName}: version must be skill semver, not system_generation")
    }

    foreach ($requiredField in @("id", "display_name", "author", "namespace", "category", "summary", "description", "trigger", "capabilities")) {
        if ($yamlText -notmatch "(?m)^$([regex]::Escape($requiredField)):") {
            $failures.Add("${skillName}: missing required metadata field '$requiredField'")
        }
    }
}

if ($failures.Count -gt 0) {
    Write-Host "Skill metadata validation failed:" -ForegroundColor Red
    foreach ($failure in $failures) {
        Write-Host " - $failure" -ForegroundColor Red
    }
    exit 1
}

Write-Host "Skill metadata validation passed for $($activeSkillDirs.Count) active skills." -ForegroundColor Green
