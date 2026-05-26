param(
    [string]$WorkspacePath = (Get-Location).Path,
    [switch]$SmokeTest
)

$ErrorActionPreference = "Stop"

$Utf8NoBom = New-Object System.Text.UTF8Encoding($false)

function Write-Utf8NoBomFile {
    param([string]$Path, [string]$Content)
    [System.IO.File]::WriteAllText($Path, $Content, $Utf8NoBom)
}

function Convert-ToFullPath {
    param([string]$Path)

    if ([System.IO.Path]::IsPathRooted($Path)) {
        return [System.IO.Path]::GetFullPath($Path)
    }

    return [System.IO.Path]::GetFullPath((Join-Path (Get-Location) $Path))
}

function Get-ReferencedHookPaths {
    param(
        [object]$JsonObject,
        [string]$WorkspaceRoot
    )

    $results = New-Object System.Collections.Generic.List[string]
    $json = $JsonObject | ConvertTo-Json -Depth 20
    $matches = [regex]::Matches($json, '\.claude/hooks/[^"\s)]+\.ps1')
    foreach ($match in $matches) {
        $relative = Convert-ToPlatformPath -Path $match.Value
        $full = Join-Path $WorkspaceRoot $relative
        if (-not $results.Contains($full)) {
            [void]$results.Add($full)
        }
    }
    $templateMatches = [regex]::Matches($json, '\{\{HOOK_RUNNER\}\}\s+([^\s"]+\.ps1)')
    foreach ($match in $templateMatches) {
        $relative = Convert-ToPlatformPath -Path $match.Groups[1].Value
        $full = Join-Path $WorkspaceRoot $relative
        if (-not $results.Contains($full)) {
            [void]$results.Add($full)
        }
    }
    return @($results)
}

function Convert-FromJsonCompat {
    param([string]$RawJson)

    $convertCommand = Get-Command ConvertFrom-Json -ErrorAction Stop
    if ($convertCommand.Parameters.ContainsKey("Depth")) {
        return $RawJson | ConvertFrom-Json -Depth 20
    }
    return $RawJson | ConvertFrom-Json
}

function Get-RegistryFiles {
    param([string]$RegistryPath)

    $files = New-Object System.Collections.Generic.List[string]
    foreach ($line in (Get-Content -Encoding UTF8 -LiteralPath $RegistryPath)) {
        if ($line -match '^\s*file:\s*([^\s#]+)\s*$') {
            [void]$files.Add($Matches[1])
        }
    }
    return @($files)
}

function Invoke-HookSmokeTest {
    param(
        [string]$HookPath,
        [string]$PayloadJson,
        [string]$WorkspaceRoot
    )

    $temp = [System.IO.Path]::GetTempFileName()
    try {
        [System.IO.File]::WriteAllText($temp, $PayloadJson, $Utf8NoBom)
        Invoke-HookThroughLauncher -HookPath $HookPath -InputPath $temp -WorkspaceRoot $WorkspaceRoot | Out-Null
        if ($LASTEXITCODE -ne 0) {
            throw "Smoke test failed for $HookPath with exit code $LASTEXITCODE"
        }
    } finally {
        Remove-Item -LiteralPath $temp -Force -ErrorAction SilentlyContinue
    }
}

function Invoke-HookSmokeFailureTest {
    param(
        [string]$HookPath,
        [string]$PayloadJson,
        [string]$ExpectedMessage,
        [string]$WorkspaceRoot
    )

    $temp = [System.IO.Path]::GetTempFileName()
    $stdoutPath = [System.IO.Path]::GetTempFileName()
    $stderrPath = [System.IO.Path]::GetTempFileName()
    try {
        [System.IO.File]::WriteAllText($temp, $PayloadJson, $Utf8NoBom)
        $process = Start-HookLauncherProcess -HookPath $HookPath -InputPath $temp -WorkspaceRoot $WorkspaceRoot -StdoutPath $stdoutPath -StderrPath $stderrPath
        if ($process.ExitCode -eq 0) {
            throw "Smoke failure test unexpectedly passed for $HookPath"
        }
        $joined = @(
            Get-Content -Raw -LiteralPath $stdoutPath -ErrorAction SilentlyContinue
            Get-Content -Raw -LiteralPath $stderrPath -ErrorAction SilentlyContinue
        ) -join "`n"
        if ($joined -notmatch [regex]::Escape($ExpectedMessage)) {
            throw "Smoke failure test for $HookPath did not emit expected message fragment: $ExpectedMessage"
        }
    } finally {
        Remove-Item -LiteralPath $temp -Force -ErrorAction SilentlyContinue
        Remove-Item -LiteralPath $stdoutPath -Force -ErrorAction SilentlyContinue
        Remove-Item -LiteralPath $stderrPath -Force -ErrorAction SilentlyContinue
    }
}

function Test-IsWindowsHost {
    return [System.IO.Path]::DirectorySeparatorChar -eq '\'
}

function Convert-ToPlatformPath {
    param([string]$Path)

    if (Test-IsWindowsHost) {
        return $Path -replace '/', '\'
    }

    return $Path -replace '\\', '/'
}

function Get-HookLauncherPath {
    param([string]$WorkspaceRoot)

    if (Test-IsWindowsHost) {
        return Join-Path $WorkspaceRoot ".claude/hooks/run-hook.cmd"
    }

    return Join-Path $WorkspaceRoot ".claude/hooks/run-hook.sh"
}

function Invoke-HookThroughLauncher {
    param(
        [string]$HookPath,
        [string]$InputPath,
        [string]$WorkspaceRoot
    )

    $launcherPath = Get-HookLauncherPath -WorkspaceRoot $WorkspaceRoot
    if (Test-IsWindowsHost) {
        & $launcherPath $HookPath -InputPath $InputPath
        return
    }

    & sh $launcherPath $HookPath -InputPath $InputPath
}

function Start-HookLauncherProcess {
    param(
        [string]$HookPath,
        [string]$InputPath,
        [string]$WorkspaceRoot,
        [string]$StdoutPath,
        [string]$StderrPath
    )

    $launcherPath = Get-HookLauncherPath -WorkspaceRoot $WorkspaceRoot
    if (Test-IsWindowsHost) {
        return Start-Process -FilePath $launcherPath -ArgumentList @(
            $HookPath,
            "-InputPath", $InputPath
        ) -Wait -PassThru -NoNewWindow -RedirectStandardOutput $StdoutPath -RedirectStandardError $StderrPath
    }

    return Start-Process -FilePath "sh" -ArgumentList @(
        $launcherPath,
        $HookPath,
        "-InputPath", $InputPath
    ) -Wait -PassThru -NoNewWindow -RedirectStandardOutput $StdoutPath -RedirectStandardError $StderrPath
}

function New-SmokeWorkbook {
    param(
        [string]$Path,
        [string[]]$SheetNames,
        [string[]]$SharedStrings,
        [hashtable]$SheetXmlByName = @{}
    )

    Add-Type -AssemblyName System.IO.Compression | Out-Null
    Add-Type -AssemblyName System.IO.Compression.FileSystem | Out-Null
    $parent = Split-Path -Parent $Path
    if ($parent -and -not (Test-Path -LiteralPath $parent)) {
        New-Item -ItemType Directory -Path $parent -Force | Out-Null
    }
    if (Test-Path -LiteralPath $Path) {
        Remove-Item -LiteralPath $Path -Force
    }

    $stream = [System.IO.File]::Open($Path, [System.IO.FileMode]::CreateNew)
    try {
        $archive = New-Object System.IO.Compression.ZipArchive($stream, [System.IO.Compression.ZipArchiveMode]::Create, $false)
        try {
            $sheetsXml = New-Object System.Text.StringBuilder
            $relsXml = New-Object System.Text.StringBuilder
            for ($i = 0; $i -lt $SheetNames.Count; $i++) {
                $sheetId = $i + 1
                $sheetName = [System.Security.SecurityElement]::Escape($SheetNames[$i])
                [void]$sheetsXml.Append("<sheet name=`"$sheetName`" sheetId=`"$sheetId`" r:id=`"rId$sheetId`" />")
                [void]$relsXml.Append("<Relationship Id=`"rId$sheetId`" Type=`"http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet`" Target=`"worksheets/sheet$sheetId.xml`" />")
            }

            $workbookXml = "<?xml version=`"1.0`" encoding=`"UTF-8`"?><workbook xmlns=`"http://schemas.openxmlformats.org/spreadsheetml/2006/main`" xmlns:r=`"http://schemas.openxmlformats.org/officeDocument/2006/relationships`"><sheets>$($sheetsXml.ToString())</sheets></workbook>"
            $workbookRelsXml = "<?xml version=`"1.0`" encoding=`"UTF-8`"?><Relationships xmlns=`"http://schemas.openxmlformats.org/package/2006/relationships`">$($relsXml.ToString())</Relationships>"

            $sharedItems = @($SharedStrings | ForEach-Object {
                "<si><t>$([System.Security.SecurityElement]::Escape($_))</t></si>"
            }) -join ""
            $sharedStringsXml = "<?xml version=`"1.0`" encoding=`"UTF-8`"?><sst xmlns=`"http://schemas.openxmlformats.org/spreadsheetml/2006/main`" count=`"$($SharedStrings.Count)`" uniqueCount=`"$($SharedStrings.Count)`">$sharedItems</sst>"

            foreach ($entrySpec in @(
                @{ Path = "xl/workbook.xml"; Content = $workbookXml }
                @{ Path = "xl/_rels/workbook.xml.rels"; Content = $workbookRelsXml }
                @{ Path = "xl/sharedStrings.xml"; Content = $sharedStringsXml }
            )) {
                $entry = $archive.CreateEntry($entrySpec.Path)
                $writer = New-Object System.IO.StreamWriter($entry.Open(), [System.Text.UTF8Encoding]::new($false))
                try { $writer.Write($entrySpec.Content) } finally { $writer.Dispose() }
            }

            for ($i = 0; $i -lt $SheetNames.Count; $i++) {
                $sheetName = $SheetNames[$i]
                $sheetXml = $SheetXmlByName[$sheetName]
                if ([string]::IsNullOrWhiteSpace($sheetXml)) {
                    $sheetXml = "<?xml version=`"1.0`" encoding=`"UTF-8`"?><worksheet xmlns=`"http://schemas.openxmlformats.org/spreadsheetml/2006/main`"><sheetData/></worksheet>"
                }
                $entry = $archive.CreateEntry("xl/worksheets/sheet$($i + 1).xml")
                $writer = New-Object System.IO.StreamWriter($entry.Open(), [System.Text.UTF8Encoding]::new($false))
                try { $writer.Write($sheetXml) } finally { $writer.Dispose() }
            }
        } finally {
            $archive.Dispose()
        }
    } finally {
        $stream.Dispose()
    }
}

