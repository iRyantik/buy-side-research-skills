param([string]$InputPath)

. (Join-Path (Split-Path -Parent $PSScriptRoot) '_hook_common.ps1')

$payload = Get-HookPayload -InputPath $InputPath
if ($null -eq $payload) { exit 0 }

foreach ($target in (Get-MarkdownTargets $payload)) {
    $isTarget = (Test-MarkdownTargetIdentity -Target $target -PathLeafPattern 'pair-trade|pair-note' -HeadingPattern '^(Pair Trade|Pair Snapshot|Pair Note)\b')
    if (-not $isTarget) { continue }

    $text = [string]$target.text
    $checks = @(
        @{ name = 'long/short leg framing'; pattern = '(?i)(long leg|short leg|long/short)' }
        @{ name = 'spread definition'; pattern = '(?i)(spread|ratio|premium|discount)' }
        @{ name = 'entry/exit triggers'; pattern = '(?i)(entry|exit|trigger|stop|take profit)' }
        @{ name = 'sizing basis'; pattern = '(?i)(sizing|position size|hedge ratio|weight)' }
        @{ name = 'risk or failure mode'; pattern = '(?i)(risk|pre-mortem|failure mode|what breaks)' }
    )

    foreach ($check in $checks) {
        if ($text -notmatch $check.pattern) {
            Write-Block "Blocked by pair_structure_floor: $($target.display) must explicitly include $($check.name)."
        }
    }
}

exit 0
