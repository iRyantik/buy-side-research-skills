param([string]$InputPath)

. (Join-Path (Split-Path -Parent $PSScriptRoot) '_hook_common.ps1')

$payload = Get-HookPayload -InputPath $InputPath
if ($null -eq $payload) { exit 0 }

$identityPattern = '(?i)(3-?statement|income statement|assumptions|gross margin|ebit margin|ni margin|segment driver|revenue growth)'
$isSheetPattern = '(?i)\b(is|income(?: statement)?|p&l)\b'
$assumptionsSheetPattern = '(?i)\b(assumptions|inputs|drivers?)\b'
$blockedDriverPattern = '(?i)(not-disclosed|review-only|unresolved|placeholder|needs mapping|source pending|pending)'

function Normalize-Label {
    param([string]$Label)

    if ([string]::IsNullOrWhiteSpace($Label)) { return "" }
    $normalized = $Label.ToLowerInvariant()
    $normalized = $normalized -replace '&', ' and '
    $normalized = $normalized -replace '/', ' '
    $normalized = $normalized -replace '[^a-z0-9]+', ' '
    return ($normalized -replace '\s+', ' ').Trim()
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
        $resultCells = @()
        if ($null -ne $labelCell) {
            $resultCells = @($cells | Where-Object { $_.Index -gt $labelCell.Index })
        }

        [void]$rows.Add([pscustomobject]@{
            SheetName = [string]$SheetInfo.Name
            RowNumber = [int]$rowNode.Attributes['r'].Value
            Cells = $cells.ToArray()
            Label = $labelText.Trim()
            LabelNormalized = Normalize-Label $labelText
            ResultCells = $resultCells
            IsBlank = ($nonEmptyCells.Count -eq 0)
        })
    }

    return $rows.ToArray()
}

function Get-RelevantValueCells {
    param($Row)

    if ($null -eq $Row) { return @() }
    return @($Row.ResultCells | Where-Object {
        $_.HasFormula -or
        -not [string]::IsNullOrWhiteSpace([string]$_.Text)
    })
}

function Test-IsPlaceholderCell {
    param($Cell)

    if ($null -eq $Cell) { return $true }
    if ($Cell.HasFormula) { return $false }

    $text = ([string]$Cell.Text).Trim()
    if ([string]::IsNullOrWhiteSpace($text)) { return $true }
    return $text -match '^(?:--|—|-|n/?a|nm)$'
}

function Test-RowHasVisibleCoverage {
    param($Row)

    $cells = @(Get-RelevantValueCells -Row $Row)
    if ($cells.Count -eq 0) { return $false }
    return (@($cells | Where-Object { -not (Test-IsPlaceholderCell -Cell $_) }).Count -gt 0)
}

function Test-RowHasBrokenVisibleCoverage {
    param($Row)

    $cells = @(Get-RelevantValueCells -Row $Row)
    if ($cells.Count -eq 0) { return $true }

    $firstCoveredIndex = -1
    for ($index = 0; $index -lt $cells.Count; $index += 1) {
        if (-not (Test-IsPlaceholderCell -Cell $cells[$index])) {
            $firstCoveredIndex = $index
            break
        }
    }

    if ($firstCoveredIndex -lt 0) { return $true }

    for ($index = $firstCoveredIndex; $index -lt $cells.Count; $index += 1) {
        if (Test-IsPlaceholderCell -Cell $cells[$index]) {
            return $true
        }
    }

    return $false
}

function Get-LabelVariants {
    param([string]$Label)

    $base = Normalize-Label $Label
    $variants = New-Object System.Collections.Generic.List[string]
    if (-not [string]::IsNullOrWhiteSpace($base)) {
        [void]$variants.Add($base)
    }

    if ($base -match '\bocean and marine\b') {
        [void]$variants.Add('ocean marine')
        [void]$variants.Add('ocean')
    }
    if ($base -match '\baerospace and space\b') {
        [void]$variants.Add('aero and space')
        [void]$variants.Add('aerospace')
    }
    if ($base -match '\bit services\b') {
        [void]$variants.Add('it service')
    }
    if ($base -match '\bconsolidation adjustment\b') {
        [void]$variants.Add('consolidation adj')
    }

    return @($variants | Select-Object -Unique)
}

