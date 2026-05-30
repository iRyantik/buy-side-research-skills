---
name: cross-market-compare
description: Compare local listings ADRs or cross-market peers across valuation currency liquidity and access.
---

# Cross-Market Compare

Compare local listings ADRs or cross-market peers across valuation currency liquidity and access.

## Research Runtime Capsule

- Hook-enforced legality, source boundary, structure floor, and table rendering rules live in workspace hooks and are not restated here.
- Shared runtime/source baseline lives in `skills/_shared/research-policy-baseline.md` and the installed workspace `CLAUDE.md`.
- Use this skill for analysis method, sequencing, and routing judgment; unresolved facts stay as gap, hypothesis, or follow-up.

处理 A/H、ADR、本地股、跨市场 peer 的估值和可交易差异。**核心价值不是罗列哪里上市**，而是判断价差来自可交易错配、流动性 / 会计 / 监管差异，还是基本合理。

如果输出只比较 P/E 或 EV/EBITDA，没有统一币种、股本、ADR ratio、会计口径和可交易性，本 skill 就失败了。

## 心法

跨市场比较最容易犯的错，是把"价格差"直接理解成"便宜 / 贵"。但 A/H、ADR、本地股和跨市场 peer 的差异常常来自结构性因素：资本管制、投资者结构、流动性、税、会计口径、borrow、指数资金、监管风险。

本 skill 的工作逻辑是 **normalize first, interpret second, trade last**：
- 先确认比较对象是不是同一经济权益，还是只是相似 peer。
- 再把币种、share count、ADR ratio、EV、会计口径和流动性调到可比。
- 最后才判断 spread 是可交易错配、结构性折价，还是需要继续研究的 market misread。

**最重要的纪律**：A/H discount、ADR discount、跨市场估值差都不是天然 alpha。必须先解释为什么存在，以及是否真的能交易。

## AI 的局限（必读，前置警告）

跨市场数据比普通单票更容易 stale 或口径错：

| 局限 | 影响 | Mitigation |
|---|---|---|
| **ADR ratio / share class 错配** | 市值、EV、价差全部算错 | 必须 source ADR ratio / ordinary equivalence |
| **FX stale** | USD-eq 估值错 | 所有换算写 FX as-of |
| **会计口径不一致** | EBITDA、FCF、ROIC 不可比 | 明确 GAAP / IFRS / local accounting 和调整项 |
| **A/H 不可套利误判** | 把结构性价差当可交易机会 | 明确资本流动限制和转换机制 |
| **OTC / local liquidity 被忽略** | 理论 spread 无法实际交易 | 列 ADV、bid-ask、borrow availability |
| **跨市场 peer group 错配** | 把不同业务、不同监管风险硬比 | 先做 comparability check |

## 触发场景

### Mode A 触发（Same-company Cross-Listing）
- "A/H 差多少"
- "ADR 和本地股怎么比"
- "港股和美股同一家公司哪个便宜"
- "这个 ADR 折价能不能套利"
- "0700.HK 和 TCEHY 怎么换算"

### Mode B 触发（Cross-Market Peer Compare）
- "某 ADR / 本地股和海外 peer 怎么比"
- "某市场设备股和另一市场设备股估值差怎么解释"
- "A 股和港股同业估值差"
- "跨市场 comparable"
- "这家公司该用哪个市场的 peer group"

### Mode C 触发（Cross-Market Hedge / Pair Candidate）
- "A 股 long 用 H 股怎么 hedge"
- "这个 ADR 能不能 short against local"
- "跨市场 pair 怎么看"
- "这个估值差可以做 market-neutral 吗"

## 输入澄清要求（必填 8 维度）

如果用户缺关键维度，先澄清或标默认假设：

| 维度 | 含义 | 默认假设（用户没说时） |
|---|---|---|
| **比较对象** | 同一公司多地上市 / 跨市场 peer / hedge candidate | 根据 ticker 判断；不确定就问 |
| **交易市场** | HK / A / US / Europe / Japan / Korea 等 | 用户给的 ticker 所在市场 |
| **币种** | 本地币和统一展示币种 | 统一为 USD-eq，并保留本地币 |
| **Share class / ADR ratio** | 经济权益转换关系 | 未验证前不计算强结论 |
| **会计口径** | GAAP / IFRS / local accounting / Non-GAAP | 明确差异，不能默认可比 |
| **目的** | 估值解释 / trade / hedge / thesis question | 默认先解释，不直接 trade |
| **流动性 / borrow** | ADV、bid-ask、short availability | 没有 source 就标 `[来源待补]` |
| **时间窗口** | 当前价差 / 1Y / 3Y / 5Y spread | 当前 + 3Y 或 5Y 历史（如可得） |

