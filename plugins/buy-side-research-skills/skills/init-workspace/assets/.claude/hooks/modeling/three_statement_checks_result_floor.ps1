param([string]$InputPath)

. (Join-Path (Split-Path -Parent $PSScriptRoot) '_hook_common.ps1')

$payload = Get-HookPayload -InputPath $InputPath
if ($null -eq $payload) { exit 0 }

$identityPattern = '(?i)(3-?statement|all checks pass|balance sheet balance|retained earnings)'
$checksSheetPattern = '(?i)(checks|audit checks|validation|model checks|error checks|integrity|sanity)'
$checksTitlePattern = '(?i)(audit checks|model integrity|validation|error checks|integrity|sanity)'
$numericLabelPattern = '(?i)(balance sheet balance|check|tie-?out|roll-?forward|reconcil|difference|delta|variance|validation|assets?\s*-\s*liabilit(?:y|ies)\s*-\s*equity|ending cash.{0,40}(bs cash|balance sheet cash)|prior\s+re.+ending\s+re|prior\s+nci.+nci\(bs\))'
$statusLabelPattern = '(?i)\b(master|overall|final|status)\b'
$positiveStatusValues = @('PASS', 'ALL CHECKS PASS', 'NO ERRORS', 'CLEAR')

function Get-WorkbookSharedStringValues {
    param($Target)

    if ($null -eq $Target -or [string]::IsNullOrWhiteSpace([string]$Target.sharedStringsText)) { return @() }
    [xml]$sharedXml = [string]$Target.sharedStringsText
    $values = New-Object System.Collections.Generic.List[string]
    foreach ($si in $sharedXml.SelectNodes("/*[local-name()='sst']/*[local-name()='si']")) {
        $textNodes = $si.SelectNodes(".//*[local-name()='t']")
        $text = (($textNodes | ForEach-Object { $_.InnerText }) -join '')
        [void]$values.Add($text)
    }
    return $values.ToArray()
}

function Get-WorksheetRowsFromSheetInfo {
    param(
        [Parameter(Mandatory = $true)]$SheetInfo,
        [string[]]$SharedStrings
    )

    $rows = New-Object System.Collections.Generic.List[object]
    [xml]$sheetXml = [string]$SheetInfo.Text
    foreach ($rowNode in $sheetXml.SelectNodes("/*[local-name()='worksheet']/*[local-name()='sheetData']/*[local-name()='row']")) {
        $cells = New-Object System.Collections.Generic.List[object]
        $cellIndex = 0
        foreach ($cellNode in $rowNode.SelectNodes("./*[local-name()='c']")) {
            $ref = if ($cellNode.Attributes['r']) { $cellNode.Attributes['r'].Value } else { "" }
            $type = if ($cellNode.Attributes['t']) { $cellNode.Attributes['t'].Value } else { "" }
            $formulaNode = $cellNode.SelectSingleNode("./*[local-name()='f']")
            $valueNode = $cellNode.SelectSingleNode("./*[local-name()='v']")
            $inlineTextNodes = $cellNode.SelectNodes("./*[local-name()='is']//*[local-name()='t']")
            $formulaText = $null
            $displayText = ""

            if ($null -ne $formulaNode -and -not [string]::IsNullOrWhiteSpace($formulaNode.InnerText)) {
                $formulaText = "=" + $formulaNode.InnerText.Trim()
            }

            if ($type -eq "s" -and $null -ne $valueNode) {
                $sharedIndex = 0
                if ([int]::TryParse($valueNode.InnerText, [ref]$sharedIndex) -and $sharedIndex -ge 0 -and $sharedIndex -lt $SharedStrings.Count) {
                    $displayText = [string]$SharedStrings[$sharedIndex]
                }
            } elseif ($type -eq "inlineStr" -and $inlineTextNodes.Count -gt 0) {
                $displayText = (($inlineTextNodes | ForEach-Object { $_.InnerText }) -join '')
            } elseif ($null -ne $valueNode) {
                $displayText = [string]$valueNode.InnerText
            }

            [void]$cells.Add([pscustomobject]@{
                Index = $cellIndex
                Ref = $ref
                Type = $type
                Text = ([string]$displayText).Trim()
                Formula = $formulaText
                HasFormula = ($null -ne $formulaNode)
            })
            $cellIndex += 1
        }

        $nonEmptyCells = @($cells | Where-Object { -not [string]::IsNullOrWhiteSpace($_.Text) -or $_.HasFormula })
        $labelCell = $nonEmptyCells | Select-Object -First 1
        $labelText = if ($null -ne $labelCell) { [string]$labelCell.Text } else { "" }
        $resultCells = @()
        if ($null -ne $labelCell) {
            $resultCells = @($cells | Where-Object { $_.Index -gt $labelCell.Index -and (-not [string]::IsNullOrWhiteSpace($_.Text) -or $_.HasFormula) })
        }

        [void]$rows.Add([pscustomobject]@{
            SheetName = [string]$SheetInfo.Name
            RowNumber = [int]$rowNode.Attributes['r'].Value
            Cells = $cells.ToArray()
            Label = ($labelText.Trim())
            ResultCells = $resultCells
            IsBlank = ($nonEmptyCells.Count -eq 0)
        })
    }

    return $rows.ToArray()
}

