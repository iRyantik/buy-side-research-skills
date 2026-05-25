param([string]$InputPath)

. "$PSScriptRoot/_hook_common.ps1"

$payload = Get-HookPayload -InputPath $InputPath
if ($null -eq $payload) { exit 0 }

$riskyInfoPattern = '(?i)(non-public|mnpi|material nonpublic|undisclosed|unpublished|\u672A\u516C\u5F00|\u672A\u62AB\u9732|\u5185\u5E55|\u91CD\u5927\u975E\u516C\u5F00|\u975E\u516C\u5F00|\u5C1A\u672A\u516C\u5E03|\u672A\u53D1\u5E03)'
$riskyBusinessPattern = '(?i)(order(s)?|guidance|customer list|specific customer|contract terms|pricing|price point|margin by customer|procurement plan|pipeline|backlog by customer|next quarter|next-half|\u8BA2\u5355|\u6307\u5F15|\u5BA2\u6237\u540D\u5355|\u5177\u4F53\u5BA2\u6237|\u5408\u540C\u6761\u6B3E|\u5B9A\u4EF7|\u4EF7\u683C\u70B9|\u5BA2\u6237\u6BDB\u5229|\u91C7\u8D2D\u8BA1\u5212|\u7BA1\u7EBF|\u8BA2\u5355\u50A8\u5907|\u4E0B\u5B63\u5EA6|\u4E0B\u534A\u5E74)'
$safeContextPattern = '(?i)(do not ask|red-line|red line|sensitive question|why risky|safer proxy|compliant rewrite|\u4E0D\u8981\u95EE|\u7EA2\u7EBF|\u654F\u611F\u95EE\u9898|\u4E3A\u4F55\u6709\u98CE\u9669|\u66FF\u4EE3\u95EE\u6CD5|\u5408\u89C4\u6539\u5199|\u53EF\u66FF\u4EE3\u4EE3\u7406\u53D8\u91CF|\u66F4\u5B89\u5168\u7684\u4EE3\u7406\u95EE\u9898|\u4E0D\u80FD\u95EE|\u907F\u514D\u76F4\u63A5\u95EE)'
$fabricatedEvidencePattern = '(?i)(expert feedback|experts said|interviews confirmed|channel checks indicate|we learned from experts|customers told us|suppliers told us|\u4E13\u5BB6\u53CD\u9988|\u4E13\u5BB6\u8868\u793A|\u8BBF\u8C08\u786E\u8BA4|\u6E20\u9053\u8C03\u7814\u663E\u793A|\u6211\u4EEC\u4ECE\u4E13\u5BB6\u5904\u4E86\u89E3\u5230|\u5BA2\u6237\u544A\u8BC9\u6211\u4EEC|\u4F9B\u5E94\u5546\u544A\u8BC9\u6211\u4EEC|\u5DF2\u7ECF\u804A\u8FC7\u4E13\u5BB6|\u4E13\u5BB6\u8BBF\u8C08\u8868\u660E|\u6E20\u9053\u786E\u8BA4)'
$plannedQualifierPattern = '(?i)(planned|target|persona|hypothesis|expected evidence|decision gate|research objective|must-ask|nice-to-have|red-line|\u8BA1\u5212|\u62DF|\u76EE\u6807|\u753B\u50CF|\u5047\u8BBE|\u9884\u671F\u8BC1\u636E|\u51B3\u7B56\u95E8\u69DB|\u7814\u7A76\u76EE\u6807|\u5FC5\u95EE|\u53EF\u9009|\u5F85\u9A8C\u8BC1|\u51C6\u5907\u8BBF\u8C08|\u8BBF\u8C08\u8BA1\u5212)'

foreach ($target in (Get-MarkdownTargets $payload)) {
    $isTargetSkill = $false
    if ($target.kind -eq "file" -and $target.path) {
        $leaf = [System.IO.Path]::GetFileName($target.path)
        if ($leaf -match 'primary-research-plan') { $isTargetSkill = $true }
    } elseif ($target.kind -eq "inline") {
        $text = [string]$target.text
        if ($text -match '(?im)^##\s*4\.\s*Compliance Guardrails\b' -or $text -match '(?im)^#\s*Primary Research Plan\b' -or $text -match '(?im)^##\s*Research Objective / Decision Impact\b') {
            $isTargetSkill = $true
        }
    }

    if (-not $isTargetSkill) { continue }

    $lines = $target.text -split "`r?`n"
    for ($i = 0; $i -lt $lines.Length; $i++) {
        $line = [string]$lines[$i]
        if ([string]::IsNullOrWhiteSpace($line)) { continue }

        if ($line -match $fabricatedEvidencePattern -and $line -notmatch $plannedQualifierPattern) {
            Write-Block "Blocked by primary_research_compliance: $($target.display) presents planned primary research as already completed expert or channel-check evidence."
        }

        if (($line -match $riskyInfoPattern -or $line -match $riskyBusinessPattern) -and $line -notmatch $safeContextPattern) {
            $contextStart = [Math]::Max(0, $i - 3)
            $contextLines = $lines[$contextStart..$i] -join "`n"
            if ($contextLines -notmatch $safeContextPattern) {
                Write-Block "Blocked by primary_research_compliance: $($target.display) includes MNPI-seeking or confidential-information-seeking question wording outside an explicit red-line or compliant-rewrite context."
            }
        }
    }
}

exit 0
