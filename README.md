# Buy-Side Research Skills Plugin

Claude/Cowork + Codex 双栈可用的买方研究 workflow 插件。目标不是写 sell-side 风格覆盖报告，而是把信息、数据和 thesis 组织成可追踪的投资判断。

当前版本：`v2.2.0`

## Governance

- `CLAUDE.md` 是唯一 project constitution / source of truth。
- `AGENTS.md` 只是 Codex entry point，不复制全局规则。
- `FRAMEWORK.md` 是 skill/system design blueprint，受 `CLAUDE.md` 约束。
- 各 `SKILL.md` 不再内嵌完整 source policy，只引用 `CLAUDE.md §3`。

## Coverage

Primary coverage:

`industrials, aerospace and defense, advanced manufacturing, oil & gas, renewable, nuclear, emerging tech themes`

Ticker 使用 Bloomberg-style canonical ticker，例如 `XOM`, `700.HK`, `ASML.NA`。

## Skills

### v1.2 Existing Skills

| Skill | 用途 | 关键输出 |
|---|---|---|
| `stock-quickread` | 30 分钟快速扫陌生公司 | 9 节 quickread、3 张数据表、对手盘假设 |
| `peer-deep-dive` | 3-8 家同业横向研究 | 行业 lens、KPI matrix、cross-cut、研究排序、pair/no-pair 判断 |
| `alpha-thesis` | 建立可 pitch 的多 / 空 thesis | 8 节 thesis，并可写 `coverage/[ticker]/thesis.md` |
| `bear-pre-mortem` | 压测 thesis | 多头 thesis 的最强空头，或 short thesis 的最强反向压测 |
| `earnings-setup` | 财报前 setup / 财报后 quick read | pre-print 决策树；post-print thesis update / decision trigger |
| `financial-model` | 搭新模型 / 更新已有 Excel model | revenue split、segment drivers、`coverage/[ticker]/model.xlsx` |

### v2.2 Discovery Skill

| Skill | 用途 | 关键输出 |
|---|---|---|
| `candidate-screener` | 从主题 / hypothesis / 条件筛选候选股票 | `screens/[hypothesis-slug]-[YYYY-MM-DD].md`，推荐进入 quickread / peer work 的 1-2 家 |

### v2.0 State Workflow Skills

| Skill | 用途 | 关键输出 |
|---|---|---|
| `decision-journal` | 记录 open/add/trim/close/review | append-only `journal/decisions.md` |
| `thesis-tracker` | 跟踪 thesis health 和 catalyst pipeline | `coverage/[ticker]/health-log.md`、`portfolio/catalyst-pipeline.md` |
| `pair-trade` | Pair builder + monitor | `pairs/[LONG_TICKER]-[SHORT_TICKER]/thesis.md`、`spread-log.md` |
| `information-impact` | Claim Check + Portfolio Impact | 传闻可信度 verdict；必要时写 `inbox/information-log.md` |
| `cross-market-compare` | A/H、ADR、跨市场估值差 | `cross-market/[group-name]-[YYYY-MM-DD].md`（可选） |

当前没有独立 `peer-scan` skill。若公司超过 8 家，先自由对话预筛，或按子行业 / business model 分组后再运行 `peer-deep-dive`。

## Workflow

```text
new idea / peer group
  ├─ candidate-screener → stock-quickread / peer-deep-dive
  ├─ peer-deep-dive → stock-quickread → financial-model → alpha-thesis
  │                                                        ├─ bear-pre-mortem
  │                                                        ├─ decision-journal
  │                                                        └─ thesis-tracker
  ├─ earnings-setup ── post-print ───────┬─ thesis update
  │                                      ├─ model update
  │                                      └─ decision entry
  ├─ pair-trade ───────────────────────── spread-log + monitor
  ├─ information-impact ───────────────── claim-check → portfolio impact
  └─ cross-market-compare ─────────────── normalized valuation spread
```

## Public State Interfaces

These paths are the stable interfaces between skills:

```text
coverage/[ticker]/thesis.md
coverage/[ticker]/model.xlsx
screens/[hypothesis-slug]-[YYYY-MM-DD].md
journal/decisions.md
pairs/[LONG_TICKER]-[SHORT_TICKER]/spread-log.md
portfolio/catalyst-pipeline.md
inbox/information-log.md
```

State files use YAML frontmatter or append-only YAML blocks as specified in `FRAMEWORK.md §6.3`.

## Source Policy

Short version:

- Every factual claim, number, KPI, quote, historical event, consensus figure, and third-party judgment needs a source link.
- Research judgment does not need a source, but the factual premises do.
- Never invent URLs, page numbers, quotes, numbers, people, or dates.
- Sub-agent URLs must be manually spot-checked before being treated as verified.

Full rules live in `CLAUDE.md §3`.

## File Structure

```text
buy-side-research-skills/
├── .claude-plugin/
│   └── plugin.json
├── AGENTS.md
├── CLAUDE.md
├── FRAMEWORK.md
├── skills/
│   ├── stock-quickread/
│   ├── candidate-screener/
│   ├── peer-deep-dive/
│   ├── alpha-thesis/
│   ├── bear-pre-mortem/
│   ├── earnings-setup/
│   ├── financial-model/
│   ├── decision-journal/
│   ├── thesis-tracker/
│   ├── pair-trade/
│   ├── information-impact/
│   └── cross-market-compare/
└── README.md
```

## Version History

### 2.2.0

- Added `candidate-screener` as the 12th skill.
- Added `screens/[hypothesis-slug]-[YYYY-MM-DD].md` as the candidate funnel state output.
- Normalized all `SKILL.md` frontmatter descriptions for parser validation and skill discovery.

### 2.1.0

- Added `financial-model` as the 11th skill.
- First version is a skeleton for revenue-first Excel models and existing-model earnings updates.
- Kept `cross-market-compare`; no existing skill was removed.

### 2.0.0

- Added `decision-journal`, `thesis-tracker`, `pair-trade`, `information-impact`, and `cross-market-compare`.
- Added state interfaces for thesis, decisions, spread logs, catalyst pipeline, and information log.
- Upgraded plugin metadata and README to the v2 state workflow system.

### 1.2.0

- Aligned existing 5 skills with `CLAUDE.md` / `FRAMEWORK.md`.
- `alpha-thesis` now defines schema-compatible `coverage/[ticker]/thesis.md` contract.
- `peer-deep-dive` outputs pair candidates or explicit no-pair conclusion.
- `earnings-setup` post-print can trigger thesis update or decision entry.
- Source policy duplicated blocks removed from skill instructions.

### 1.1.0

- Added `peer-deep-dive` and industry KPI templates.

### 1.0.0

- Initial 4 core skills: `stock-quickread`, `alpha-thesis`, `bear-pre-mortem`, `earnings-setup`.

## Philosophy

买方研究就是和市场分歧打架。这套 skills 强制把分歧定位在具体数据、假设和可复盘决策上，而不是漂亮故事。
