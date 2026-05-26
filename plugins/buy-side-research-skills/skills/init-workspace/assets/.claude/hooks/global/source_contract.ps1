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

    if ($text -match '\[(?:S|P|I|LBG)\d+\]\((?:link|url)\)') {
        Write-Block "Blocked by source_contract: $($target.display) still contains placeholder citations such as '(link)' or '(url)'."
    }

    $body = $text -replace '(?ms)^## Resources\b.*$',''
    $anchors = [regex]::Matches($body, '\[(?:S|P|I|LBG)\d+[^\]]*\]\([^)]+\)')
    $numericLinesWithoutAnchors = @()
    foreach ($line in ($body -split "`r?`n")) {
        if (-not (Test-FactualLine -Line $line)) { continue }
        if ($line -match '\[(?:S|P|I|LBG)\d+[^\]]*\]\([^)]+\)') { continue }
        $numericLinesWithoutAnchors += $line.Trim()
    }

    if ($anchors.Count -eq 0 -and $numericLinesWithoutAnchors.Count -ge 2) {
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

