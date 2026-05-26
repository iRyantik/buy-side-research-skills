param([string]$InputPath)

. (Join-Path (Split-Path -Parent $PSScriptRoot) '_hook_common.ps1')

$payload = Get-HookPayload -InputPath $InputPath
if ($null -eq $payload) { exit 0 }

$identityPattern = '(?i)(dcf|wacc|terminal value|sensitivity analysis)'
$requiredSlots = @(
    @{ Label = "Market Data & Key Inputs"; Pattern = '(?i)(market data\s*(?:&|and)\s*key inputs|key inputs)' }
    @{ Label = "Scenario Assumptions"; Pattern = '(?i)(scenario assumptions|bear case|base case|bull case)' }
    @{ Label = "Free Cash Flow"; Pattern = '(?i)(free cash flow|\bfcf\b)' }
    @{ Label = "WACC"; Pattern = '(?i)\bwacc\b' }
    @{ Label = "Terminal Value"; Pattern = '(?i)(terminal value|terminal growth|exit multiple)' }
    @{ Label = "Valuation Summary"; Pattern = '(?i)(valuation summary|equity value|implied share price|price target)' }
    @{ Label = "Sensitivity Analysis"; Pattern = '(?i)(sensitivity analysis|sensitivity table)' }
)

foreach ($target in (Get-WorkbookTargets $payload)) {
    if (-not (Test-WorkbookTargetIdentity -Target $target -PathLeafPattern 'dcf-model' -SearchPattern $identityPattern)) { continue }

    $searchText = Get-WorkbookSearchText -Target $target
    $missing = @()
    foreach ($slot in $requiredSlots) {
        if ($searchText -notmatch $slot.Pattern) {
            $missing += $slot.Label
        }
    }

    if ($missing.Count -gt 0) {
        Write-Block "Blocked by dcf_structure_floor: $($target.display) is missing canonical DCF slots: $($missing -join ', ')."
    }
}

exit 0
