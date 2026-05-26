param([string]$InputPath)

. (Join-Path (Split-Path -Parent $PSScriptRoot) '_hook_common.ps1')

$payload = Get-HookPayload -InputPath $InputPath
if ($null -eq $payload) { exit 0 }

$identityPattern = '(?i)(3-?statement|historical actuals|income statement.+balance sheet.+cash flow)'
$statementSheetPatterns = @{
    income_statement = '(?i)\b(is|p&l|income(?: statement)?)\b'
    balance_sheet = '(?i)\b(bs|balance(?: sheet)?)\b'
    cash_flow = '(?i)\b(cf|cfs|cash ?flow(?: statement)?)\b'
}
$actualHeaderPattern = '(?i)^(?:fy\s*)?\d{4}\s*a(?:ctual)?$|^(?:fy\s*)?q[1-4]\s*\d{4}\s*a(?:ctual)?$|^(?:q[1-4]\s*)?(?:fy\s*)?\d{4}\s*a(?:ctual)?$|^ltm$|^tm$'
$blockedStatusPattern = '(?i)(provider-gap|unavailable|failed|review-only|needs mapping|llm-extracted-review|provider-normalized-review|partial-review|unreconciled-review|not-disclosed|source pending)'
$safeBlankPattern = '(?i)(provider-gap|unavailable|failed|review-only|needs mapping|llm-extracted-review|provider-normalized-review|partial-review|unreconciled-review|not-disclosed|source pending)'

function Normalize-Label {
    param([string]$Label)

    if ([string]::IsNullOrWhiteSpace($Label)) { return "" }
    $normalized = $Label.ToLowerInvariant()
    $normalized = $normalized -replace '&', 'and'
    $normalized = $normalized -replace '[^a-z0-9]+', ' '
    return ($normalized -replace '\s+', ' ').Trim()
}

function Normalize-PeriodLabel {
    param([string]$Label)

    if ([string]::IsNullOrWhiteSpace($Label)) { return "" }
    $clean = ($Label.ToUpperInvariant() -replace '\s+', '')

    if ($clean -match '^FY?(\d{4})A(?:CTUAL)?$') { return "FY$($Matches[1])A" }
    if ($clean -match '^(\d{4})A(?:CTUAL)?$') { return "FY$($Matches[1])A" }
    if ($clean -match '^Q([1-4])FY?(\d{4})A(?:CTUAL)?$') { return "Q$($Matches[1])FY$($Matches[2])A" }
    if ($clean -match '^FY?(\d{4})Q([1-4])A(?:CTUAL)?$') { return "Q$($Matches[2])FY$($Matches[1])A" }
    if ($clean -match '^LTM$') { return "LTM" }
    if ($clean -match '^TM$') { return "TM" }

    return $clean
}

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
            $displayText = ""

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
                Text = ([string]$displayText).Trim()
                HasFormula = ($null -ne $formulaNode)
            })
            $cellIndex += 1
        }

        $nonEmptyCells = @($cells | Where-Object { -not [string]::IsNullOrWhiteSpace($_.Text) -or $_.HasFormula })
        $labelCell = $nonEmptyCells | Select-Object -First 1
        $labelText = if ($null -ne $labelCell) { [string]$labelCell.Text } else { "" }

        [void]$rows.Add([pscustomobject]@{
            SheetName = [string]$SheetInfo.Name
            RowNumber = [int]$rowNode.Attributes['r'].Value
            Cells = $cells.ToArray()
            Label = $labelText.Trim()
            IsBlank = ($nonEmptyCells.Count -eq 0)
        })
    }

    return $rows.ToArray()
}

function Get-HistoricalColumns {
    param([object[]]$Rows)

    $best = $null
    foreach ($row in @($Rows | Where-Object { $_.RowNumber -le 15 })) {
        $actualCells = @($row.Cells | Where-Object { -not [string]::IsNullOrWhiteSpace($_.Text) -and (Normalize-PeriodLabel $_.Text) -match '^(FY\d{4}A|Q[1-4]FY\d{4}A|LTM|TM)$' })
        if ($actualCells.Count -eq 0) { continue }
        if ($null -eq $best -or $actualCells.Count -gt $best.ActualColumns.Count) {
            $best = [pscustomobject]@{
                HeaderRow = $row
                ActualColumns = @($actualCells | ForEach-Object {
                    [pscustomobject]@{
                        Index = $_.Index
                        Ref = $_.Ref
                        Header = $_.Text
                        Period = Normalize-PeriodLabel $_.Text
                    }
                })
            }
        }
    }

    return $best
}

function Get-StatementKeyFromName {
    param([string]$Name)

    foreach ($key in $statementSheetPatterns.Keys) {
        if ($Name -match $statementSheetPatterns[$key]) { return $key }
    }
    return $null
}

