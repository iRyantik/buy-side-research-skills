param([string]$InputPath)

. (Join-Path (Split-Path -Parent $PSScriptRoot) '_hook_common.ps1')

$payload = Get-HookPayload -InputPath $InputPath
if ($null -eq $payload) { exit 0 }

foreach ($target in (Get-MarkdownTargets $payload)) {
    $isTargetSkill = $false
    if ($target.kind -eq "file" -and $target.path) {
        $leaf = [System.IO.Path]::GetFileName($target.path)
        if ($leaf -match 'stock-quickread|consensus-map|earnings-setup|pair-trade|bear-pre-mortem') { $isTargetSkill = $true }
    }

    if (-not $isTargetSkill) { continue }

    $text = [string]$target.text
    $hasExpectationLanguage = $text -match '(?is)\b(market expectation|priced-in|implied belief|expectation|buy-side bar|consensus)\b' -or
        $text -match '(预期|定价|隐含|一致预期|buy-side bar)'

    if (-not $hasExpectationLanguage) {
        Write-Block "Blocked by must_state_market_expectation: $($target.display) must explicitly state market expectation, priced-in narrative, or implied belief."
    }
}

exit 0

