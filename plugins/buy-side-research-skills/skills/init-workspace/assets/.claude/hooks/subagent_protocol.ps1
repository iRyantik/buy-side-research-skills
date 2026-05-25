param([string]$InputPath)

. "$PSScriptRoot/_hook_common.ps1"

$payload = Get-HookPayload -InputPath $InputPath
if ($null -eq $payload) { exit 0 }

$text = Get-LastAssistantMessage $payload
if ([string]::IsNullOrWhiteSpace($text)) { exit 0 }

$evidenceLabelCount = 0
foreach ($label in @('claim\s*:', 'evidence\s*:', 'source\s*:', 'confidence\s*:', 'open_questions\s*:', 'open questions\s*:')) {
    if ($text -match $label) { $evidenceLabelCount++ }
}

$looksLikeFinalSynthesis = $text -match '(?is)(verdict|thesis|ranking|bull|bear|priced-in|variant\s+view|position|sizing|recommend)' -or
    $text -match '(结论|建议|做多|做空|排序|定价|隐含预期|非共识)'

if ($looksLikeFinalSynthesis -and $evidenceLabelCount -lt 3) {
    Write-Block "Blocked by subagent_protocol: subagent output must stay evidence-only and cannot return final thesis or verdict prose."
}

if ($text -match '(?im)^##\s*(verdict|thesis|recommendation|conclusion)\b' -and $evidenceLabelCount -lt 3) {
    Write-Block "Blocked by subagent_protocol: subagent output cannot return a final verdict or conclusion section."
}

if ($text.Length -gt 1200 -and $evidenceLabelCount -lt 3) {
    Write-Block "Blocked by subagent_protocol: long free-form subagent output must be converted into evidence cards before returning."
}

exit 0
