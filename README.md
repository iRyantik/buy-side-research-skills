# Buy-Side Research Skills — AI Research Toolkit

> v5.14.4 | Claude Code + Codex Dual-Host | [iRyantik/buy-side-research-skills](https://github.com/iRyantik/buy-side-research-skills)
>
> 中文版：[README.cn.md](./README.cn.md)

---

## 0. Install

Tell Claude or Codex:

```
Follow https://github.com/iRyantik/buy-side-research-skills/blob/main/docs/install.md to install buy-side-research-skills
```

---

## 0a. Upgrade

Tell Claude or Codex:

```
/update-agent-runtime
```

Automatically pulls the latest GitHub release, updates the plugin version, and syncs workspace hooks. Run once after each release.

---

---

## 1. Additional Configuration

| Need | How to Get It |
|---|---|
| **SEC EDGAR Identity** | Tell Claude "Set EDGAR identity to Name, Email" |
| **DART API Key** (Korea) | Free registration at [dart.fss.or.kr](https://dart.fss.or.kr), tell Claude "Set DART_API_KEY to xxx" |
| **EDINET Tools** (Japan) | Tell Claude "Install EDINET dependencies." Data from [disclosure.edinet-fsa.go.jp](https://disclosure.edinet-fsa.go.jp), free |
| **EU ESEF Package** | Download annual report from company IR page (iXBRL, .zip containing .xhtml). Provide file path to financial-data |
| **ingest Document Conversion** | Tell Claude "Check ingest dependencies" — auto-detects and prompts for installation |
| **Longbridge Account** | Register at [longbridge.com](https://longbridge.com), tell Claude "Connect Longbridge" |

> Unlisted skills require no configuration — ready to use out of the box.

### Runtime Requirements

`/init-workspace` checks and auto-installs all dependencies. One command, zero manual setup.

| Dependency | Purpose | Required |
|---|---|---|
| Python 3.10+ | All script execution | ✅ Required |
| Node.js ≥18 + npx | Playwright MCP (Tier 2 data verification, image download) | ✅ Required |
| curl | Tier 3 fallback data extraction | ✅ Required |

> `/init-workspace` will auto-install missing dependencies via `winget` (Windows) or `brew` (macOS). See `docs/install.md` for manual setup.

---

## 2. Quick Start: Two Core Workflows

### Industry-First (Find Opportunities)

```
Step 1: teach-in              → Build physical intuition for an unfamiliar industry ~20min
Step 2: industry-landscape    → Full industry picture: value pool, competitive landscape, company registry ~20min
Step 3: mechanism-insight     → Deep-dive key segments (die bonding, coupling, burn-in, CPO divergence) ~30min
Step 4: market-sizing         → TAM breakdown (CPO burn-in $1.2B, coupling $2.8B) ~15min
Step 5: candidate-screener    → 3-regime scenario-based L/S ranking + 7 strategy archetypes ~40min
  ├→ scenario-model           → CPO >15% scenario: AEHR theoretical market cap +148%
  └→ peer-deep-dive           → Top 5 cross-market comparison, unified USD, growth-adjusted PEG
```

### Company-First (Deep-Dive a Single Name)

```
Step 1: stock-quickread       → 5-minute first pass: business overview, focus products, financial tables,
                                  growth drivers & KPIs, cycle position, 5 deep questions ~30min
  ├→ Equipment company → mandatory backlog/orders/ASP/B2B; process industry → output/cost/utilization
  └→ Auto-route next: moat-analysis / catalyst-map / capital-allocation
Step 2: financial-data --lite → Financial statements + market snapshot ~15s
Step 3: driver-map            → Decompose drivers (organic vs M&A / price vs volume / backlog visibility)
                                  + Growth Quality (leading indicator / margin trajectory) ~30min
Step 4: moat-analysis         → Five-dimension scoring + peer benchmarking + Hard/Medium/Soft evidence + Killer Question
  ├→ catalyst-map             → Probability-weighted catalyst chain + payoff ratio + timeline
  └→ capital-allocation       → 10Y buyback/M&A/dividend/capex ROI + moat bridge
Step 5: consensus-map         → Consensus-implied growth vs. PE-implied growth — where's the gap?
Step 6: scenario-model        → Bull/base/bear odds memo + Growth/Margin/Multiple three-dimensional driver mix + sensitivity
Step 7: alpha-thesis          → Thesis + kill criteria + next catalyst
```

---

> 📖 **Don't want to read docs?** Follow a real case study: [/examples/optical-module-equipment/](examples/optical-module-equipment/) — from zero knowledge to scenario-based L/S ranking, 5-step conversation log.

---

## 3. Complete Skill Catalog (39 skills)

### Triage Layer

| Skill | One-Liner | Trigger |
|---|---|---|
| `stock-quickread` | First pass on an unfamiliar company | "Run stock-quickread on xxx" |
| `information-impact` | Verify a single claim or rumor | "Is this news credible?" |
| `meeting-minutes` | Structure and RAG-verify meeting transcripts | "Structure this call transcript" 🆕 |
| `next-step` | What to research next | "What should I look at next?" |
| `post-earnings-quick` | 5-minute post-earnings verdict | "xxx just reported, quick take" |
| `reddit-sentiment` | Social media sentiment check | "What's Reddit saying?" |

### Foundation Layer

| Skill | One-Liner | Trigger |
|---|---|---|
| `teach-in` | Zero-to-one physical intuition | "What is an optical module?" |
| `industry-landscape` | Full industry picture + investment thesis | "Run industry-landscape on xxx sector" |
| `financial-data` | Financial statements + market snapshot | "Pull xxx financials" |
| `market-sizing` | TAM / SAM / SOM breakdown | "How big is this market?" |
| `mechanism-insight` | Deep-dive a single mechanism or equipment chain | "How does a die bonder work?" |
| `driver-map` | Revenue / margin driver decomposition | "What drives xxx's revenue?" |
| `company-history` | Business evolution + disclosure history | "How did xxx become what it is?" |
| `consensus-map` | Market expectations + priced-in gap | "What is the market expecting from xxx?" |

### Deep-Work Layer

| Skill | One-Liner | Trigger |
|---|---|---|
| `candidate-screener` | Scenario-based L/S ranking (7 strategy archetypes) | "How do these names rank?" |
| `scenario-model` | Bull/base/bear odds memo + assumption tracing | "What is AEHR worth if CPO hits 15%?" |
| `peer-deep-dive` | Cross-market peer comparison | "Compare these names" |
| `moat-analysis` | Competitive barrier quantification | "How strong is xxx's moat?" |
| `catalyst-map` | Catalyst timeline + probability weighting | "What catalysts does xxx have?" |
| `capital-allocation` | Management capital allocation 10Y ROI | "How well does xxx management allocate capital?" |
| `earnings-setup` | Pre-earnings preparation | "xxx is about to report — how to set up?" |
| `alpha-thesis` | Investment thesis | "Write the thesis for xxx" |
| `bear-pre-mortem` | Short-side pre-mortem | "How does xxx die?" |
| `pair-trade` | L/S pair analysis | "Long A short B — does it work?" |
| `primary-research-plan` | Expert calls, channel checks, surveys | "How to verify xxx hypothesis?" |
| `3-statement-model` | Full financial model | "Build a model for xxx" |
| `dcf-model` | DCF valuation | "Value xxx using DCF" |
| `comps-analysis` | Comparable company analysis | "Value xxx using comps" |

### Supporting Layer

| Skill | One-Liner | Trigger |
|---|---|---|
| `research-viz` | Visualization | "Turn this into a chart" |

### Memory Layer

| Skill | One-Liner | Trigger |
|---|---|---|
| `research-journal` | Capture earned research insights | "Record today's findings" |
| `coverage-tracker` | Track coverage status and priorities | "Update coverage priorities" |

---

## 4. FAQ

**Q: Can't pull financial data?**
Tell Claude `Check financial-data dependencies`.

**Q: US stock earnings throwing errors?**
Configure EDGAR identity. Tell Claude `Set EDGAR identity to Name, Email`.

**Q: How to connect Longbridge?**
Tell Claude `Connect Longbridge`. Required for US/HK/SH/SZ only.

**Q: How to get Japan/Korea/Europe stock data?**
See §1 configuration table. Japan: free. Korea: requires API key. Europe: requires ESEF package download.

**Q: How to update the plugin?**
Tell Claude `/update-agent-runtime`. Automatically pulls the latest GitHub release, updates plugin + syncs workspace hooks. Run once after each new release.

---

## 5. Version History

| Version | Date | Key Changes |
|---|---|---|
| v5.14.4 | 2026-06-09 | All consumer skills: `/financial-data` → Skill tool + CLI fallback. EN capsule `references/` → workspace `.references/`. Path sweep: `_scripts/` → `.scripts/` residuals fixed. |
| v5.14.3 | 2026-06-09 | stock-quickread pipeline bug fixes: Step 1 direct CLI (--identifier not --ticker), actuals-to-appendix search path update, evidence_ledger -t flag required, PYTHONIOENCODING note |
| v5.14.2 | 2026-06-08 | Pipeline discipline enforcement: CLAUDE.md §6 Workflow Execution Discipline (8 rules), Capsule GATE strengthened (50+ files), stock-quickread pipeline command hardening, pre_write_gate CHECK 15 (pipeline report header) |
| v5.14.1 | 2026-06-08 | Hide `.obsidian/` and `*.sh` in VSCode file tree |
| v5.14.0 | 2026-06-08 | Workspace restructure: hide non-user-facing dirs (`.references/`, `.scripts/`, `.memory/`, `.vscode/settings.json`), bilingual init (ZH/EN templates), `_inbox/` stays visible, remove `.gitignore`. All Python scripts: `_scripts/`→`.scripts/` paths + Windows encoding fix (`sys.stdout.reconfigure`). SKILL.md batch: `references/`→`.references/`, GATE lines on all capsules, stock-quickread HARD GATE. New: `fix-bare-anchors.py` (batch fix bare source anchors). evidence_ledger hook: accept both artifact-stem and ticker-based naming. |
| v5.13.15 | 2026-06-08 | update-agent-runtime: Python script automates full pipeline — GitHub fetch → cache populate → marketplace refresh → workspace sync → verify. Single command, stdlib only. |
| v5.13.14 | 2026-06-08 | init-workspace: remove venv, `pip install --user` global install (no admin/sudo, designed for blank machines) |
| v5.13.13 | 2026-06-08 | Financial-data cache restructure: remove `datasets/` middle layer (`_raw/financial-data/`, `_cache/financial-data/`), eliminate `internal/` subdirectory (14 files → 4: actuals-resolved.json, evidence-pack.json, full-filing.md, summary.md), drop copytree of `_raw`, rename `financial-data-summary.md` → `summary.md`. SEC provider cache leak fix (`_provider_cache_dir()` cross-platform). download-image.py logo priority reorder (Wikipedia → Homepage → Google Finance), `_ticker_to_domain` expanded to ~180 entries. verify-runtime.py npx.cmd + node_js key bugfixes. |
| v5.13.12 | 2026-06-08 | Concept mapping (_load_concept_map from statement-line-items.md across 7 markets, _map_concept, SEC XBRL concept map 60+ entries), get_fields() consumer helper (lite/full field filter), 3Y→5Y + fy_y2/y1/y0→dynamic FY key docs alignment, financial-data SKILL.md/en.md consumer contract update |
| v5.13.11 | 2026-06-05 | PDF auto-cache hook (multi-market IR/filing detection + auto to-markdown + delete PDF), cache-first rule in research-runtime + CLAUDE.md, to-markdown.py --rm --auto flags, common.py .pdf path detection |
| v5.11.1 | 2026-06 | Pre-write gate 11 CHECK hardening, topics→industry full migration, meeting-minutes skill, §9 single-industry residence + §10 segment priority, source badge removal, CONTEXT.md |
| v5.6.0 | 2026-06 | RAG 4-tier fallback (WebFetch→Playwright→curl→[UNVERIFIED]), evidence ledger (ticker-scoped cross-artifact reuse), sentence-level anchors across all skills, 16 hook regression tests, actuals source_map provenance |
| v5.4.0 | 2026-06 | Source contract full injection: 27 skill output tables with Ev column, paragraph-level source density hook, table-row financial number check |
| v5.3.0 | 2026-06 | Actuals-only ratio constraint: 17 skills prohibited from using FY2026E/consensus/forward estimates in ratios |
| v5.2.1 | 2026-06 | Directory-level auto-discovery: new skill scripts deploy with zero changes. Meta-skill directory spec |
| v5.1.0 | 2026-06 | Python unified bootstrap, init-workspace rewrite (Class A+B deployment manifest), interactive provider configuration |
| v5.0.0 | 2026-06 | 7 new skills, candidate-screener scenario-based L/S, full-chain hook governance, cross-market consolidation, fact governance layer, Codex dual-host |
| v4.6.2 | 2026-05 | Runtime Capsule standardization, market data trust-based fill, C-level modeling hooks |
| v4.5.6 | 2026-05 | mechanism-insight/industry-landscape/teach-in renamed, peer-deep-dive restructured |
