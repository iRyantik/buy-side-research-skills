param(
    [Parameter(Mandatory = $true)]
    [string]$WorkspacePath
)

$ErrorActionPreference = "Stop"

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$skillRoot = Resolve-Path (Join-Path $scriptRoot "..")
$skillsRoot = Split-Path -Parent $skillRoot
$pluginAssetsRoot = Join-Path $skillRoot "assets"
$localAssetsRoot = Join-Path $scriptRoot "init-assets"
$assetsRoot = if (Test-Path -LiteralPath $pluginAssetsRoot) { $pluginAssetsRoot } else { $localAssetsRoot }
$ingestScriptsRoot = Join-Path $skillsRoot "ingest/scripts"
$ingestAssetsRoot = Join-Path $skillsRoot "ingest/assets"
$financialDataScriptsRoot = Join-Path $skillsRoot "financial-data/scripts"
$financialDataAssetsRoot = Join-Path $skillsRoot "financial-data/assets"
if (-not (Test-Path -LiteralPath $ingestScriptsRoot)) {
    $ingestScriptsRoot = $scriptRoot
}
if (-not (Test-Path -LiteralPath $ingestAssetsRoot)) {
    $ingestAssetsRoot = $scriptRoot
}
if (-not (Test-Path -LiteralPath $financialDataScriptsRoot)) {
    $financialDataScriptsRoot = Join-Path $scriptRoot "financial-data"
}
if (-not (Test-Path -LiteralPath $financialDataAssetsRoot)) {
    $financialDataAssetsRoot = Join-Path $scriptRoot "financial-data"
}

function Convert-ToFullPath {
    param([string]$Path)

    if ([System.IO.Path]::IsPathRooted($Path)) {
        return [System.IO.Path]::GetFullPath($Path)
    }

    return [System.IO.Path]::GetFullPath((Join-Path (Get-Location) $Path))
}

function Get-RelativePath {
    param(
        [string]$BasePath,
        [string]$TargetPath
    )

    $separator = [System.IO.Path]::DirectorySeparatorChar
    $baseUri = [System.Uri]((Resolve-Path -LiteralPath $BasePath).Path.TrimEnd($separator) + $separator)
    $targetUri = [System.Uri](Resolve-Path -LiteralPath $TargetPath).Path
    $relative = $baseUri.MakeRelativeUri($targetUri).ToString()
    return [System.Uri]::UnescapeDataString($relative).Replace('/', $separator)
}

function Add-Result {
    param(
        [System.Collections.Generic.List[string]]$List,
        [string]$Value
    )

    [void]$List.Add($Value)
}

function Test-IsWindowsHost {
    return [System.IO.Path]::DirectorySeparatorChar -eq '\'
}

function Convert-ToPosixPath {
    param([string]$Path)

    return $Path -replace '\\', '/'
}

function Convert-ToPlatformRelativePath {
    param([string]$Path)

    if (Test-IsWindowsHost) {
        return $Path -replace '/', '\'
    }

    return $Path -replace '\\', '/'
}

function Get-HookLauncherCommand {
    param(
        [string]$WorkspaceRoot,
        [string]$RelativeHookPath
    )

    $hookPath = Join-Path $WorkspaceRoot (Convert-ToPlatformRelativePath $RelativeHookPath)
    if (Test-IsWindowsHost) {
        $runner = Join-Path $WorkspaceRoot ".claude/hooks/run-hook.cmd"
        return ('"{0}" "{1}"' -f $runner, $hookPath)
    }

    $runner = Convert-ToPosixPath (Join-Path $WorkspaceRoot ".claude/hooks/run-hook.sh")
    $hookPath = Convert-ToPosixPath $hookPath
    return ('sh "{0}" "{1}"' -f $runner, $hookPath)
}

function Convert-FromJsonCompat {
    param([string]$RawJson)

    $convertCommand = Get-Command ConvertFrom-Json -ErrorAction Stop
    if ($convertCommand.Parameters.ContainsKey("Depth")) {
        return $RawJson | ConvertFrom-Json -Depth 100
    }

    return $RawJson | ConvertFrom-Json
}

function Resolve-HookConfigNode {
    param(
        [object]$Node,
        [string]$WorkspaceRoot
    )

    if ($Node -is [string]) {
        if ($Node -match '^\{\{HOOK_RUNNER\}\}\s+([^\s"]+\.ps1)$') {
            return Get-HookLauncherCommand -WorkspaceRoot $WorkspaceRoot -RelativeHookPath $Matches[1]
        }
        return $Node
    }

    if ($Node -is [System.Collections.IList]) {
        foreach ($item in $Node) {
            [void](Resolve-HookConfigNode -Node $item -WorkspaceRoot $WorkspaceRoot)
        }
        return $Node
    }

    if ($Node -is [psobject]) {
        foreach ($property in $Node.PSObject.Properties) {
            $property.Value = Resolve-HookConfigNode -Node $property.Value -WorkspaceRoot $WorkspaceRoot
        }
        return $Node
    }

    return $Node
}

