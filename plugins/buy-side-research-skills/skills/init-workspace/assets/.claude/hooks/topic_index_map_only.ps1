param([string]$InputPath)

. "$PSScriptRoot/_hook_common.ps1"

$payload = Get-HookPayload -InputPath $InputPath
if ($null -eq $payload) { exit 0 }

$indexMarkerPattern = '(?i)(##\s*Sessions|##\s*Current Map|##\s*Open Questions|\u672C\u8F6E\u7814\u7A76\u5730\u56FE|\u4F1A\u8BDD|\u5F00\u653E\u95EE\u9898)'
$trackerPattern = '(?i)(portfolio|watchlist|coverage|decision journal|checklist|position status|catalyst pipeline|\u7EC4\u5408|\u8986\u76D6|\u51B3\u7B56\u65E5\u5FD7|\u68C0\u67E5\u8868|\u72B6\u6001\u8DDF\u8E2A)'

foreach ($target in (Get-MarkdownTargets $payload)) {
    $isTarget = $false
    if ($target.kind -eq "file" -and $target.path) {
        $leaf = [System.IO.Path]::GetFileName($target.path)
        if ($leaf -ieq 'index.md' -and (Test-IsTopicArtifactRootFile -Path $target.path -WorkspaceRoot (Get-WorkspaceRoot $payload))) {
            $isTarget = $true
        }
    } elseif ($target.kind -eq "inline") {
        $text = [string]$target.text
        if ($text -match $indexMarkerPattern) { $isTarget = $true }
    }

    if (-not $isTarget) { continue }

    $text = [string]$target.text
    if ($text -match $trackerPattern) {
        Write-Block "Blocked by topic_index_map_only: $($target.display) turns topic index content into a tracker, coverage list, checklist, or portfolio state store instead of an evolutionary map."
    }
    if ($text -notmatch $indexMarkerPattern) {
        Write-Block "Blocked by topic_index_map_only: $($target.display) must preserve map-style sections such as sessions, current map, or open questions."
    }
}

exit 0
