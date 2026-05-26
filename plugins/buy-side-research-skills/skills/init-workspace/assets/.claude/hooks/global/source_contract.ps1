param([string]$InputPath)

. (Join-Path (Split-Path -Parent $PSScriptRoot) '_hook_common.ps1')

function Test-FactualLine {
    param([string]$Line)

    if ([string]::IsNullOrWhiteSpace($Line)) { return $false }
    if ($Line -match '^\s*#') { return $false }
    if ($Line -match '^\s*[-*]\s+') { return $false }
    if ($Line -match '^\s*>') { return $false }
    if ($Line -match '^\s*\|(?:\s*-+\s*\|)+\s*$') { return $false }
    if ($Line -notmatch '\d') { return $false }
    return $true
}

$payload = Get-HookPayload -InputPath $InputPath
if ($null -eq $payload) { exit 0 }

foreach ($target in (Get-MarkdownTargets $payload)) {
    $text = [string]$target.text
    if ($target.kind -eq "inline" -and -not (Test-IsArtifactLikeText -Text $text)) {
        continue
    }

    $resourcesMatches = [regex]::Matches($text, '(?m)^## Resources\b')
    if ($resourcesMatches.Count -ne 1) {
        Write-Block "Blocked by source_contract: $($target.display) must contain exactly one '## Resources' section."
    }

    $contract = Get-SourceContractState -Text $text
    $body = [string]$contract.Body
    $resourceEntries = @($contract.ResourceEntries)
    $resourceMap = $contract.ResourceMap
    $bodyAnchors = @($contract.BodyAnchors)

    foreach ($entry in $resourceEntries) {
        if (-not (Test-IsValidSourceTarget -Target $entry.Target)) {
            Write-Block "Blocked by source_contract: $($target.display) has an invalid ## Resources target for [$($entry.Code)] ($($entry.Target))."
        }
    }

    foreach ($code in @($resourceMap.Keys)) {
        $entriesForCode = @($resourceMap[$code])
        if ($entriesForCode.Count -gt 1) {
            $distinctTargets = @($entriesForCode | ForEach-Object { $_.Target } | Select-Object -Unique)
            if ($distinctTargets.Count -ne 1) {
                Write-Block "Blocked by source_contract: $($target.display) defines [$code] more than once with inconsistent ## Resources targets."
            }
            Write-Block "Blocked by source_contract: $($target.display) defines duplicate ## Resources entries for [$code]."
        }
    }

    foreach ($anchor in $bodyAnchors) {
        if ($anchor.Target -match '^(?i:link|url)$') {
            Write-Block "Blocked by source_contract: $($target.display) still contains placeholder citations such as '(link)' or '(url)'."
        }
        if (-not (Test-IsValidSourceTarget -Target $anchor.Target)) {
            Write-Block "Blocked by source_contract: $($target.display) uses an invalid inline source target for [$($anchor.Code)] ($($anchor.Target))."
        }
        if (-not $resourceMap.ContainsKey($anchor.Code)) {
            Write-Block "Blocked by source_contract: $($target.display) uses [$($anchor.Code)] inline without a matching ## Resources entry."
        }

        $resourceEntry = @($resourceMap[$anchor.Code])[0]
        if ($anchor.Target -ne $resourceEntry.Target) {
            Write-Block "Blocked by source_contract: $($target.display) must keep inline [$($anchor.Code)] target identical to its ## Resources target."
        }
    }

    $numericLinesWithoutAnchors = @()
    foreach ($line in ($body -split "`r?`n")) {
        if (-not (Test-FactualLine -Line $line)) { continue }
        if ($line -match '\[(?:S|P|I|LBG)\d+[^\]]*\]\([^)]+\)') { continue }
        $numericLinesWithoutAnchors += $line.Trim()
    }

    if ($bodyAnchors.Count -eq 0 -and $numericLinesWithoutAnchors.Count -ge 2) {
        Write-Block "Blocked by source_contract: $($target.display) contains factual-looking lines without inline anchors."
    }

    $tableRowsWithoutEvidence = @()
    foreach ($line in ($body -split "`r?`n")) {
        if ($line -notmatch '^\s*\|') { continue }
        if ($line -match '^\s*\|(?:\s*-+\s*\|)+\s*$') { continue }
        if ($line -notmatch '\d|%|bps|x\b') { continue }
        if ($line -match '\[(?:S|P|I|LBG)\d+[^\]]*\]\([^)]+\)') { continue }
        $tableRowsWithoutEvidence += $line.Trim()
    }

    if ($tableRowsWithoutEvidence.Count -ge 2) {
        Write-Block "Blocked by source_contract: $($target.display) has table rows with factual data but no evidence anchors."
    }
}

exit 0