function Get-ChecksBlockCandidate {
    param(
        [Parameter(Mandatory = $true)][object[]]$SheetRows,
        [Parameter(Mandatory = $true)][string]$SheetName
    )

    if ($SheetRows.Count -eq 0) { return $null }

    $checkRows = @($SheetRows | Where-Object {
        $_.ResultCells.Count -gt 0 -and $_.Label -match $numericLabelPattern
    })
    if ($checkRows.Count -lt 2) { return $null }

    $groups = @()
    $current = @()
    foreach ($row in $checkRows) {
        if ($current.Count -eq 0) {
            $current += $row
            continue
        }

        $last = $current[$current.Count - 1]
        if (($row.RowNumber - $last.RowNumber) -le 2) {
            $current += $row
        } else {
            $groups += ,@($current)
            $current = @($row)
        }
    }
    if ($current.Count -gt 0) {
        $groups += ,@($current)
    }

    $best = $null
    foreach ($group in @($groups)) {
        $groupRows = @($group)
        $startRow = ($groupRows | Select-Object -First 1).RowNumber
        $endRow = ($groupRows | Select-Object -Last 1).RowNumber
        $contextRows = @($SheetRows | Where-Object { $_.RowNumber -ge [Math]::Max(1, $startRow - 3) -and $_.RowNumber -le $endRow })
        $titleMatches = @($contextRows | Where-Object { $_.Label -match $checksTitlePattern })
        $titleScore = if ($SheetName -match $checksSheetPattern) { 4 } elseif ($titleMatches.Count -gt 0) { 2 } else { 0 }
        $score = $groupRows.Count + $titleScore
        if ($null -eq $best -or $score -gt $best.Score) {
            $best = [pscustomobject]@{
                SheetName = $SheetName
                Rows = $groupRows
                Score = $score
            }
        }
    }

    return $best
}

function Get-ChecksBlockFromWorkbookTarget {
    param([Parameter(Mandatory = $true)]$Target)

    $best = $null
    foreach ($sheetInfo in @($Target.sheets)) {
        $sheetRows = @()
        if ($sheetInfo.PSObject.Properties.Name -contains "Rows") {
            $sheetRows = @($sheetInfo.Rows)
        } else {
            $sharedStrings = @(Get-WorkbookSharedStringValues -Target $Target)
            $sheetRows = @(Get-WorksheetRowsFromSheetInfo -SheetInfo $sheetInfo -SharedStrings $sharedStrings)
        }
        if ($sheetRows.Count -eq 0) { continue }
        $candidate = Get-ChecksBlockCandidate -SheetRows $sheetRows -SheetName ([string]$sheetInfo.Name)
        if ($null -ne $candidate -and ($null -eq $best -or $candidate.Score -gt $best.Score)) {
            $best = $candidate
        }
    }
    return $best
}

function Get-ResultKind {
    param([Parameter(Mandatory = $true)]$Row)

    if ([string]::IsNullOrWhiteSpace($Row.Label)) { return $null }
    if ($Row.Label -match $statusLabelPattern) { return "status" }
    if ($Row.Label -match $numericLabelPattern) { return "numeric" }
    return $null
}

