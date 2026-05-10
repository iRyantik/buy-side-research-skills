param()

$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")

$requirements = @{
    'skills/alpha-thesis/SKILL.md' = @(
        '### Primitive Preflight',
        '## Primitive Handoff Required',
        'Variant View',
        'Kill Criteria',
        'price-volume-mix',
        'driver-map'
    )
    'skills/peer-deep-dive/SKILL.md' = @(
        '0A.',
        'Preflight',
        '## Primitive Handoff Required',
        'Mechanism / value-capture',
        'KPI',
        'mechanism-map',
        'driver-map'
    )
    'skills/bear-pre-mortem/SKILL.md' = @(
        '## Mechanism Assumption Audit',
        '## Primitive Handoff Required',
        'Unit Economics',
        'Value capture',
        'mechanism-map',
        'driver-map'
    )
    'skills/earnings-setup/SKILL.md' = @(
        'Primitive Readiness',
        '## Primitive Handoff Required',
        'mechanism_map_trigger',
        'driver_map_trigger',
        'mechanism-map',
        'driver-map'
    )
}

$failures = New-Object System.Collections.Generic.List[string]

foreach ($relativePath in $requirements.Keys) {
    $path = Join-Path $repoRoot $relativePath

    if (-not (Test-Path -LiteralPath $path)) {
        $failures.Add("Missing target skill: $relativePath")
        continue
    }

    $text = Get-Content -Raw -Encoding UTF8 -LiteralPath $path
    $h1 = [regex]::Match($text, "(?m)^# ")

    if (-not $h1.Success) {
        $failures.Add("${relativePath}: missing first H1 heading; cannot isolate body from capsule")
        continue
    }

    # Only inspect content from the first H1 onward so the shared capsule cannot satisfy routing checks.
    $body = $text.Substring($h1.Index)

    foreach ($phrase in $requirements[$relativePath]) {
        if (-not $body.Contains($phrase)) {
            $failures.Add("${relativePath}: body is missing primitive routing anchor '$phrase'")
        }
    }

    if ($relativePath -eq 'skills/earnings-setup/SKILL.md') {
        $readinessCount = ([regex]::Matches($body, [regex]::Escape("Primitive Readiness"))).Count
        if ($readinessCount -lt 2) {
            $failures.Add("${relativePath}: expected Primitive Readiness in both pre-print and post-print modes")
        }
    }
}

if ($failures.Count -gt 0) {
    Write-Host "Primitive routing validation failed:" -ForegroundColor Red
    foreach ($failure in $failures) {
        Write-Host " - $failure" -ForegroundColor Red
    }
    exit 1
}

Write-Host "Primitive routing validation passed for $($requirements.Count) deep research skills." -ForegroundColor Green
