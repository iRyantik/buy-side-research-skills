Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Get-HookPayload {
    param([string]$InputPath)

    $raw = ""
    if ($InputPath) {
        $raw = Get-Content -Raw -Encoding UTF8 -LiteralPath $InputPath
    } else {
        try { $raw = [Console]::In.ReadToEnd() } catch { $raw = "" }
    }

    if ([string]::IsNullOrWhiteSpace($raw)) { return $null }

    try {
        $convertCommand = Get-Command ConvertFrom-Json -ErrorAction Stop
        if ($convertCommand.Parameters.ContainsKey("Depth")) {
            return $raw | ConvertFrom-Json -Depth 30
        }
        return $raw | ConvertFrom-Json
    } catch {
        return $null
    }
}

function Write-Block {
    param([Parameter(Mandatory = $true)][string]$Message)
    [Console]::Error.WriteLine($Message)
    exit 2
}

function Get-WorkspaceRoot {
    param($Payload)
    if ($null -ne $Payload -and $Payload.PSObject.Properties.Name -contains "cwd" -and $Payload.cwd) {
        return [System.IO.Path]::GetFullPath([string]$Payload.cwd)
    }
    return [System.IO.Path]::GetFullPath((Get-Location).Path)
}

function Convert-ToWorkspacePath {
    param(
        [Parameter(Mandatory = $true)][string]$WorkspaceRoot,
        [Parameter(Mandatory = $true)][string]$Path
    )

    $clean = $Path.Trim().Trim('"').Trim("'")
    if ([string]::IsNullOrWhiteSpace($clean)) { return $null }
    if ([System.IO.Path]::IsPathRooted($clean)) { return [System.IO.Path]::GetFullPath($clean) }
    return [System.IO.Path]::GetFullPath((Join-Path $WorkspaceRoot $clean))
}

function Test-PathUnder {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Root
    )

    $fullPath = [System.IO.Path]::GetFullPath($Path)
    $fullRoot = [System.IO.Path]::GetFullPath($Root)
    if (-not $fullRoot.EndsWith([System.IO.Path]::DirectorySeparatorChar)) {
        $fullRoot += [System.IO.Path]::DirectorySeparatorChar
    }
    return $fullPath.StartsWith($fullRoot, [System.StringComparison]::OrdinalIgnoreCase)
}

function Get-RelativeDisplayPath {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Root
    )

    $separator = [System.IO.Path]::DirectorySeparatorChar
    $uriPath = New-Object System.Uri([System.IO.Path]::GetFullPath($Path))
    $uriRoot = New-Object System.Uri(([System.IO.Path]::GetFullPath($Root).TrimEnd($separator) + $separator))
    return ($uriRoot.MakeRelativeUri($uriPath).ToString() -replace '/', $separator)
}

function Get-ToolName {
    param($Payload)
    if ($null -eq $Payload) { return "" }
    if ($Payload.PSObject.Properties.Name -contains "tool_name") { return [string]$Payload.tool_name }
    if ($Payload.PSObject.Properties.Name -contains "toolName") { return [string]$Payload.toolName }
    return ""
}

function Get-ToolInput {
    param($Payload)
    if ($null -eq $Payload) { return $null }
    if ($Payload.PSObject.Properties.Name -contains "tool_input") { return $Payload.tool_input }
    if ($Payload.PSObject.Properties.Name -contains "toolInput") { return $Payload.toolInput }
    return $null
}

function Get-StringProperty {
    param($Object, [string[]]$Names)

    if ($null -eq $Object) { return $null }
    $propertyNames = @()
    if ($null -ne $Object.PSObject -and $null -ne $Object.PSObject.Properties) {
        $propertyNames = @($Object.PSObject.Properties | ForEach-Object { $_.Name })
    }
    foreach ($name in $Names) {
        if ($propertyNames -contains $name) {
            $value = $Object.$name
            if ($null -ne $value -and -not [string]::IsNullOrWhiteSpace([string]$value)) {
                return [string]$value
            }
        }
    }
    return $null
}

function Get-CommandText {
    param($Payload)
    $toolInput = Get-ToolInput $Payload
    return Get-StringProperty $toolInput @("command", "patch", "text")
}

function Get-ApplyPatchPaths {
    param([string]$Command)

    $paths = New-Object System.Collections.Generic.List[string]
    if ([string]::IsNullOrWhiteSpace($Command)) { return @() }
    foreach ($match in [regex]::Matches($Command, '(?m)^\*\*\* (?:Add|Update) File:\s+(.+?)\s*$')) {
        [void]$paths.Add($match.Groups[1].Value.Trim())
    }
    return @($paths | Select-Object -Unique)
}

function Get-RedirectionPaths {
    param([string]$Command)

    $paths = New-Object System.Collections.Generic.List[string]
    if ([string]::IsNullOrWhiteSpace($Command)) { return @() }
    foreach ($match in [regex]::Matches($Command, '(?:(?:>|>>)\s*)(["'']?)([^"''\s]+?\.(?:md|html|xlsx))\1')) {
        [void]$paths.Add($match.Groups[2].Value.Trim())
    }
    return @($paths | Select-Object -Unique)
}

