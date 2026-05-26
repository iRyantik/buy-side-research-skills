param([string]$InputPath)

. (Join-Path (Split-Path -Parent $PSScriptRoot) '_hook_common.ps1')

$payload = Get-HookPayload -InputPath $InputPath
if ($null -eq $payload) { exit 0 }

$identityPattern = '(?i)(dcf|wacc|terminal value|sensitivity analysis)'
$bridgePattern = '(?i)(valuation summary|equity value|equity bridge|implied share price|per share)'
$sensitivityPattern = '(?i)(sensitivity analysis|wacc\s*vs|terminal growth|beta\s*vs|revenue growth\s*vs|ebit margin)'
$placeholderPattern = '(?i)(todo|placeholder|manual step|use excel.?s data table feature|what-if analysis)'

foreach ($target in (Get-WorkbookTargets $payload)) {
    if (-not (Test-WorkbookTargetIdentity -Target $target -PathLeafPattern 'dcf-model' -SearchPattern $identityPattern)) { continue }

    $searchText = Get-WorkbookSearchText -Target $target
    if ($searchText -notmatch '\bWACC\b' -or $searchText -notmatch '(?i)(terminal value|terminal growth|exit multiple)') {
        Write-Block "Blocked by dcf_audit_floor: $($target.display) must include explicit WACC and terminal value basis."
    }
    if ($searchText -notmatch $bridgePattern) {
        Write-Block "Blocked by dcf_audit_floor: $($target.display) must include a visible valuation bridge or valuation summary."
    }
    if ($searchText -notmatch $sensitivityPattern) {
        Write-Block "Blocked by dcf_audit_floor: $($target.display) must include visible sensitivity table evidence."
    }
    if ($searchText -match $placeholderPattern) {
        Write-Block "Blocked by dcf_audit_floor: $($target.display) still shows placeholder or manual-step language in DCF delivery."
    }
}

exit 0
