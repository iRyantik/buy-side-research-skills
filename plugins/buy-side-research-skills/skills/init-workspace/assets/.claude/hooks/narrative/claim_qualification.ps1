param([string]$InputPath)

. (Join-Path (Split-Path -Parent $PSScriptRoot) '_hook_common.ps1')

$payload = Get-HookPayload -InputPath $InputPath
if ($null -eq $payload) { exit 0 }

$strongRelationshipPattern = '(?i)(direct supplier|supplier to|customer of|direct exposure|confirmed catalyst|confirmed order|confirmed relationship|entered .{0,40}supply chain|confirmed exposure|direct beneficiary|\u76F4\u63A5\u4F9B\u5E94\u5546|\u6838\u5FC3\u4F9B\u5E94\u5546|\u4F9B\u8D27\u7ED9|\u5BA2\u6237\u662F|\u76F4\u63A5\u655E\u53E3|\u76F4\u63A5\u53D7\u76CA|\u786E\u5B9A\u53D7\u76CA|\u786E\u5B9A\u50AC\u5316\u5242|\u786E\u8BA4\u8BA2\u5355|\u786E\u8BA4\u5173\u7CFB|\u8FDB\u5165.{0,20}\u4F9B\u5E94\u94FE|\u6838\u5FC3\u5BA2\u6237|\u76F4\u63A5\u5BA2\u6237|\u660E\u786E\u53D7\u76CA\u6807\u7684|\u5B9E\u9524)'
$weakProvenancePattern = '(?i)(rumor|unverified|screenshot|headline|title-only|social media|forum|chat record|theme association|product can be used|tier-2|indirect|\u4F20\u95FB|\u672A\u7ECF\u8BC1\u5B9E|\u672A\u8BC1\u5B9E|\u622A\u56FE|\u6807\u9898|\u6807\u9898\u515A|\u793E\u5A92|\u793E\u4EA4\u5A92\u4F53|\u8BBA\u575B|\u8D34\u5427|\u804A\u5929\u8BB0\u5F55|\u4E3B\u9898\u5173\u8054|\u6982\u5FF5\u6620\u5C04|\u4EA7\u54C1\u53EF\u7528\u4E8E|\u4E8C\u7EA7\u5173\u8054|\u4E09\u7EA7\u5173\u8054|\u95F4\u63A5|\u63A8\u6D4B|\u731C\u6D4B|\u5C0F\u4F5C\u6587)'
$safeQualifierPattern = '(?i)(not independently confirmed|screenshot-only|title-only|plausible but unconfirmed|for follow-up only|\u672A\u72EC\u7ACB\u6838\u5B9E|\u672A\u72EC\u7ACB\u786E\u8BA4|\u4EC5\u622A\u56FE|\u4EC5\u6807\u9898|\u53EF\u80FD\u4F46\u672A\u8BC1\u5B9E|\u4F20\u95FB\u5C42\u9762|\u7EBF\u7D22\u5C42\u9762|\u4EC5\u4F5C\u7EBF\u7D22|\u5F85\u6838\u5B9E|\u9700\u6838\u5B9E|\u4E0D\u80FD\u786E\u8BA4|\u4EC5\u4F9B\u540E\u7EED\u9A8C\u8BC1)'

foreach ($target in (Get-MarkdownTargets $payload)) {
    $isTargetSkill = $false
    if ($target.kind -eq "file" -and $target.path) {
        $leaf = [System.IO.Path]::GetFileName($target.path)
        if ($leaf -match 'information-impact|candidate-screener') { $isTargetSkill = $true }
    } elseif ($target.kind -eq "inline") {
        $text = [string]$target.text
        if ($text -match '(?im)^##\s*Claim Check\b' -or $text -match '(?im)^#\s*Information Impact\b' -or $text -match '(?im)^#\s*Candidate Screener\b' -or $text -match '(?i)\*\*Verdict\*\*:') {
            $isTargetSkill = $true
        }
    }

    if (-not $isTargetSkill) { continue }

    $text = [string]$target.text
    if ($text -notmatch $weakProvenancePattern) { continue }

    foreach ($line in ($text -split "`r?`n")) {
        if ($line -notmatch $strongRelationshipPattern) { continue }
        if ($line -match $safeQualifierPattern) { continue }
        Write-Block "Blocked by claim_qualification: $($target.display) upgrades rumor-, title-, screenshot-, or tiered-source evidence into an unqualified confirmed relationship or catalyst claim."
    }
}

exit 0

