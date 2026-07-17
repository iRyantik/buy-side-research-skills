# Buy-Side Research Skills

> v8.0.0 | Claude Code + Codex Dual-Host | [iRyantik/buy-side-research-skills](https://github.com/iRyantik/buy-side-research-skills)

A journal-first buy-side equity research skill suite: 39 skills covering triage, foundation, deep-work, and operations layers. Source-tracked, evidence-gated, cross-market.

---

## 0. Install

### VS Code Extension（大部分用户）

Copy this into Claude Code:

```
1. Write "skipWebFetchPreflight": true to ~/.claude/settings.json, then restart CC
2. Follow https://github.com/iRyantik/buy-side-research-skills/blob/main/docs/install-vscode.md to install buy-side-research-skills
```

### CC Terminal

```
/plugin marketplace add iRyantik/buy-side-research-skills
/plugin install buy-side-research-skills
```

## 0a. Upgrade

```
/update-agent-runtime
```

---

## 1. Optional Configuration

| Need | How to get |
|---|---|
| **SEC EDGAR identity** | Tell Claude: "set EDGAR identity to Name, Email" |
| **DART API Key** | Free at [dart.fss.or.kr](https://dart.fss.or.kr), tell Claude: "set DART_API_KEY to xxx" |
| **EDINET Tools** | Tell Claude: "install EDINET dependencies". Free data from [disclosure.edinet-fsa.go.jp](https://disclosure.edinet-fsa.go.jp) |
| **EU ESEF packages** | Download annual report from company IR page (iXBRL, .zip with .xhtml) |
| **ingest doc conversion** | Tell Claude: "check ingest dependencies", auto-detects and prompts |
| **Longbridge account** | Register at [longbridge.com](https://longbridge.com), tell Claude: "connect Longbridge" |

> Unlisted skills work out of the box. Playwright MCP recommended as shared browser capability.

---

## 2. Quick Start

**Industry-first**: `teach-in` → `industry-landscape` → `mechanism-insight` → `market-sizing` → `candidate-screener`

**Company-first**: `stock-quickread` → `financial-data --lite` → `driver-map` → `moat-analysis` → `consensus-map` → `scenario-model` → `alpha-thesis`

📖 Walk through a real case: [/examples/optical-module-equipment/](examples/optical-module-equipment/)

---

## 3. Full Skill List (39 skills)

### Triage Layer

| Skill | One-liner |
|---|---|
| `stock-quickread` | First pass on an unfamiliar company |
| `information-impact` | Verify and assess impact of a piece of news |
| `post-earnings-quick` | 5-min post-earnings judgment |
| `reddit-sentiment` | Social media sentiment analysis |

### Foundation Layer

| Skill | One-liner |
|---|---|
| `teach-in` | Build physical intuition from zero |
| `industry-landscape` | Industry panorama + investment judgment |
| `financial-data` | Structured financials + market snapshot |
| `market-sizing` | TAM/SAM/SOM breakdown |
| `mechanism-insight` | Technical/engineering mechanism deep-dive |
| `driver-map` | Revenue/margin driver decomposition |
| `company-history` | Business evolution + disclosure history |
| `consensus-map` | Market expectations + priced-in analysis |

### Deep-Work Layer

| Skill | One-liner |
|---|---|
| `candidate-screener` | L/S ranking across regimes (7 strategy archetypes) |
| `scenario-model` | Bull/base/bear odds memo + assumption tracing |
| `peer-deep-dive` | Cross-company / cross-market comparison |
| `moat-analysis` | Competitive moat quantitative scorecard |
| `catalyst-map` | Catalyst timeline + probability weighting |
| `capital-allocation` | 10Y management capital allocation ROI |
| `earnings-setup` | Pre-earnings preparation |
| `alpha-thesis` | Investment thesis |
| `bear-pre-mortem` | Short-side pre-mortem |
| `pair-trade` | Long-short pair |
| `primary-research-plan` | Primary research fieldwork plan |

### Supporting

| Skill | One-liner |
|---|---|
| `research-viz` | Turn research into memo-ready charts |

### Memory

| Skill | One-liner |
|---|---|
| `research-journal` | Capture and organize research insights |
| `coverage-tracker` | Track coverage status across companies |

---

## 4. FAQ

**Q: Financial data not pulling?**
Tell Claude: `check financial-data dependencies`.

**Q: US stock filings error?**
Configure EDGAR identity. Tell Claude: `set EDGAR identity to Name, Email`.

**Q: How to connect Longbridge?**
Tell Claude: `connect Longbridge`. US/HK/SH/SZ only.

**Q: Japan/Korea/EU stock data?**
See §1 config table. Japan: free. Korea: API key required. EU: download ESEF package.

**Q: How to update the plugin?**
Tell Claude: `/update-agent-runtime`. Auto-pulls latest from GitHub Releases.

---

## 5. Version History

| Version | Date | Changes |
|---|---|---|
| v8.2.1 | 2026-07 | Tool alias table, CLAUDE.md section 11 agent behavior rules |
| v8.2.0 | 2026-07 | Workspace summary + validate-names scripts, remove 3 modeling skills |
| v8.1.0 | 2026-07 | workspace-locate.py, transcribe encoding fix, meeting-minutes workspace awareness |
| v8.0.0 | 2026-07 | Colleague-ready: Python auto-install, PreToolUse hooks, all hardcoded paths removed |

Full history: [CHANGELOG.md](CHANGELOG.md)

---

中文版 → [README_zh.md](README_zh.md)
