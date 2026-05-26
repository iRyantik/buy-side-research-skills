param([string]$InputPath)

. (Join-Path (Split-Path -Parent $PSScriptRoot) '_hook_common.ps1')

$payload = Get-HookPayload -InputPath $InputPath
if ($null -eq $payload) { exit 0 }

$missingPattern = '(?i)(missing|unmapped|review-only|mapping gap|\[source pending\]|\[needs mapping\]|\u7f3a\u5931|\u672a\u6620\u5c04|\u5f85\u6620\u5c04|\u4ec5\u5ba1\u9605|\u7f3a\u53e3|\u5f85\u8865)'
$zeroPattern = '(?i)(set to 0|set to zero|filled with 0|plugged as 0|assumed zero|\u5199\u62100|\u586b0|\u8865\u96f6|\u63090\u5904\u7406|\u9ed8\u8ba4\u4e3a0)'
$safePattern = '(?i)(left blank|left as gap|review flag|flagged|not set to zero|\u4fdd\u7559\u7a7a\u767d|\u4fdd\u7559\u7f3a\u53e3|\u5df2\u6807\u8bb0\u4e14\u672a\u63090\u5904\u7406|review-only)'

foreach ($target in (Get-MarkdownTargets $payload)) {
    $isTargetSkill = $false
    if ($target.kind -eq "file" -and $target.path) {
        $leaf = [System.IO.Path]::GetFileName($target.path)
        if ($leaf -match '3-statement-model|dcf-model|model-update') { $isTargetSkill = $true }
    } elseif ($target.kind -eq "inline") {
        $text = [string]$target.text
        if ($text -match '(?im)^#\s*3-Statement Model\b' -or $text -match '(?im)^#\s*DCF Model\b' -or $text -match '(?im)^#\s*Model Update\b') {
            $isTargetSkill = $true
        }
    }

    if (-not $isTargetSkill) { continue }

    $lines = [string]$target.text -split "`r?`n"
    for ($i = 0; $i -lt $lines.Length; $i++) {
        $line = [string]$lines[$i]
        if ($line -notmatch $missingPattern -and $line -notmatch $zeroPattern) { continue }
        $contextStart = [Math]::Max(0, $i - 2)
        $contextEnd = [Math]::Min($lines.Length - 1, $i + 1)
        $context = ($lines[$contextStart..$contextEnd] -join "`n")
        if ($context -match $missingPattern -and $context -match $zeroPattern -and $context -notmatch $safePattern) {
            Write-Block "Blocked by missing_actuals_not_zero: $($target.display) appears to convert missing or unmapped actuals into zero instead of leaving an honest gap or review flag."
        }
    }
}

exit 0

