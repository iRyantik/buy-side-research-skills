param([string]$InputPath)

. (Join-Path (Split-Path -Parent $PSScriptRoot) '_hook_common.ps1')

$payload = Get-HookPayload -InputPath $InputPath
if ($null -eq $payload) { exit 0 }

$comparisonPattern = '(?i)(premium|discount|spread|valuation|liquidity|multiple|EV/EBITDA|P/E|P/B|basis)'
$listingPattern = '(?i)(ADR|A-share|H-share|ordinary share|primary listing|secondary listing|dual-listed|listing identity|listing venue|venue basis|NYSE|NASDAQ|HKEX|SSE|SZSE)'
$currencyPattern = '(?i)(USD|HKD|CNY|RMB|JPY|KRW|EUR|currency basis|FX|translated at|converted at)'
$asOfPattern = '(?i)(as of|timestamp|close as of|market close|updated|collected on)'

foreach ($target in (Get-MarkdownTargets $payload)) {
    $isTargetSkill = $false
    if ($target.kind -eq "file" -and $target.path) {
        $leaf = [System.IO.Path]::GetFileName($target.path)
        if ($leaf -match 'cross-market-compare') { $isTargetSkill = $true }
    } elseif ($target.kind -eq "inline") {
        $text = [string]$target.text
        if ($text -match '(?im)^#\s*Cross-Market Compare\b') {
            $isTargetSkill = $true
        }
    }

    if (-not $isTargetSkill) { continue }

    $text = [string]$target.text
    if ($text -notmatch $comparisonPattern) { continue }
    if ($text -notmatch $listingPattern) {
        Write-Warn "cross_market_parity: $($target.display) must explicitly state listing identity or venue basis for cross-market comparison."
    }
    if ($text -notmatch $currencyPattern) {
        Write-Warn "cross_market_parity: $($target.display) must explicitly state currency basis or FX translation basis for cross-market comparison."
    }
    if ($text -notmatch $asOfPattern) {
        Write-Warn "cross_market_parity: $($target.display) must explicitly state as-of date or timestamp basis for cross-market comparison."
    }
}

exit 0

