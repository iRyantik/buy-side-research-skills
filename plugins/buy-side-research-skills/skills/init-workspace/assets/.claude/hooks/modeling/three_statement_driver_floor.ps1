param([string]$InputPath)

. (Join-Path (Split-Path -Parent $PSScriptRoot) '_hook_common.ps1')

$payload = Get-HookPayload -InputPath $InputPath
if ($null -eq $payload) { exit 0 }

$identityPattern = '(?i)(3-?statement|revenue growth|drivers|price.?volume.?mix|segment driver)'
$driverBlockPattern = '(?i)(assumptions|inputs|drivers?)'
$structuredDriverPattern = '(?i)(revenue growth|volume.?price.?mix|segment driver|driver block|assumption block|price.?mix|volume)'

foreach ($target in (Get-WorkbookTargets $payload)) {
    if (-not (Test-WorkbookTargetIdentity -Target $target -PathLeafPattern '3-statement-model' -SearchPattern $identityPattern)) { continue }

    $searchText = Get-WorkbookSearchText -Target $target
    $hasDriverBlock = $searchText -match $driverBlockPattern
    $hasStructuredDriver = $searchText -match $structuredDriverPattern

    if (-not ($hasDriverBlock -and $hasStructuredDriver)) {
        Write-Block "Blocked by three_statement_driver_floor: $($target.display) must show a structured revenue/driver breakdown (assumption block, segment driver, or volume-price-mix style split), not only a single topline growth statement."
    }
}

exit 0