function Test-IsFormulaTextFailure {
    param([Parameter(Mandatory = $true)]$Cell)

    $text = [string]$Cell.Text
    return (($Cell.HasFormula -and [string]::IsNullOrWhiteSpace($text)) -or $text.Trim().StartsWith('='))
}

function Test-IsZeroLike {
    param([string]$Text)

    if ([string]::IsNullOrWhiteSpace($Text)) { return $false }
    $clean = $Text.Trim()
    if ($clean.StartsWith('=')) { return $false }
    if ($clean.EndsWith('%')) {
        $clean = $clean.Substring(0, $clean.Length - 1).Trim()
    }
    $clean = $clean.Replace(',', '')

    $value = 0.0
    if (-not [double]::TryParse($clean, [System.Globalization.NumberStyles]::Float, [System.Globalization.CultureInfo]::InvariantCulture, [ref]$value)) {
        return $false
    }
    return [math]::Abs($value) -lt 1e-12
}

function Test-IsPositiveStatus {
    param([string]$Text)

    if ([string]::IsNullOrWhiteSpace($Text)) { return $false }
    $normalized = ($Text.Trim()).ToUpperInvariant()
    return $positiveStatusValues -contains $normalized
}

$skipNativeRecalc = Get-BooleanProperty $payload @("smoke_test", "test_mode")
$workspaceRoot = Get-WorkspaceRoot $payload

foreach ($target in (Get-WorkbookTargets $payload)) {
    if (-not (Test-WorkbookTargetIdentity -Target $target -PathLeafPattern '3-statement-model' -SearchPattern $identityPattern)) { continue }

    $analysisTarget = $target
    if (-not $skipNativeRecalc) {
        $sessionSnapshot = Get-NativeExcelWorkbookSessionSnapshot -Path $target.path
        if ($sessionSnapshot.Succeeded -and @($sessionSnapshot.Sheets).Count -gt 0) {
            $analysisTarget = [pscustomobject]@{
                kind = "workbook-session"
                path = $target.path
                display = $target.display
                sharedStringsText = ""
                sheets = @($sessionSnapshot.Sheets)
                sheetNames = @($sessionSnapshot.Sheets | ForEach-Object { $_.Name })
            }
        }
    }

    $block = Get-ChecksBlockFromWorkbookTarget -Target $analysisTarget
    if ($null -eq $block) {
        Write-Block "Blocked by three_statement_checks_result_floor: $($target.display) must include a recognizable checks-like block with structured check rows."
    }

    $checkedRows = 0
    foreach ($row in @($block.Rows)) {
        $kind = Get-ResultKind -Row $row
        if ([string]::IsNullOrWhiteSpace($kind)) { continue }

        $resultCells = @($row.ResultCells)
        if ($resultCells.Count -eq 0) {
            Write-Block "Blocked by three_statement_checks_result_floor: $($target.display) row '$($row.Label)' has no visible result cells."
        }

        $checkedRows += 1
        foreach ($cell in $resultCells) {
            if (Test-IsFormulaTextFailure -Cell $cell) {
                Write-Block "Blocked by three_statement_checks_result_floor: $($target.display) row '$($row.Label)' still shows formula text in $($cell.Ref) instead of a final calculated result."
            }

            if ($kind -eq "numeric") {
                if (-not (Test-IsZeroLike -Text $cell.Text)) {
                    Write-Block "Blocked by three_statement_checks_result_floor: $($target.display) row '$($row.Label)' must resolve to 0, but $($cell.Ref) shows '$($cell.Text)'."
                }
            } elseif ($kind -eq "status") {
                if (-not (Test-IsPositiveStatus -Text $cell.Text)) {
                    Write-Block "Blocked by three_statement_checks_result_floor: $($target.display) status row '$($row.Label)' must show a positive pass state, but $($cell.Ref) shows '$($cell.Text)'."
                }
            }
        }
    }

    if ($checkedRows -eq 0) {
        Write-Block "Blocked by three_statement_checks_result_floor: $($target.display) has a checks-like block but no recognizable numeric or status check rows."
    }
}

exit 0
