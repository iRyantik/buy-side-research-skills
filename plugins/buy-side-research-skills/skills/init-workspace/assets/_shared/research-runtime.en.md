# Research Runtime

Shared runtime baseline for all research skills. Each research skill's `## Research Runtime Capsule` references this file instead of repeating declarations.

Hook-enforced rules (source boundary, structure floor, table render, mermaid syntax) are enforced by workspace hooks and not restated here.

---

## 1. Data Pipeline

```
/financial-data --lite <TICKER>
  → _cache/financial-data/internal/actuals-resolved.json
```

- Default `--lite`: returns `latest_fy` + `latest_quarter`
- Multi-period appendix: `--lite --periods 3Y` (writes `fy_y2/y1/y0` + `sub_0/1/2/3`)
- All provider routing, trust ranking, and market-data fallback chains execute inside financial-data
- Consuming skills read directly from `actuals-resolved.json` — do not repeat provider/tier declarations

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
2. Register company/industry reference in `index.md`
3. Update `COVERAGE.md` (if present)

See `references/policy/research-policy-baseline.md` §9-11.
