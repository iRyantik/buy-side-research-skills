param([string]$InputPath)

. (Join-Path (Split-Path -Parent $PSScriptRoot) '_hook_common.ps1')

$payload = Get-HookPayload -InputPath $InputPath
if ($null -eq $payload) { exit 0 }

foreach ($target in (Get-MarkdownTargets $payload)) {
    if (-not (Test-MarkdownTargetIdentity -Target $target -PathLeafPattern 'consensus-map' -HeadingPattern '^Consensus Map\b')) { continue }

    $text = [string]$target.text
    $checks = @(
        @{ name = 'market expectation framing'; pattern = '(?im)^##\s*Market Expectation\b|(?i)(buy-side bar|priced-in|consensus expects)' }
        @{ name = 'consensus baseline'; pattern = '(?im)^##\s*Consensus\b|(?i)(street consensus|sell-side baseline)' }
        @{ name = 'variant gap'; pattern = '(?im)^##\s*Variant Gap\b|(?i)(gap vs consensus|what is missed)' }
        @{ name = 'bar framing'; pattern = '(?im)^##\s*Bar\b|(?i)(bar is|hurdle|beat and raise)' }
    )

    foreach ($check in $checks) {
        if ($text -notmatch $check.pattern) {
            Write-Block "Blocked by consensus_floor: $($target.display) must explicitly include $($check.name)."
        }
    }
}

exit 0