function Get-EmbeddedArtifactPathsFromText {
    param([string]$Text)

    $paths = New-Object System.Collections.Generic.List[string]
    if ([string]::IsNullOrWhiteSpace($Text)) { return @() }

    foreach ($match in [regex]::Matches($Text, '\[[^\]]+\]\(([^)]+?\.(?:md|html|xlsx))\)')) {
        [void]$paths.Add($match.Groups[1].Value.Trim())
    }

    foreach ($match in [regex]::Matches($Text, '(?i)([A-Z]:\\[^<>\r\n\t"]+?\.xlsx)')) {
        [void]$paths.Add($match.Groups[1].Value.Trim())
    }

    foreach ($match in [regex]::Matches($Text, '(?i)(?:^|[\s(])((?:\./|\.\./|topics/|_models/)[^\s)]+?\.xlsx)(?:$|[\s)])')) {
        [void]$paths.Add($match.Groups[1].Value.Trim())
    }

    return @($paths | Select-Object -Unique)
}

function Get-CandidatePaths {
    param($Payload)

    $workspaceRoot = Get-WorkspaceRoot $Payload
    $toolInput = Get-ToolInput $Payload
    $paths = New-Object System.Collections.Generic.List[string]

    foreach ($propertyName in @("file_path", "path", "target_file", "destination", "output_path")) {
        $value = Get-StringProperty $toolInput @($propertyName)
        if ($value) {
            $resolved = Convert-ToWorkspacePath -WorkspaceRoot $workspaceRoot -Path $value
            if ($resolved) { [void]$paths.Add($resolved) }
        }
    }

    $command = Get-CommandText $Payload
    foreach ($path in (Get-ApplyPatchPaths -Command $command)) {
        $resolved = Convert-ToWorkspacePath -WorkspaceRoot $workspaceRoot -Path $path
        if ($resolved) { [void]$paths.Add($resolved) }
    }
    foreach ($path in (Get-RedirectionPaths -Command $command)) {
        $resolved = Convert-ToWorkspacePath -WorkspaceRoot $workspaceRoot -Path $path
        if ($resolved) { [void]$paths.Add($resolved) }
    }

    $lastMessage = Get-LastAssistantMessage $Payload
    foreach ($path in (Get-EmbeddedArtifactPathsFromText -Text $lastMessage)) {
        $resolved = Convert-ToWorkspacePath -WorkspaceRoot $workspaceRoot -Path $path
        if ($resolved) { [void]$paths.Add($resolved) }
    }

    return @($paths | Select-Object -Unique)
}

function Get-LastAssistantMessage {
    param($Payload)
    if ($null -eq $Payload) { return $null }
    return Get-StringProperty $Payload @("last_assistant_message", "lastAssistantMessage")
}

function Get-BooleanProperty {
    param($Object, [string[]]$Names)

    if ($null -eq $Object) { return $false }
    foreach ($name in $Names) {
        if ($Object.PSObject.Properties.Name -contains $name) {
            $value = $Object.$name
            if ($value -is [bool]) { return [bool]$value }
            if ($null -ne $value) {
                $text = ([string]$value).Trim()
                if ($text -match '^(?i:true|1|yes)$') { return $true }
                if ($text -match '^(?i:false|0|no)$') { return $false }
            }
        }
    }

    return $false
}

function Get-MarkdownTargets {
    param($Payload)

    $targets = New-Object System.Collections.Generic.List[object]
    $workspaceRoot = Get-WorkspaceRoot $Payload

    foreach ($path in (Get-CandidatePaths $Payload)) {
        if ($path -match '\.(md|html)$' -and (Test-Path -LiteralPath $path)) {
            [void]$targets.Add([pscustomobject]@{
                kind = "file"
                path = $path
                display = Get-RelativeDisplayPath -Path $path -Root $workspaceRoot
                text = Get-Content -Raw -Encoding UTF8 -LiteralPath $path
            })
        }
    }

    $lastMessage = Get-LastAssistantMessage $Payload
    if ([string]::IsNullOrWhiteSpace($lastMessage) -eq $false) {
        [void]$targets.Add([pscustomobject]@{
            kind = "inline"
            path = $null
            display = "last_assistant_message"
            text = [string]$lastMessage
        })
    }

    return $targets.ToArray()
}

function Get-WorkbookTargets {
    param($Payload)

    $targets = New-Object System.Collections.Generic.List[object]
    $workspaceRoot = Get-WorkspaceRoot $Payload

    foreach ($path in (Get-CandidatePaths $Payload)) {
        if ($path -match '\.xlsx$' -and (Test-Path -LiteralPath $path)) {
            $info = Get-XlsxWorkbookInfo -Path $path -WorkspaceRoot $workspaceRoot
            if ($null -ne $info) {
                [void]$targets.Add($info)
            }
        }
    }

    return $targets.ToArray()
}

function Get-WorkbookSearchText {
    param($Target)

    if ($null -eq $Target) { return "" }

    $sheetNames = @()
    if ($Target.PSObject.Properties.Name -contains "sheetNames") {
        $sheetNames = @($Target.sheetNames)
    }

    $sheetTexts = @()
    if ($Target.PSObject.Properties.Name -contains "sheets") {
        $sheetTexts = @($Target.sheets | ForEach-Object { [string]$_.Text })
    }

    return @(
        ($sheetNames -join "`n")
        [string]$Target.sharedStringsText
        ($sheetTexts -join "`n")
    ) -join "`n"
}

