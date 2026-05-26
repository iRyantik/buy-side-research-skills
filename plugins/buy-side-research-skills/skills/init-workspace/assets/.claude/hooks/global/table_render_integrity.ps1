param([string]$InputPath)

. (Join-Path (Split-Path -Parent $PSScriptRoot) '_hook_common.ps1')

function Test-IsMarkdownTableLikeLine {
    param([string]$Line)

    if ([string]::IsNullOrWhiteSpace($Line)) { return $false }
    if (Test-IsMarkdownTableSeparatorLine -Line $Line) { return $false }

    $trimmed = $Line.Trim()
    if (-not ($trimmed.StartsWith('|') -and $trimmed.EndsWith('|'))) { return $false }

    return (Get-MarkdownTableColumnCount -Line $trimmed) -gt 1
}

$payload = Get-HookPayload -InputPath $InputPath
if ($null -eq $payload) { exit 0 }

foreach ($target in (Get-MarkdownTargets $payload)) {
    $text = [string]$target.text
    $lines = $text -split "`r?`n"
    $tables = @(Get-MarkdownPipeTables -Text $text)
    $coveredLines = New-Object 'System.Collections.Generic.HashSet[int]'

    foreach ($table in $tables) {
        $tableLineCount = @($table.Lines).Count
        for ($offset = 0; $offset -lt $tableLineCount; $offset++) {
            [void]$coveredLines.Add(($table.StartLine - 1) + $offset)
        }
    }

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

    for ($i = 0; $i -lt $lines.Count; $i++) {
        if ($coveredLines.Contains($i)) { continue }

        $line = [string]$lines[$i]
        if (-not (Test-IsMarkdownTableLikeLine -Line $line)) { continue }

        $next = if ($i + 1 -lt $lines.Count) { [string]$lines[$i + 1] } else { "" }
        if (Test-IsMarkdownTableSeparatorLine -Line $next) { continue }

        Write-Block "Blocked by table_render_integrity: $($target.display) has a table-like row near line $($i + 1) outside a valid contiguous markdown table block."
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
