param([string]$InputPath)

. (Join-Path (Split-Path -Parent $PSScriptRoot) '_hook_common.ps1')

$payload = Get-HookPayload -InputPath $InputPath
if ($null -eq $payload) { exit 0 }

foreach ($target in (Get-MarkdownTargets $payload)) {
    $text = [string]$target.text
    $lines = $text -split "`r?`n"
    $tables = @(Get-MarkdownPipeTables -Text $text)

    for ($i = 0; $i -lt ($lines.Count - 1); $i++) {
        $line = [string]$lines[$i]
        $next = [string]$lines[$i + 1]
        if ($line -notmatch '\|') { continue }
        if ($next -notmatch '\|' -or (Test-IsMarkdownTableSeparatorLine -Line $next)) { continue }

        $prevBlank = $i -eq 0 -or [string]::IsNullOrWhiteSpace([string]$lines[$i - 1])
        if ($prevBlank) {
            Write-Block "Blocked by table_render_integrity: $($target.display) has a pipe-table block near line $($i + 1) without a valid separator row."
        }
    }

    foreach ($table in $tables) {
        $tableLines = @($table.Lines)
        if ($tableLines.Count -lt 2) { continue }

        $headerCount = Get-MarkdownTableColumnCount -Line $tableLines[0]
        $separatorCount = Get-MarkdownTableColumnCount -Line $tableLines[1]
        if ($headerCount -le 1) {
            Write-Block "Blocked by table_render_integrity: $($target.display) has a malformed table header near line $($table.StartLine)."
        }
        if ($headerCount -ne $separatorCount) {
            Write-Block "Blocked by table_render_integrity: $($target.display) has mismatched header and separator column counts near line $($table.StartLine)."
        }

        for ($rowIndex = 2; $rowIndex -lt $tableLines.Count; $rowIndex++) {
            $row = [string]$tableLines[$rowIndex]
            $rowCount = Get-MarkdownTableColumnCount -Line $row
            if ($rowCount -ne $headerCount) {
                $lineNumber = $table.StartLine + $rowIndex
                Write-Block "Blocked by table_render_integrity: $($target.display) has a table row with $rowCount columns but expected $headerCount near line $lineNumber."
            }
        }
    }
}

exit 0
