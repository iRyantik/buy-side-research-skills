param([string]$InputPath)

. "$PSScriptRoot/_hook_common.ps1"

$payload = Get-HookPayload -InputPath $InputPath
if ($null -eq $payload) { exit 0 }

$workspaceRoot = Get-WorkspaceRoot $payload
$toolName = Get-ToolName $payload

foreach ($path in (Get-CandidatePaths $payload)) {
    if (-not (Test-PathUnder -Path $path -Root $workspaceRoot)) {
        Write-Block "Blocked by workspace_guard: write target escapes the workspace root ($path)."
    }

    $relative = (Get-RelativeDisplayPath -Path $path -Root $workspaceRoot) -replace '\\', '/'
    if ($relative -match '^(screens|peers|quickreads|cross-market)/') {
        Write-Block "Blocked by workspace_guard: legacy root artifact paths are not allowed ($relative). Use topics/... instead."
    }

    if ($relative -like "topics/*" -and (Test-IsTopicArtifactRootFile -Path $path -WorkspaceRoot $workspaceRoot)) {
        $leaf = Split-Path -Leaf $path
        if ($leaf -ne "index.md" -and $leaf -notmatch '^\d{4}-\d{2}-\d{2}-[a-z0-9][a-z0-9\-]*\.(md|html)$') {
            Write-Block "Blocked by workspace_guard: topic root artifact names must be date-prefixed and qualifier-safe ($relative)."
        }
        if ($toolName -eq "Write" -and (Test-Path -LiteralPath $path) -and $leaf -ne "index.md") {
            Write-Block "Blocked by workspace_guard: use Edit/apply_patch for existing topic artifacts instead of blind Write ($relative)."
        }
    }
}

exit 0