function Render-HookConfigText {
    param(
        [string]$SourcePath,
        [string]$WorkspaceRoot
    )

    $text = Get-Content -Raw -Encoding UTF8 -LiteralPath $SourcePath
    $jsonObject = Convert-FromJsonCompat -RawJson $text
    $rendered = Resolve-HookConfigNode -Node $jsonObject -WorkspaceRoot $WorkspaceRoot
    return ($rendered | ConvertTo-Json -Depth 100)
}

$fullWorkspacePath = Convert-ToFullPath $WorkspacePath
$created = New-Object System.Collections.Generic.List[string]
$updated = New-Object System.Collections.Generic.List[string]
$skipped = New-Object System.Collections.Generic.List[string]

if (Test-Path -LiteralPath $fullWorkspacePath) {
    $existingMarkers = @(
        ".claude-plugin/plugin.json",
        ".codex-plugin/plugin.json",
        "skills"
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
    "_scripts",
    "topics"
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
    -TemplatePath (Join-Path $assetsRoot "AGENTS.md.template") `
    -TargetPath (Join-Path $fullWorkspacePath "AGENTS.md") `
    -RelativeName "AGENTS.md"

Write-TemplateIfMissing `
    -TemplatePath (Join-Path $assetsRoot "gitignore.template") `
    -TargetPath (Join-Path $fullWorkspacePath ".gitignore") `
    -RelativeName ".gitignore"

Write-TemplateIfMissing `
    -TemplatePath (Join-Path $assetsRoot "edge-radar.md") `
    -TargetPath (Join-Path $fullWorkspacePath "edge-radar.md") `
    -RelativeName "edge-radar.md"

function Copy-ScriptIfMissing {
    param(
        [string]$SourcePath,
        [string]$RelativeTarget
    )

    $targetPath = Join-Path $fullWorkspacePath $RelativeTarget
    if (Test-Path -LiteralPath $targetPath) {
        Add-Result $script:skipped ($RelativeTarget.Replace("\", "/"))
        return
    }

    $targetParent = Split-Path -Parent $targetPath
    if (-not (Test-Path -LiteralPath $targetParent)) {
        New-Item -ItemType Directory -Path $targetParent -Force | Out-Null
    }
    Copy-Item -LiteralPath $SourcePath -Destination $targetPath
    Add-Result $script:created ($RelativeTarget.Replace("\", "/"))
}

function Sync-ManagedFile {
    param(
        [string]$SourcePath,
        [string]$RelativeTarget
    )

    $targetPath = Join-Path $fullWorkspacePath $RelativeTarget
    $relativeName = $RelativeTarget.Replace("\", "/")
    $targetParent = Split-Path -Parent $targetPath
    if (-not (Test-Path -LiteralPath $targetParent)) {
        New-Item -ItemType Directory -Path $targetParent -Force | Out-Null
    }

    if (-not (Test-Path -LiteralPath $targetPath)) {
        Copy-Item -LiteralPath $SourcePath -Destination $targetPath
        Add-Result $script:created $relativeName
        return
    }

    $sourceHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $SourcePath).Hash
    $targetHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $targetPath).Hash
    if ($sourceHash -eq $targetHash) {
        Add-Result $script:skipped $relativeName
        return
    }

    Copy-Item -LiteralPath $SourcePath -Destination $targetPath -Force
    Add-Result $script:updated $relativeName
}

function Sync-ManagedTextFile {
    param(
        [string]$Content,
        [string]$RelativeTarget
    )

    $targetPath = Join-Path $fullWorkspacePath $RelativeTarget
    $relativeName = $RelativeTarget.Replace("\", "/")
    $targetParent = Split-Path -Parent $targetPath
    if (-not (Test-Path -LiteralPath $targetParent)) {
        New-Item -ItemType Directory -Path $targetParent -Force | Out-Null
    }

    if (-not (Test-Path -LiteralPath $targetPath)) {
        Set-Content -LiteralPath $targetPath -Value $Content -Encoding UTF8
        Add-Result $script:created $relativeName
        return
    }

    $targetContent = Get-Content -Raw -Encoding UTF8 -LiteralPath $targetPath
    if ($targetContent -eq $Content) {
        Add-Result $script:skipped $relativeName
        return
    }

    Set-Content -LiteralPath $targetPath -Value $Content -Encoding UTF8
    Add-Result $script:updated $relativeName
}

Sync-ManagedFile `
    -SourcePath $MyInvocation.MyCommand.Path `
    -RelativeTarget "_scripts/init-research-workspace.ps1"

foreach ($assetName in @("CLAUDE.md.template", "AGENTS.md.template", "gitignore.template", "edge-radar.md", "env-setup.ps1.template")) {
    $sourceAsset = Join-Path $assetsRoot $assetName
    if (Test-Path -LiteralPath $sourceAsset) {
        Copy-ScriptIfMissing `
            -SourcePath $sourceAsset `
            -RelativeTarget (Join-Path "_scripts/init-assets" $assetName)
    }
}

foreach ($relativeAsset in @(
    ".claude/settings.json",
    ".codex/hooks.json"
)) {
    $sourceAsset = Join-Path $assetsRoot $relativeAsset
    if (Test-Path -LiteralPath $sourceAsset) {
        $renderedConfig = Render-HookConfigText `
            -SourcePath $sourceAsset `
            -WorkspaceRoot $fullWorkspacePath

        Sync-ManagedTextFile `
            -Content $renderedConfig `
            -RelativeTarget $relativeAsset

        Sync-ManagedTextFile `
            -Content $renderedConfig `
            -RelativeTarget (Join-Path "_scripts/init-assets" $relativeAsset)
    }
}

$hooksRoot = Join-Path $assetsRoot ".claude/hooks"
if (Test-Path -LiteralPath $hooksRoot) {
    Get-ChildItem -LiteralPath $hooksRoot -Recurse -File | ForEach-Object {
        $relativeHook = Get-RelativePath -BasePath $hooksRoot -TargetPath $_.FullName
        $workspaceHookTarget = Join-Path ".claude/hooks" $relativeHook
        Sync-ManagedFile `
            -SourcePath $_.FullName `
            -RelativeTarget $workspaceHookTarget

        Sync-ManagedFile `
            -SourcePath $_.FullName `
            -RelativeTarget (Join-Path "_scripts/init-assets/.claude/hooks" $relativeHook)
    }
}

foreach ($scriptName in @("ingest.py", "ingest_xlsx.py", "ingest_table_crosscheck.py", "bootstrap-ingest-deps.ps1", "bootstrap-ingest-deps.sh")) {
    $sourceScript = Join-Path $ingestScriptsRoot $scriptName
    if (Test-Path -LiteralPath $sourceScript) {
        Copy-ScriptIfMissing `
            -SourcePath $sourceScript `
            -RelativeTarget (Join-Path "_scripts" $scriptName)
    }
}

$requirementsPath = Join-Path $ingestAssetsRoot "requirements-ingest.txt"
if (Test-Path -LiteralPath $requirementsPath) {
    Copy-ScriptIfMissing `
        -SourcePath $requirementsPath `
        -RelativeTarget "_scripts/requirements-ingest.txt"
}

$financialDataRoot = Join-Path "_scripts" "financial-data"
foreach ($scriptName in @("financial_data.py", "bootstrap-financial-data-deps.ps1")) {
    $sourceScript = Join-Path $financialDataScriptsRoot $scriptName
    if (Test-Path -LiteralPath $sourceScript) {
        Copy-ScriptIfMissing `
            -SourcePath $sourceScript `
            -RelativeTarget (Join-Path $financialDataRoot $scriptName)
    }
}

$providerRoot = Join-Path $financialDataScriptsRoot "providers"
foreach ($providerName in @("sec_provider.py", "akshare_provider.py", "edinet_provider.py", "dart_provider.py", "openesef_provider.py")) {
    $sourceProvider = Join-Path $providerRoot $providerName
    if (Test-Path -LiteralPath $sourceProvider) {
        Copy-ScriptIfMissing `
            -SourcePath $sourceProvider `
            -RelativeTarget (Join-Path (Join-Path $financialDataRoot "providers") $providerName)
    }
}

$financialRequirementsPath = Join-Path $financialDataAssetsRoot "requirements-financial-data.txt"
if (Test-Path -LiteralPath $financialRequirementsPath) {
    Copy-ScriptIfMissing `
        -SourcePath $financialRequirementsPath `
        -RelativeTarget (Join-Path $financialDataRoot "requirements-financial-data.txt")
}

$result = [ordered]@{
    workspace_path = $fullWorkspacePath
    created = @($created)
    updated = @($updated)
    skipped = @($skipped)
    note = "No git init, no dependency install, and no ingest execution were performed. No financial-data execution was performed. To enable toolchains, run the platform-appropriate bootstrap checks first: Windows may use powershell for .ps1, while macOS requires pwsh for .ps1 helpers and may use _scripts/bootstrap-ingest-deps.sh where provided."
}

$result | ConvertTo-Json -Depth 4
