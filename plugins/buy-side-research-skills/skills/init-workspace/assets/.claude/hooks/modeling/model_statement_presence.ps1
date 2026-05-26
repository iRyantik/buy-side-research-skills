param([string]$InputPath)

. (Join-Path (Split-Path -Parent $PSScriptRoot) '_hook_common.ps1')

$payload = Get-HookPayload -InputPath $InputPath
if ($null -eq $payload) { exit 0 }

$isPattern = '(?i)\b(is|p&l|income(?: statement)?)\b'
$bsPattern = '(?i)\b(bs|balance(?: sheet)?)\b'
$cfPattern = '(?i)\b(cf|cfs|cash ?flow(?: statement)?)\b'

foreach ($target in (Get-WorkbookTargets $payload)) {
    $sheetNames = @($target.sheetNames)
    $shared = [string]$target.sharedStringsText

    $hasIS = @($sheetNames | Where-Object { $_ -match $isPattern }).Count -gt 0 -or $shared -match $isPattern
    $hasBS = @($sheetNames | Where-Object { $_ -match $bsPattern }).Count -gt 0 -or $shared -match $bsPattern
    $hasCF = @($sheetNames | Where-Object { $_ -match $cfPattern }).Count -gt 0 -or $shared -match $cfPattern

    if (-not ($hasIS -or $hasBS -or $hasCF)) { continue }
    if (-not ($hasIS -and $hasBS -and $hasCF)) {
        Write-Block "Blocked by model_statement_presence: $($target.display) must include Income Statement, Balance Sheet, and Cash Flow statement tabs or equivalent names."
    }
}

exit 0

