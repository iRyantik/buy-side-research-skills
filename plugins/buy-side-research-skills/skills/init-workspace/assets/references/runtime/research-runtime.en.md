# Research Runtime

Shared runtime baseline for all research skills. Each research skill's `## Research Runtime Capsule` references this file instead of repeating declarations.

Hook-enforced rules (source boundary, structure floor, table render, mermaid syntax) are enforced by workspace hooks and not restated here.

---

## 1. Data Pipeline

```
/financial-data <TICKER>
  → _cache/financial-data/internal/actuals-resolved.json
```

- Default Lite: `/financial-data <ticker>` → latest FY + latest Q/H (~46 fields)
- Full mode: `/financial-data <ticker> --mode full` → 5 FY + 4 Q/H (~72 fields)
- Flexible periods: `/financial-data <ticker> --periods FY2020-FY2025`
- Period keys read dynamically from provider values dict (e.g. `"FY 2025"`); do not hardcode `fy_y2/y1/y0`
- All provider routing, trust ranking, and market-data fallback chains execute inside financial-data
- Consuming skills read directly from `actuals-resolved.json` — do not repeat provider/tier declarations
- **Sync artifacts after actuals update**: any field modified → find all artifacts referencing that ticker → sync numbers, conclusions, valuations (rule details in workspace `CLAUDE.md` §5.5)

---

## 2. Source Verification Chain

```
python _scripts/shared/verify-claim.py <url>
```

Automated Tier 1→2→3 fallback:

| Tier | Method | Description |
|---|---|---|
| 1 | HTTP GET | `urllib.request`, 30s timeout, extract visible text |
| 2 | Playwright MCP | Script outputs instruction; agent executes `browser_navigate` + `browser_snapshot` |
| 3 | curl | Subprocess `curl -sL`, last resort |
| 4 | [UNVERIFIED] | All tiers exhausted, mark `[UNVERIFIED]` |

Usage:
```
# First attempt
python _scripts/shared/verify-claim.py <url> --json

# If Tier 1 fails → script outputs Playwright instruction → agent executes → feed back
python _scripts/shared/verify-claim.py <url> --playwright-text "<snapshot>"
```

