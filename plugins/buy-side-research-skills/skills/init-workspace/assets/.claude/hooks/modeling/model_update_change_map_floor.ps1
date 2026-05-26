param([string]$InputPath)

. (Join-Path (Split-Path -Parent $PSScriptRoot) '_hook_common.ps1')

$payload = Get-HookPayload -InputPath $InputPath
if ($null -eq $payload) { exit 0 }

$requiredSlots = @(
    @{ Label = "What Changed"; Pattern = '(?i)(what changed|update trigger)' }
    @{ Label = "Actual vs Prior"; Pattern = '(?i)(actual vs prior|prior estimate|actual)' }
    @{ Label = "Forward Revisions"; Pattern = '(?i)(forward revisions|old fy est|new fy est|revise forward estimates)' }
    @{ Label = "Valuation Impact"; Pattern = '(?i)(valuation impact|price target|fair value)' }
    @{ Label = "Update Map"; Pattern = '(?i)(update map|formula changes|assumption changes|change map)' }
)

foreach ($target in (Get-MarkdownTargets $payload)) {
    if (-not (Test-MarkdownTargetIdentity -Target $target -PathLeafPattern 'model-update' -HeadingPattern '(?i)^Model Update$')) { continue }

    $text = [string]$target.text
    $missing = @()
    foreach ($slot in $requiredSlots) {
        if ($text -notmatch $slot.Pattern) {
            $missing += $slot.Label
        }
    }

    if ($missing.Count -gt 0) {
        Write-Block "Blocked by model_update_change_map_floor: $($target.display) is missing change-map slots: $($missing -join ', ')."
    }
}

exit 0
