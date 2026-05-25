param([string]$InputPath)

. "$PSScriptRoot/_hook_common.ps1"

$payload = Get-HookPayload -InputPath $InputPath
if ($null -eq $payload) { exit 0 }

$targetSheetPattern = '(?i)(income|balance|cash flow|dcf|discount|valuation|sensitivity|forecast|projection)'
$excludeSheetPattern = '(?i)(assump|input|raw|source|data|readme|cover|check|audit|validation)'

foreach ($target in (Get-WorkbookTargets $payload)) {
    $relevantSheets = @($target.sheets | Where-Object { $_.Name -match $targetSheetPattern -and $_.Name -notmatch $excludeSheetPattern })
    if ($relevantSheets.Count -eq 0) { continue }

    $formulaSheetCount = @($relevantSheets | Where-Object { $_.FormulaCount -gt 0 }).Count
    $totalFormulas = ($relevantSheets | Measure-Object -Property FormulaCount -Sum).Sum
    if ($null -eq $totalFormulas) { $totalFormulas = 0 }

    if ($formulaSheetCount -lt 1 -or $totalFormulas -lt 10) {
        Write-Block "Blocked by no_hardcoded_formula_assumption: $($target.display) appears to use too few formulas in projection or valuation sheets and may rely on hardcoded derived values."
    }
}

exit 0
