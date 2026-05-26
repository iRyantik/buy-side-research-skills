param([string]$InputPath)

. (Join-Path (Split-Path -Parent $PSScriptRoot) '_hook_common.ps1')

$payload = Get-HookPayload -InputPath $InputPath
if ($null -eq $payload) { exit 0 }

$fallbackAnchorPattern = '\[(?:I|LBG)\d+\]\([^)]+\)'
$allowedInfoImpactPattern = '(?i)(market[_ -]?reaction|price[_ -]?action|share[_ -]?price|stock[_ -]?move|trading[_ -]?volume|implied[_ -]?move|gap[_ -]?up|gap[_ -]?down|股价|涨跌|跳空|成交量|隐含波动|价格反应)'
$forbiddenTruthPattern = '(?i)(company disclosed|management said|customer|supplier|segment|product|backlog|kpi|order|capacity|shipment|business model|project|contract|guidance wording)'

foreach ($target in (Get-MarkdownTargets $payload)) {
    $isTargetSkill =
        (Test-MarkdownTargetIdentity -Target $target -PathLeafPattern 'company-primer|mechanism-map|driver-map|primary-research-plan|information-impact' -HeadingPattern '^(Company Primer|Mechanism Map|Driver Map|Primary Research Plan|Information Impact)\b') -or
        (([string]$target.text) -match '(?im)^#\s*(Company Primer|Mechanism Map|Driver Map|Primary Research Plan|Information Impact)\b')

    if (-not $isTargetSkill) { continue }

    $text = [string]$target.text
    $heading = Get-PrimaryHeading -Text $text
    $isInformationImpact = $heading -match '^Information Impact\b'

    $contract = Get-SourceContractState -Text $text
    $body = [string]$contract.Body
    if ($body -notmatch $fallbackAnchorPattern) { continue }

    foreach ($line in ($body -split "`r?`n")) {
        if ($line -notmatch $fallbackAnchorPattern) { continue }

        if ($isInformationImpact -and $line -match $allowedInfoImpactPattern -and $line -notmatch $forbiddenTruthPattern) {
            continue
        }

        Write-Block "Blocked by disclosure_fact_source_boundary: $($target.display) uses internet source or trusted-market-bridge fallback in a disclosure-fact workflow."
    }
}

exit 0
