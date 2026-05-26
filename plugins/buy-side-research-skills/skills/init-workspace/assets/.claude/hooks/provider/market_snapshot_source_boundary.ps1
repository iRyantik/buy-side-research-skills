param([string]$InputPath)

. (Join-Path (Split-Path -Parent $PSScriptRoot) '_hook_common.ps1')

$payload = Get-HookPayload -InputPath $InputPath
if ($null -eq $payload) { exit 0 }

$internetAnchorPattern = '\[I\d+\]\([^)]+\)'
$bridgeAnchorPattern = '\[LBG\d+\]\([^)]+\)'
$allowedFieldPattern = '(?i)(market[_ -]?quote|valuation[_ -]?snapshot|price[_ -]?action|consensus|financial[_ -]?snapshot|liquidity|borrow|short interest|implied move|fx|premium|discount|spread|multiple|p/e|p/b|ev/ebitda|ev/sales|fcf yield|market multiple|crowding|\u80a1\u4ef7|\u4f30\u503c|\u6d41\u52a8\u6027|\u501f\u5238|\u505a\u7a7a|\u9690\u542b\u6ce2\u52a8|\u9884\u671f|\u4e00\u81f4\u9884\u671f|\u6ea2\u4ef7|\u6298\u4ef7|\u70b9\u5dee|\u500d\u6570|\u6c47\u7387)'
$forbiddenFieldPattern = '(?i)(business description|segment economics|customer|product|backlog|company disclosed|management said|disclosure wording|\u4e1a\u52a1\u63cf\u8ff0|\u5206\u90e8\u7ecf\u6d4e|\u5ba2\u6237|\u4ea7\u54c1|\u79ef\u538b\u8ba2\u5355|\u79ef\u538b|\u516c\u53f8\u62ab\u9732|\u7ba1\u7406\u5c42\u8868\u793a|\u62ab\u9732\u53e3\u5f84)'
$pairArtifactPattern = '(?im)^(#\s*Pair Snapshot\b|#\s*Pair Note\b|##\s*Spread \u72b6\u6001\b|##\s*P/L \u6765\u6e90\u62c6\u89e3\b)'
$skillMarkerPattern = '(?im)^#\s*(Stock Quickread|Consensus Map|Earnings Setup|Pair Trade|Alpha Thesis|Bear Pre-Mortem|Peer Deep Dive|Industry Quickread|Cross-Market Compare|Candidate Screener|Information Impact)\b'

function Test-IsTargetSkill {
    param($Target)

    if ($Target.kind -eq "file" -and $Target.path) {
        $leaf = [System.IO.Path]::GetFileName($Target.path)
        if ($leaf -match 'stock-quickread|consensus-map|earnings-setup|pair-trade|pair-note|alpha-thesis|bear-pre-mortem|peer-deep-dive|industry-quickread|cross-market-compare|candidate-screener|information-impact') { return $true }
    }

    $text = [string]$Target.text
    if ($text -match $skillMarkerPattern -or $text -match $pairArtifactPattern) { return $true }
    return $false
}

function Test-HasFallbackDisclosure {
    param([string]$Text)

    $hasTaggedSource = $Text -match '(?i)(internet source|trusted-market-bridge)'
    $hasFallbackWord = $Text -match '(?i)fallback'

    return ($hasTaggedSource -and $hasFallbackWord)
}

foreach ($target in (Get-MarkdownTargets $payload)) {
    if (-not (Test-IsTargetSkill $target)) { continue }

    $text = [string]$target.text
    $contract = Get-SourceContractState -Text $text
    $body = [string]$contract.Body
    $resources = [string]$contract.Resources
    $resourceMap = $contract.ResourceMap

    $hasInternetAnchor = $body -match $internetAnchorPattern
    $hasBridgeAnchor = $body -match $bridgeAnchorPattern

    if (-not $hasInternetAnchor -and -not $hasBridgeAnchor) { continue }

    if (-not (Test-HasFallbackDisclosure -Text $body)) {
        Write-Block "Blocked by market_snapshot_source_boundary: $($target.display) uses internet source or trusted-market-bridge anchors without the required fallback disclosure."
    }

    if ([string]::IsNullOrWhiteSpace($resources)) {
        Write-Block "Blocked by market_snapshot_source_boundary: $($target.display) uses fallback market-snapshot anchors but is missing a final ## Resources section."
    }

    $lines = $body -split "`r?`n"
    foreach ($line in $lines) {
        if ($line -notmatch $internetAnchorPattern -and $line -notmatch $bridgeAnchorPattern) { continue }
        if ($line -match $forbiddenFieldPattern) {
            Write-Block "Blocked by market_snapshot_source_boundary: $($target.display) uses fallback market-snapshot anchors in a business-fact or disclosure-truth context."
        }
        if ($line -notmatch $allowedFieldPattern) {
            Write-Block "Blocked by market_snapshot_source_boundary: $($target.display) uses fallback market-snapshot anchors outside allowed market / valuation / consensus / liquidity / price-action fields."
        }
    }

    if ($hasInternetAnchor) {
        $internetCodes = @([regex]::Matches($body, '\[I\d+\]\([^)]+\)') | ForEach-Object {
            [regex]::Match($_.Value, '\[(I\d+)\]').Groups[1].Value
        } | Select-Object -Unique)
        foreach ($code in $internetCodes) {
            if (-not $resourceMap.ContainsKey($code)) {
                Write-Block "Blocked by market_snapshot_source_boundary: $($target.display) uses [$code] without a matching ## Resources entry."
            }

            $entries = @($resourceMap[$code])
            foreach ($entry in $entries) {
                if (-not (Test-IsValidSourceTarget -Target $entry.Target)) {
                    Write-Block "Blocked by market_snapshot_source_boundary: $($target.display) has an invalid ## Resources target for [$code] ($($entry.Target))."
                }
                if ($entry.Line -notmatch '(?i)\binternet source\b' -or $entry.Line -notmatch '(?i)\bas-of\b' -or $entry.Line -notmatch '(?i)(fallback reason|reason:)') {
                    Write-Block "Blocked by market_snapshot_source_boundary: $($target.display) must expand each [$code] entry with provider, as-of, and fallback reason in ## Resources."
                }
            }
        }
    }

    if ($hasBridgeAnchor) {
        $bridgeCodes = @([regex]::Matches($body, '\[LBG\d+\]\([^)]+\)') | ForEach-Object {
            [regex]::Match($_.Value, '\[(LBG\d+)\]').Groups[1].Value
        } | Select-Object -Unique)
        foreach ($code in $bridgeCodes) {
            if (-not $resourceMap.ContainsKey($code)) {
                Write-Block "Blocked by market_snapshot_source_boundary: $($target.display) uses [$code] without a matching ## Resources entry."
            }

            $entries = @($resourceMap[$code])
            foreach ($entry in $entries) {
                if (-not (Test-IsValidSourceTarget -Target $entry.Target)) {
                    Write-Block "Blocked by market_snapshot_source_boundary: $($target.display) has an invalid ## Resources target for [$code] ($($entry.Target))."
                }
                if ($entry.Line -notmatch '(?i)(Longbridge|trusted-market-bridge)' -or $entry.Line -notmatch '(?i)\bas-of\b' -or $entry.Line -notmatch '(?i)(fallback reason|reason:)') {
                    Write-Block "Blocked by market_snapshot_source_boundary: $($target.display) must expand each [$code] entry with provider, as-of, and fallback reason in ## Resources."
                }
            }
        }
    }
}

exit 0
