param([string]$InputPath)

. (Join-Path (Split-Path -Parent $PSScriptRoot) '_hook_common.ps1')

$payload = Get-HookPayload -InputPath $InputPath
if ($null -eq $payload) { exit 0 }

$socialPattern = '(?i)(reddit|subreddit|forum|social post|community|thread|post|comment|social chatter|\u8BBA\u575B|\u793E\u533A|\u5E16\u5B50|\u8BC4\u8BBA|\u793E\u5A92|\u793E\u4EA4\u5A92\u4F53|\u5C0F\u4F5C\u6587|\u8206\u60C5)'
$strongFactPattern = '(?i)(proves|confirms|verified|shows that.+(direct supplier|customer|order|demand)|direct supplier|customer of|confirmed relationship|\u8BC1\u660E|\u8BC1\u5B9E|\u786E\u8BA4|\u5B9E\u9524|\u5750\u5B9E|\u76F4\u63A5\u4F9B\u5E94\u5546|\u5BA2\u6237\u662F|\u786E\u8BA4\u5173\u7CFB|\u786E\u8BA4\u8BA2\u5355|\u9700\u6C42\u88AB\u8BC1\u5B9E)'
$safeCluePattern = '(?i)(clue-only|sentiment-only|social-evidence-only|suggests|may indicate|cannot confirm|not independently confirmed|for follow-up only|\u4EC5\u4F5C\u7EBF\u7D22|\u60C5\u7EEA\u7EBF\u7D22|\u793E\u4EA4\u7EBF\u7D22|\u63D0\u793A|\u6697\u793A|\u4E0D\u80FD\u786E\u8BA4|\u672A\u72EC\u7ACB\u786E\u8BA4|\u4EC5\u4F9B\u540E\u7EED\u9A8C\u8BC1|\u4EC5\u53CD\u6620\u793E\u533A\u53D9\u4E8B)'

foreach ($target in (Get-MarkdownTargets $payload)) {
    $isTargetSkill = $false
    if ($target.kind -eq "file" -and $target.path) {
        $leaf = [System.IO.Path]::GetFileName($target.path)
        if ($leaf -match 'reddit-sentiment') { $isTargetSkill = $true }
    } elseif ($target.kind -eq "inline") {
        $text = [string]$target.text
        if ($text -match '(?im)^#\s*Reddit Sentiment\b') {
            $isTargetSkill = $true
        }
    }

    if (-not $isTargetSkill) { continue }

    foreach ($line in ([string]$target.text -split "`r?`n")) {
        if ($line -notmatch $socialPattern) { continue }
        if ($line -notmatch $strongFactPattern) { continue }
        if ($line -match $safeCluePattern) { continue }
        Write-Block "Blocked by social_clue_only: $($target.display) cannot upgrade Reddit, forum, or social chatter into confirmed company, demand, or customer facts."
    }
}

exit 0

