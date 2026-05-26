param([string]$InputPath)

. (Join-Path (Split-Path -Parent $PSScriptRoot) '_hook_common.ps1')

$payload = Get-HookPayload -InputPath $InputPath
if ($null -eq $payload) { exit 0 }

$genericNamePattern = '(?i)^(?:\d{4}-\d{2}-\d{2}-)?research-viz(?:-[^.]+)?\.html$'
$datedHtmlPattern = '^\d{4}-\d{2}-\d{2}-.+\.html$'
$titlePattern = '(?is)(<title>.+?</title>|<h1\b[^>]*>.+?</h1>)'
$subtitlePattern = '(?is)(subtitle|sub-title|class=["''][^"'']*subtitle|as-of|updated|ticker|currency)'
$sourcePattern = '(?is)(source line|sources?:|data source|class=["''][^"'']*source|\u6765\u6E90)'
$externalAssetPattern = '(?is)<(?:script|link|img)\b[^>]+(?:src|href)=["''](?:https?:)?//'

foreach ($target in (Get-MarkdownTargets $payload)) {
    $isTargetSkill = $false
    if ($target.kind -eq "file" -and $target.path) {
        $leaf = [System.IO.Path]::GetFileName($target.path)
        if ($leaf -match '\.html$') { $isTargetSkill = $true }
        if ($leaf -match 'research-viz') { $isTargetSkill = $true }
    } elseif ($target.kind -eq "inline") {
        $text = [string]$target.text
        if ($text -match '(?im)^#\s*Research Viz\b' -or $text -match '(?is)<html') { $isTargetSkill = $true }
    }

    if (-not $isTargetSkill) { continue }

    if ($target.path) {
        $leaf = [System.IO.Path]::GetFileName($target.path)
        if ($leaf -match $genericNamePattern) {
            Write-Block "Blocked by viz_delivery_contract: $($target.display) must bind topic-side HTML to the base research stem, not a generic research-viz file name."
        }
        if ($leaf -notmatch $datedHtmlPattern) {
            Write-Block "Blocked by viz_delivery_contract: $($target.display) must use a dated base-research stem HTML name."
        }
    }

    $text = [string]$target.text
    if ($text -match $externalAssetPattern) {
        Write-Block "Blocked by viz_delivery_contract: $($target.display) must be self-contained and cannot depend on external http(s) assets."
    }
    if ($text -notmatch $titlePattern) {
        Write-Block "Blocked by viz_delivery_contract: $($target.display) must include a visible title."
    }
    if ($text -notmatch $subtitlePattern) {
        Write-Block "Blocked by viz_delivery_contract: $($target.display) must include subtitle-style context such as ticker, as-of, updated time, or currency basis."
    }
    if ($text -notmatch $sourcePattern) {
        Write-Block "Blocked by viz_delivery_contract: $($target.display) must include a source line."
    }
}

exit 0

