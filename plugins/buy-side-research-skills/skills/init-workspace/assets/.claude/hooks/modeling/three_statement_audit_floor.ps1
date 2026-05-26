param([string]$InputPath)

. (Join-Path (Split-Path -Parent $PSScriptRoot) '_hook_common.ps1')

$payload = Get-HookPayload -InputPath $InputPath
if ($null -eq $payload) { exit 0 }

$identityPattern = '(?i)(3-?statement|all checks pass|balance sheet balance|retained earnings)'
$balancePattern = '(?i)(balance sheet balance|assets?\s*-\s*liabilit(?:y|ies)\s*-\s*equity|assets?\s*=\s*liabilit(?:y|ies)\s*\+\s*equity)'
$cashTiePattern = '(?i)(cash tie-?out|ending cash.{0,50}(balance sheet|bs cash)|cf ending cash.{0,50}bs cash)'
$retainedEarningsPattern = '(?i)(retained earnings roll-?forward|retained earnings|ni[- /]?dividend)'
$masterCheckPattern = '(?i)(master check|all checks pass|errors detected)'
$debtPresencePattern = '(?i)(debt schedule|total debt|debt balance|debt maturity)'
$debtTiePattern = '(?i)(debt tie-?out|debt balance tie|debt roll-?forward)'
$equityPresencePattern = '(?i)(equity issuance|apic|common stock|share issuance)'
$equityTiePattern = '(?i)(equity raise tie-?out|common stock\/apic|equity issuance tie)'

foreach ($target in (Get-WorkbookTargets $payload)) {
    if (-not (Test-WorkbookTargetIdentity -Target $target -PathLeafPattern '3-statement-model' -SearchPattern $identityPattern)) { continue }

    $searchText = Get-WorkbookSearchText -Target $target

    if ($searchText -notmatch $balancePattern) {
        Write-Block "Blocked by three_statement_audit_floor: $($target.display) must include a Balance Sheet Balance audit row showing Assets - Liabilities - Equity = 0."
    }
    if ($searchText -notmatch $cashTiePattern) {
        Write-Block "Blocked by three_statement_audit_floor: $($target.display) must include an explicit CF ending cash to BS cash tie-out."
    }
    if ($searchText -notmatch $retainedEarningsPattern) {
        Write-Block "Blocked by three_statement_audit_floor: $($target.display) must include a retained earnings roll-forward or NI-dividend linkage audit row."
    }
    if ($searchText -notmatch $masterCheckPattern) {
        Write-Block "Blocked by three_statement_audit_floor: $($target.display) must include a master check with explicit pass/fail status."
    }
    if ($searchText -match $debtPresencePattern -and $searchText -notmatch $debtTiePattern) {
        Write-Block "Blocked by three_statement_audit_floor: $($target.display) shows debt schedule content but no explicit Debt Tie-Out."
    }
    if ($searchText -match $equityPresencePattern -and $searchText -notmatch $equityTiePattern) {
        Write-Block "Blocked by three_statement_audit_floor: $($target.display) shows equity issuance/APIC content but no explicit Equity Raise Tie-Out."
    }
}

exit 0