$workspaceRoot = Convert-ToFullPath $WorkspacePath
$claudeSettings = Join-Path $workspaceRoot ".claude/settings.json"
$codexHooks = Join-Path $workspaceRoot ".codex/hooks.json"
$hooksRoot = Join-Path $workspaceRoot ".claude/hooks"
$commonHook = Join-Path $hooksRoot "_hook_common.ps1"
$hookLauncherCmd = Join-Path $hooksRoot "run-hook.cmd"
$hookLauncherSh = Join-Path $hooksRoot "run-hook.sh"
$registryPath = Join-Path $hooksRoot "hooks.registry.yaml"

foreach ($required in @($claudeSettings, $codexHooks, $hooksRoot, $commonHook, $hookLauncherCmd, $hookLauncherSh, $registryPath)) {
    if (-not (Test-Path -LiteralPath $required)) {
        throw "Missing runtime asset: $required"
    }
}

$claudeRaw = Get-Content -Raw -Encoding UTF8 -LiteralPath $claudeSettings
$codexRaw = Get-Content -Raw -Encoding UTF8 -LiteralPath $codexHooks
if ($claudeRaw -match 'powershell -NoProfile -ExecutionPolicy Bypass -File' -or $codexRaw -match 'powershell -NoProfile -ExecutionPolicy Bypass -Command') {
    throw "Hook adapter config still hardcodes powershell; expected launcher-based commands."
}

$claudeJson = Convert-FromJsonCompat -RawJson $claudeRaw
$codexJson = Convert-FromJsonCompat -RawJson $codexRaw

$adapterPaths = @(
    (Get-ReferencedHookPaths -JsonObject $claudeJson -WorkspaceRoot $workspaceRoot)
    (Get-ReferencedHookPaths -JsonObject $codexJson -WorkspaceRoot $workspaceRoot)
) | Select-Object -Unique

foreach ($path in $adapterPaths) {
    if (-not (Test-Path -LiteralPath $path)) {
        throw "Adapter references missing hook file: $path"
    }
}

$registryFiles = Get-RegistryFiles -RegistryPath $registryPath
if ($registryFiles.Count -eq 0) {
    throw "hooks.registry.yaml did not yield any file entries."
}

$registryFullPaths = @()
foreach ($relativeFile in $registryFiles) {
    $full = Join-Path $hooksRoot (Convert-ToPlatformPath -Path $relativeFile)
    $registryFullPaths += $full
    if (-not (Test-Path -LiteralPath $full)) {
        throw "Registry references missing hook file: $full"
    }
}

foreach ($registryPathFull in $registryFullPaths) {
    if ($adapterPaths -notcontains $registryPathFull) {
        throw "Registry hook is not referenced by any adapter: $registryPathFull"
    }
}

foreach ($adapterPath in $adapterPaths) {
    if ($registryFullPaths -notcontains $adapterPath -and -not $adapterPath.EndsWith("_hook_common.ps1")) {
        throw "Adapter hook is missing from registry: $adapterPath"
    }
}

