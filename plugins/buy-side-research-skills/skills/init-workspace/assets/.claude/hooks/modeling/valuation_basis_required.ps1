param([string]$InputPath)

. (Join-Path (Split-Path -Parent $PSScriptRoot) '_hook_common.ps1')

$payload = Get-HookPayload -InputPath $InputPath
if ($null -eq $payload) { exit 0 }

$dcfHeadingPattern = '(?im)^#\s*DCF Model\b'
$compsHeadingPattern = '(?im)^#\s*Comps Analysis\b|(?im)^#\s*Comparable Company Analysis\b'
$updateHeadingPattern = '(?im)^#\s*Model Update\b'
$valuationVerdictPattern = '(?i)(price target|fair value|valuation|target multiple|\u4f30\u503c|\u76ee\u6807\u4ef7|\u516c\u5141\u4ef7\u503c)'
$waccPattern = '(?i)\bWACC\b'
$terminalPattern = '(?i)(terminal value|terminal growth|exit multiple)'
$multiplePattern = '(?i)(EV/EBITDA|P/E|EV/Sales|multiple|peer multiple|trading multiple)'
$asOfPattern = '(?i)(as of|as-of|updated|collected on|\u622a\u81f3|\u66f4\u65b0\u4e8e|\u65e5\u671f|\u65f6\u70b9)'
$normalizationPattern = '(?i)(currency|fx|USD|HKD|RMB|fiscal|calendarized|LTM|NTM|normalization|\u5e01\u79cd|\u6c47\u7387|\u8d22\u5e74|\u53e3\u5f84)'

foreach ($target in (Get-MarkdownTargets $payload)) {
    $text = [string]$target.text
    $leaf = if ($target.path) { [System.IO.Path]::GetFileName($target.path) } else { "" }

    if ($leaf -match 'dcf-model' -or $text -match $dcfHeadingPattern) {
        if ($text -match $valuationVerdictPattern -and ($text -notmatch $waccPattern -or $text -notmatch $terminalPattern)) {
            Write-Block "Blocked by valuation_basis_required: $($target.display) must explicitly state WACC and terminal value basis for DCF valuation output."
        }
        continue
    }

    if ($leaf -match 'comps-analysis' -or $text -match $compsHeadingPattern) {
        if ($text -notmatch $multiplePattern -or $text -notmatch $asOfPattern -or $text -notmatch $normalizationPattern) {
            Write-Block "Blocked by valuation_basis_required: $($target.display) must explicitly state comps multiple basis, as-of basis, and currency or fiscal-period normalization."
        }
        continue
    }

    if ($leaf -match 'model-update' -or $text -match $updateHeadingPattern) {
        if ($text -match $valuationVerdictPattern) {
            $hasDcfBasis = $text -match $waccPattern -and $text -match $terminalPattern
            $hasCompsBasis = $text -match $multiplePattern -and $text -match $asOfPattern -and $text -match $normalizationPattern
            if (-not ($hasDcfBasis -or $hasCompsBasis)) {
                Write-Block "Blocked by valuation_basis_required: $($target.display) gives an updated valuation verdict without an explicit DCF or comps basis."
            }
        }
    }
}

exit 0

