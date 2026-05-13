param(
    [Parameter(Mandatory = $true)]
    [string]$Version
)

$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$packageName = "buy-side-research-skills-$Version"
$distRoot = Join-Path $repoRoot "dist"
$stageRoot = Join-Path $distRoot $packageName
$zipPath = Join-Path $distRoot "$packageName.zip"

$includeItems = @(
    ".claude-plugin",
    ".codex-plugin",
    "skills",
    "README.md"
)

if (Test-Path -LiteralPath $stageRoot) {
    Remove-Item -LiteralPath $stageRoot -Recurse -Force
}

if (Test-Path -LiteralPath $zipPath) {
    Remove-Item -LiteralPath $zipPath -Force
}

New-Item -ItemType Directory -Force -Path $stageRoot | Out-Null

foreach ($item in $includeItems) {
    $source = Join-Path $repoRoot $item
    if (-not (Test-Path -LiteralPath $source)) {
        throw "Release include item does not exist: $item"
    }

    $destination = Join-Path $stageRoot $item
    $destinationParent = Split-Path -Parent $destination
    if (-not (Test-Path -LiteralPath $destinationParent)) {
        New-Item -ItemType Directory -Force -Path $destinationParent | Out-Null
    }

    Copy-Item -LiteralPath $source -Destination $destination -Recurse -Force
}

$topLevelItems = @(Get-ChildItem -LiteralPath $stageRoot -Force | ForEach-Object { $_.FullName })
if ($topLevelItems.Count -eq 0) {
    throw "Release staging directory is empty: $stageRoot"
}

Compress-Archive -LiteralPath $topLevelItems -DestinationPath $zipPath -Force
Remove-Item -LiteralPath $stageRoot -Recurse -Force

Write-Host "Release package written to $zipPath" -ForegroundColor Green
