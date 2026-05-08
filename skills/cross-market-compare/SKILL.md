---
name: cross-market-compare
description: Use when comparing A/H shares, ADRs, local listings, or cross-market peers where valuation, currency, accounting, liquidity, or access differences matter.
---

# Cross-Market Compare

处理 A/H、ADR、本地股、跨市场可比公司的估值和基本面差异。目标不是罗列哪里上市，而是判断价差是否来自可交易错配、流动性 / 会计 /监管差异，还是基本合理。

## Source 政策

遵守 `CLAUDE.md §3`；若冲突，以 `CLAUDE.md` 为准。价格、FX、market cap、EV、会计口径、股本结构、可转换关系都必须有 source 和 as-of 时间。

## 触发场景

- "A/H 差多少"
- "ADR 和本地股怎么比"
- "ASML.NA 和美股半导体怎么比"
- "港股 / A 股 / 美股估值差怎么解释"
- "跨市场 comparable"

## 输出结构

### 1. Instrument Map

不只列 ticker，列出可投资性差异：

| Ticker | 交易所 | 币种 | Share class | ADR ratio (如适用) | 流通股数 | 日均成交量 | Borrow availability | Source |
|---|---|---|---|---|---|---|---|---|

例（某 A/H/ADR 三重上市）：
- 0700.HK（港股，HKD，普通股）
- TCEHY（OTC，USD，1 ADR = 1 ord）
- 注：A 股无（中国大陆未上市）

### 2. Normalized Valuation Table

**关键约束**：必须统一币种、统一 share count、统一会计准则（尽可能 reconcile）。所有数值必须给 as-of 时间点。

| Metric | Ticker A (本地) | Ticker A (USD-eq) | Ticker B (本地) | Ticker B (USD-eq) | Spread | 5Y mean | Z-score | Source |
|---|---|---|---|---|---|---|---|---|
| Market cap | ... | ... | ... | ... | ... | ... | ... | ... |
| EV/EBITDA NTM | ... | ... | ... | ... | ... | ... | ... | ... |
| P/E NTM | ... | ... | ... | ... | ... | ... | ... | ... |
| FCF yield | ... | ... | ... | ... | ... | ... | ... | ... |
| EV/Sales | ... | ... | ... | ... | ... | ... | ... | ... |

注：A/H 同一公司比较时，要明确 H 股 / A 股的 free-float 和投资者结构差异，普通用 ADR ratio 等价的 share count 计算 EV。

### 3. Adjustment Layers（多维差异，关键）

横向比较的"陷阱"几乎都来自以下 dimension 没 normalize。每个 dimension 都要 quickly assess + 给 magnitude。

#### 3.1 Accounting / Disclosure 差异
- 会计准则（GAAP / IFRS / 中国会计准则）
- Reporting frequency（季报 vs 半年报，影响 visibility）
- Segment disclosure 详尽度（10-K segment data vs A 股年报较粗）
- Non-GAAP / 调整项口径

#### 3.2 Investor Structure（影响估值习惯）
- 机构 vs 散户占比（A 股散户 main、美股机构 main、港股 mixed）
- Index inclusion（MSCI、CSI 300、HSCEI、Stoxx 600 etc.）
- Foreign ownership 限制 / QFII / 港股通额度
- 主要 marginal buyer / seller 是谁

#### 3.3 Regulatory / Political Risk Premium
- 中概股 ADR delisting risk（HFCAA 等）
- A 股 IPO 政策、退市制度
- VIE 结构风险（中概股 / 港股部分公司）
- 跨境监管事件（如 DiDi、滴滴）历史 precedent
- 外资准入限制（日韩外资上限）

#### 3.4 流动性 / 套利 Mechanism
- ADR-Local 套利可行性（是否可双向 convert）
- 港股通 / 沪股通 / 深股通 资金流向
- A/H 价差是否可套利（实际上中国大陆资本管制下 A/H 无法套利）
- Borrow availability + cost
- Bid-ask spread + 单笔大额交易冲击

#### 3.5 税收差异
- Withholding tax on dividend（不同上市地不同）
- Capital gains tax 差异
- 对个人 vs 机构 投资者的影响

每个 dimension 给一句话 takeaway，magnitude 评估（low / medium / high impact），并指明 source。

### 4. Spread Interpretation

基于 §2 + §3，判断 spread 是：
- **可交易错配**：spread 偏离 history 显著 + 没有结构性差异理由 → entry opportunity
- **结构性差异 priced in**：spread 反映真实差异（流动性、监管、税）→ 不要硬 trade
- **混合**：部分错配 + 部分结构性 → 需细分

例："腾讯 ADR vs 港股 spread 当前 -1.5σ。但其中 ~60% 可解释为 ADR delisting risk premium（中概股近 12 个月 widen），剩 40% 是真错配——可作为 pair 候选 long 0700.HK / short TCEHY 套利。"

### 5. Action

- **Ignore**：spread 反映合理结构性差异，不可 trade
- **Monitor**：spread 接近 historical mean，等待错配出现
- **Pair candidate**：spread 是可交易错配，触发 `pair-trade` Mode A
- **Thesis review**：跨市场比较暴露单一标的 thesis 假设有误，触发 `alpha-thesis` 重审
- **Cross-market hedge**：用对侧市场对冲单边风险（如 A 股 long + H 股 short）

## 写入

默认输出到对话；如果用户要求保存，写入 `cross-market/[group-name]-[YYYY-MM-DD].md`。

## 反模式

- 只比较 P/E，不统一币种、股本、会计口径。
- 把 A/H discount 直接当便宜，不解释可交易性和资本流动限制。
- 忽略 ADR ratio、FX as-of、双重上市 share class 差异。
