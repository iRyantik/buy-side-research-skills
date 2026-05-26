param([string]$InputPath)

. (Join-Path (Split-Path -Parent $PSScriptRoot) '_hook_common.ps1')

$payload = Get-HookPayload -InputPath $InputPath
if ($null -eq $payload) { exit 0 }

$assertiveFactPattern = '(?i)(\d|%|bps|million|billion|guidance|customer|supplier|segment|backlog|order|capacity|shipment|management said|company disclosed|market expects|收入|利润|毛利率|客户|供应商|分部|订单|产能|出货|管理层|公司披露|市场预期)'
$safeMarkerPattern = '(?i)(hypothesis|working hypothesis|need to verify|gap|unknown|tbd|\[来源待补\]|\[需查证\]|待查|假设|线索)'

foreach ($target in (Get-MarkdownTargets $payload)) {
    if (-not (Test-MarkdownTargetIdentity -Target $target -PathLeafPattern 'next-step' -HeadingPattern '^Next Step\b')) { continue }

    foreach ($line in (([string]$target.text -split "`r?`n"))) {
        $trimmed = $line.Trim()
        if ([string]::IsNullOrWhiteSpace($trimmed)) { continue }
        if ($trimmed -match '^(#|##|###|\||- \[|\* )') { continue }
        if ($trimmed -notmatch $assertiveFactPattern) { continue }
        if ($trimmed -match '\[(?:S|P|I|LBG)\d+\]\([^)]+\)') { continue }
        if ($trimmed -match $safeMarkerPattern) { continue }

        Write-Block "Blocked by next_step_anchored_facts_only: $($target.display) introduces an assertive fact in next-step output without an anchor or explicit hypothesis/gap marker."
    }
}

exit 0
