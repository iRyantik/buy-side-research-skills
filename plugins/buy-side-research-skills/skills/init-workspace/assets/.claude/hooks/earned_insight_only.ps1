param([string]$InputPath)

. "$PSScriptRoot/_hook_common.ps1"

$payload = Get-HookPayload -InputPath $InputPath
if ($null -eq $payload) { exit 0 }

$processPattern = '(?i)(todo|reminder|note to self|transcript|process recap|\u5F85\u529E|\u63D0\u9192|\u539F\u59CB\u8BB0\u5F55|\u804A\u5929\u8FC7\u7A0B|\u8FC7\u7A0B\u590D\u8FF0)'
$insightPattern = '(?i)(settled insight|open questions?|implication|takeaways?|conclusion|unresolved|\u7ED3\u8BBA|\u672A\u89E3\u95EE\u9898|\u5F00\u653E\u95EE\u9898|\u542F\u793A|\u672C\u8F6E\u7814\u7A76\u5730\u56FE|\u7814\u7A76\u95EE\u9898|\u7814\u7A76\u5730\u56FE)'

foreach ($target in (Get-MarkdownTargets $payload)) {
    $isTargetSkill = $false
    if ($target.kind -eq "file" -and $target.path) {
        $leaf = [System.IO.Path]::GetFileName($target.path)
        if ($leaf -match 'research-journal|boss-brief') { $isTargetSkill = $true }
    } elseif ($target.kind -eq "inline") {
        $text = [string]$target.text
        if ($text -match '(?im)^#\s*Research Journal\b' -or $text -match '(?im)^#\s*Boss Brief\b') { $isTargetSkill = $true }
    }

    if (-not $isTargetSkill) { continue }

    $processMatches = ([regex]::Matches([string]$target.text, $processPattern)).Count
    $insightMatches = ([regex]::Matches([string]$target.text, $insightPattern)).Count
    if ($processMatches -ge 2 -and $insightMatches -eq 0) {
        Write-Block "Blocked by earned_insight_only: $($target.display) reads like raw process notes or reminders instead of settled insight, unresolved questions, and implications."
    }
}

exit 0