function Test-WorkbookTargetIdentity {
    param(
        [Parameter(Mandatory = $true)]$Target,
        [string]$PathLeafPattern,
        [string]$SearchPattern
    )

    if ($Target.kind -ne "workbook") { return $false }

    if ($Target.path -and $PathLeafPattern) {
        $leaf = [System.IO.Path]::GetFileName($Target.path)
        if ($leaf -match $PathLeafPattern) { return $true }
    }

    if ($SearchPattern) {
        $searchText = Get-WorkbookSearchText -Target $Target
        if ($searchText -match $SearchPattern) { return $true }
    }

    return $false
}

function Test-IsArtifactLikeText {
    param([string]$Text)

    if ([string]::IsNullOrWhiteSpace($Text)) { return $false }
    if ($Text.Length -ge 600) { return $true }
    if ($Text -match '(?m)^##\s+' -or $Text -match '(?m)^\|\s*.+\s*\|$') { return $true }
    return $false
}

function Get-ResourcesSectionText {
    param([string]$Text)

    if ([string]::IsNullOrWhiteSpace($Text)) { return $null }
    $match = [regex]::Match($Text, '(?is)^##\s*Resources\b(.*)$', [System.Text.RegularExpressions.RegexOptions]::Multiline)
    if (-not $match.Success) { return $null }
    return $match.Groups[1].Value.Trim()
}

function Get-BodyWithoutResources {
    param([string]$Text)

    if ([string]::IsNullOrWhiteSpace($Text)) { return "" }
    return ([regex]::Replace($Text, '(?is)^##\s*Resources\b.*$', '', [System.Text.RegularExpressions.RegexOptions]::Multiline)).Trim()
}

function Get-ShortAnchorMatches {
    param([string]$Text)

    $results = New-Object System.Collections.Generic.List[object]
    if ([string]::IsNullOrWhiteSpace($Text)) { return @() }

    $pattern = '\[((?:S|P|I|LBG)\d+)([^\]]*)\]\(([^)]+)\)'
    foreach ($match in [regex]::Matches($Text, $pattern)) {
        [void]$results.Add([pscustomobject]@{
            Code = $match.Groups[1].Value
            LabelSuffix = $match.Groups[2].Value
            Target = $match.Groups[3].Value.Trim()
            FullMatch = $match.Value
        })
    }

    return $results.ToArray()
}

function Get-ResourcesEntries {
    param([string]$ResourcesText)

    $results = New-Object System.Collections.Generic.List[object]
    if ([string]::IsNullOrWhiteSpace($ResourcesText)) { return @() }

    $pattern = '(?im)^\s*-\s*\[((?:S|P|I|LBG)\d+)([^\]]*)\]\(([^)]+)\)\s*=\s*(.*)$'
    foreach ($match in [regex]::Matches($ResourcesText, $pattern)) {
        [void]$results.Add([pscustomobject]@{
            Code = $match.Groups[1].Value
            LabelSuffix = $match.Groups[2].Value
            Target = $match.Groups[3].Value.Trim()
            Metadata = $match.Groups[4].Value.Trim()
            Line = $match.Value.Trim()
        })
    }

    return $results.ToArray()
}

function Test-IsValidSourceTarget {
    param([string]$Target)

    if ([string]::IsNullOrWhiteSpace($Target)) { return $false }

    $clean = $Target.Trim()
    if ($clean -match '^(?i:link|url)$') { return $false }
    if ($clean.StartsWith('#') -or $clean.StartsWith('?') -or $clean.StartsWith('&')) { return $false }

    $absoluteUri = $null
    if ([System.Uri]::TryCreate($clean, [System.UriKind]::Absolute, [ref]$absoluteUri)) {
        return $absoluteUri.Scheme -in @('http', 'https')
    }

    if ([System.IO.Path]::IsPathRooted($clean)) {
        try {
            [void][System.IO.Path]::GetFullPath($clean)
            return $true
        } catch {
            return $false
        }
    }

    if ($clean -match '^[A-Za-z][A-Za-z0-9+\.-]*:') {
        return $false
    }

    $invalidChars = [System.IO.Path]::GetInvalidPathChars()
    if ($clean.IndexOfAny($invalidChars) -ge 0) { return $false }

    $looksLikeRelativePath =
        ($clean -match '^[.]{1,2}[\\/]') -or
        ($clean -match '[\\/]') -or
        ($clean -match '^[^\\/:*?""<>|]+\.[A-Za-z0-9]{1,10}$')

    if (-not $looksLikeRelativePath) { return $false }

    try {
        [void][System.IO.Path]::GetFullPath((Join-Path (Get-Location).Path $clean))
        return $true
    } catch {
        return $false
    }
}

function Get-SourceContractState {
    param([string]$Text)

    $body = Get-BodyWithoutResources -Text $Text
    $resources = Get-ResourcesSectionText -Text $Text
    $bodyAnchors = @(Get-ShortAnchorMatches -Text $body)
    $resourceEntries = @(Get-ResourcesEntries -ResourcesText $resources)

    $resourceMap = @{}
    foreach ($entry in $resourceEntries) {
        if (-not $resourceMap.ContainsKey($entry.Code)) {
            $resourceMap[$entry.Code] = @()
        }
        $resourceMap[$entry.Code] += $entry
    }

    [pscustomobject]@{
        Body = $body
        Resources = $resources
        BodyAnchors = $bodyAnchors
        ResourceEntries = $resourceEntries
        ResourceMap = $resourceMap
    }
}