如果用户只问"A/H 差多少"，至少确认 ticker、比较的是 price premium 还是 valuation premium，以及是否需要可交易性判断。

## Mode A: Same-company Cross-Listing

### A.1 推理路径

**Step 1: Instrument map**

先确认经济权益和交易约束：

| Ticker | Exchange | Currency | Share class | ADR ratio / conversion | ADV | Borrow | Ev |
|---|---|---|---|---|---|---|---|

**Step 2: Price / valuation normalization**

统一币种、share count、EV、cash/debt、ADR ratio：

| Metric | Listing A | Listing B | Spread | Ev |
|---|---:|---:|---:|---|
| Price local | | | | [S1](https://example.com/local-line-quote) |
| Price USD-eq | | | | [S1](https://example.com/local-line-quote) |
| Market cap USD-eq | | | | [S1](https://example.com/local-line-quote) |

正文 claim 示例：`The ADR trades at a 2.4% premium to the local line after FX and ratio adjustment, while local ADV is 3.1x the ADR ADV. [I1](https://example.com/adr-premium)`
| EV USD-eq | | | | |
| P/E NTM | | | | |
| EV/EBITDA NTM | | | | |

**Step 3: Explain spread**

把价差拆成：
- 经济权益差异
- 流动性 / access
- 税收 / dividend withholding
- 监管 / delisting / capital control
- 投资者结构
- 指数 / passive flow
- true mispricing

**Step 4: Action**

给 `Ignore / Monitor / Research edge / Hedge candidate`，不要直接把 spread 写成交易建议。

### A.2 输出结构

```markdown
## Cross-Listing Compare

**结论先行**
[一句话说明价差大致是否合理，是否有研究/交易价值]

## Instrument Map

| Ticker | Exchange | Currency | Share class | ADR ratio / conversion | ADV | Borrow | Ev |
|---|---|---|---|---|---|---|---|

## 

## 归一化估值公式

| # | 计算 | 公式 | 输入来源 |
|---|---|---|---|
| 1 | 归一化 EV | Local EV × FX Rate → common currency | FS, MKT (FX) |
| 2 | 归一化 Shares | basic shares → diluted (ADR × ratio) | FS |
| 3 | Spread | (多地 PE 差) ÷ max PE | MKT — ≥ 20% 才是 meaningful gap |
| 4 | 流动性折价 | 低流动性端 volume ÷ 高流动性端 volume | MKT — < 10% 标出来 |


Normalized Valuation

| Metric | Listing A | Listing B | Spread | Ev |
|---|---:|---:|---:|---|

## Spread Explanation

| Driver | Impact | Evidence |
|---|---|---|

## Action

- Ignore / Monitor / Research edge / Hedge candidate
```

## Mode B: Cross-Market Peer Compare

### B.1 推理路径

**Step 1: Comparability check**

先判断是不是合理 peer：

| Dimension | Company A | Company B | Comparable? |
|---|---|---|---|
| Business mix | | | High / Medium / Low |
| End-market | | | |
| Margin structure | | | |
| Growth / cyclicality | | | |
| Accounting | | | |
| Capital return | | | |

**Step 2: Normalize valuation**

必须统一：
- 币种
- accounting
- forward period
- EV adjustments
- one-offs
- share count
- non-GAAP adjustments

**Step 3: Adjustment layers**

逐层解释差异：

| Layer | Question | Typical impact |
|---|---|---|
| Accounting / disclosure | 报表口径是否可比 | EBITDA / FCF / ROIC 差异 |
| Investor structure | marginal buyer 是谁 | 估值习惯和波动 |
| Regulatory / political risk | 是否有监管折价 | discount / risk premium |
| Liquidity / access | 是否能交易 / short | 可交易性 |
| Tax | dividend withholding / capital gains | required return |

**Step 4: Interpret**

判断估值差是：
- **可交易错配**：spread 偏离 history 显著 + 没有结构性理由。
- **结构性差异 priced in**：流动性、监管、税、会计差异合理解释。
- **研究 edge**：价差暴露 market misread、peer mismatch 或 accounting gap。

### B.2 输出结构

```markdown
## Cross-Market Peer Compare

**结论先行**
[一句话说明差异是否合理，还是暴露研究问题]

## Comparability Check

| Dimension | A | B | Comparable? | Ev |
|---|---|---|---|---|

## Normalized Valuation Table

| Metric | A local | A USD-eq | B local | B USD-eq | Spread | History / z-score | Ev |
|---|---:|---:|---:|---:|---:|---:|---|

## Adjustment Layers

| Layer | Impact | Evidence | Read-through |
|---|---|---|---|

## Interpretation

- 可交易错配 / 结构性差异 / 研究 edge
```

## Mode C: Cross-Market Hedge / Pair Candidate

跨市场 hedge 不是自动套利。先问：共同 factor 是否足够高、经济权益是否一致、borrow / conversion / liquidity 是否支持。

输出必须包含：

| Check | Required answer |
|---|---|
| Common factor | 两边是否受同一 business / macro driver 影响 |
| Idiosyncratic difference | 价差来自什么可研究差异 |
| Liquidity / borrow | 是否能执行 |
| Conversion / access | 是否能转换或套利 |
| Failure mode | 什么情况下 spread 不会回归 |

若 pair 逻辑成立，handoff 到 `pair-trade`；否则只作为 cross-market observation。

## Workflow 联动

| 场景 | 下一步 |
|---|---|
| 跨市场价差暴露研究问题 | `next-step` |
| 差异来自 business / peer mismatch | `peer-deep-dive` |
| 差异来自 revenue / margin / backlog driver 不同 | `driver-map` |
| 价差可形成 hedge / pair 候选 | `pair-trade` |
| 估值差改变单票 thesis | `alpha-thesis` |
| 研究后形成认知增量 | `research-journal` |

## 写入

默认输出到对话。用户明确要求保存时，写入当前日期化保存路径：

```text
topics/[topic-namespace]/[topic-slug]/[YYYY-MM-DD]-cross-market-compare.md
```

本 skill 的 `artifact_policy.naming_mode = optional_qualifier`。完整 local-vs-ADR / cross-market 主比较默认继续使用 `YYYY-MM-DD-<artifact>.md`；如果这次只比较某个 listing angle、liquidity gap 或 access issue，则应改由 `new-session` 解析成 `YYYY-MM-DD-<artifact>-<qualifier>.md`。

如果当前日期化保存路径不明确，先 handoff 到 `new-session` 解析路径；不要临时发明目录或未解析路径就写入。

不要自动维护状态库。

## 反模式自查

### Normalization 类
- ❌ 只比较 P/E，不统一币种、股本、会计口径。
- ❌ 忽略 ADR ratio、FX as-of、share class。
- ❌ 用不同时间点价格 / FX / EV 做 spread。
- ❌ 把 Non-GAAP EBITDA 和 GAAP EBIT 混用。
- ❌ 把 sub-agent evidence card 直接写成 spread interpretation / trade verdict，而没有主 agent 抽查 share class、FX、ADR ratio 和会计口径。

### Interpretation 类
- ❌ 把 A/H discount 直接当便宜。
- ❌ 把结构性监管 / 流动性折价写成 mispricing。
- ❌ 没解释 marginal buyer / capital access。
- ❌ 跨市场 peer 业务差异巨大还硬比。

### Trading 类
- ❌ 忽略 borrow availability / borrow cost。
- ❌ 假设 ADR-local 一定可双向 convert。
- ❌ 把不可套利价差写成套利机会。
- ❌ 没写 failure mode 就建议 hedge / pair。

## 篇幅基准

- Same-company quick compare：500-900 字 + 2 张表。
- Cross-market peer compare：900-1600 字 + comparability / valuation / adjustment 表。
- Hedge / pair candidate：700-1200 字；若进入完整 pair，应 handoff 到 `pair-trade`。
- 超过 1800 字通常说明需要拆成 `peer-deep-dive` 或 `pair-trade`。

## 与相邻 skill 的边界

- `peer-deep-dive` 做同业横向；本 skill 专注跨市场 normalization 和 access adjustment。
- `driver-map` 拆业务实质和 model driver；当跨市场价差来自 driver 差异时，先用它统一口径。
- `pair-trade` 做完整 long/short setup；本 skill 只判断跨市场 spread 是否可能成为 pair。
- `alpha-thesis` 写投资论点；本 skill 只提供跨市场估值 / access read-through。
- `next-step` 把价差背后的怪异点变成研究问题。
