param([string]$InputPath)

. (Join-Path (Split-Path -Parent $PSScriptRoot) '_hook_common.ps1')

$payload = Get-HookPayload -InputPath $InputPath
if ($null -eq $payload) { exit 0 }

foreach ($target in (Get-MarkdownTargets $payload)) {
    if (-not (Test-MarkdownTargetIdentity -Target $target -PathLeafPattern 'peer-deep-dive' -HeadingPattern '^Peer Deep Dive\b')) { continue }

    $text = [string]$target.text
    if ($text -notmatch '(?i)(peer matrix|peer snapshot)') {
        Write-Block "Blocked by peer_matrix_floor: $($target.display) must include a core peer matrix or peer snapshot section."
    }
    if ($text -notmatch '(?i)(cross-cut|cross cut|what matters across peers)') {
        Write-Block "Blocked by peer_matrix_floor: $($target.display) must include a cross-cut comparison section."
    }
}

exit 0