function Get-PrimaryHeading {
    param([string]$Text)

    if ([string]::IsNullOrWhiteSpace($Text)) { return $null }
    $match = [regex]::Match($Text, '(?im)^#\s+(.+?)\s*$')
    if (-not $match.Success) { return $null }
    return $match.Groups[1].Value.Trim()
}

function Test-MarkdownTargetIdentity {
    param(
        [Parameter(Mandatory = $true)]$Target,
        [string]$PathLeafPattern,
        [string]$HeadingPattern
    )

    if ($Target.kind -eq "file" -and $Target.path -and $PathLeafPattern) {
        $leaf = [System.IO.Path]::GetFileName($Target.path)
        if ($leaf -match $PathLeafPattern) { return $true }
    }

    if ($HeadingPattern) {
        $heading = Get-PrimaryHeading -Text ([string]$Target.text)
        if ($heading -and $heading -match $HeadingPattern) { return $true }
    }

    return $false
}

function Test-IsMarkdownTableSeparatorLine {
    param([string]$Line)

    if ([string]::IsNullOrWhiteSpace($Line)) { return $false }
    return $Line -match '^\s*\|?(?:\s*:?-{3,}:?\s*\|)+(?:\s*:?-{3,}:?\s*)\|?\s*$'
}

function Get-MarkdownTableColumnCount {
    param([string]$Line)

    if ([string]::IsNullOrWhiteSpace($Line)) { return 0 }

    $clean = $Line.Trim()
    if ($clean.StartsWith('|')) { $clean = $clean.Substring(1) }
    if ($clean.EndsWith('|')) { $clean = $clean.Substring(0, $clean.Length - 1) }
    if ([string]::IsNullOrWhiteSpace($clean)) { return 0 }

    return @($clean -split '(?<!\\)\|').Count
}

function Get-MarkdownPipeTables {
    param([string]$Text)

    $tables = New-Object System.Collections.Generic.List[object]
    if ([string]::IsNullOrWhiteSpace($Text)) { return @() }

    $lines = $Text -split "`r?`n"
    $index = 0
    while ($index -lt ($lines.Count - 1)) {
        $header = [string]$lines[$index]
        $separator = [string]$lines[$index + 1]

        if ($header -match '\|' -and (Test-IsMarkdownTableSeparatorLine -Line $separator)) {
            $blockLines = New-Object System.Collections.Generic.List[string]
            [void]$blockLines.Add($header)
            [void]$blockLines.Add($separator)

            $cursor = $index + 2
            while ($cursor -lt $lines.Count) {
                $line = [string]$lines[$cursor]
                if ([string]::IsNullOrWhiteSpace($line)) { break }
                if ($line -notmatch '\|') { break }
                [void]$blockLines.Add($line)
                $cursor += 1
            }

            [void]$tables.Add([pscustomobject]@{
                StartLine = $index + 1
                Lines = $blockLines.ToArray()
            })

            $index = $cursor
            continue
        }

        $index += 1
    }

    return $tables.ToArray()
}

function Test-IsTopicArtifactRootFile {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$WorkspaceRoot
    )

    $relative = (Get-RelativeDisplayPath -Path $Path -Root $WorkspaceRoot) -replace '\\', '/'
    $parts = $relative.Split('/')
    if ($parts.Length -ne 4) { return $false }
    return $parts[0] -eq "topics"
}

function Read-ZipEntryText {
    param(
        [Parameter(Mandatory = $true)]$Archive,
        [Parameter(Mandatory = $true)][string]$EntryPath
    )

    $entry = $Archive.GetEntry($EntryPath)
    if ($null -eq $entry) { return $null }

    $stream = $entry.Open()
    try {
        $reader = New-Object System.IO.StreamReader($stream, [System.Text.Encoding]::UTF8, $true)
        try {
            return $reader.ReadToEnd()
        } finally {
            $reader.Dispose()
        }
    } finally {
        $stream.Dispose()
    }
}

function Read-JsonFileIfPresent {
    param([Parameter(Mandatory = $true)][string]$Path)

    if (-not (Test-Path -LiteralPath $Path)) { return $null }
    $raw = Get-Content -Raw -Encoding UTF8 -LiteralPath $Path
    if ([string]::IsNullOrWhiteSpace($raw)) { return $null }

    $convertCommand = Get-Command ConvertFrom-Json -ErrorAction Stop
    if ($convertCommand.Parameters.ContainsKey("Depth")) {
        return $raw | ConvertFrom-Json -Depth 50
    }

    return $raw | ConvertFrom-Json
}

function Get-TopicRootFromWorkbookPath {
    param([Parameter(Mandatory = $true)][string]$WorkbookPath)

    $fullPath = [System.IO.Path]::GetFullPath($WorkbookPath)
    $directory = Split-Path -Parent $fullPath
    while (-not [string]::IsNullOrWhiteSpace($directory)) {
        $leaf = Split-Path -Leaf $directory
        if ($leaf -ieq "_models") {
            return Split-Path -Parent $directory
        }
        $parent = Split-Path -Parent $directory
        if ($parent -eq $directory) { break }
        $directory = $parent
    }

    return $null
}