function Get-LineItemVariants {
    param(
        [string]$Label,
        [string]$StatementKey
    )

    $base = Normalize-Label $Label
    $variants = New-Object System.Collections.Generic.List[string]
    if (-not [string]::IsNullOrWhiteSpace($base)) { [void]$variants.Add($base) }

    $aliasMap = @{
        'revenue' = @('sales', 'total revenue')
        'sales' = @('revenue', 'total sales')
        'cost of revenue' = @('cost of sales', 'cogs', 'cost of goods sold')
        'cost of sales' = @('cost of revenue', 'cogs', 'cost of goods sold')
        'gross profit' = @('gross income')
        'operating income' = @('ebit')
        'ebit' = @('operating income')
        'net income' = @('net profit', 'profit attributable to owners')
        'cash and cash equivalents' = @('cash', 'cash equivalents')
        'accounts receivable' = @('ar', 'trade receivables')
        'inventory' = @('inventories')
        'accounts payable' = @('ap', 'trade payables')
        'property plant and equipment' = @('ppe', 'fixed assets')
        'capital expenditures' = @('capex')
        'operating cash flow' = @('cash from operations', 'net cash from operating activities', 'cfo')
        'ending cash' = @('ending cash balance', 'cash ending balance')
        'total assets' = @('assets')
        'total liabilities' = @('liabilities')
        'total equity' = @('shareholders equity', 'stockholders equity', 'total shareholders equity', 'total stockholders equity')
    }

    if ($aliasMap.ContainsKey($base)) {
        foreach ($alias in $aliasMap[$base]) {
            [void]$variants.Add((Normalize-Label $alias))
        }
    }

    return @($variants | Where-Object { -not [string]::IsNullOrWhiteSpace($_) } | Select-Object -Unique)
}

function Test-IsRowModelUsable {
    param(
        $Row,
        [object]$StatementCompleteness
    )

    $signals = @(
        [string](Get-StringProperty $Row @('status', 'confidence', 'model_usable', 'completeness_status', 'reconciliation_status', 'axis_completeness_status', 'source_type', 'extraction_method', 'caveat'))
    )
    if ($null -ne $StatementCompleteness) {
        $signals += [string](Get-StringProperty $StatementCompleteness @('status', 'model_usable', 'caveat'))
        $statementModelUsable = Get-StringProperty $StatementCompleteness @('model_usable')
        if ($statementModelUsable -and $statementModelUsable.Trim().ToLowerInvariant() -eq 'false') {
            return $false
        }
    }

    foreach ($signal in $signals) {
        if (-not [string]::IsNullOrWhiteSpace($signal) -and $signal -match $blockedStatusPattern) {
            return $false
        }
    }

    if ($Row.PSObject.Properties.Name -contains 'review_required' -and $Row.review_required) {
        return $false
    }

    return $true
}

function Get-CompletenessMap {
    param($ActualsResolved, $EvidencePack)

    $items = @()
    if ($null -ne $ActualsResolved -and $ActualsResolved.PSObject.Properties.Name -contains 'completeness') {
        $items += @($ActualsResolved.completeness)
    }
    if ($null -ne $EvidencePack -and $EvidencePack.PSObject.Properties.Name -contains 'completeness') {
        $items += @($EvidencePack.completeness)
    }

    $map = @{}
    foreach ($item in $items) {
        $dataItem = Get-StringProperty $item @('data_item')
        if ($dataItem) { $map[$dataItem] = $item }
    }

    return $map
}

function Get-ActualsRequirements {
    param(
        $ActualsResolved,
        $EvidencePack
    )

    if ($null -eq $ActualsResolved -or $ActualsResolved.PSObject.Properties.Name -notcontains 'statements') { return @() }

    $requirements = New-Object System.Collections.Generic.List[object]
    $statementMap = @{
        income_statement = 'income_statement'
        income_statement_quarterly_derived = 'income_statement'
        balance_sheet = 'balance_sheet'
        cash_flow = 'cash_flow'
        cash_flow_quarterly_derived = 'cash_flow'
    }
    $completenessMap = Get-CompletenessMap -ActualsResolved $ActualsResolved -EvidencePack $EvidencePack

    foreach ($statementName in $statementMap.Keys) {
        if ($ActualsResolved.statements.PSObject.Properties.Name -notcontains $statementName) { continue }
        $rows = @($ActualsResolved.statements.$statementName)
        if ($rows.Count -eq 0) { continue }
        $statementKey = $statementMap[$statementName]
        $statementCompleteness = if ($completenessMap.ContainsKey($statementKey)) { $completenessMap[$statementKey] } else { $null }

        foreach ($row in $rows) {
            if (-not (Test-IsRowModelUsable -Row $row -StatementCompleteness $statementCompleteness)) { continue }
            $label = Get-StringProperty $row @('label', 'line_item', 'item', 'name', 'display_name', 'member', 'concept')
            if ([string]::IsNullOrWhiteSpace($label)) { continue }
            $values = $row.values
            if ($null -eq $values) { continue }
            foreach ($property in @($values.PSObject.Properties)) {
                $periodKey = [string]$property.Name
                $value = $property.Value
                if ($null -eq $value -or [string]::IsNullOrWhiteSpace([string]$value)) { continue }
                [void]$requirements.Add([pscustomobject]@{
                    StatementKey = $statementKey
                    StatementSource = $statementName
                    Label = $label
                    LabelVariants = @(Get-LineItemVariants -Label $label -StatementKey $statementKey)
                    Period = Normalize-PeriodLabel $periodKey
                    RawPeriod = $periodKey
                    Value = [string]$value
                })
            }
        }
    }

    return $requirements.ToArray()
}

