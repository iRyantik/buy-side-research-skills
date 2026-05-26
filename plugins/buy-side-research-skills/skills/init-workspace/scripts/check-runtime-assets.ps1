param(
    [string]$WorkspacePath = (Get-Location).Path,
    [switch]$SmokeTest
)

$ErrorActionPreference = "Stop"

function Convert-ToFullPath {
    param([string]$Path)

    if ([System.IO.Path]::IsPathRooted($Path)) {
        return [System.IO.Path]::GetFullPath($Path)
    }

    return [System.IO.Path]::GetFullPath((Join-Path (Get-Location) $Path))
}

function Get-ReferencedHookPaths {
    param(
        [object]$JsonObject,
        [string]$WorkspaceRoot
    )

    $results = New-Object System.Collections.Generic.List[string]
    $json = $JsonObject | ConvertTo-Json -Depth 20
    $matches = [regex]::Matches($json, '\.claude/hooks/[^"\s)]+\.ps1')
    foreach ($match in $matches) {
        $relative = ($match.Value -replace '/', '\')
        $full = Join-Path $WorkspaceRoot $relative
        if (-not $results.Contains($full)) {
            [void]$results.Add($full)
        }
    }
    return @($results)
}

function Convert-FromJsonCompat {
    param([string]$RawJson)

    $convertCommand = Get-Command ConvertFrom-Json -ErrorAction Stop
    if ($convertCommand.Parameters.ContainsKey("Depth")) {
        return $RawJson | ConvertFrom-Json -Depth 20
    }
    return $RawJson | ConvertFrom-Json
}

function Get-RegistryFiles {
    param([string]$RegistryPath)

    $files = New-Object System.Collections.Generic.List[string]
    foreach ($line in (Get-Content -Encoding UTF8 -LiteralPath $RegistryPath)) {
        if ($line -match '^\s*file:\s*([^\s#]+)\s*$') {
            [void]$files.Add($Matches[1])
        }
    }
    return @($files)
}

function Invoke-HookSmokeTest {
    param(
        [string]$HookPath,
        [string]$PayloadJson
    )

    $temp = [System.IO.Path]::GetTempFileName()
    try {
        Set-Content -LiteralPath $temp -Value $PayloadJson -Encoding UTF8
        & powershell -NoProfile -ExecutionPolicy Bypass -File $HookPath -InputPath $temp | Out-Null
        if ($LASTEXITCODE -ne 0) {
            throw "Smoke test failed for $HookPath with exit code $LASTEXITCODE"
        }
    } finally {
        Remove-Item -LiteralPath $temp -Force -ErrorAction SilentlyContinue
    }
}

$workspaceRoot = Convert-ToFullPath $WorkspacePath
$claudeSettings = Join-Path $workspaceRoot ".claude\settings.json"
$codexHooks = Join-Path $workspaceRoot ".codex\hooks.json"
$hooksRoot = Join-Path $workspaceRoot ".claude\hooks"
$commonHook = Join-Path $hooksRoot "_hook_common.ps1"
$registryPath = Join-Path $hooksRoot "hooks.registry.yaml"

foreach ($required in @($claudeSettings, $codexHooks, $hooksRoot, $commonHook, $registryPath)) {
    if (-not (Test-Path -LiteralPath $required)) {
        throw "Missing runtime asset: $required"
    }
}

$claudeJson = Convert-FromJsonCompat -RawJson (Get-Content -Raw -Encoding UTF8 -LiteralPath $claudeSettings)
$codexJson = Convert-FromJsonCompat -RawJson (Get-Content -Raw -Encoding UTF8 -LiteralPath $codexHooks)

$adapterPaths = @(
    (Get-ReferencedHookPaths -JsonObject $claudeJson -WorkspaceRoot $workspaceRoot)
    (Get-ReferencedHookPaths -JsonObject $codexJson -WorkspaceRoot $workspaceRoot)
) | Select-Object -Unique

foreach ($path in $adapterPaths) {
    if (-not (Test-Path -LiteralPath $path)) {
        throw "Adapter references missing hook file: $path"
    }
}

$registryFiles = Get-RegistryFiles -RegistryPath $registryPath
if ($registryFiles.Count -eq 0) {
    throw "hooks.registry.yaml did not yield any file entries."
}

$registryFullPaths = @()
foreach ($relativeFile in $registryFiles) {
    $full = Join-Path $hooksRoot ($relativeFile -replace '/', '\')
    $registryFullPaths += $full
    if (-not (Test-Path -LiteralPath $full)) {
        throw "Registry references missing hook file: $full"
    }
}

foreach ($registryPathFull in $registryFullPaths) {
    if ($adapterPaths -notcontains $registryPathFull) {
        throw "Registry hook is not referenced by any adapter: $registryPathFull"
    }
}

foreach ($adapterPath in $adapterPaths) {
    if ($registryFullPaths -notcontains $adapterPath -and -not $adapterPath.EndsWith("_hook_common.ps1")) {
        throw "Adapter hook is missing from registry: $adapterPath"
    }
}

if ($SmokeTest) {
    $markdownPath = Join-Path $workspaceRoot "runtime-smoke.md"
    $payload = @{
        cwd = $workspaceRoot
        tool_name = "Write"
        transcript_path = $markdownPath
        last_assistant_message = "## Verdict`nSource-backed statement. [S1](https://example.com)`n`n## Resources`n- [S1](https://example.com) = web | sample | as-of | note"
    } | ConvertTo-Json -Depth 10

    Invoke-HookSmokeTest -HookPath (Join-Path $hooksRoot "global\source_contract.ps1") -PayloadJson $payload
    Invoke-HookSmokeTest -HookPath (Join-Path $hooksRoot "global\subagent_protocol.ps1") -PayloadJson (@{
        cwd = $workspaceRoot
        last_assistant_message = "claim:`n- sample"
    } | ConvertTo-Json -Depth 10)
    Invoke-HookSmokeTest -HookPath (Join-Path $hooksRoot "global\workspace_guard.ps1") -PayloadJson (@{
        cwd = $workspaceRoot
        tool_name = "Write"
        transcript_path = (Join-Path $workspaceRoot "topics\company\sample\2026-01-01-stock-quickread.md")
    } | ConvertTo-Json -Depth 10)
}

[ordered]@{
    workspace_path = $workspaceRoot
    adapter_hook_count = @($adapterPaths).Count
    registry_hook_count = @($registryFullPaths).Count
    smoke_test = [bool]$SmokeTest
    status = "ok"
} | ConvertTo-Json -Depth 5