function Get-ModelingFinancialDataInputs {
    param([Parameter(Mandatory = $true)][string]$WorkbookPath)

    $topicRoot = Get-TopicRootFromWorkbookPath -WorkbookPath $WorkbookPath
    if ([string]::IsNullOrWhiteSpace($topicRoot)) {
        return [pscustomobject]@{
            TopicRoot = $null
            FinancialDataInternal = $null
            ActualsResolvedPath = $null
            EvidencePackPath = $null
            ActualsResolved = $null
            EvidencePack = $null
        }
    }

    $internalDir = Join-Path $topicRoot "_cache/financial-data/internal"
    $actualsResolvedPath = Join-Path $internalDir "actuals-resolved.json"
    $evidencePackPath = Join-Path $internalDir "evidence-pack.json"

    return [pscustomobject]@{
        TopicRoot = $topicRoot
        FinancialDataInternal = $internalDir
        ActualsResolvedPath = $actualsResolvedPath
        EvidencePackPath = $evidencePackPath
        ActualsResolved = Read-JsonFileIfPresent -Path $actualsResolvedPath
        EvidencePack = Read-JsonFileIfPresent -Path $evidencePackPath
    }
}

function Get-ModelingDriverMapInputs {
    param([Parameter(Mandatory = $true)][string]$WorkbookPath)

    $topicRoot = Get-TopicRootFromWorkbookPath -WorkbookPath $WorkbookPath
    if ([string]::IsNullOrWhiteSpace($topicRoot)) {
        return [pscustomobject]@{
            TopicRoot = $null
            DriverMapInternal = $null
            DriverMapPath = $null
            DriverMap = $null
        }
    }

    $internalDir = Join-Path $topicRoot "_cache/driver-map/internal"
    $driverMapPath = Join-Path $internalDir "driver-map.json"

    return [pscustomobject]@{
        TopicRoot = $topicRoot
        DriverMapInternal = $internalDir
        DriverMapPath = $driverMapPath
        DriverMap = Read-JsonFileIfPresent -Path $driverMapPath
    }
}

function Test-IsWindowsHostPlatform {
    return [System.Runtime.InteropServices.RuntimeInformation]::IsOSPlatform([System.Runtime.InteropServices.OSPlatform]::Windows)
}

function Test-IsMacOSHostPlatform {
    return [System.Runtime.InteropServices.RuntimeInformation]::IsOSPlatform([System.Runtime.InteropServices.OSPlatform]::OSX)
}

function Convert-ExcelColumnNumberToLetters {
    param([Parameter(Mandatory = $true)][int]$ColumnNumber)

    $current = $ColumnNumber
    $letters = ""
    while ($current -gt 0) {
        $current -= 1
        $letters = [char](65 + ($current % 26)) + $letters
        $current = [math]::Floor($current / 26)
    }

    return $letters
}

function New-WorkbookSessionCellRecord {
    param(
        [Parameter(Mandatory = $true)][int]$Index,
        [Parameter(Mandatory = $true)][string]$Ref,
        $Value,
        [string]$Text,
        [string]$Formula,
        [bool]$HasFormula
    )

    $resolvedText = ""
    if (-not [string]::IsNullOrWhiteSpace($Text)) {
        $resolvedText = [string]$Text
    } elseif ($null -ne $Value) {
        $resolvedText = [string]$Value
    }

    return [pscustomobject]@{
        Index = $Index
        Ref = $Ref
        Text = $resolvedText.Trim()
        Value = $Value
        Formula = $Formula
        HasFormula = $HasFormula
    }
}

