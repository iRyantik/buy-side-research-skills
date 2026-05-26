param([string]$InputPath)

. (Join-Path (Split-Path -Parent $PSScriptRoot) '_hook_common.ps1')

$payload = Get-HookPayload -InputPath $InputPath
if ($null -eq $payload) { exit 0 }

$isPattern = '(?i)\b(is|p&l|income(?: statement)?)\b'
$bsPattern = '(?i)\b(bs|balance(?: sheet)?)\b'
$cfPattern = '(?i)\b(cf|cfs|cash ?flow(?: statement)?)\b'
$checkSheetPattern = '(?i)(check|audit|validation|control)'
$balanceEvidencePattern = '(?i)(balance check|assets?.{0,40}liabilit(?:y|ies).{0,40}equity|a\s*=\s*l\s*\+\s*e|assets\s*=\s*liabilities\s*\+\s*equity)'
$cashTiePattern = '(?i)(cash tie|tie-?out|ending cash.{0,40}(balance sheet|bs cash)|cash balance check)'

foreach ($target in (Get-WorkbookTargets $payload)) {
    $sheetNames = @($target.sheetNames)
    $shared = [string]$target.sharedStringsText
    $allText = @($target.sheets | ForEach-Object { [string]$_.Text }) -join "`n"
    $searchText = "$shared`n$allText"

    $hasIS = @($sheetNames | Where-Object { $_ -match $isPattern }).Count -gt 0 -or $searchText -match $isPattern
    $hasBS = @($sheetNames | Where-Object { $_ -match $bsPattern }).Count -gt 0 -or $searchText -match $bsPattern
    $hasCF = @($sheetNames | Where-Object { $_ -match $cfPattern }).Count -gt 0 -or $searchText -match $cfPattern
    if (-not ($hasIS -or $hasBS -or $hasCF)) { continue }

    $hasCheckSheet = @($sheetNames | Where-Object { $_ -match $checkSheetPattern }).Count -gt 0
    $hasBalanceEvidence = $searchText -match $balanceEvidencePattern
    $hasCashTie = $searchText -match $cashTiePattern

    if (-not ($hasCheckSheet -or $hasBalanceEvidence)) {
        Write-Block "Blocked by model_balance_integrity: $($target.display) must include an explicit balance/check/audit area or a visible balance-check trace."
    }
    if (-not $hasCashTie) {
        Write-Block "Blocked by model_balance_integrity: $($target.display) must include an explicit ending-cash to balance-sheet cash tie-out trace."
    }
}

exit 0

