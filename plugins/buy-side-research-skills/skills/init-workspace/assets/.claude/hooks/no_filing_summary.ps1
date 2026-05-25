param([string]$InputPath)

. "$PSScriptRoot/_hook_common.ps1"

$payload = Get-HookPayload -InputPath $InputPath
if ($null -eq $payload) { exit 0 }

foreach ($target in (Get-MarkdownTargets $payload)) {
    $isTargetSkill = $false
    if ($target.kind -eq "file" -and $target.path) {
        $leaf = [System.IO.Path]::GetFileName($target.path)
        if ($leaf -match 'stock-quickread|peer-deep-dive') { $isTargetSkill = $true }
    }

    if (-not $isTargetSkill) { continue }

    $text = [string]$target.text
    $summaryMatches = ([regex]::Matches($text, '(?is)\b(founded|headquartered|management team|company history|operates through|business overview)\b')).Count +
        ([regex]::Matches($text, '(成立于|总部位于|管理层|公司历史|业务概览|主要业务|分为.+部门)')).Count
    $judgmentMatches = ([regex]::Matches($text, '(?is)\b(investability|expectation|priced-in|variant|next step|industry lens|cross-cut|ranking)\b')).Count +
        ([regex]::Matches($text, '(可投性|预期|定价|隐含|非共识|下一步|行业 lens|横向洞察|排序)')).Count

    if ($summaryMatches -ge 3 -and $judgmentMatches -eq 0) {
        Write-Block "Blocked by no_filing_summary: $($target.display) reads like a filing or company recap instead of a buy-side research artifact."
    }
}

exit 0