function Find-MatchingRows {
    param(
        [object[]]$Rows,
        [string[]]$LabelVariants
    )

    $matches = New-Object System.Collections.Generic.List[object]
    foreach ($row in @($Rows | Where-Object { -not [string]::IsNullOrWhiteSpace($_.Label) -and @(Get-RelevantValueCells -Row $_).Count -gt 0 })) {
        foreach ($variant in $LabelVariants) {
            if ($row.LabelNormalized -eq $variant -or $row.LabelNormalized.Contains($variant) -or $variant.Contains($row.LabelNormalized)) {
                [void]$matches.Add($row)
                break
            }
        }
    }

    return @($matches | Sort-Object RowNumber -Unique)
}

function Get-MachineReadableDriverCoverage {
    param($DriverMap)

    if ($null -eq $DriverMap) {
        return [pscustomobject]@{
            RevenueBuckets = @()
            HasRevenueDrivers = $false
            HasMarginDrivers = $false
        }
    }

    $bucketMap = @{}
    foreach ($driver in @($DriverMap.revenue_drivers)) {
        if ($null -eq $driver) { continue }
        $bucket = Get-StringProperty $driver @('business_bucket', 'bucket', 'model_bucket')
        $evidenceStatus = Get-StringProperty $driver @('evidence_status', 'model_treatment', 'confidence_source_status')
        if ([string]::IsNullOrWhiteSpace($bucket)) { continue }
        if (-not [string]::IsNullOrWhiteSpace($evidenceStatus) -and $evidenceStatus -match $blockedDriverPattern) { continue }
        if ((Normalize-Label $bucket) -match '(consolidation adjustment|non model line|non-model line)') { continue }
        $bucketMap[$bucket] = $true
    }

    foreach ($segment in @($DriverMap.segment_geography_treatment.filing_native_segments)) {
        if ($null -eq $segment) { continue }
        $bucket = Get-StringProperty $segment @('model_bucket')
        if ([string]::IsNullOrWhiteSpace($bucket)) { continue }
        if ((Normalize-Label $bucket) -match '(consolidation adjustment|non model line|non-model line|exclude from operating analysis)') { continue }
        $bucketMap[$bucket] = $true
    }

    return [pscustomobject]@{
        RevenueBuckets = @($bucketMap.Keys | Sort-Object)
        HasRevenueDrivers = (@($DriverMap.revenue_drivers).Count -gt 0 -or @($bucketMap.Keys).Count -gt 0)
        HasMarginDrivers = (@($DriverMap.margin_drivers).Count -gt 0)
    }
}

function Get-FirstTitleRowNumber {
    param(
        [object[]]$Rows,
        [string]$Pattern
    )

    $match = @($Rows | Where-Object { $_.Label -match $Pattern } | Sort-Object RowNumber | Select-Object -First 1)
    if ($match.Count -eq 0) { return $null }
    return [int]$match[0].RowNumber
}

