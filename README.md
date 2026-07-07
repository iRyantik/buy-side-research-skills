# Buy-Side Research Skills

> v7.5.3 | Claude Code + Codex Dual-Host | [iRyantik/buy-side-research-skills](https://github.com/iRyantik/buy-side-research-skills)

A journal-first buy-side equity research skill suite: 38 skills covering triage, foundation, deep-work, and operations layers. Source-tracked, evidence-gated, cross-market.

---

## 0. Install

Tell Claude or Codex:

```
Follow https://github.com/iRyantik/buy-side-research-skills/blob/main/docs/install.md to install buy-side-research-skills
```

## 0a. Upgrade

```
/update-agent-runtime
```

Pulls latest from GitHub Releases, updates plugin version + syncs workspace hooks. Run once after each release.

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

> Unlisted skills work out of the box. Playwright runtime recommended as shared browser capability. See `docs/install.md`.

---

## 2. Quick Start: Two Most Common Workflows

### Industry-first (find opportunities)

```
Step 1: teach-in              → Build physical intuition ~20min
Step 2: industry-landscape    → Panorama: value pool, competition, company registry ~20min
Step 3: mechanism-insight     → Deep-dive key segments ~30min
Step 4: market-sizing         → TAM breakdown ~15min
Step 5: candidate-screener    → L/S ranking across 3 regimes + 7 strategy archetypes ~40min
  ├→ scenario-model           → Quantified upside scenarios
  └→ peer-deep-dive           → Top 5 cross-market comparison
```

### Company-first (deep-dive a single name)

```
Step 1: stock-quickread       → 5-min first pass: business overview, financials, growth drivers ~30min
  ├→ Equipment → force-check backlog/orders/ASP; Process → output/cost/utilization
  └→ Auto-routes to moat-analysis / catalyst-map / capital-allocation
Step 2: financial-data --lite → 3 statements + market snapshot ~15s
Step 3: driver-map            → Revenue/margin drivers, growth quality ~30min
Step 4: moat-analysis         → 5-dimension scorecard + peer benchmarking
  ├→ catalyst-map             → Probability-weighted catalyst chain
  └→ capital-allocation       → 10Y buyback/M&A/dividend/capex ROI
Step 5: consensus-map         → Consensus implied growth vs PE-implied growth gap
Step 6: scenario-model        → Bull/base/bear odds memo + 3D driver mix + sensitivity
Step 7: alpha-thesis          → Thesis + kill criteria + next catalyst
```

> 📖 **Prefer learning by example?** Walk through a real case: [/examples/optical-module-equipment/](examples/optical-module-equipment/)

---

## 3. Full Skill List (38 skills)

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
| `3-statement-model` | Full 3-statement operating model |
| `dcf-model` | DCF valuation |
| `comps-analysis` | Comparable company valuation |

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
| v7.5.3 | 2026-07 | docs: §9 cross-machine sync — new machine setup, dual repo discipline, switch workflow |
| v7.5.2 | 2026-07 | fix: pip show fallback for cross-machine Python path detection (Store Python / custom installs) |
| v7.5.1 | 2026-07 | browser-cdp recipes + sync subdirectory support; remove browser-act skills |
| v7.5.0 | 2026-07 | browser-harness CDP tier: browser-cdp.py, verify-claim Tier 2 CDP (real Chrome, Cloudflare bypass), web-extract --cdp, verify-runtime +browser-harness check |
| v7.3.4 | 2026-07 | driver-map v1.5.1: Sum of Q = Y, checks.json + q_checks, vol_asp Q driver fix, Lumentum seg OP reconciliation |
| v7.1.1 | 2026-07 | fix: SOTP Enterprise Value→Net Debt→Mkt Cap bidirectional, Total label, MCap sign |
| v7.1.0 | 2026-07 | driver-map v1.5.0: EBITDA depth, P&L F/A rules, Hidden Bridge actuals zone, Check line redesign, SOTP restructure |
| v7.0.0 | 2026-06 | driver-map v2.0: Q driver allocation restructure, Blend step, 1:1 GM/OM references |
| v6.7.0 | 2026-06 | driver-map v1.4.0: CF/HL/BOLD helpers, yoy module, multi-depth profit chain, style system |
| v6.5.14 | 2026-06 | RAG 4-tier fallback, Evidence Ledger, sentence-end anchors, 16-hook regression, actuals provenance |
| v5.4.0 | 2026-06 | Source contract injection: 27 skill output tables + Ev column, paragraph-level source density hook |
| v5.3.0 | 2026-06 | Actuals-only ratio constraint: no forward estimates in ratios across 17 skills |
| v5.2.1 | 2026-06 | Directory auto-discovery: new skill scripts deploy with zero config changes |
| v5.1.0 | 2026-06 | Python unified bootstrap, init-workspace rewrite (Class A+B deployment), interactive provider config |
| v5.0.0 | 2026-06 | 7 new skills, regime-based candidate screener, full-chain hook governance, cross-market merge, Codex dual-host |
| v4.5.6 | 2026-05 | mechanism-insight/industry-landscape/teach-in renamed, peer-deep-dive restructured |

---

# Buy-Side Research Skills — AI 研究员工具箱

> v7.5.3 | Claude Code + Codex 双宿主 | [iRyantik/buy-side-research-skills](https://github.com/iRyantik/buy-side-research-skills)

journal-first 买方股权研究 skill 套件：38 个 skill 覆盖 triage、foundation、deep-work、operations 四层。source-tracked、evidence-gated、跨市场。

---

## 0. 安装

对 Claude / Codex 说：

```
按照 https://github.com/iRyantik/buy-side-research-skills/blob/main/docs/install.md 安装 buy-side-research-skills
```

## 0a. 升级

```
/update-agent-runtime
```

自动从 GitHub Release 拉最新版，更新插件版本 + 同步 workspace hooks。每次发版后跑一次即可。

---

## 1. 可选配置

| 需要什么 | 怎么拿到 |
|---|---|
| **SEC EDGAR 身份** | 对 Claude 说"设置 EDGAR 身份为 姓名,邮箱" |
| **DART API Key** | [dart.fss.or.kr](https://dart.fss.or.kr) 免费申请 |
| **EDINET Tools** | 对 Claude 说"安装 EDINET 依赖" |
| **欧股 ESEF 包** | 从公司 IR 页下载 annual report（iXBRL） |
| **ingest 文档转换** | 对 Claude 说"检查 ingest 依赖" |
| **Longbridge 账户** | [longbridge.com](https://longbridge.com) 注册 |

> 未列出的 skill 无需配置。推荐启用 Playwright runtime 作为共享 browser 能力。

---

## 2. 快速开始

### 从行业出发（找机会）

```
teach-in → industry-landscape → mechanism-insight → market-sizing
→ candidate-screener → scenario-model / peer-deep-dive
```

### 从公司出发（深挖一只票）

```
stock-quickread → financial-data → driver-map → moat-analysis
→ catalyst-map / capital-allocation → consensus-map → scenario-model → alpha-thesis
```

> 📖 真实案例走一遍：[/examples/optical-module-equipment/](examples/optical-module-equipment/)

---

## 3. 完整 Skill 清单（38 个）

### Triage 层

| Skill | 一句话 |
|---|---|
| `stock-quickread` | 陌生公司 first pass |
| `information-impact` | 信息的真假和影响 |
| `post-earnings-quick` | 财报后 5 分钟判断 |
| `reddit-sentiment` | 社交媒体情绪 |

### Foundation 层

| Skill | 一句话 |
|---|---|
| `teach-in` | 零基础建立物理直觉 |
| `industry-landscape` | 行业全景 + 投资判断 |
| `financial-data` | 三表 + 市场快照 |
| `market-sizing` | TAM/SAM/SOM 拆解 |
| `mechanism-insight` | 技术/工程机制深挖 |
| `driver-map` | 收入/利润驱动拆解 |
| `company-history` | 业务演变 + 披露口径 |
| `consensus-map` | 市场预期 + priced-in |

### Deep-Work 层

| Skill | 一句话 |
|---|---|
| `candidate-screener` | 分场景 L/S 排序（7 种策略原型） |
| `scenario-model` | bull/base/bear odds memo + 假设溯源 |
| `peer-deep-dive` | 横向比较（跨市场） |
| `moat-analysis` | 竞争壁垒量化 scorecard |
| `catalyst-map` | 催化剂时间线 + 概率加权 |
| `capital-allocation` | 管理层资本配置 10 年 ROI |
| `earnings-setup` | 财报前 setup |
| `alpha-thesis` | 投资 thesis |
| `bear-pre-mortem` | 空头 pre-mortem |
| `pair-trade` | LS 对 |
| `primary-research-plan` | 一手研究计划 |
| `3-statement-model` | 完整三表模型 |
| `dcf-model` | DCF 估值 |
| `comps-analysis` | 可比估值 |

### Supporting

| Skill | 一句话 |
|---|---|
| `research-viz` | 可视化 |

### Memory

| Skill | 一句话 |
|---|---|
| `research-journal` | 沉淀研究认知 |
| `coverage-tracker` | 跟踪覆盖公司状态 |

---

## 4. 常见问题

详见上方 English 版 §4 FAQ。

---

## 5. 版本历史

详见上方 English 版 §5 Version History。
