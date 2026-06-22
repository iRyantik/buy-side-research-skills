# Cache Contract

> Who writes what to `.cache/`, what can be deleted, what must be preserved.

## Directory Layout

```
.cache/                                    ← workspace root: coverage-monitor + shared images
  coverage-monitor/                         ← daily-state.json, enrichment-YYYY-MM-DD.json
  images/                                   ← shared product/logo cache (download-image.py)

industry/<slug>/.cache/                     ← industry-level
  images/                                   ← industry charts, photos
  evidence/                                 ← research evidence packs
  institution/                              ← institutional reports (PDFs, extracts)

industry/<slug>/companies/<ticker>/.cache/  ← company-level
  financial-data/
    internal/
      actuals-resolved.json                 ← source-of-record structured financials
      .raw/                                 ← raw provider payloads, filings, identity sources
  disclosure/                               ← cached company filings (annual reports, quarterly, prospectus)
  driver-map/                               ← driver-map artifact cache + history
  datasets/                                 ← scraped/scrapi datasets (reddit-sentiment, etc.)
  evidence/                                 ← claim evidence packs
  images/                                   ← company/product images

industry/<slug>/panorama/<artifact>/.cache/ ← artifact-level
  evidence/                                 ← per-artifact evidence
```

## Per-Skill Contract

| Skill | Writes to | Rebuildable? | Notes |
|---|---|---|---|
| `financial-data` | `companies/<ticker>/.cache/financial-data/` | Yes | `actuals-resolved.json` is source-of-record; `.raw/` contains cacheable payloads |
| `stock-quickread` | `companies/<ticker>/.cache/disclosure/`, `images/` | Yes | Disclosure PDFs re-fetchable from primary sources |
| `coverage-monitor` | `.cache/coverage-monitor/` | Yes | `daily-state.json` overwritten each run; `enrichment-*.json` per-date |
| `download-image.py` | `.cache/images/`, `companies/<ticker>/.cache/images/` | Yes | URL-based cache key; re-download if missing |
| `driver-map` | `companies/<ticker>/.cache/driver-map/` | No | Contains history snapshots; keep for audit trail |
| `ingest` | `companies/<ticker>/.cache/disclosure/` | Yes | Ingested filings re-fetchable |
| `primary-research-plan` | `companies/<ticker>/.cache/datasets/` | Maybe | Scraped datasets may be expensive to re-fetch |
| `mechanism-insight` | `panorama/<artifact>/.cache/evidence/` | Yes | Evidence re-fetchable |
| `industry-landscape` | `panorama/<artifact>/.cache/evidence/` | Yes | Evidence re-fetchable |
| `teach-in` | `panorama/<artifact>/.cache/evidence/` | Yes | Evidence re-fetchable |
| `peer-deep-dive` | `companies/<ticker>/.cache/evidence/` | Yes | Evidence re-fetchable |
| All (evidence packs) | `companies/<ticker>/.cache/evidence/` | Yes | Evidence ledger-managed |

## Deletion Rules

- **Safe to delete**: `.cache/coverage-monitor/`, `.cache/images/`, `disclosure/`, `evidence/`, `datasets/`
- **Preserve**: `financial-data/actuals-resolved.json`, `driver-map/history/`
- **Check first**: `.raw/` — contains primary-source snapshots; if `actuals-resolved.json` exists and is fresh (<180d), `.raw/` can be regenerated

## Naming Convention

- Cache directory names use dot prefix: `.cache/`, `.raw/`, `.inbox/`, `.shots/`
- No underscore-prefixed cache directories (`_cache`, `_raw`, `_images`) — migrated to dot prefix 2026-06-22
