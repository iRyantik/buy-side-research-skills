# Cache Contract

> Who writes what to which cache, what can be deleted, what must be preserved.

## Visibility Rules

| Path | VSCode | Rationale |
|---|---|---|
| `**/.cache/` | Hidden | All caches: coverage-monitor state, financial data, disclosures, evidence |
| `**/.raw/` | Hidden | Raw provider payloads |
| `**/.inbox/` | Hidden | Industry/company-level inbox |
| `inbox/` (root) | Visible | Workspace inbox, daily use |
| `**/models/` | Visible | Financial model files, researcher needs to open |

## Directory Layout

```
.cache/                                    ← workspace root: coverage-monitor state (hidden)
  coverage-monitor/                         ← daily-state.json, enrichment-YYYY-MM-DD.json
  images/                                   ← shared product/logo cache (download-image.py)

industry/<slug>/
  .cache/                                   ← industry-level cache (hidden)
  .inbox/                                   ← incoming materials (hidden)
  .raw/                                     ← raw payloads (hidden)

  companies/<ticker>/
    .cache/                                 ← company-level cache (hidden)
      financial-data/                       ← actuals-resolved.json, summary.md
        .raw/                               ← raw provider payloads (hidden)
      disclosure/                           ← cached company filings
      driver-map/                           ← driver-map artifact cache + history
      datasets/                             ← scraped/scrapi datasets
      evidence/                             ← claim evidence packs
      images/                               ← company/product images
    models/                                 ← visible
    .inbox/                                 ← hidden
    .raw/                                   ← hidden
```

## Per-Skill Contract

| Skill | Writes to | Rebuildable? |
|---|---|---|
| `financial-data` | `cache/financial-data/` | Yes (providers re-fetchable) |
| `coverage-monitor` | `.cache/coverage-monitor/` | Yes (recreated each run) |
| `stock-quickread` | `cache/disclosure/`, `cache/images/` | Yes |
| `driver-map` | `cache/driver-map/` | No (history snapshots) |
| `ingest` | `cache/disclosure/` | Yes |
| `mechanism-insight` | `cache/evidence/` | Yes |
| `industry-landscape` | `cache/evidence/` | Yes |
| `teach-in` | `cache/evidence/` | Yes |
| `peer-deep-dive` | `cache/evidence/` | Yes |
| `download-image.py` | `cache/images/` | Yes |

## Deletion Rules

- **Safe**: `.cache/coverage-monitor/`, `cache/disclosure/`, `cache/evidence/`, `cache/images/`
- **Preserve**: `cache/financial-data/actuals-resolved.json`, `cache/driver-map/history/`
- **Check first**: `.raw/` — regeneratable if actuals-resolved.json fresh (<180d)
