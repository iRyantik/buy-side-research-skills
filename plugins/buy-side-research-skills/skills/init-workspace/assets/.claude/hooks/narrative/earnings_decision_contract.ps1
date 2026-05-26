param([string]$InputPath)

. (Join-Path (Split-Path -Parent $PSScriptRoot) '_hook_common.ps1')

$payload = Get-HookPayload -InputPath $InputPath
if ($null -eq $payload) { exit 0 }

foreach ($target in (Get-MarkdownTargets $payload)) {
    if (-not (Test-MarkdownTargetIdentity -Target $target -PathLeafPattern 'earnings-setup' -HeadingPattern '^Earnings Setup\b')) { continue }

    $text = [string]$target.text
    $isPostPrint = $text -match '(?i)(actual|reported|results|post-print|reported vs|实绩|已公布|业绩已出|盘后复盘)'

    $checks = if ($isPostPrint) {
        @(
            @{ name = 'actual-vs-setup'; pattern = '(?i)(actual vs|vs setup|reported vs expectation)' }
            @{ name = 'thesis health'; pattern = '(?i)(thesis health|thesis intact|broken|thesis update|thesis status)' }
            @{ name = 'action output'; pattern = '(?i)(action|rating change|what to do|next move|hold|add|reduce|exit)' }
        )
    } else {
        @(
            @{ name = 'expectation framing'; pattern = '(?i)(market expectation|consensus|buy-side bar|expectation)' }
            @{ name = 'observation points'; pattern = '(?i)(observation point|watch item|watch list)' }
            @{ name = 'decision tree'; pattern = '(?i)(decision tree|if/then|scenario)' }
        )
    }

    foreach ($check in $checks) {
        if ($text -notmatch $check.pattern) {
            Write-Block "Blocked by earnings_decision_contract: $($target.display) must explicitly include $($check.name)."
        }
    }
}

exit 0
