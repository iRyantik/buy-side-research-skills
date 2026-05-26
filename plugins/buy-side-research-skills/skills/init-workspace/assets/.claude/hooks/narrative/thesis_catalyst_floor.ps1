param([string]$InputPath)

. (Join-Path (Split-Path -Parent $PSScriptRoot) '_hook_common.ps1')

$payload = Get-HookPayload -InputPath $InputPath
if ($null -eq $payload) { exit 0 }

foreach ($target in (Get-MarkdownTargets $payload)) {
    $isTarget = (Test-MarkdownTargetIdentity -Target $target -PathLeafPattern 'alpha-thesis|bear-pre-mortem' -HeadingPattern '^(Alpha Thesis|Bear Pre-Mortem)\b')
    if (-not $isTarget) { continue }

    $text = [string]$target.text
    $checks = @(
        @{ name = 'catalyst'; pattern = '(?i)(catalyst|trigger)' }
        @{ name = 'variant or debate gap'; pattern = '(?i)(variant|debate gap|priced-in|what market misses)' }
        @{ name = 'kill criteria'; pattern = '(?i)(kill criteria|disconfirm|what breaks|thesis break)' }
    )

    foreach ($check in $checks) {
        if ($text -notmatch $check.pattern) {
            Write-Block "Blocked by thesis_catalyst_floor: $($target.display) must explicitly include $($check.name)."
        }
    }
}

exit 0