if ($SmokeTest) {
    $markdownPath = Join-Path $workspaceRoot "runtime-smoke.md"
    $payload = @{
        cwd = $workspaceRoot
        tool_name = "Write"
        transcript_path = $markdownPath
        last_assistant_message = "## Verdict`nSource-backed statement. [S1](https://example.com)`n`n## Resources`n- [S1](https://example.com) = web | sample | as-of | note"
    } | ConvertTo-Json -Depth 10

    Invoke-HookSmokeTest -HookPath (Join-Path $hooksRoot "global/source_contract.ps1") -PayloadJson $payload -WorkspaceRoot $workspaceRoot
    Invoke-HookSmokeTest -HookPath (Join-Path $hooksRoot "global/subagent_protocol.ps1") -PayloadJson (@{
        cwd = $workspaceRoot
        last_assistant_message = "claim:`n- sample"
    } | ConvertTo-Json -Depth 10) -WorkspaceRoot $workspaceRoot
    Invoke-HookSmokeTest -HookPath (Join-Path $hooksRoot "global/workspace_guard.ps1") -PayloadJson (@{
        cwd = $workspaceRoot
        tool_name = "Write"
        transcript_path = (Join-Path $workspaceRoot "topics/company/sample/2026-01-01-stock-quickread.md")
    } | ConvertTo-Json -Depth 10) -WorkspaceRoot $workspaceRoot
    Invoke-HookSmokeTest -HookPath (Join-Path $hooksRoot "provider/market_snapshot_source_boundary.ps1") -PayloadJson (@{
        cwd = $workspaceRoot
        tool_name = "Write"
        transcript_path = (Join-Path $workspaceRoot "topics/company/sample/2026-01-01-stock-quickread.md")
        last_assistant_message = @"
# Stock Quickread

以下标记为 internet source 的字段为本地 cache 缺失后的公开网页 fallback，不等同于公司披露原文。

## 1. Snapshot

| Field | Value | Ev |
|---|---|---|
| market_quote | 100 | [I1](https://example.com/quote) |

## Resources
- [I1](https://example.com/quote) = internet source | Example Quote Provider | as-of 2026-05-26 | fallback reason: local market snapshot cache unavailable
"@
    } | ConvertTo-Json -Depth 10) -WorkspaceRoot $workspaceRoot
    Invoke-HookSmokeTest -HookPath (Join-Path $hooksRoot "global/source_contract.ps1") -PayloadJson (@{
        cwd = $workspaceRoot
        tool_name = "Write"
        transcript_path = $markdownPath
        last_assistant_message = "## Verdict`nEvidence cache snapshot. [I1](topics/company/sample/evidence/quote.pdf)`n`n## Resources`n- [I1](topics/company/sample/evidence/quote.pdf) = local file | sample cache | as-of 2026-05-26 | note"
    } | ConvertTo-Json -Depth 10) -WorkspaceRoot $workspaceRoot
    Invoke-HookSmokeTest -HookPath (Join-Path $hooksRoot "global/table_render_integrity.ps1") -PayloadJson (@{
        cwd = $workspaceRoot
        tool_name = "Write"
        transcript_path = $markdownPath
        last_assistant_message = @"
# Table Sample

| Field | Value | Ev |
|---|---|---|
| revenue | 10 | [S1](https://example.com/revenue) |

## Resources
- [S1](https://example.com/revenue) = web | sample | as-of 2026-05-26 | note
"@
    } | ConvertTo-Json -Depth 10) -WorkspaceRoot $workspaceRoot
    Invoke-HookSmokeTest -HookPath (Join-Path $hooksRoot "provider/disclosure_fact_source_boundary.ps1") -PayloadJson (@{
        cwd = $workspaceRoot
        tool_name = "Write"
        transcript_path = (Join-Path $workspaceRoot "topics/company/sample/2026-01-01-information-impact.md")
        last_assistant_message = @"
# Information Impact

## Impact

| Field | Value | Ev |
|---|---|---|
| market_reaction | shares moved +4% | [I1](https://example.com/quote) |

## Resources
- [I1](https://example.com/quote) = internet source | Example quote page | as-of 2026-05-26 | fallback reason: local market snapshot cache unavailable
"@
    } | ConvertTo-Json -Depth 10) -WorkspaceRoot $workspaceRoot
    Invoke-HookSmokeTest -HookPath (Join-Path $hooksRoot "narrative/next_step_anchored_facts_only.ps1") -PayloadJson (@{
        cwd = $workspaceRoot
        tool_name = "Write"
        transcript_path = (Join-Path $workspaceRoot "topics/company/sample/2026-01-01-next-step.md")
        last_assistant_message = @"
# Next Step

- Highest-leverage next question: Did management guide gross margin above 35%? [S1](https://example.com/guidance)

## Resources
- [S1](https://example.com/guidance) = primary public | earnings call | as-of 2026-05-26 | note
"@
    } | ConvertTo-Json -Depth 10) -WorkspaceRoot $workspaceRoot
    Invoke-HookSmokeTest -HookPath (Join-Path $hooksRoot "narrative/pair_structure_floor.ps1") -PayloadJson (@{
        cwd = $workspaceRoot
        tool_name = "Write"
        transcript_path = (Join-Path $workspaceRoot "topics/company/sample/2026-01-01-pair-note.md")
        last_assistant_message = @"
# Pair Trade

## Long / Short
Long leg versus short leg framing.

## Spread
Spread definition and percentile context.

## Triggers
Entry trigger, exit trigger, and stop basis.

## Sizing
Sizing basis and hedge ratio.

## Risk
Pre-mortem and failure mode.
"@
    } | ConvertTo-Json -Depth 10) -WorkspaceRoot $workspaceRoot
    Invoke-HookSmokeTest -HookPath (Join-Path $hooksRoot "narrative/thesis_catalyst_floor.ps1") -PayloadJson (@{
        cwd = $workspaceRoot
        tool_name = "Write"
        transcript_path = (Join-Path $workspaceRoot "topics/company/sample/2026-01-01-alpha-thesis.md")
        last_assistant_message = @"
# Alpha Thesis

## Variant View
What market misses and the debate gap.

## Catalyst
Catalyst and trigger path.

## Kill Criteria
Kill criteria and disconfirming signal.
"@
    } | ConvertTo-Json -Depth 10) -WorkspaceRoot $workspaceRoot
    Invoke-HookSmokeTest -HookPath (Join-Path $hooksRoot "narrative/earnings_decision_contract.ps1") -PayloadJson (@{
        cwd = $workspaceRoot
        tool_name = "Write"
        transcript_path = (Join-Path $workspaceRoot "topics/company/sample/2026-01-01-earnings-setup.md")
        last_assistant_message = @"
# Earnings Setup

## Market Expectation
Consensus and buy-side bar.

## Observation Points
Key watch items.

## Decision Tree
If / then scenario tree.
"@
    } | ConvertTo-Json -Depth 10) -WorkspaceRoot $workspaceRoot
    Invoke-HookSmokeTest -HookPath (Join-Path $hooksRoot "narrative/peer_matrix_floor.ps1") -PayloadJson (@{
        cwd = $workspaceRoot
        tool_name = "Write"
        transcript_path = (Join-Path $workspaceRoot "topics/company/sample/2026-01-01-peer-deep-dive.md")
        last_assistant_message = @"
# Peer Deep Dive

## Peer Matrix
Core peer snapshot table.

## Cross-Cut
Cross-cut comparison and what matters across peers.
"@
    } | ConvertTo-Json -Depth 10) -WorkspaceRoot $workspaceRoot
    Invoke-HookSmokeTest -HookPath (Join-Path $hooksRoot "narrative/consensus_floor.ps1") -PayloadJson (@{
        cwd = $workspaceRoot
        tool_name = "Write"
        transcript_path = (Join-Path $workspaceRoot "topics/company/sample/2026-01-01-consensus-map.md")
        last_assistant_message = @"
# Consensus Map

## Market Expectation
Buy-side bar and market expectation framing.

## Consensus
Street consensus baseline.

## Variant Gap
Gap versus consensus and what is missed.

## Bar
The hurdle and beat-and-raise framing.
"@
    } | ConvertTo-Json -Depth 10) -WorkspaceRoot $workspaceRoot
    $threeStatementPassPath = Join-Path $workspaceRoot "topics/company/sample/2026-01-01-3-statement-model.xlsx"
    $threeStatementNoMasterPath = Join-Path $workspaceRoot "topics/company/sample/2026-01-01-3-statement-model-no-master.xlsx"
    $threeStatementNoRetainedPath = Join-Path $workspaceRoot "topics/company/sample/2026-01-01-3-statement-model-no-retained.xlsx"
    $threeStatementNoDebtTiePath = Join-Path $workspaceRoot "topics/company/sample/2026-01-01-3-statement-model-no-debt-tie.xlsx"
    $threeStatementNoDriverPath = Join-Path $workspaceRoot "topics/company/sample/2026-01-01-3-statement-model-no-driver.xlsx"
    $threeStatementChecksPassPath = Join-Path $workspaceRoot "topics/company/sample/2026-01-01-3-statement-model-checks-pass.xlsx"
    $threeStatementChecksNonZeroPath = Join-Path $workspaceRoot "topics/company/sample/2026-01-01-3-statement-model-checks-nonzero.xlsx"
    $threeStatementChecksFormulaPath = Join-Path $workspaceRoot "topics/company/sample/2026-01-01-3-statement-model-checks-formula.xlsx"
    $threeStatementHistoricalPassPath = Join-Path $workspaceRoot "topics/company/sample/_models/2026-01-01-3-statement-model-historical-pass.xlsx"
    $threeStatementHistoricalMissingPath = Join-Path $workspaceRoot "topics/company/sample/_models/2026-01-01-3-statement-model-historical-missing.xlsx"
    $threeStatementDriverCoveragePassPath = Join-Path $workspaceRoot "topics/company/sample/_models/2026-01-01-3-statement-model-driver-coverage-pass.xlsx"
    $threeStatementDriverCoverageFailPath = Join-Path $workspaceRoot "topics/company/sample/_models/2026-01-01-3-statement-model-driver-coverage-fail.xlsx"
    $dcfPassPath = Join-Path $workspaceRoot "topics/company/sample/2026-01-01-dcf-model.xlsx"
    $dcfNoBridgePath = Join-Path $workspaceRoot "topics/company/sample/2026-01-01-dcf-model-no-bridge.xlsx"
    $dcfNoSensitivityPath = Join-Path $workspaceRoot "topics/company/sample/2026-01-01-dcf-model-no-sensitivity.xlsx"
    $compsPassPath = Join-Path $workspaceRoot "topics/company/sample/2026-01-01-comps-analysis.xlsx"
    $financialDataInternal = Join-Path $workspaceRoot "topics/company/sample/_cache/financial-data/internal"
    $driverMapInternal = Join-Path $workspaceRoot "topics/company/sample/_cache/driver-map/internal"
    New-Item -ItemType Directory -Path $financialDataInternal -Force | Out-Null
    New-Item -ItemType Directory -Path $driverMapInternal -Force | Out-Null
    Write-Utf8NoBomFile (Join-Path $financialDataInternal "actuals-resolved.json") @'
{
  "schema_version": 1,
  "status": "ok",
  "statements": {
    "income_statement": [
      { "label": "Revenue", "confidence": "model-ready", "values": { "FY2023A": 100, "FY2024A": 120 } },
      { "label": "Gross Profit", "confidence": "model-ready", "values": { "FY2023A": 40, "FY2024A": 50 } },
      { "label": "Net Income", "confidence": "model-ready", "values": { "FY2023A": 10, "FY2024A": 15 } }
    ],
    "balance_sheet": [
      { "label": "Cash and Cash Equivalents", "confidence": "model-ready", "values": { "FY2023A": 20, "FY2024A": 25 } },
      { "label": "Total Assets", "confidence": "model-ready", "values": { "FY2023A": 200, "FY2024A": 220 } },
      { "label": "Inventory", "confidence": "review-only", "values": { "FY2023A": 30, "FY2024A": 35 } }
    ],
    "cash_flow": [
      { "label": "Operating Cash Flow", "confidence": "model-ready", "values": { "FY2023A": 15, "FY2024A": 18 } },
      { "label": "Capital Expenditures", "confidence": "model-ready", "values": { "FY2023A": -5, "FY2024A": -6 } },
      { "label": "Ending Cash", "confidence": "model-ready", "values": { "FY2023A": 20, "FY2024A": 25 } }
    ]
  },
  "completeness": [
    { "data_item": "income_statement", "status": "available", "model_usable": "true" },
    { "data_item": "balance_sheet", "status": "available", "model_usable": "true" },
    { "data_item": "cash_flow", "status": "available", "model_usable": "true" }
  ]
}
'@
    Write-Utf8NoBomFile (Join-Path $financialDataInternal "evidence-pack.json") @'
{
  "schema_version": 1,
  "completeness": [
    { "data_item": "income_statement", "status": "available", "model_usable": "true" },
    { "data_item": "balance_sheet", "status": "available", "model_usable": "true" },
    { "data_item": "cash_flow", "status": "available", "model_usable": "true" }
  ]
}
'@
    Write-Utf8NoBomFile (Join-Path $driverMapInternal "driver-map.json") @'
{
  "company": "Sample Co",
  "segment_geography_treatment": {
    "model_structure": "Driver-based segment model",
    "filing_native_segments": [
      { "reported_bucket": "Defense", "model_bucket": "Defense" },
      { "reported_bucket": "Aerospace", "model_bucket": "Aerospace" }
    ]
  },
  "revenue_drivers": [
    {
      "driver": "Defense revenue conversion",
      "business_bucket": "Defense",
      "evidence_status": "company disclosed",
      "confidence": "High",
      "model_treatment": "base case"
    },
    {
      "driver": "Aerospace deliveries",
      "business_bucket": "Aerospace",
      "evidence_status": "company disclosed",
      "confidence": "Medium",
      "model_treatment": "base case"
    }
  ],
  "margin_drivers": [
    {
      "driver": "Defense export mix",
      "evidence_status": "company disclosed",
      "confidence": "Medium",
      "model_treatment": "base case margin bridge"
    }
  ],
  "confidence_source_status": {
    "financial_data_status": "available"
  }
}
'@
    $threeStatementChecksPassSheetXml = @"
<?xml version="1.0" encoding="UTF-8"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>
<row r="1"><c r="A1" t="inlineStr"><is><t>Audit Checks &amp; Model Integrity</t></is></c></row>
<row r="2"><c r="B2" t="inlineStr"><is><t>FY2026E</t></is></c><c r="C2" t="inlineStr"><is><t>FY2027E</t></is></c></row>
<row r="3"><c r="A3" t="inlineStr"><is><t>Balance Sheet Balance</t></is></c><c r="B3"><v>0</v></c><c r="C3"><v>0</v></c></row>
<row r="4"><c r="A4" t="inlineStr"><is><t>Cash Tie-Out</t></is></c><c r="B4"><v>0</v></c><c r="C4"><v>0</v></c></row>
<row r="5"><c r="A5" t="inlineStr"><is><t>Retained Earnings Roll-Forward</t></is></c><c r="B5"><v>0</v></c><c r="C5"><v>-0</v></c></row>
<row r="6"><c r="A6" t="inlineStr"><is><t>Master Check</t></is></c><c r="B6" t="inlineStr"><is><t>ALL CHECKS PASS</t></is></c><c r="C6" t="inlineStr"><is><t>ALL CHECKS PASS</t></is></c></row>
</sheetData></worksheet>
"@
    $threeStatementChecksNonZeroSheetXml = @"
<?xml version="1.0" encoding="UTF-8"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>
<row r="1"><c r="A1" t="inlineStr"><is><t>Checks</t></is></c></row>
<row r="2"><c r="B2" t="inlineStr"><is><t>FY2026E</t></is></c></row>
<row r="3"><c r="A3" t="inlineStr"><is><t>Balance Sheet Balance</t></is></c><c r="B3"><v>1</v></c></row>
<row r="4"><c r="A4" t="inlineStr"><is><t>Cash Tie-Out</t></is></c><c r="B4"><v>0</v></c></row>
<row r="5"><c r="A5" t="inlineStr"><is><t>Master Status</t></is></c><c r="B5" t="inlineStr"><is><t>ERRORS DETECTED</t></is></c></row>
</sheetData></worksheet>
"@
    $threeStatementChecksFormulaSheetXml = @"
<?xml version="1.0" encoding="UTF-8"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>
<row r="1"><c r="A1" t="inlineStr"><is><t>Audit Checks</t></is></c></row>
<row r="2"><c r="B2" t="inlineStr"><is><t>FY2026E</t></is></c></row>
<row r="3"><c r="A3" t="inlineStr"><is><t>Balance Sheet Balance</t></is></c><c r="B3"><f>BS!E19-BS!E35-BS!E43</f></c></row>
<row r="4"><c r="A4" t="inlineStr"><is><t>Cash Tie-Out</t></is></c><c r="B4"><f>CF!E22-BS!E50</f></c></row>
<row r="5"><c r="A5" t="inlineStr"><is><t>Master Check</t></is></c><c r="B5"><f>IF(TRUE,&quot;ALL CHECKS PASS&quot;,&quot;ERRORS DETECTED&quot;)</f></c></row>
</sheetData></worksheet>
"@
    $historicalIncomePassSheetXml = @"
<?xml version="1.0" encoding="UTF-8"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>
<row r="1"><c r="A1" t="inlineStr"><is><t>Income Statement</t></is></c></row>
<row r="2"><c r="A2" t="inlineStr"><is><t>Line Item</t></is></c><c r="B2" t="inlineStr"><is><t>FY2023A</t></is></c><c r="C2" t="inlineStr"><is><t>FY2024A</t></is></c><c r="D2" t="inlineStr"><is><t>FY2025E</t></is></c></row>
<row r="3"><c r="A3" t="inlineStr"><is><t>Revenue</t></is></c><c r="B3"><v>100</v></c><c r="C3"><v>120</v></c></row>
<row r="4"><c r="A4" t="inlineStr"><is><t>Gross Profit</t></is></c><c r="B4"><v>40</v></c><c r="C4"><v>50</v></c></row>
<row r="5"><c r="A5" t="inlineStr"><is><t>Net Income</t></is></c><c r="B5"><v>10</v></c><c r="C5"><v>15</v></c></row>
</sheetData></worksheet>
"@
    $historicalIncomeMissingSheetXml = @"
<?xml version="1.0" encoding="UTF-8"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>
<row r="1"><c r="A1" t="inlineStr"><is><t>Income Statement</t></is></c></row>
<row r="2"><c r="A2" t="inlineStr"><is><t>Line Item</t></is></c><c r="B2" t="inlineStr"><is><t>FY2023A</t></is></c><c r="C2" t="inlineStr"><is><t>FY2024A</t></is></c><c r="D2" t="inlineStr"><is><t>FY2025E</t></is></c></row>
<row r="3"><c r="A3" t="inlineStr"><is><t>Revenue</t></is></c><c r="B3"><v>100</v></c><c r="C3"><v>120</v></c></row>
<row r="4"><c r="A4" t="inlineStr"><is><t>Gross Profit</t></is></c><c r="B4"><v>40</v></c></row>
<row r="5"><c r="A5" t="inlineStr"><is><t>Net Income</t></is></c><c r="B5"><v>10</v></c><c r="C5"><v>15</v></c></row>
</sheetData></worksheet>
"@
    $historicalBalanceSheetXml = @"
<?xml version="1.0" encoding="UTF-8"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>
<row r="1"><c r="A1" t="inlineStr"><is><t>Balance Sheet</t></is></c></row>
<row r="2"><c r="A2" t="inlineStr"><is><t>Line Item</t></is></c><c r="B2" t="inlineStr"><is><t>FY2023A</t></is></c><c r="C2" t="inlineStr"><is><t>FY2024A</t></is></c><c r="D2" t="inlineStr"><is><t>FY2025E</t></is></c></row>
<row r="3"><c r="A3" t="inlineStr"><is><t>Cash and Cash Equivalents</t></is></c><c r="B3"><v>20</v></c><c r="C3"><v>25</v></c></row>
<row r="4"><c r="A4" t="inlineStr"><is><t>Total Assets</t></is></c><c r="B4"><v>200</v></c><c r="C4"><v>220</v></c></row>
<row r="5"><c r="A5" t="inlineStr"><is><t>Inventory</t></is></c></row>
</sheetData></worksheet>
"@
    $historicalCashFlowXml = @"
<?xml version="1.0" encoding="UTF-8"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>
<row r="1"><c r="A1" t="inlineStr"><is><t>Cash Flow Statement</t></is></c></row>
<row r="2"><c r="A2" t="inlineStr"><is><t>Line Item</t></is></c><c r="B2" t="inlineStr"><is><t>FY2023A</t></is></c><c r="C2" t="inlineStr"><is><t>FY2024A</t></is></c><c r="D2" t="inlineStr"><is><t>FY2025E</t></is></c></row>
<row r="3"><c r="A3" t="inlineStr"><is><t>Operating Cash Flow</t></is></c><c r="B3"><v>15</v></c><c r="C3"><v>18</v></c></row>
<row r="4"><c r="A4" t="inlineStr"><is><t>Capital Expenditures</t></is></c><c r="B4"><v>-5</v></c><c r="C4"><v>-6</v></c></row>
<row r="5"><c r="A5" t="inlineStr"><is><t>Ending Cash</t></is></c><c r="B5"><v>20</v></c><c r="C5"><v>25</v></c></row>
</sheetData></worksheet>
"@
    $driverCoveragePassIsSheetXml = @"
<?xml version="1.0" encoding="UTF-8"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>
<row r="1"><c r="A1" t="inlineStr"><is><t>Income Statement</t></is></c></row>
<row r="2"><c r="A2" t="inlineStr"><is><t>Line Item</t></is></c><c r="B2" t="inlineStr"><is><t>FY2024A</t></is></c><c r="C2" t="inlineStr"><is><t>FY2025A</t></is></c><c r="D2" t="inlineStr"><is><t>FY2026E</t></is></c><c r="E2" t="inlineStr"><is><t>FY2027E</t></is></c></row>
<row r="3"><c r="A3" t="inlineStr"><is><t>Defense</t></is></c><c r="B3" t="inlineStr"><is><t>--</t></is></c><c r="C3"><v>100</v></c><c r="D3"><f>SUM(C3)</f></c><c r="E3"><f>SUM(D3)</f></c></row>
<row r="4"><c r="A4" t="inlineStr"><is><t>Aerospace</t></is></c><c r="B4" t="inlineStr"><is><t>--</t></is></c><c r="C4"><v>50</v></c><c r="D4"><f>SUM(C4)</f></c><c r="E4"><f>SUM(D4)</f></c></row>
<row r="5"><c r="A5" t="inlineStr"><is><t>Total Revenue</t></is></c><c r="B5"><v>150</v></c><c r="C5"><v>150</v></c><c r="D5"><f>SUM(D3:D4)</f></c><c r="E5"><f>SUM(E3:E4)</f></c></row>
<row r="6"><c r="A6" t="inlineStr"><is><t>YoY Growth %</t></is></c><c r="C6"><f>C5/B5-1</f></c><c r="D6"><f>D5/C5-1</f></c><c r="E6"><f>E5/D5-1</f></c></row>
<row r="7"><c r="A7" t="inlineStr"><is><t>Gross Margin %</t></is></c><c r="B7"><f>0.3</f></c><c r="C7"><f>0.31</f></c><c r="D7"><f>0.32</f></c><c r="E7"><f>0.33</f></c></row>
<row r="8"><c r="A8" t="inlineStr"><is><t>EBIT Margin %</t></is></c><c r="B8"><f>0.1</f></c><c r="C8"><f>0.11</f></c><c r="D8"><f>0.12</f></c><c r="E8"><f>0.13</f></c></row>
<row r="9"><c r="A9" t="inlineStr"><is><t>NI Margin %</t></is></c><c r="B9"><f>0.08</f></c><c r="C9"><f>0.09</f></c><c r="D9"><f>0.1</f></c><c r="E9"><f>0.11</f></c></row>
</sheetData></worksheet>
"@
    $driverCoveragePassAssumptionsSheetXml = @"
<?xml version="1.0" encoding="UTF-8"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>
<row r="1"><c r="A1" t="inlineStr"><is><t>Assumptions</t></is></c></row>
<row r="2"><c r="A2" t="inlineStr"><is><t>Line Item</t></is></c><c r="B2" t="inlineStr"><is><t>FY2025A</t></is></c><c r="C2" t="inlineStr"><is><t>FY2026E</t></is></c><c r="D2" t="inlineStr"><is><t>FY2027E</t></is></c></row>
<row r="3"><c r="A3" t="inlineStr"><is><t>Defense</t></is></c><c r="B3" t="inlineStr"><is><t>--</t></is></c><c r="C3"><v>0.12</v></c><c r="D3"><v>0.10</v></c></row>
<row r="4"><c r="A4" t="inlineStr"><is><t>Aerospace</t></is></c><c r="B4" t="inlineStr"><is><t>--</t></is></c><c r="C4"><v>0.08</v></c><c r="D4"><v>0.07</v></c></row>
<row r="5"><c r="A5" t="inlineStr"><is><t>Downside Growth</t></is></c></row>
<row r="6"><c r="A6" t="inlineStr"><is><t>Defense</t></is></c><c r="B6"><v>0.22</v></c><c r="C6"><v>0.20</v></c><c r="D6"><v>0.20</v></c></row>
<row r="7"><c r="A7" t="inlineStr"><is><t>Aerospace</t></is></c><c r="B7"><v>0.10</v></c><c r="C7"><v>0.11</v></c><c r="D7"><v>0.11</v></c></row>
<row r="8"><c r="A8" t="inlineStr"><is><t>Upside Margin</t></is></c></row>
</sheetData></worksheet>
"@
    $driverCoverageFailIsSheetXml = @"
<?xml version="1.0" encoding="UTF-8"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>
<row r="1"><c r="A1" t="inlineStr"><is><t>Income Statement</t></is></c></row>
<row r="2"><c r="A2" t="inlineStr"><is><t>Line Item</t></is></c><c r="B2" t="inlineStr"><is><t>FY2024A</t></is></c><c r="C2" t="inlineStr"><is><t>FY2025A</t></is></c><c r="D2" t="inlineStr"><is><t>FY2026E</t></is></c><c r="E2" t="inlineStr"><is><t>FY2027E</t></is></c></row>
<row r="3"><c r="A3" t="inlineStr"><is><t>Defense</t></is></c><c r="B3" t="inlineStr"><is><t>--</t></is></c><c r="C3" t="inlineStr"><is><t>--</t></is></c><c r="D3" t="inlineStr"><is><t>--</t></is></c><c r="E3" t="inlineStr"><is><t>--</t></is></c></row>
<row r="4"><c r="A4" t="inlineStr"><is><t>Aerospace</t></is></c><c r="B4" t="inlineStr"><is><t>--</t></is></c><c r="C4"><v>50</v></c><c r="D4"><f>SUM(C4)</f></c><c r="E4"><f>SUM(D4)</f></c></row>
<row r="5"><c r="A5" t="inlineStr"><is><t>Total Revenue</t></is></c><c r="B5"><v>50</v></c><c r="C5"><v>50</v></c><c r="D5"><f>SUM(D3:D4)</f></c><c r="E5"><f>SUM(E3:E4)</f></c></row>
<row r="6"><c r="A6" t="inlineStr"><is><t>YoY Growth %</t></is></c><c r="C6"><f>C5/B5-1</f></c><c r="D6"></c><c r="E6"><f>E5/D5-1</f></c></row>
<row r="7"><c r="A7" t="inlineStr"><is><t>Gross Margin %</t></is></c><c r="B7"><f>0.3</f></c><c r="C7"><f>0.31</f></c><c r="D7"><f>0.32</f></c><c r="E7"><f>0.33</f></c></row>
<row r="8"><c r="A8" t="inlineStr"><is><t>EBIT Margin %</t></is></c><c r="B8"><f>0.1</f></c><c r="C8"><f>0.11</f></c><c r="D8"><f>0.12</f></c><c r="E8"><f>0.13</f></c></row>
<row r="9"><c r="A9" t="inlineStr"><is><t>NI Margin %</t></is></c><c r="B9"><f>0.08</f></c><c r="C9"><f>0.09</f></c><c r="D9"><f>0.1</f></c><c r="E9"><f>0.11</f></c></row>
</sheetData></worksheet>
"@
    $driverCoverageFailAssumptionsSheetXml = @"
<?xml version="1.0" encoding="UTF-8"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>
<row r="1"><c r="A1" t="inlineStr"><is><t>Assumptions</t></is></c></row>
<row r="2"><c r="A2" t="inlineStr"><is><t>Line Item</t></is></c><c r="B2" t="inlineStr"><is><t>FY2025A</t></is></c><c r="C2" t="inlineStr"><is><t>FY2026E</t></is></c><c r="D2" t="inlineStr"><is><t>FY2027E</t></is></c></row>
<row r="3"><c r="A3" t="inlineStr"><is><t>Defense</t></is></c><c r="B3" t="inlineStr"><is><t>--</t></is></c><c r="C3" t="inlineStr"><is><t>--</t></is></c><c r="D3" t="inlineStr"><is><t>--</t></is></c></row>
<row r="4"><c r="A4" t="inlineStr"><is><t>Aerospace</t></is></c><c r="B4" t="inlineStr"><is><t>--</t></is></c><c r="C4"><v>0.08</v></c><c r="D4"><v>0.07</v></c></row>
<row r="5"><c r="A5" t="inlineStr"><is><t>Downside Growth</t></is></c></row>
<row r="6"><c r="A6" t="inlineStr"><is><t>Aerospace</t></is></c><c r="B6"><v>0.10</v></c><c r="C6"><v>0.11</v></c><c r="D6"><v>0.11</v></c></row>
<row r="7"><c r="A7" t="inlineStr"><is><t>Upside Margin</t></is></c></row>
</sheetData></worksheet>
"@

    New-SmokeWorkbook -Path $threeStatementPassPath -SheetNames @(
        "Historical Actuals",
        "Income Statement",
        "Balance Sheet",
        "Cash Flow Statement",
        "Audit Checks",
        "Master Check",
        "Debt Schedule"
    ) -SharedStrings @(
        "Historical Actuals",
        "Income Statement",
        "Balance Sheet",
        "Cash Flow Statement",
        "Audit Checks",
        "Master Check",
        "ALL CHECKS PASS",
        "Balance Sheet Balance",
        "Assets - Liabilities - Equity = 0",
        "Cash Tie-Out",
        "CF ending cash = BS cash",
        "Retained Earnings Roll-Forward",
        "NI-dividend linkage",
        "Debt Schedule",
        "Debt Tie-Out",
        "Equity issuance",
        "APIC",
        "Equity Raise Tie-Out",
        "Assumptions",
        "Revenue Growth",
        "Segment Driver",
        "Volume-Price-Mix"
    )
    New-SmokeWorkbook -Path $threeStatementNoMasterPath -SheetNames @(
        "Historical Actuals",
        "Income Statement",
        "Balance Sheet",
        "Cash Flow Statement",
        "Audit Checks"
    ) -SharedStrings @(
        "Historical Actuals",
        "Income Statement",
        "Balance Sheet",
        "Cash Flow Statement",
        "Audit Checks",
        "Balance Sheet Balance",
        "Assets - Liabilities - Equity = 0",
        "Cash Tie-Out",
        "CF ending cash = BS cash",
        "Retained Earnings Roll-Forward",
        "Assumptions",
        "Revenue Growth"
    )
    New-SmokeWorkbook -Path $threeStatementNoRetainedPath -SheetNames @(
        "Historical Actuals",
        "Income Statement",
        "Balance Sheet",
        "Cash Flow Statement",
        "Audit Checks",
        "Master Check"
    ) -SharedStrings @(
        "Historical Actuals",
        "Income Statement",
        "Balance Sheet",
        "Cash Flow Statement",
        "Audit Checks",
        "Master Check",
        "ALL CHECKS PASS",
        "Balance Sheet Balance",
        "Assets - Liabilities - Equity = 0",
        "Cash Tie-Out",
        "CF ending cash = BS cash",
        "Assumptions",
        "Revenue Growth",
        "Segment Driver"
    )
    New-SmokeWorkbook -Path $threeStatementNoDebtTiePath -SheetNames @(
        "Historical Actuals",
        "Income Statement",
        "Balance Sheet",
        "Cash Flow Statement",
        "Audit Checks",
        "Master Check",
        "Debt Schedule"
    ) -SharedStrings @(
        "Historical Actuals",
        "Income Statement",
        "Balance Sheet",
        "Cash Flow Statement",
        "Audit Checks",
        "Master Check",
        "ALL CHECKS PASS",
        "Balance Sheet Balance",
        "Assets - Liabilities - Equity = 0",
        "Cash Tie-Out",
        "CF ending cash = BS cash",
        "Retained Earnings Roll-Forward",
        "Debt Schedule",
        "Total Debt",
        "Assumptions",
        "Revenue Growth",
        "Segment Driver"
    )
    New-SmokeWorkbook -Path $threeStatementNoDriverPath -SheetNames @(
        "Historical Actuals",
        "Income Statement",
        "Balance Sheet",
        "Cash Flow Statement",
        "Audit Checks",
        "Master Check"
    ) -SharedStrings @(
        "Historical Actuals",
        "Income Statement",
        "Balance Sheet",
        "Cash Flow Statement",
        "Audit Checks",
        "Master Check",
        "ALL CHECKS PASS",
        "Balance Sheet Balance",
        "Assets - Liabilities - Equity = 0",
        "Cash Tie-Out",
        "CF ending cash = BS cash",
        "Retained Earnings Roll-Forward",
        "Revenue"
    )
    New-SmokeWorkbook -Path $threeStatementChecksPassPath -SheetNames @(
        "Income Statement",
        "Audit Checks"
    ) -SharedStrings @() -SheetXmlByName @{
        "Audit Checks" = $threeStatementChecksPassSheetXml
    }
    New-SmokeWorkbook -Path $threeStatementChecksNonZeroPath -SheetNames @(
        "Income Statement",
        "Checks"
    ) -SharedStrings @() -SheetXmlByName @{
        "Checks" = $threeStatementChecksNonZeroSheetXml
    }
    New-SmokeWorkbook -Path $threeStatementChecksFormulaPath -SheetNames @(
        "Balance Sheet",
        "Audit Checks"
    ) -SharedStrings @() -SheetXmlByName @{
        "Audit Checks" = $threeStatementChecksFormulaSheetXml
    }
    New-SmokeWorkbook -Path $threeStatementHistoricalPassPath -SheetNames @(
        "Income Statement",
        "Balance Sheet",
        "Cash Flow Statement"
    ) -SharedStrings @() -SheetXmlByName @{
        "Income Statement" = $historicalIncomePassSheetXml
        "Balance Sheet" = $historicalBalanceSheetXml
        "Cash Flow Statement" = $historicalCashFlowXml
    }
    New-SmokeWorkbook -Path $threeStatementHistoricalMissingPath -SheetNames @(
        "Income Statement",
        "Balance Sheet",
        "Cash Flow Statement"
    ) -SharedStrings @() -SheetXmlByName @{
        "Income Statement" = $historicalIncomeMissingSheetXml
        "Balance Sheet" = $historicalBalanceSheetXml
        "Cash Flow Statement" = $historicalCashFlowXml
    }
    New-SmokeWorkbook -Path $threeStatementDriverCoveragePassPath -SheetNames @(
        "Income Statement",
        "Assumptions"
    ) -SharedStrings @() -SheetXmlByName @{
        "Income Statement" = $driverCoveragePassIsSheetXml
        "Assumptions" = $driverCoveragePassAssumptionsSheetXml
    }
    New-SmokeWorkbook -Path $threeStatementDriverCoverageFailPath -SheetNames @(
        "Income Statement",
        "Assumptions"
    ) -SharedStrings @() -SheetXmlByName @{
        "Income Statement" = $driverCoverageFailIsSheetXml
        "Assumptions" = $driverCoverageFailAssumptionsSheetXml
    }
    New-SmokeWorkbook -Path $dcfPassPath -SheetNames @(
        "Market Data & Key Inputs",
        "Scenario Assumptions",
        "Valuation Summary",
        "Sensitivity Analysis"
    ) -SharedStrings @(
        "Market Data & Key Inputs",
        "Scenario Assumptions",
        "Bear Case",
        "Base Case",
        "Bull Case",
        "Free Cash Flow",
        "WACC",
        "Terminal Value",
        "Valuation Summary",
        "Equity Value",
        "Implied Share Price",
        "Sensitivity Analysis",
        "WACC vs Terminal Growth"
    )
    New-SmokeWorkbook -Path $dcfNoBridgePath -SheetNames @(
        "Market Data & Key Inputs",
        "Scenario Assumptions",
        "Sensitivity Analysis"
    ) -SharedStrings @(
        "Market Data & Key Inputs",
        "Scenario Assumptions",
        "Free Cash Flow",
        "WACC",
        "Terminal Value",
        "Sensitivity Analysis",
        "WACC vs Terminal Growth"
    )
    New-SmokeWorkbook -Path $dcfNoSensitivityPath -SheetNames @(
        "Market Data & Key Inputs",
        "Scenario Assumptions",
        "Valuation Summary"
    ) -SharedStrings @(
        "Market Data & Key Inputs",
        "Scenario Assumptions",
        "Free Cash Flow",
        "WACC",
        "Terminal Value",
        "Valuation Summary",
        "Equity Value",
        "Implied Share Price"
    )
    New-SmokeWorkbook -Path $compsPassPath -SheetNames @(
        "Comparable Company Analysis",
        "Operating Metrics",
        "Valuation Multiples",
        "Statistics"
    ) -SharedStrings @(
        "Comparable Company Analysis",
        "As of 2026-05-26",
        "All figures in USD Millions",
        "Operating Metrics",
        "Operating Statistics",
        "Valuation Multiples",
        "EV/EBITDA",
        "Statistics",
        "Maximum",
        "75th Percentile",
        "Median",
        "25th Percentile",
        "Minimum",
        "Notes",
        "Methodology",
        "Source"
    )
    Invoke-HookSmokeTest -HookPath (Join-Path $hooksRoot "modeling/three_statement_structure_floor.ps1") -PayloadJson (@{
        cwd = $workspaceRoot
        tool_name = "Write"
        tool_input = @{ path = $threeStatementPassPath }
    } | ConvertTo-Json -Depth 10) -WorkspaceRoot $workspaceRoot
    Invoke-HookSmokeTest -HookPath (Join-Path $hooksRoot "modeling/three_statement_audit_floor.ps1") -PayloadJson (@{
        cwd = $workspaceRoot
        tool_name = "Write"
        tool_input = @{ path = $threeStatementPassPath }
    } | ConvertTo-Json -Depth 10) -WorkspaceRoot $workspaceRoot
    Invoke-HookSmokeTest -HookPath (Join-Path $hooksRoot "modeling/three_statement_driver_floor.ps1") -PayloadJson (@{
        cwd = $workspaceRoot
        tool_name = "Write"
        tool_input = @{ path = $threeStatementPassPath }
    } | ConvertTo-Json -Depth 10) -WorkspaceRoot $workspaceRoot
    Invoke-HookSmokeTest -HookPath (Join-Path $hooksRoot "modeling/three_statement_checks_result_floor.ps1") -PayloadJson (@{
        cwd = $workspaceRoot
        tool_name = "Write"
        smoke_test = $true
        tool_input = @{ path = $threeStatementChecksPassPath }
    } | ConvertTo-Json -Depth 10) -WorkspaceRoot $workspaceRoot
    Invoke-HookSmokeTest -HookPath (Join-Path $hooksRoot "modeling/historical_actuals_fill_floor.ps1") -PayloadJson (@{
        cwd = $workspaceRoot
        tool_name = "Write"
        tool_input = @{ path = $threeStatementHistoricalPassPath }
    } | ConvertTo-Json -Depth 10) -WorkspaceRoot $workspaceRoot
    Invoke-HookSmokeTest -HookPath (Join-Path $hooksRoot "modeling/driver_breakdown_coverage_floor.ps1") -PayloadJson (@{
        cwd = $workspaceRoot
        tool_name = "Write"
        tool_input = @{ path = $threeStatementDriverCoveragePassPath }
    } | ConvertTo-Json -Depth 10) -WorkspaceRoot $workspaceRoot
    Invoke-HookSmokeTest -HookPath (Join-Path $hooksRoot "modeling/dcf_structure_floor.ps1") -PayloadJson (@{
        cwd = $workspaceRoot
        tool_name = "Write"
        tool_input = @{ path = $dcfPassPath }
    } | ConvertTo-Json -Depth 10) -WorkspaceRoot $workspaceRoot
    Invoke-HookSmokeTest -HookPath (Join-Path $hooksRoot "modeling/dcf_audit_floor.ps1") -PayloadJson (@{
        cwd = $workspaceRoot
        tool_name = "Write"
        tool_input = @{ path = $dcfPassPath }
    } | ConvertTo-Json -Depth 10) -WorkspaceRoot $workspaceRoot
    Invoke-HookSmokeTest -HookPath (Join-Path $hooksRoot "modeling/comps_structure_floor.ps1") -PayloadJson (@{
        cwd = $workspaceRoot
        tool_name = "Write"
        tool_input = @{ path = $compsPassPath }
    } | ConvertTo-Json -Depth 10) -WorkspaceRoot $workspaceRoot
    Invoke-HookSmokeTest -HookPath (Join-Path $hooksRoot "modeling/model_update_change_map_floor.ps1") -PayloadJson (@{
        cwd = $workspaceRoot
        tool_name = "Write"
        transcript_path = (Join-Path $workspaceRoot "topics/company/sample/2026-01-01-model-update.md")
        last_assistant_message = @"
# Model Update

## What Changed
New quarter actuals and revised demand assumptions.

## Actual vs Prior
Prior estimate versus reported actuals bridge.

## Forward Revisions
Old FY estimate versus new FY estimate.

## Valuation Impact
Updated DCF and target multiple impact.

## Update Map
Changed actuals, assumptions, and formula touchpoints.
"@
    } | ConvertTo-Json -Depth 10) -WorkspaceRoot $workspaceRoot
    Invoke-HookSmokeFailureTest -HookPath (Join-Path $hooksRoot "global/source_contract.ps1") -PayloadJson (@{
        cwd = $workspaceRoot
        tool_name = "Write"
        transcript_path = $markdownPath
        last_assistant_message = "## Verdict`nMismatch. [S1](https://example.com/a)`n`n## Resources`n- [S1](https://example.com/b) = web | sample | as-of | note"
    } | ConvertTo-Json -Depth 10) -ExpectedMessage "must keep inline [S1] target identical" -WorkspaceRoot $workspaceRoot
    Invoke-HookSmokeFailureTest -HookPath (Join-Path $hooksRoot "global/source_contract.ps1") -PayloadJson (@{
        cwd = $workspaceRoot
        tool_name = "Write"
        transcript_path = $markdownPath
        last_assistant_message = "## Verdict`nBad target. [S1](foo)`n`n## Resources`n- [S1](foo) = web | sample | as-of | note"
    } | ConvertTo-Json -Depth 10) -ExpectedMessage "invalid ## Resources target" -WorkspaceRoot $workspaceRoot
    Invoke-HookSmokeFailureTest -HookPath (Join-Path $hooksRoot "provider/market_snapshot_source_boundary.ps1") -PayloadJson (@{
        cwd = $workspaceRoot
        tool_name = "Write"
        transcript_path = (Join-Path $workspaceRoot "topics/company/sample/2026-01-01-stock-quickread.md")
        last_assistant_message = @"
# Stock Quickread

Below uses internet source as a fallback snapshot.

## 1. Snapshot

| Field | Value | Ev |
|---|---|---|
| market_quote | 100 | [I1](https://example.com/quote) |

## Resources
- [I1](https://example.com/quote) = internet source | Example Quote Provider | as-of 2026-05-26
"@
    } | ConvertTo-Json -Depth 10) -ExpectedMessage "must expand each [I1] entry with provider, as-of, and fallback reason" -WorkspaceRoot $workspaceRoot
    Invoke-HookSmokeFailureTest -HookPath (Join-Path $hooksRoot "global/table_render_integrity.ps1") -PayloadJson (@{
        cwd = $workspaceRoot
        tool_name = "Write"
        transcript_path = $markdownPath
        last_assistant_message = @"
# Table Failure

| Field | Value | Ev |
|---|---|---|
| revenue | 10 |
"@
    } | ConvertTo-Json -Depth 10) -ExpectedMessage "table row with 2 columns but expected 3" -WorkspaceRoot $workspaceRoot
    Invoke-HookSmokeFailureTest -HookPath (Join-Path $hooksRoot "global/table_render_integrity.ps1") -PayloadJson (@{
        cwd = $workspaceRoot
        tool_name = "Write"
        transcript_path = $markdownPath
        last_assistant_message = @"
# Interrupted Table Failure

| Field | Value | Ev |
|---|---|---|
| revenue | 10 | [S1](https://example.com/revenue) |

Inline claim example between rows.
| margin | 20% | [S2](https://example.com/margin) |

## Resources
- [S1](https://example.com/revenue) = web | sample | as-of 2026-05-26 | note
- [S2](https://example.com/margin) = web | sample | as-of 2026-05-26 | note
"@
    } | ConvertTo-Json -Depth 10) -ExpectedMessage "table-like row near line 8 outside a valid contiguous markdown table block" -WorkspaceRoot $workspaceRoot
    Invoke-HookSmokeFailureTest -HookPath (Join-Path $hooksRoot "provider/disclosure_fact_source_boundary.ps1") -PayloadJson (@{
        cwd = $workspaceRoot
        tool_name = "Write"
        transcript_path = (Join-Path $workspaceRoot "topics/company/sample/2026-01-01-company-primer.md")
        last_assistant_message = @"
# Company Primer

Customer relationship confirmed. [I1](https://example.com/blog)

## Resources
- [I1](https://example.com/blog) = internet source | Example blog | as-of 2026-05-26 | fallback reason: local cache unavailable
"@
    } | ConvertTo-Json -Depth 10) -ExpectedMessage "uses internet source or trusted-market-bridge fallback in a disclosure-fact workflow" -WorkspaceRoot $workspaceRoot
    Invoke-HookSmokeFailureTest -HookPath (Join-Path $hooksRoot "narrative/next_step_anchored_facts_only.ps1") -PayloadJson (@{
        cwd = $workspaceRoot
        tool_name = "Write"
        transcript_path = (Join-Path $workspaceRoot "topics/company/sample/2026-01-01-next-step.md")
        last_assistant_message = @"
# Next Step

- Next move: company disclosed 35% gross margin and backlog doubled, so meet management next.
"@
    } | ConvertTo-Json -Depth 10) -ExpectedMessage "introduces an assertive fact" -WorkspaceRoot $workspaceRoot
    Invoke-HookSmokeFailureTest -HookPath (Join-Path $hooksRoot "narrative/pair_structure_floor.ps1") -PayloadJson (@{
        cwd = $workspaceRoot
        tool_name = "Write"
        transcript_path = (Join-Path $workspaceRoot "topics/company/sample/2026-01-01-pair-note.md")
        last_assistant_message = @"
# Pair Trade

Relative-value idea with no structure.
"@
    } | ConvertTo-Json -Depth 10) -ExpectedMessage "must explicitly include long/short leg framing" -WorkspaceRoot $workspaceRoot
    Invoke-HookSmokeFailureTest -HookPath (Join-Path $hooksRoot "narrative/thesis_catalyst_floor.ps1") -PayloadJson (@{
        cwd = $workspaceRoot
        tool_name = "Write"
        transcript_path = (Join-Path $workspaceRoot "topics/company/sample/2026-01-01-alpha-thesis.md")
        last_assistant_message = @"
# Alpha Thesis

## Variant View
Only a debate gap.
"@
    } | ConvertTo-Json -Depth 10) -ExpectedMessage "must explicitly include catalyst" -WorkspaceRoot $workspaceRoot
    Invoke-HookSmokeFailureTest -HookPath (Join-Path $hooksRoot "narrative/earnings_decision_contract.ps1") -PayloadJson (@{
        cwd = $workspaceRoot
        tool_name = "Write"
        transcript_path = (Join-Path $workspaceRoot "topics/company/sample/2026-01-01-earnings-setup.md")
        last_assistant_message = @"
# Earnings Setup

## Market Expectation
Consensus only.
"@
    } | ConvertTo-Json -Depth 10) -ExpectedMessage "must explicitly include observation points" -WorkspaceRoot $workspaceRoot
    Invoke-HookSmokeFailureTest -HookPath (Join-Path $hooksRoot "narrative/peer_matrix_floor.ps1") -PayloadJson (@{
        cwd = $workspaceRoot
        tool_name = "Write"
        transcript_path = (Join-Path $workspaceRoot "topics/company/sample/2026-01-01-peer-deep-dive.md")
        last_assistant_message = @"
# Peer Deep Dive

Only prose, no matrix.
"@
    } | ConvertTo-Json -Depth 10) -ExpectedMessage "must include a core peer matrix" -WorkspaceRoot $workspaceRoot
    Invoke-HookSmokeFailureTest -HookPath (Join-Path $hooksRoot "narrative/consensus_floor.ps1") -PayloadJson (@{
        cwd = $workspaceRoot
        tool_name = "Write"
        transcript_path = (Join-Path $workspaceRoot "topics/company/sample/2026-01-01-consensus-map.md")
        last_assistant_message = @"
# Consensus Map

## Market Expectation
Only buy-side bar.
"@
    } | ConvertTo-Json -Depth 10) -ExpectedMessage "must explicitly include consensus baseline" -WorkspaceRoot $workspaceRoot
    Invoke-HookSmokeFailureTest -HookPath (Join-Path $hooksRoot "modeling/three_statement_audit_floor.ps1") -PayloadJson (@{
        cwd = $workspaceRoot
        tool_name = "Write"
        tool_input = @{ path = $threeStatementNoMasterPath }
    } | ConvertTo-Json -Depth 10) -ExpectedMessage "must include a master check" -WorkspaceRoot $workspaceRoot
    Invoke-HookSmokeFailureTest -HookPath (Join-Path $hooksRoot "modeling/three_statement_audit_floor.ps1") -PayloadJson (@{
        cwd = $workspaceRoot
        tool_name = "Write"
        tool_input = @{ path = $threeStatementNoRetainedPath }
    } | ConvertTo-Json -Depth 10) -ExpectedMessage "retained earnings roll-forward" -WorkspaceRoot $workspaceRoot
    Invoke-HookSmokeFailureTest -HookPath (Join-Path $hooksRoot "modeling/three_statement_audit_floor.ps1") -PayloadJson (@{
        cwd = $workspaceRoot
        tool_name = "Write"
        tool_input = @{ path = $threeStatementNoDebtTiePath }
    } | ConvertTo-Json -Depth 10) -ExpectedMessage "no explicit Debt Tie-Out" -WorkspaceRoot $workspaceRoot
    Invoke-HookSmokeFailureTest -HookPath (Join-Path $hooksRoot "modeling/three_statement_driver_floor.ps1") -PayloadJson (@{
        cwd = $workspaceRoot
        tool_name = "Write"
        tool_input = @{ path = $threeStatementNoDriverPath }
    } | ConvertTo-Json -Depth 10) -ExpectedMessage "structured revenue/driver breakdown" -WorkspaceRoot $workspaceRoot
    Invoke-HookSmokeFailureTest -HookPath (Join-Path $hooksRoot "modeling/three_statement_checks_result_floor.ps1") -PayloadJson (@{
        cwd = $workspaceRoot
        tool_name = "Write"
        smoke_test = $true
        tool_input = @{ path = $threeStatementChecksNonZeroPath }
    } | ConvertTo-Json -Depth 10) -ExpectedMessage "must resolve to 0" -WorkspaceRoot $workspaceRoot
    Invoke-HookSmokeFailureTest -HookPath (Join-Path $hooksRoot "modeling/three_statement_checks_result_floor.ps1") -PayloadJson (@{
        cwd = $workspaceRoot
        tool_name = "Write"
        smoke_test = $true
        tool_input = @{ path = $threeStatementChecksFormulaPath }
    } | ConvertTo-Json -Depth 10) -ExpectedMessage "still shows formula text" -WorkspaceRoot $workspaceRoot
    Invoke-HookSmokeFailureTest -HookPath (Join-Path $hooksRoot "modeling/three_statement_checks_result_floor.ps1") -PayloadJson (@{
        cwd = $workspaceRoot
        tool_name = "Write"
        smoke_test = $true
        tool_input = @{ path = $threeStatementNoMasterPath }
    } | ConvertTo-Json -Depth 10) -ExpectedMessage "recognizable checks-like block" -WorkspaceRoot $workspaceRoot
    Invoke-HookSmokeFailureTest -HookPath (Join-Path $hooksRoot "modeling/historical_actuals_fill_floor.ps1") -PayloadJson (@{
        cwd = $workspaceRoot
        tool_name = "Write"
        tool_input = @{ path = $threeStatementHistoricalMissingPath }
    } | ConvertTo-Json -Depth 10) -ExpectedMessage "leaves source-mapped model-usable historical actuals blank" -WorkspaceRoot $workspaceRoot
    Invoke-HookSmokeFailureTest -HookPath (Join-Path $hooksRoot "modeling/driver_breakdown_coverage_floor.ps1") -PayloadJson (@{
        cwd = $workspaceRoot
        tool_name = "Write"
        tool_input = @{ path = $threeStatementDriverCoverageFailPath }
    } | ConvertTo-Json -Depth 10) -ExpectedMessage "leaves driver-map-backed revenue breakdown or margin/growth blocks as placeholders" -WorkspaceRoot $workspaceRoot
    Invoke-HookSmokeFailureTest -HookPath (Join-Path $hooksRoot "modeling/dcf_audit_floor.ps1") -PayloadJson (@{
        cwd = $workspaceRoot
        tool_name = "Write"
        tool_input = @{ path = $dcfNoBridgePath }
    } | ConvertTo-Json -Depth 10) -ExpectedMessage "visible valuation bridge or valuation summary" -WorkspaceRoot $workspaceRoot
    Invoke-HookSmokeFailureTest -HookPath (Join-Path $hooksRoot "modeling/dcf_audit_floor.ps1") -PayloadJson (@{
        cwd = $workspaceRoot
        tool_name = "Write"
        tool_input = @{ path = $dcfNoSensitivityPath }
    } | ConvertTo-Json -Depth 10) -ExpectedMessage "visible sensitivity table evidence" -WorkspaceRoot $workspaceRoot
    Invoke-HookSmokeFailureTest -HookPath (Join-Path $hooksRoot "modeling/model_update_change_map_floor.ps1") -PayloadJson (@{
        cwd = $workspaceRoot
        tool_name = "Write"
        transcript_path = (Join-Path $workspaceRoot "topics/company/sample/2026-01-01-model-update.md")
        last_assistant_message = @"
# Model Update

## What Changed
Only the quarter changed.

## Actual vs Prior
Prior estimate versus actual.

## Forward Revisions
Updated FY bridge.

## Valuation Impact
Target price changed.
"@
    } | ConvertTo-Json -Depth 10) -ExpectedMessage "missing change-map slots: Update Map" -WorkspaceRoot $workspaceRoot
}

[ordered]@{
    workspace_path = $workspaceRoot
    adapter_hook_count = @($adapterPaths).Count
    registry_hook_count = @($registryFullPaths).Count
    smoke_test = [bool]$SmokeTest
    status = "ok"
} | ConvertTo-Json -Depth 5
