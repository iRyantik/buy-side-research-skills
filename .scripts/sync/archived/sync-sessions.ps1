# sync-sessions.ps1
# Merge-based bidirectional sync: .sessions/ <-> ~/.claude/projects/s--/
# Line-level union merge — no message loss when two machines write same session
# Requires: Windows PowerShell 5.1+

$ErrorActionPreference = "Continue"

$scriptDir  = Split-Path -Parent $MyInvocation.MyCommand.Path
$sessions   = [System.IO.Path]::GetFullPath("$scriptDir\..\..\.sessions")
$hash       = "$env:USERPROFILE\.claude\projects\s--"

# ── Config ──────────────────────────────────────────────
$SKIP_MINUTES = 10   # skip files touched within this window (active Claude Code sessions)
# ─────────────────────────────────────────────────────────

if (-not (Test-Path $sessions)) {
    Write-Host "[ERROR] .sessions/ not found at $sessions" -ForegroundColor Red
    exit 1
}

New-Item -ItemType Directory -Force -Path $hash | Out-Null

$stats = @{ copied = 0; merged = 0; skipped = 0; newFiles = 0; active = 0; cleaned = 0 }
$cutoff = (Get-Date).ToUniversalTime().AddMinutes(-$SKIP_MINUTES)

# ── Clean up OneDrive conflict copies ───────────────────
Get-ChildItem -Path $sessions -Recurse -File -ErrorAction SilentlyContinue | ForEach-Object {
    if ($_.Name -match '-(DEREK|iRyantik|DESKTOP-[A-Z0-9]+)(-\(\d+\))?\.jsonl$') {
        Write-Host "  [clean] Removing conflict copy: $($_.Name)" -ForegroundColor Yellow
        Remove-Item -Path $_.FullName -Force -ErrorAction SilentlyContinue
        $stats.cleaned++
    }
}
Get-ChildItem -Path $hash -Recurse -File -ErrorAction SilentlyContinue | ForEach-Object {
    if ($_.Name -match '-(DEREK|iRyantik|DESKTOP-[A-Z0-9]+)(-\(\d+\))?\.jsonl$') {
        Write-Host "  [clean] Removing conflict copy: $($_.Name)" -ForegroundColor Yellow
        Remove-Item -Path $_.FullName -Force -ErrorAction SilentlyContinue
        $stats.cleaned++
    }
}

function Merge-File {
    param($pathA, $pathB)

    try {
        $linesA = @(Get-Content -Path $pathA -Encoding UTF8 | Where-Object { $_.Trim() -ne '' })
        $linesB = @(Get-Content -Path $pathB -Encoding UTF8 | Where-Object { $_.Trim() -ne '' })

        $set = [System.Collections.Generic.HashSet[string]]::new()
        foreach ($l in $linesA) { $set.Add($l) | Out-Null }
        foreach ($l in $linesB) { $set.Add($l) | Out-Null }

        $maxBefore = [Math]::Max($linesA.Count, $linesB.Count)

        if ($set.Count -gt $maxBefore) {
            # Both sides contributed unique lines — write merged
            $merged = @($set)
            $utf8 = New-Object System.Text.UTF8Encoding $false
            [System.IO.File]::WriteAllLines($pathA, $merged, $utf8)
            [System.IO.File]::WriteAllLines($pathB, $merged, $utf8)
            return 'merged'
        }
        else {
            # One side is a subset — sync the larger
            $src = if ($linesA.Count -ge $linesB.Count) { $linesA } else { $linesB }
            $utf8 = New-Object System.Text.UTF8Encoding $false
            [System.IO.File]::WriteAllLines($pathA, $src, $utf8)
            [System.IO.File]::WriteAllLines($pathB, $src, $utf8)
            return 'copied'
        }
    }
    catch {
        # JSON parse failure or IO error → fallback: newer wins
        $tA = (Get-Item $pathA).LastWriteTimeUtc
        $tB = (Get-Item $pathB).LastWriteTimeUtc
        if ($tA -gt $tB) { Copy-Item -Path $pathA -Destination $pathB -Force }
        else              { Copy-Item -Path $pathB -Destination $pathA -Force }
        return 'copied'
    }
}

