param(
    [Parameter(Mandatory = $true)]
    [string]$Version,

    [string]$ZipPath
)

$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
if ([string]::IsNullOrWhiteSpace($ZipPath)) {
    $ZipPath = Join-Path $repoRoot "dist\buy-side-research-skills-$Version.zip"
}

$failures = New-Object System.Collections.Generic.List[string]

if (-not (Test-Path -LiteralPath $ZipPath)) {
    $failures.Add("Release zip does not exist: $ZipPath")
} else {
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $zip = [System.IO.Compression.ZipFile]::OpenRead((Resolve-Path $ZipPath))

    try {
        $entryNames = @($zip.Entries | ForEach-Object { $_.FullName.Replace("\", "/") })
        $entrySet = New-Object "System.Collections.Generic.HashSet[string]"
        foreach ($name in $entryNames) {
            [void]$entrySet.Add($name)
        }

        function Require-Entry {
            param([string]$Entry)

            if (-not $entrySet.Contains($Entry)) {
                $script:failures.Add("Missing release entry: $Entry")
            }
        }

        function Require-Prefix {
            param([string]$Prefix)

            if (-not ($entryNames | Where-Object { $_.StartsWith($Prefix) } | Select-Object -First 1)) {
                $script:failures.Add("Missing release prefix: $Prefix")
            }
        }

        function Get-ZipEntryText {
            param([string]$Entry)

            $match = $zip.Entries | Where-Object { $_.FullName.Replace("\", "/") -eq $Entry } | Select-Object -First 1
            if (-not $match) {
                return $null
            }

            $stream = $match.Open()
            try {
                $reader = [System.IO.StreamReader]::new($stream, [System.Text.Encoding]::UTF8)
                try {
                    return $reader.ReadToEnd()
                } finally {
                    $reader.Dispose()
                }
            } finally {
                $stream.Dispose()
            }
        }

        foreach ($required in @(
            ".claude-plugin/plugin.json",
            ".codex-plugin/plugin.json",
            "skills/company-primer/SKILL.md",
            "skills/company-primer/skill.yaml",
            "skills/init/SKILL.md",
            "skills/init/skill.yaml",
            "skills/init/assets/CLAUDE.md.template",
            "skills/init/assets/AGENTS.md.template",
            "skills/init/assets/gitignore.template",
            "skills/init/assets/edge-radar.md",
            "skills/init/scripts/init-research-workspace.ps1",
            "skills/ingest/SKILL.md",
            "skills/ingest/skill.yaml",
            "skills/ingest/assets/requirements-ingest.txt",
            "skills/ingest/scripts/ingest.py",
            "skills/ingest/scripts/ingest_xlsx.py",
            "skills/ingest/scripts/ingest_table_crosscheck.py",
            "skills/ingest/scripts/bootstrap-ingest-deps.ps1",
            "skills/meta-skill/SKILL.md",
            "skills/meta-skill/skill.yaml",
            "skills/new-session/SKILL.md",
            "skills/new-session/skill.yaml",
            "docs/install.md",
            "docs/architecture.md",
            "README.md"
        )) {
            Require-Entry $required
        }

        foreach ($prefix in @("skills/", "docs/", "examples/")) {
            Require-Prefix $prefix
        }

        $forbiddenPrefixes = @(".git/", ".claude/", "dist/", "scripts/", ("archive" + "/"))
        foreach ($forbidden in $forbiddenPrefixes) {
            if ($entryNames | Where-Object { $_.StartsWith($forbidden) } | Select-Object -First 1) {
                $failures.Add("Release zip includes forbidden prefix: $forbidden")
            }
        }

        $forbiddenFiles = @(
            "RTK.md",
            "AGENTS.md",
            "CLAUDE.md",
            ("FRAMEWORK" + ".md"),
            ("META-SKILL" + ".md"),
            "docs/release.md"
        )
        foreach ($forbiddenFile in $forbiddenFiles) {
            if ($entrySet.Contains($forbiddenFile)) {
                $failures.Add("Release zip includes forbidden file: $forbiddenFile")
            }
        }

        $activeSkillNames = New-Object "System.Collections.Generic.HashSet[string]"
        foreach ($entry in $entryNames) {
            $match = [regex]::Match($entry, "^skills/([^/]+)/SKILL\.md$")
            if ($match.Success -and $match.Groups[1].Value -ne "_shared") {
                [void]$activeSkillNames.Add($match.Groups[1].Value)
            }
        }

        if ($activeSkillNames.Count -ne 19) {
            $failures.Add("Expected 19 active skills in release zip, found $($activeSkillNames.Count): $($activeSkillNames -join ', ')")
        }

        if (-not $activeSkillNames.Contains("company-primer")) {
            $failures.Add("Release zip is missing active skill: company-primer")
        }

        if (-not $activeSkillNames.Contains("init")) {
            $failures.Add("Release zip is missing active skill: init")
        }

        if (-not $activeSkillNames.Contains("ingest")) {
            $failures.Add("Release zip is missing active skill: ingest")
        }

        if (-not $activeSkillNames.Contains("meta-skill")) {
            $failures.Add("Release zip is missing active skill: meta-skill")
        }

        if (-not $activeSkillNames.Contains("new-session")) {
            $failures.Add("Release zip is missing active skill: new-session")
        }

        $claudeManifestText = Get-ZipEntryText ".claude-plugin/plugin.json"
        $codexManifestText = Get-ZipEntryText ".codex-plugin/plugin.json"
        if ($claudeManifestText) {
            $claudeManifest = $claudeManifestText | ConvertFrom-Json
            if ($claudeManifest.version -ne $Version) {
                $failures.Add("Claude manifest version '$($claudeManifest.version)' does not match expected '$Version'")
            }
        }
        if ($codexManifestText) {
            $codexManifest = $codexManifestText | ConvertFrom-Json
            if ($codexManifest.version -ne $Version) {
                $failures.Add("Codex manifest version '$($codexManifest.version)' does not match expected '$Version'")
            }
        }
    } finally {
        $zip.Dispose()
    }
}

if ($failures.Count -gt 0) {
    Write-Host "Release package validation failed:" -ForegroundColor Red
    foreach ($failure in $failures) {
        Write-Host " - $failure" -ForegroundColor Red
    }
    exit 1
}

Write-Host "Release package validation passed for version $Version." -ForegroundColor Green
