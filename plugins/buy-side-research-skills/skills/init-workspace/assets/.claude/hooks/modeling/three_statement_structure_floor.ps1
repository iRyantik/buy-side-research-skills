param([string]$InputPath)

. (Join-Path (Split-Path -Parent $PSScriptRoot) '_hook_common.ps1')

$payload = Get-HookPayload -InputPath $InputPath
if ($null -eq $payload) { exit 0 }

$searchPattern = '(?i)(3-?statement|income statement.+balance sheet.+cash flow|historical actuals)'
$requiredSlots = @(
    @{ Label = "Historical Actuals"; Pattern = '(?i)(historical actuals|historicals|actuals)' }
    @{ Label = "Income Statement"; Pattern = '(?i)\b(income statement|p&l|is)\b' }
    @{ Label = "Balance Sheet"; Pattern = '(?i)\b(balance sheet|bs)\b' }
    @{ Label = "Cash Flow Statement"; Pattern = '(?i)\b(cash flow statement|cash flow|cfs|cf)\b' }
    @{ Label = "Audit Checks"; Pattern = '(?i)(audit checks|checks|validation|audit)' }
    @{ Label = "Master Check"; Pattern = '(?i)(master check|all checks pass|errors detected)' }
)

foreach ($target in (Get-WorkbookTargets $payload)) {
    if (-not (Test-WorkbookTargetIdentity -Target $target -PathLeafPattern '3-statement-model' -SearchPattern $searchPattern)) { continue }

    $searchText = Get-WorkbookSearchText -Target $target
    $missing = @()
    foreach ($slot in $requiredSlots) {
        if ($searchText -notmatch $slot.Pattern) {
            $missing += $slot.Label
        }
    }

    if ($missing.Count -gt 0) {
        Write-Block "Blocked by three_statement_structure_floor: $($target.display) is missing canonical 3-statement slots: $($missing -join ', ')."
    }
}

exit 0
