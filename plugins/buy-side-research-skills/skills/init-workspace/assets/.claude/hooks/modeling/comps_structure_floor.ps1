param([string]$InputPath)

. (Join-Path (Split-Path -Parent $PSScriptRoot) '_hook_common.ps1')

$payload = Get-HookPayload -InputPath $InputPath
if ($null -eq $payload) { exit 0 }

$identityPattern = '(?i)(comparable company analysis|valuation multiples|operating metrics|statistics)'
$requiredSlots = @(
    @{ Label = "Header Block"; Pattern = '(?i)(comparable company analysis|as of|all figures in)' }
    @{ Label = "Operating Metrics"; Pattern = '(?i)(operating metrics|operating statistics|financial metrics)' }
    @{ Label = "Valuation Multiples"; Pattern = '(?i)(valuation multiples|ev\/ebitda|p\/e|ev\/sales)' }
    @{ Label = "Statistics"; Pattern = '(?i)(maximum|75th percentile|median|25th percentile|minimum|statistics)' }
    @{ Label = "Notes / Methodology"; Pattern = '(?i)(notes|methodology|source)' }
)

foreach ($target in (Get-WorkbookTargets $payload)) {
    if (-not (Test-WorkbookTargetIdentity -Target $target -PathLeafPattern 'comps-analysis' -SearchPattern $identityPattern)) { continue }

    $searchText = Get-WorkbookSearchText -Target $target
    $missing = @()
    foreach ($slot in $requiredSlots) {
        if ($searchText -notmatch $slot.Pattern) {
            $missing += $slot.Label
        }
    }

    if ($missing.Count -gt 0) {
        Write-Block "Blocked by comps_structure_floor: $($target.display) is missing canonical comps slots: $($missing -join ', ')."
    }
}

exit 0