In skill artifacts, every [I#] source must pass at least Tier 1-2 verification (hook: `evidence_ledger_floor`).

### 2.2 Source Discipline

**Core rule: Never write claims using numbers from WebSearch summaries.** Market share, growth rates, order amounts, customer counts, precision specs — every number must be verified by opening the source page with your own eyes. Summaries may be right; they may be wrong.

**Verification chain (mandatory)**:
```
1. WebSearch returns summary → find candidate URL
2. WebFetch / Playwright browser_navigate opens that URL
3. Find the number in the original page → confirm URL matches number ✅ → write to artifact
4. Number NOT found in original page → mark [needs verification] or find new source
```

**Source Priority (mandatory)**:

```
1. actuals-resolved.json    Local cache, machine-collected, zero latency, highest confidence
   -> Read [S#](url) tags from source_map field. Do not write bare [actuals] in artifacts.

2. [S#] Company disclosure  IR PDF, annual report, AGM presentation, earnings transcript
   -> Fields not in actuals: order details, management quotes, product roadmap, capacity plans
   -> verify-claim.py to verify source text -> label [S1-S9]

3. [I#] Third-party         Industry reports, news media, Yahoo Finance, sell-side reports
   -> actuals and company disclosure don't cover: market share, TAM, competitive landscape, targets, consensus
   -> verify-claim.py to verify source text -> label [I1-I20]

One claim = one source at the highest priority.
Example: Revenue -> already in actuals -> don't label [S1]. Q1 orders -> not in actuals -> [S1]. TSMC 60%+ -> company doesn't disclose -> [I1].
```

**Forbidden**:
- ❌ Summary says "50%+ market share" → attach a plausible-looking URL → write to artifact
- ❌ Multiple unverified claims under one URL
- ❌ Personal blogs as industry data sources
- ❌ Source label doesn't match actual page content (label says "product page" but page is about lasers)

**Self-check — after reading this section, confirm**:
- What's the difference between [S#] and [I#]? Where does Revenue data come from — [S1] or [I1]?
- WebSearch summary says TSMC has 60% share. Can you use that directly? What should you do next?


### 2.1 Material Collection

```
python _scripts/shared/web-extract.py <url> [--markdown]          # clean body text from web pages
python _scripts/shared/pdf-extract.py <file_or_url> [--tables]    # PDF text + tables
```

| Tool | Purpose | Engine chain |
|---|---|---|
| `web-extract.py` | Extract clean body text (strip nav/ads/scripts) | `urllib` HTTP GET → HTML parser → clean text |
| `pdf-extract.py` | Extract PDF text + structured tables | pymupdf → pdfplumber → pypdf fallback |

Agent calls these directly when collecting web/PDF content — do not reinvent.

---

## 3. Evidence Protocol

Subagent evidence card format: `references/policy/evidence-card-schema.json`.

Main agent extracts 1-3 evidence triplets per card, embedded as:

```
claim: <key factual claim>
evidence: <supporting data>
source: [S#](url) or [I#](url)
```

Minimum 1 triplet (3 lines) required by `subagent_protocol` hook.

---

## 2.5 Image Download

```
python _scripts/shared/download-image.py --logo <TICKER>         # Logo mode (auto cache + naming)
python _scripts/shared/download-image.py <url> --output <slug>   # Product/equipment image
```

Automated Tier 1→2 fallback:

| Tier | Method | Description |
|---|---|---|
| 1 | HTTP | `urllib` direct download; logo mode auto-checks Google Finance→Wikipedia→Company homepage |
| 2 | Playwright MCP | Script outputs instruction; agent executes `browser_navigate` + `browser_evaluate` to extract base64 |
| 3 | `[missing]` | All tiers exhausted, mark `[missing image]` |

Cache: `_cache/images/` + `.cache.json` index, workspace-level, cross-skill shared. Same ticker logo downloads once.

Logo naming: `<TICKER>-logo.{ext}` (auto). Product naming: `<slug>.{ext}` (manual `--output`).

**Forbidden**: `browser_take_screenshot` for image capture — hook `pre_write_gate` CHECK 6a blocks it.

---

## 4. Artifact Output Contract

### 4.1 Structure Floor

- §0 Task Definition → §1 Conclusion First → §2-§N Body → `## Resources` → `## Appendix`
- Tables must have separator rows; header/separator/data column counts must match
- Mermaid diagrams must use valid types (`quadrantChart` not `scatterchart`, `flowchart` not `waterfall`)

### 4.2 Hook Defense

| Hook | Checks |
|---|---|
| `pre_write_gate` | source anchors, paragraph density, image existence, mermaid type, table structure |
| `source_contract` | bare anchors, invalid source labels, Resources section format |
| `table_render_integrity` | column count consistency, separator row presence |
| `mermaid_syntax` | diagram type validity |
| `skill_structure_contract` | required section presence |
| `evidence_ledger_floor` | Tier 2 verification coverage ≥80% |

### 4.3 Appendix

```
python _scripts/financial-data/actuals-to-appendix.py --tickers <T1>,<T2>,...
```

**Must execute BEFORE writing the artifact body.** Embed output in `## Appendix` section. Never leave a placeholder.

---

## 5. Save Contract

### 5.1 Path

```
industry/<industry>/companies/<ticker>/YYYY-MM-DD-<artifact>.md     # company-level
industry/<industry>/YYYY-MM-DD-<artifact>.md                        # industry-level
```

### 5.2 Auto-Scaffolding

Agent completes before saving artifact:
1. `mkdir -p` missing directories
2. Register company/industry reference in `RESEARCH.md`
3. Update `COVERAGE.md` (if present)

See `references/policy/research-policy-baseline.md` §9-11.

---

## 6. Pre-Artifact Checklist

**After writing the artifact body, before saving — go through each item. Any FAIL → fix first, don't save.**

```
□ 1.  Every number comes from actuals (Tier 0) or WebFetch/Playwright verified original page (Tier 1-2), NOT WebSearch summary
□ 2.  Every [S#]/[I#] has a corresponding entry in evidence ledger (hook: evidence_ledger_floor Rule 0)
□ 3.  Every [I#] has ≥1 Tier 1-2 verification record (hook: evidence_ledger_floor Rule 4)
□ 4.  No bare [actuals] (§2.2: read [S#] tags from source_map)
□ 5.  No browser_take_screenshot (use download-image.py)
□ 6.  Images downloaded to _cache/images/, cache index updated
□ 7.  [missing] only used after all tiers exhausted, ledger has attempt record
□ 8.  [needs verification] count ≤ 8 (hook: pre_write_gate CHECK 8)
□ 9.  Table header/separator/data column counts match, ≤12 columns (hook: pre_write_gate CHECK 13)
□ 10. Mermaid diagrams use valid types (quadrantChart not scatterchart) (hook: mermaid_syntax)
□ 11. `## Resources` section format correct, each label is [S#] or [I#]
□ 12. `## Appendix: Financial Data` embedded (actuals-to-appendix.py ran first, no placeholder)
```
