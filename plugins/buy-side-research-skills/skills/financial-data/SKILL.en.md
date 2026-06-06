---
name: financial-data
description: Acquire evidence and commit source-tracked canonical financial facts.
---

# Financial Data

`financial-data` is the unified acquisition and canonical facts pipeline. Providers, PDF extractors, web gap-fillers, and hooks may only produce candidates. Only `FactsRepository` may write the canonical store. `actuals-resolved.json` remains permanently available as a generated read-only compatibility view.

## CLI

```powershell
python _scripts/financial-data.py fetch <ticker> --profile lite
python _scripts/financial-data.py fetch <ticker> --profile full
python _scripts/financial-data.py fetch <ticker> --profile lite --from FY2018 --to FY2025
python _scripts/financial-data.py fetch <ticker> --profile full --from 2022-01-01 --to latest
python _scripts/financial-data.py render <ticker>
python _scripts/financial-data.py migrate <ticker|--all>
python _scripts/financial-data.py check-deps [--group <name>]
```

When `--market` is omitted, the CLI performs best-effort market inference from common ticker suffixes and shapes. In a fresh workspace with no company topic yet, `fetch` creates `industry/uncategorized/companies/<ticker>/` as the default destination so the `stock-quickread` zero-to-one workflow does not require manual directory setup.

## Lite / Full

Lite/Full controls field breadth, document depth, evidence, and validation strength only. It does not control the time range.

| Dimension | Lite | Full |
|---|---|---|
| Default periods | Latest complete FY + latest interim | Latest 5 complete FY + current-FY interim |
| Custom periods | Arbitrary `--from/--to` | Arbitrary `--from/--to` |
| Fields | Core statements, major segments, key supplementary fields | All mappable standard fields in the requested range |
| Documents | Targeted gap fill | Full acquisition, conversion, and indexing |
| Validation | Core gates, periods, units, major conflicts | Full-field reconciliation, completeness, and audit |

`--from/--to` filters inclusively by `period_end` and accepts `earliest`, `latest`, `YYYY-MM-DD`, and `FY2024`. Legacy `--periods 3Y` remains for one version and means the latest three available complete FYs plus current interim.

## Stores

```text
_cache/financial-data/internal/
  facts-store.json
  market-snapshots.jsonl
  consensus-snapshots.jsonl
  actuals-resolved.json

_cache/datasets/financial-data/<provider>/<run-id>/
_raw/datasets/financial-data/<provider>/<run-id>/
```

Every canonical fact includes metric, period_id, value, unit, currency, dimensions, source_id, source_layer, status, and confidence. Missing values stay missing. Derived facts must be marked. Lower-trust sources never silently overwrite higher-trust sources. Conflicts are retained.

## Pipeline

```text
resolve identity
→ resolve requested time range
→ acquire provider/source evidence
→ normalize fact candidates
→ merge by trust/period/unit policy
→ reconcile and validate
→ atomically commit canonical stores
→ generate compatibility and human views
```

Local PDF/XLSX/CSV files first go through Source Intake registration and conversion, then enter the pipeline as candidates carrying source ID, page/original label, period, unit, and confidence.
