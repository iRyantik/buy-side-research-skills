param(
    [Parameter(Mandatory = $true)]
    [string]$WorkspacePath
)

$ErrorActionPreference = "Stop"

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$skillRoot = Resolve-Path (Join-Path $scriptRoot "..")
$assetsRoot = Join-Path $skillRoot "assets"

function Convert-ToFullPath {
    param([string]$Path)

    if ([System.IO.Path]::IsPathRooted($Path)) {
        return [System.IO.Path]::GetFullPath($Path)
    }

    return [System.IO.Path]::GetFullPath((Join-Path (Get-Location) $Path))
}

function Add-Result {
    param(
        [System.Collections.Generic.List[string]]$List,
        [string]$Value
    )

    [void]$List.Add($Value)
}

$fullWorkspacePath = Convert-ToFullPath $WorkspacePath
$created = New-Object System.Collections.Generic.List[string]
$skipped = New-Object System.Collections.Generic.List[string]

if (Test-Path -LiteralPath $fullWorkspacePath) {
    $existingMarkers = @(
        ".claude-plugin\plugin.json",
        ".codex-plugin\plugin.json",
        "skills",
        "META-SKILL.md"
    )

    $pluginMarkerHits = @()
    foreach ($marker in $existingMarkers) {
        if (Test-Path -LiteralPath (Join-Path $fullWorkspacePath $marker)) {
            $pluginMarkerHits += $marker
        }
    }

    if ($pluginMarkerHits.Count -ge 2) {
        throw "Refusing to initialize research workspace inside a plugin repo or plugin install directory: $fullWorkspacePath"
    }
}

$directories = @(
    "_inbox",
    "_raw",
    "_raw\filings",
    "_raw\transcripts",
    "_raw\sellside",
    "_raw\industry",
    "_raw\irdecks",
    "_raw\datasets",
    "_cache",
    "_models",
    "_scripts",
    "topics",
    "topics\_meta",
    "topics\company",
    "topics\theme",
    "topics\event"
)

foreach ($relativeDir in $directories) {
    $target = Join-Path $fullWorkspacePath $relativeDir
    if (Test-Path -LiteralPath $target) {
        Add-Result $skipped $relativeDir
    } else {
        New-Item -ItemType Directory -Path $target -Force | Out-Null
        Add-Result $created $relativeDir
    }
}

function Write-TemplateIfMissing {
    param(
        [string]$TemplatePath,
        [string]$TargetPath,
        [string]$RelativeName
    )

    if (Test-Path -LiteralPath $TargetPath) {
        Add-Result $script:skipped $RelativeName
        return
    }

    $text = Get-Content -Raw -Encoding UTF8 -LiteralPath $TemplatePath
    $text = $text.Replace("{{WORKSPACE_PATH}}", $fullWorkspacePath)
    $text = $text.Replace("{{DATE}}", (Get-Date -Format "yyyy-MM-dd"))
    Set-Content -LiteralPath $TargetPath -Value $text -Encoding UTF8
    Add-Result $script:created $RelativeName
}

Write-TemplateIfMissing `
    -TemplatePath (Join-Path $assetsRoot "CLAUDE.md.template") `
    -TargetPath (Join-Path $fullWorkspacePath "CLAUDE.md") `
    -RelativeName "CLAUDE.md"

Write-TemplateIfMissing `
    -TemplatePath (Join-Path $assetsRoot "gitignore.template") `
    -TargetPath (Join-Path $fullWorkspacePath ".gitignore") `
    -RelativeName ".gitignore"

Write-TemplateIfMissing `
    -TemplatePath (Join-Path $assetsRoot "edge-radar.md") `
    -TargetPath (Join-Path $fullWorkspacePath "topics\_meta\edge-radar.md") `
    -RelativeName "topics/_meta/edge-radar.md"

$copiedScriptTarget = Join-Path $fullWorkspacePath "_scripts\init-research-workspace.ps1"
if (Test-Path -LiteralPath $copiedScriptTarget) {
    Add-Result $skipped "_scripts/init-research-workspace.ps1"
} else {
    Copy-Item -LiteralPath $MyInvocation.MyCommand.Path -Destination $copiedScriptTarget
    Add-Result $created "_scripts/init-research-workspace.ps1"
}

$result = [ordered]@{
    workspace_path = $fullWorkspacePath
    created = @($created)
    skipped = @($skipped)
    note = "No git init and no ingest were performed."
}

$result | ConvertTo-Json -Depth 4