foreach ($target in (Get-WorkbookTargets $payload)) {
    if (-not (Test-WorkbookTargetIdentity -Target $target -PathLeafPattern '3-statement-model' -SearchPattern $identityPattern)) { continue }

    $driverMapInputs = Get-ModelingDriverMapInputs -WorkbookPath $target.path
    if ($null -eq $driverMapInputs.DriverMap) { continue }

    $driverCoverage = Get-MachineReadableDriverCoverage -DriverMap $driverMapInputs.DriverMap
    if (-not $driverCoverage.HasRevenueDrivers -and -not $driverCoverage.HasMarginDrivers) { continue }

    $sharedStrings = @(Get-WorkbookSharedStringValues -Target $target)
    $sheetContexts = @{}
    foreach ($sheetInfo in @($target.sheets)) {
        $sheetName = [string]$sheetInfo.Name
        if ($sheetName -match $isSheetPattern -or $sheetName -match $assumptionsSheetPattern) {
            $sheetContexts[$sheetName] = @(Get-WorksheetRowsFromSheetInfo -SheetInfo $sheetInfo -SharedStrings $sharedStrings)
        }
    }

    $isSheetName = @($sheetContexts.Keys | Where-Object { $_ -match $isSheetPattern } | Select-Object -First 1)
    $assumptionsSheetName = @($sheetContexts.Keys | Where-Object { $_ -match $assumptionsSheetPattern } | Select-Object -First 1)

    $failures = New-Object System.Collections.Generic.List[string]

    if ($isSheetName.Count -gt 0) {
        $isRows = @($sheetContexts[$isSheetName[0]])
        $matchedRevenueBuckets = 0
        foreach ($bucket in @($driverCoverage.RevenueBuckets)) {
            $bucketVariants = Get-LabelVariants -Label $bucket
            $bucketRows = @(Find-MatchingRows -Rows $isRows -LabelVariants $bucketVariants)
            if ($bucketRows.Count -eq 0) { continue }

            $matchedRevenueBuckets += 1
            foreach ($bucketRow in $bucketRows) {
                if (-not (Test-RowHasVisibleCoverage -Row $bucketRow)) {
                    [void]$failures.Add("$($isSheetName[0]) row '$($bucketRow.Label)' is a driver-map revenue bucket ('$bucket') but remains a placeholder with no visible coverage.")
                    break
                }
            }
        }

        if ($matchedRevenueBuckets -gt 0) {
            foreach ($metricLabel in @('YoY Growth %', 'Gross Margin %', 'EBIT Margin %', 'NI Margin %')) {
                $metricRows = @(Find-MatchingRows -Rows $isRows -LabelVariants (Get-LabelVariants -Label $metricLabel))
                if ($metricRows.Count -eq 0) { continue }
                foreach ($metricRow in $metricRows) {
                    if (Test-RowHasBrokenVisibleCoverage -Row $metricRow) {
                        [void]$failures.Add("$($isSheetName[0]) row '$($metricRow.Label)' has visible model periods but breaks into blank or placeholder cells after coverage begins.")
                    }
                }
            }
        }
    }

    if ($assumptionsSheetName.Count -gt 0 -and (@($driverCoverage.RevenueBuckets).Count -gt 0) -and ($driverCoverage.HasRevenueDrivers -or $driverCoverage.HasMarginDrivers)) {
        $assumptionRows = @($sheetContexts[$assumptionsSheetName[0]])
        $upsideGrowthRow = Get-FirstTitleRowNumber -Rows $assumptionRows -Pattern '(?i)upside growth|downside growth'
        $upsideMarginRow = Get-FirstTitleRowNumber -Rows $assumptionRows -Pattern '(?i)upside margin|downside margin'

        foreach ($bucket in @($driverCoverage.RevenueBuckets)) {
            $bucketVariants = Get-LabelVariants -Label $bucket
            $allMatches = @(Find-MatchingRows -Rows $assumptionRows -LabelVariants $bucketVariants)
            if ($allMatches.Count -eq 0) { continue }

            $growthMatches = @($allMatches | Where-Object {
                ($null -eq $upsideGrowthRow -or $_.RowNumber -lt $upsideGrowthRow)
            })

            $marginMatches = @($allMatches | Where-Object {
                ($null -eq $upsideMarginRow -or $_.RowNumber -lt $upsideMarginRow) -and
                ($null -eq $upsideGrowthRow -or $_.RowNumber -gt $upsideGrowthRow)
            })

            if ($driverCoverage.HasRevenueDrivers) {
                if ($growthMatches.Count -eq 0) {
                    [void]$failures.Add("$($assumptionsSheetName[0]) is missing a visible growth-driver row for driver-map bucket '$bucket'.")
                } else {
                    foreach ($growthRow in $growthMatches) {
                        if (-not (Test-RowHasVisibleCoverage -Row $growthRow)) {
                            [void]$failures.Add("$($assumptionsSheetName[0]) row '$($growthRow.Label)' should carry driver-map growth input for bucket '$bucket' but is blank or placeholder-only.")
                            break
                        }
                    }
                }
            }

            if ($driverCoverage.HasMarginDrivers) {
                if ($marginMatches.Count -eq 0) {
                    [void]$failures.Add("$($assumptionsSheetName[0]) is missing a visible margin-driver row for driver-map bucket '$bucket'.")
                } else {
                    foreach ($marginRow in $marginMatches) {
                        if (-not (Test-RowHasVisibleCoverage -Row $marginRow)) {
                            [void]$failures.Add("$($assumptionsSheetName[0]) row '$($marginRow.Label)' should carry driver-map margin input for bucket '$bucket' but is blank or placeholder-only.")
                            break
                        }
                    }
                }
            }
        }
    }

    if ($failures.Count -gt 0) {
        $sample = @($failures | Select-Object -First 6) -join " "
        Write-Block "Blocked by driver_breakdown_coverage_floor: $($target.display) leaves driver-map-backed revenue breakdown or margin/growth blocks as placeholders. $sample"
    }
}

exit 0
