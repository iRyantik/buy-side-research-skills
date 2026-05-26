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

    $uriPath = New-Object System.Uri([System.IO.Path]::GetFullPath($Path))
    $uriRoot = New-Object System.Uri(([System.IO.Path]::GetFullPath($Root).TrimEnd('\') + '\'))
    return ($uriRoot.MakeRelativeUri($uriPath).ToString() -replace '/', '\')
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

    return @($paths | Select-Object -Unique)
}

function Get-LastAssistantMessage {
    param($Payload)
    if ($null -eq $Payload) { return $null }
    return Get-StringProperty $Payload @("last_assistant_message", "lastAssistantMessage")
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