function Ensure-DirStructure {
    param($src, $dst)
    Get-ChildItem -Path $src -Directory -Recurse -ErrorAction SilentlyContinue | ForEach-Object {
        $rel = $_.FullName.Substring($src.Length).TrimStart('\')
        if ($rel -eq '') { return }
        $target = Join-Path $dst $rel
        if (-not (Test-Path $target)) {
            New-Item -ItemType Directory -Force -Path $target | Out-Null
        }
    }
}

function Get-FileIndex {
    param($root)
    $idx = @{}
    Get-ChildItem -Path $root -Filter "*.jsonl" -Recurse -ErrorAction SilentlyContinue | ForEach-Object {
        $rel = $_.FullName.Substring($root.Length).TrimStart('\')
        $idx[$rel] = $_.FullName
    }
    return $idx
}

# Ensure directory mirroring
Ensure-DirStructure $sessions $hash
Ensure-DirStructure $hash $sessions

# Build indices
$sIdx = Get-FileIndex $sessions
$hIdx = Get-FileIndex $hash

# Collect all unique paths
$allKeys = [System.Collections.Generic.HashSet[string]]::new()
foreach ($k in $sIdx.Keys) { $allKeys.Add($k) | Out-Null }
foreach ($k in $hIdx.Keys) { $allKeys.Add($k) | Out-Null }

$total = $allKeys.Count

foreach ($relPath in $allKeys) {
    $inS = $sIdx.ContainsKey($relPath)
    $inH = $hIdx.ContainsKey($relPath)

    # ── Skip active sessions (recently modified) ─────────
    $skipActive = $false
    if ($inS) {
        $sMtime = (Get-Item $sIdx[$relPath]).LastWriteTimeUtc
        if ($sMtime -gt $cutoff) { $skipActive = $true }
    }
    if ($inH -and -not $skipActive) {
        $hMtime = (Get-Item $hIdx[$relPath]).LastWriteTimeUtc
        if ($hMtime -gt $cutoff) { $skipActive = $true }
    }
    if ($skipActive) {
        $stats.active++
        continue
    }
    # ─────────────────────────────────────────────────────

    if ($inS -and -not $inH) {
        $dst = Join-Path $hash $relPath
        $dir = Split-Path $dst -Parent
        if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
        Copy-Item -Path $sIdx[$relPath] -Destination $dst -Force
        $stats.newFiles++
    }
    elseif ($inH -and -not $inS) {
        $dst = Join-Path $sessions $relPath
        $dir = Split-Path $dst -Parent
        if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
        Copy-Item -Path $hIdx[$relPath] -Destination $dst -Force
        $stats.newFiles++
    }
    else {
        $sFile = Get-Item $sIdx[$relPath]
        $hFile = Get-Item $hIdx[$relPath]

        if ($sFile.Length -eq $hFile.Length -and $sFile.LastWriteTimeUtc -eq $hFile.LastWriteTimeUtc) {
            $stats.skipped++
        }
        else {
            $result = Merge-File -pathA $sFile.FullName -pathB $hFile.FullName
            $stats[$result]++
        }
    }
}

$hashCount     = @(Get-ChildItem "$hash\*.jsonl" -Recurse -ErrorAction SilentlyContinue).Count
$sessionsCount = @(Get-ChildItem "$sessions\*.jsonl" -Recurse -ErrorAction SilentlyContinue).Count

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Claude Code Session Sync" -ForegroundColor Cyan
Write-Host "  mode: merge  |  files: $total" -ForegroundColor Gray
Write-Host "  new: $($stats.newFiles)  copied: $($stats.copied)  merged: $($stats.merged)" -ForegroundColor Green
Write-Host "  skipped: $($stats.skipped)  active: $($stats.active)  cleaned: $($stats.cleaned)" -ForegroundColor Gray
Write-Host "  s-- hash      : $hashCount sessions" -ForegroundColor White
Write-Host "  .sessions     : $sessionsCount sessions" -ForegroundColor White
Write-Host "========================================" -ForegroundColor Cyan