function ConvertTo-WorkbookSessionRows {
    param(
        [Parameter(Mandatory = $true)]$Worksheet,
        [Parameter(Mandatory = $true)]$UsedRange
    )

    $rows = New-Object System.Collections.Generic.List[object]
    $startRow = [int]$UsedRange.Row
    $startColumn = [int]$UsedRange.Column
    $rowCount = [int]$UsedRange.Rows.Count
    $columnCount = [int]$UsedRange.Columns.Count

    for ($rowOffset = 0; $rowOffset -lt $rowCount; $rowOffset += 1) {
        $cells = New-Object System.Collections.Generic.List[object]
        for ($columnOffset = 0; $columnOffset -lt $columnCount; $columnOffset += 1) {
            $rowIndex = $rowOffset + 1
            $columnIndex = $columnOffset + 1
            $cell = $UsedRange.Cells.Item($rowIndex, $columnIndex)
            try {
                $absoluteRow = $startRow + $rowOffset
                $absoluteColumn = $startColumn + $columnOffset
                $ref = "$(Convert-ExcelColumnNumberToLetters -ColumnNumber $absoluteColumn)$absoluteRow"
                $value = $null
                $text = ""
                $formula = $null
                $hasFormula = $false

                try { $value = $cell.Value2 } catch {}
                try { $text = [string]$cell.Text } catch {}
                try {
                    if ($cell.HasFormula) {
                        $hasFormula = $true
                        $formula = [string]$cell.Formula
                    }
                } catch {}

                [void]$cells.Add((New-WorkbookSessionCellRecord -Index $columnOffset -Ref $ref -Value $value -Text $text -Formula $formula -HasFormula $hasFormula))
            } finally {
                try { [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($cell) } catch {}
            }
        }

        $nonEmptyCells = @($cells | Where-Object {
            -not [string]::IsNullOrWhiteSpace([string]$_.Text) -or
            $_.HasFormula -or
            $null -ne $_.Value
        })
        $labelCell = $nonEmptyCells | Select-Object -First 1
        $labelText = if ($null -ne $labelCell) { [string]$labelCell.Text } else { "" }
        $resultCells = @()
        if ($null -ne $labelCell) {
            $resultCells = @($cells | Where-Object {
                $_.Index -gt $labelCell.Index -and (
                    -not [string]::IsNullOrWhiteSpace([string]$_.Text) -or
                    $_.HasFormula -or
                    $null -ne $_.Value
                )
            })
        }

        [void]$rows.Add([pscustomobject]@{
            SheetName = [string]$Worksheet.Name
            RowNumber = $startRow + $rowOffset
            Cells = $cells.ToArray()
            Label = ($labelText.Trim())
            ResultCells = $resultCells
            IsBlank = ($nonEmptyCells.Count -eq 0)
        })
    }

    return $rows.ToArray()
}

function Get-NativeExcelWorkbookSessionSnapshot {
    param(
        [Parameter(Mandatory = $true)][string]$Path
    )

    if (-not (Test-Path -LiteralPath $Path)) {
        return [pscustomobject]@{
            Attempted = $false
            Succeeded = $false
            Method = "missing-path"
            Message = "Workbook path does not exist."
            Sheets = @()
        }
    }

    if (Test-IsWindowsHostPlatform) {
        $excel = $null
        $workbook = $null
        try {
            $excel = New-Object -ComObject Excel.Application
            $excel.Visible = $false
            $excel.DisplayAlerts = $false
            $excel.AskToUpdateLinks = $false
            $excel.EnableEvents = $false
            $excel.ScreenUpdating = $false
            try { $excel.AutomationSecurity = 3 } catch {}

            $workbook = $excel.Workbooks.Open($Path, $false, $false)
            try { $workbook.ForceFullCalculation = $true } catch {}
            try { $workbook.RefreshAll() } catch {}
            try { $excel.CalculateFullRebuild() } catch { $excel.Calculate() }
            try { $excel.CalculateUntilAsyncQueriesDone() } catch {}

            $sheetRecords = New-Object System.Collections.Generic.List[object]
            $preferredSheets = @()
            foreach ($worksheet in @($workbook.Worksheets)) {
                try {
                    if ([string]$worksheet.Name -match '(?i)(checks|audit checks|validation|model checks|master checks|error checks|integrity|sanity)') {
                        $preferredSheets += $worksheet
                    }
                } catch {
                    try { [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($worksheet) } catch {}
                }
            }

            $worksheetsToRead = if ($preferredSheets.Count -gt 0) { @($preferredSheets) } else { @($workbook.Worksheets) }
            foreach ($worksheet in $worksheetsToRead) {
                $usedRange = $null
                try {
                    $usedRange = $worksheet.UsedRange
                    if ($null -eq $usedRange) { continue }
                    $rows = @(ConvertTo-WorkbookSessionRows -Worksheet $worksheet -UsedRange $usedRange)
                    [void]$sheetRecords.Add([pscustomobject]@{
                        Name = [string]$worksheet.Name
                        Rows = $rows
                    })
                } finally {
                    if ($null -ne $usedRange) {
                        try { [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($usedRange) } catch {}
                    }
                    try { [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($worksheet) } catch {}
                }
            }

            $workbook.Save()
            return [pscustomobject]@{
                Attempted = $true
                Succeeded = $true
                Method = "excel-com"
                Message = "Workbook recalculated and inspected with Excel COM."
                Sheets = $sheetRecords.ToArray()
            }
        } catch {
            return [pscustomobject]@{
                Attempted = $true
                Succeeded = $false
                Method = "excel-com"
                Message = $_.Exception.Message
                Sheets = @()
            }
        } finally {
            if ($null -ne $workbook) {
                try { $workbook.Close($true) } catch {}
                try { [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($workbook) } catch {}
            }
            if ($null -ne $excel) {
                try { $excel.Quit() } catch {}
                try { [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($excel) } catch {}
            }
            [System.GC]::Collect()
            [System.GC]::WaitForPendingFinalizers()
        }
    }

    if (Test-IsMacOSHostPlatform) {
        $osascript = Get-Command osascript -ErrorAction SilentlyContinue
        if ($null -eq $osascript) {
            return [pscustomobject]@{
                Attempted = $false
                Succeeded = $false
                Method = "excel-applescript"
                Message = "osascript not available."
                Sheets = @()
            }
        }

        $tempJsonPath = Join-Path ([System.IO.Path]::GetTempPath()) ("codex-excel-session-" + [System.Guid]::NewGuid().ToString("N") + ".json")
        $escapedPath = $Path.Replace('\', '\\').Replace('"', '\"')
        $escapedJsonPath = $tempJsonPath.Replace('\', '\\').Replace('"', '\"')
        $script = @"
var excel = Application('Microsoft Excel');
var se = Application('System Events');
excel.includeStandardAdditions = true;
var workbookPath = "$escapedPath";
var outputPath = "$escapedJsonPath";

function rowRecord(sheetName, rowNumber, cells) {
  var nonEmpty = cells.filter(function (cell) {
    return (cell.Text && cell.Text.trim() !== '') || cell.HasFormula || cell.Value !== null;
  });
  var labelCell = nonEmpty.length > 0 ? nonEmpty[0] : null;
  var resultCells = labelCell ? cells.filter(function (cell) {
    return cell.Index > labelCell.Index && ((cell.Text && cell.Text.trim() !== '') || cell.HasFormula || cell.Value !== null);
  }) : [];
  return {
    SheetName: sheetName,
    RowNumber: rowNumber,
    Cells: cells,
    Label: labelCell ? String(labelCell.Text || '').trim() : '',
    ResultCells: resultCells,
    IsBlank: nonEmpty.length === 0
  };
}

var workbook = excel.open(Path(workbookPath));
excel.calculate();
workbook.save();

var sheets = [];
for (var i = 0; i < workbook.worksheets.length; i++) {
  var sheet = workbook.worksheets[i];
  var name = sheet.name();
  if (!/(checks|audit checks|validation|model checks|master checks|error checks|integrity|sanity)/i.test(name)) {
    continue;
  }
  var usedRange = sheet.usedRange();
  var rowCount = Number(usedRange.rowCount());
  var columnCount = Number(usedRange.columnCount());
  var startRow = Number(usedRange.rowIndex());
  var startColumn = Number(usedRange.columnIndex());
  var rows = [];
  for (var r = 0; r < rowCount; r++) {
    var cells = [];
    for (var c = 0; c < columnCount; c++) {
      var cell = sheet.cells.item(startRow + r, startColumn + c);
      var formula = '';
      try { formula = String(cell.formula()); } catch (e) {}
      var value = null;
      try { value = cell.value(); } catch (e) {}
      var text = '';
      if (value !== null && value !== undefined) { text = String(value); }
      cells.push({
        Index: c,
        Ref: '',
        Text: text.trim(),
        Value: value,
        Formula: formula,
        HasFormula: !!formula
      });
    }
    rows.push(rowRecord(name, startRow + r, cells));
  }
  sheets.push({ Name: name, Rows: rows });
}

workbook.close({ saving: 'yes' });
excel.quit();
excel.doShellScript('python3 - <<''PY''\nimport json, pathlib\npath = pathlib.Path(r''' + outputPath + r''')\npath.write_text(json.dumps({"Sheets": ' + JSON.stringify(sheets) + r'}, ensure_ascii=False), encoding="utf-8")\nPY');
"@

        try {
            & $osascript.Source -l JavaScript -e $script | Out-Null
            if (-not (Test-Path -LiteralPath $tempJsonPath)) {
                return [pscustomobject]@{
                    Attempted = $true
                    Succeeded = $false
                    Method = "excel-applescript"
                    Message = "Microsoft Excel automation completed but returned no session snapshot."
                    Sheets = @()
                }
            }

            $snapshot = Get-Content -Raw -Encoding UTF8 -LiteralPath $tempJsonPath | ConvertFrom-Json -Depth 20
            return [pscustomobject]@{
                Attempted = $true
                Succeeded = $true
                Method = "excel-applescript"
                Message = "Workbook recalculated and inspected with Microsoft Excel."
                Sheets = @($snapshot.Sheets)
            }
        } catch {
            return [pscustomobject]@{
                Attempted = $true
                Succeeded = $false
                Method = "excel-applescript"
                Message = $_.Exception.Message
                Sheets = @()
            }
        } finally {
            if (Test-Path -LiteralPath $tempJsonPath) {
                Remove-Item -LiteralPath $tempJsonPath -Force -ErrorAction SilentlyContinue
            }
        }
    }

    return [pscustomobject]@{
        Attempted = $false
        Succeeded = $false
        Method = "unsupported-host"
        Message = "No native Excel automation path for this host."
        Sheets = @()
    }
}

function Invoke-NativeExcelWorkbookRecalc {
    param(
        [Parameter(Mandatory = $true)][string]$Path
    )

    if (-not (Test-Path -LiteralPath $Path)) {
        return [pscustomobject]@{
            Attempted = $false
            Succeeded = $false
            Method = "missing-path"
            Message = "Workbook path does not exist."
        }
    }

    if (Test-IsWindowsHostPlatform) {
        $excel = $null
        $workbook = $null
        try {
            $excel = New-Object -ComObject Excel.Application
            $excel.Visible = $false
            $excel.DisplayAlerts = $false
            $excel.AskToUpdateLinks = $false
            $excel.EnableEvents = $false
            $excel.ScreenUpdating = $false
            try {
                $excel.AutomationSecurity = 3
            } catch {}
            $workbook = $excel.Workbooks.Open($Path, $false, $false)
            try { $workbook.ForceFullCalculation = $true } catch {}
            try { $workbook.RefreshAll() } catch {}
            try { $excel.CalculateFullRebuild() } catch { $excel.Calculate() }
            try { $excel.CalculateUntilAsyncQueriesDone() } catch {}
            $workbook.Save()
            return [pscustomobject]@{
                Attempted = $true
                Succeeded = $true
                Method = "excel-com"
                Message = "Workbook recalculated with Excel COM."
            }
        } catch {
            return [pscustomobject]@{
                Attempted = $true
                Succeeded = $false
                Method = "excel-com"
                Message = $_.Exception.Message
            }
        } finally {
            if ($null -ne $workbook) {
                try { $workbook.Close($true) } catch {}
                try { [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($workbook) } catch {}
            }
            if ($null -ne $excel) {
                try { $excel.Quit() } catch {}
                try { [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($excel) } catch {}
            }
            [System.GC]::Collect()
            [System.GC]::WaitForPendingFinalizers()
        }
    }

    if (Test-IsMacOSHostPlatform) {
        $osascript = Get-Command osascript -ErrorAction SilentlyContinue
        if ($null -eq $osascript) {
            return [pscustomobject]@{
                Attempted = $false
                Succeeded = $false
                Method = "excel-applescript"
                Message = "osascript not available."
            }
        }

        $escapedPath = $Path.Replace('\', '\\').Replace('"', '\"')
        $script = @(
            'tell application "Microsoft Excel"',
            "set wb to open POSIX file ""$escapedPath""",
            'calculate now',
            'save workbook wb',
            'close workbook wb saving yes',
            'quit',
            'end tell'
        ) -join "`n"

        try {
            & $osascript.Source -e $script | Out-Null
            return [pscustomobject]@{
                Attempted = $true
                Succeeded = $true
                Method = "excel-applescript"
                Message = "Workbook recalculated with Microsoft Excel."
            }
        } catch {
            return [pscustomobject]@{
                Attempted = $true
                Succeeded = $false
                Method = "excel-applescript"
                Message = $_.Exception.Message
            }
        }
    }

    return [pscustomobject]@{
        Attempted = $false
        Succeeded = $false
        Method = "unsupported-host"
        Message = "No native Excel automation path for this host."
    }
}

function Resolve-XlsxEntryPath {
    param([Parameter(Mandatory = $true)][string]$Target)

    $clean = ($Target -replace '\\', '/').Trim()
    if ($clean.StartsWith('/')) { $clean = $clean.TrimStart('/') }
    if ($clean.StartsWith('xl/')) { return $clean }
    return "xl/$clean"
}

function Get-XlsxWorkbookInfo {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$WorkspaceRoot
    )

    Add-Type -AssemblyName System.IO.Compression.FileSystem | Out-Null

    $archive = [System.IO.Compression.ZipFile]::OpenRead($Path)
    try {
        $workbookText = Read-ZipEntryText -Archive $archive -EntryPath 'xl/workbook.xml'
        if ([string]::IsNullOrWhiteSpace($workbookText)) { return $null }
        $relsText = Read-ZipEntryText -Archive $archive -EntryPath 'xl/_rels/workbook.xml.rels'
        $sharedStringsText = Read-ZipEntryText -Archive $archive -EntryPath 'xl/sharedStrings.xml'

        [xml]$workbookXml = $workbookText
        [xml]$relsXml = if ([string]::IsNullOrWhiteSpace($relsText)) { '<Relationships />' } else { $relsText }

        $relationshipMap = @{}
        foreach ($rel in $relsXml.DocumentElement.ChildNodes) {
            if ($rel.Attributes['Id'] -and $rel.Attributes['Target']) {
                $relationshipMap[$rel.Attributes['Id'].Value] = Resolve-XlsxEntryPath -Target $rel.Attributes['Target'].Value
            }
        }

        $sheetInfos = New-Object System.Collections.Generic.List[object]
        foreach ($sheet in $workbookXml.SelectNodes("/*[local-name()='workbook']/*[local-name()='sheets']/*[local-name()='sheet']")) {
            $sheetName = $sheet.Attributes['name'].Value
            $relId = $null
            foreach ($attr in $sheet.Attributes) {
                if ($attr.LocalName -eq 'id') { $relId = $attr.Value; break }
            }
            if (-not $relId -or -not $relationshipMap.ContainsKey($relId)) { continue }
            $entryPath = $relationshipMap[$relId]
            $sheetText = Read-ZipEntryText -Archive $archive -EntryPath $entryPath
            if ([string]::IsNullOrWhiteSpace($sheetText)) { continue }
            $formulaCount = ([regex]::Matches($sheetText, '<f(?:\s|>)')).Count
            $cellCount = ([regex]::Matches($sheetText, '<c\b')).Count
            [void]$sheetInfos.Add([pscustomobject]@{
                Name = $sheetName
                EntryPath = $entryPath
                Text = $sheetText
                FormulaCount = $formulaCount
                CellCount = $cellCount
            })
        }

        return [pscustomobject]@{
            kind = "workbook"
            path = $Path
            display = Get-RelativeDisplayPath -Path $Path -Root $WorkspaceRoot
            sharedStringsText = [string]$sharedStringsText
            sheets = $sheetInfos.ToArray()
            sheetNames = @($sheetInfos | ForEach-Object { $_.Name })
        }
    } finally {
        $archive.Dispose()
    }
}