function Find-MatchingWorksheetRow {
    param(
        [object[]]$Rows,
        [string[]]$LabelVariants,
        [int]$HeaderRowNumber
    )

    $candidateRows = @($Rows | Where-Object { $_.RowNumber -gt $HeaderRowNumber -and -not [string]::IsNullOrWhiteSpace($_.Label) })
    $exactMatches = @()
    foreach ($row in $candidateRows) {
        $rowLabel = Normalize-Label $row.Label
        if ($LabelVariants -contains $rowLabel) {
            $exactMatches += $row
        }
    }
    if ($exactMatches.Count -eq 1) { return $exactMatches[0] }
    if ($exactMatches.Count -gt 1) { return $null }

    $containMatches = @()
    foreach ($row in $candidateRows) {
        $rowLabel = Normalize-Label $row.Label
        foreach ($variant in $LabelVariants) {
            if ($variant.Length -lt 6) { continue }
            if ($rowLabel.Contains($variant) -or $variant.Contains($rowLabel)) {
                $containMatches += $row
                break
            }
        }
    }
    if ($containMatches.Count -eq 1) { return $containMatches[0] }
    return $null
}

function Test-CellFilled {
    param($Cell)

    if ($null -eq $Cell) { return $false }
    return -not [string]::IsNullOrWhiteSpace([string]$Cell.Text)
}

foreach ($target in (Get-WorkbookTargets $payload)) {
    if (-not (Test-WorkbookTargetIdentity -Target $target -PathLeafPattern '3-statement-model' -SearchPattern $identityPattern)) { continue }

    $inputs = Get-ModelingFinancialDataInputs -WorkbookPath $target.path
    if ($null -eq $inputs.ActualsResolved) { continue }

    $requirements = @(Get-ActualsRequirements -ActualsResolved $inputs.ActualsResolved -EvidencePack $inputs.EvidencePack)
    if ($requirements.Count -eq 0) { continue }

    $sharedStrings = @(Get-WorkbookSharedStringValues -Target $target)
    $sheetContexts = @{}
    foreach ($sheetInfo in @($target.sheets)) {
        $statementKey = Get-StatementKeyFromName -Name ([string]$sheetInfo.Name)
        if ([string]::IsNullOrWhiteSpace($statementKey)) { continue }
        $rows = @(Get-WorksheetRowsFromSheetInfo -SheetInfo $sheetInfo -SharedStrings $sharedStrings)
        $historicalColumns = Get-HistoricalColumns -Rows $rows
        if ($null -eq $historicalColumns -or @($historicalColumns.ActualColumns).Count -eq 0) { continue }
        if (-not $sheetContexts.ContainsKey($statementKey)) {
            $sheetContexts[$statementKey] = New-Object System.Collections.Generic.List[object]
        }
        [void]$sheetContexts[$statementKey].Add([pscustomobject]@{
            SheetName = [string]$sheetInfo.Name
            Rows = $rows
            HeaderRow = $historicalColumns.HeaderRow
            ActualColumns = @($historicalColumns.ActualColumns)
        })
    }

    $failures = New-Object System.Collections.Generic.List[string]
    foreach ($requirement in $requirements) {
        if (-not $sheetContexts.ContainsKey($requirement.StatementKey)) { continue }

        $evaluated = $false
        foreach ($sheetContext in @($sheetContexts[$requirement.StatementKey].ToArray())) {
            $periodColumn = @($sheetContext.ActualColumns | Where-Object { $_.Period -eq $requirement.Period } | Select-Object -First 1)
            if ($periodColumn.Count -eq 0) { continue }

            $matchedRow = Find-MatchingWorksheetRow -Rows $sheetContext.Rows -LabelVariants $requirement.LabelVariants -HeaderRowNumber $sheetContext.HeaderRow.RowNumber
            if ($null -eq $matchedRow) { continue }
            $evaluated = $true

            $targetCell = @($matchedRow.Cells | Where-Object { $_.Index -eq $periodColumn[0].Index } | Select-Object -First 1)
            if ($targetCell.Count -eq 0) {
                [void]$failures.Add("$($requirement.StatementKey) row '$($requirement.Label)' period '$($requirement.RawPeriod)' is model-usable in actuals-resolved but workbook $($sheetContext.SheetName) has no visible historical cell in column $($periodColumn[0].Ref).")
                break
            }
            if (-not (Test-CellFilled -Cell $targetCell[0])) {
                [void]$failures.Add("$($requirement.StatementKey) row '$($requirement.Label)' period '$($requirement.RawPeriod)' is model-usable in actuals-resolved but workbook $($sheetContext.SheetName)!$($targetCell[0].Ref) is blank.")
            }
            break
        }
    }

    if ($failures.Count -gt 0) {
        $sample = @($failures | Select-Object -First 6) -join " "
        Write-Block "Blocked by historical_actuals_fill_floor: $($target.display) leaves source-mapped model-usable historical actuals blank. $sample"
    }
}

exit 0
