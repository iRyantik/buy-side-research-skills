# Bridge Skill Map

> **Generated from `capability-matrix.json`**. Maintain the matrix — this file is a human-readable derivative.
>
> Bridge → Domain → MCP Tool 的 section 级完整映射。
> Agent 执行 skill 时，读到 `[→ Bridge: domain]` 标记 → 查本文件 → 确定 MCP 工具调用。
> 与 CLAUDE.md §4.1 路由规则配合使用。

---

## stock-quickread

| Section | Bridge Domain | MCP Tool |
|---|---|---|
| §5 什么在驱动股价 | price_action, market_quote | `candlesticks`, `intraday`, `quote` |
| §6 市场在交易什么 | consensus, valuation_snapshot, valuation_peer | `consensus`, `forecast_eps`, `valuation`, `valuation_comparison` |
| §9 最近在发生什么 | news, price_action | `news`, `quote`, `candlesticks` |

## consensus-map

| Section | Bridge Domain | MCP Tool |
|---|---|---|
| §2 Sell-Side Consensus Numbers | consensus, forecast_eps | `consensus`, `forecast_eps` |
| §3 Buy-Side / Market-Implied Bar | valuation_snapshot, valuation_peer | `valuation`, `valuation_comparison` |
| §4 Narrative And Debate Map | news, institution_rating | `news`, `institution_rating`, `institutional_views` |
| §7 What Would Change Consensus | calendar | `finance_calendar` |

## earnings-setup

| Section | Bridge Domain | MCP Tool |
|---|---|---|
| A §1 当前 Setup | valuation_snapshot, price_action, news | `valuation`, `candlesticks`, `news` |
| A §2 Sell-Side vs Buy-Side Bar | consensus, forecast_eps, institution_rating | `consensus`, `forecast_eps`, `institution_rating` |
| A §3 真正要听/看的 3 件事 | calendar | `finance_calendar` |
| B §2 KPI Actuals vs Setup | financial_snapshot_detail, news | `financial_report_snapshot`, `news` |

## post-earnings-quick

| Section | Bridge Domain | MCP Tool |
|---|---|---|
| Verdict | financial_snapshot_detail | `financial_report_snapshot` |
| Quality Check | financial_snapshot_detail, consensus | `financial_report_snapshot`, `consensus` |
| Thesis Impact | price_action, news | `candlesticks`, `news` |

## peer-deep-dive

| Section | Bridge Domain | MCP Tool |
|---|---|---|
| 估值对比 | valuation_peer, industry_valuation, industry_valuation_dist | `valuation_comparison`, `valuation`, `industry_valuation`, `industry_valuation_dist` |
| 市场数据截面 | market_quote, price_action | `quote`, `candlesticks` |

## pair-trade

| Section | Bridge Domain | MCP Tool |
|---|---|---|
| 价差/价格序列 | price_action | `history_candlesticks_by_date`, `candlesticks` |
| 估值对比 | valuation_snapshot, valuation_peer | `valuation`, `valuation_comparison` |

## candidate-screener

| Section | Bridge Domain | MCP Tool |
|---|---|---|
| 筛选/候选生成 | market_screen, screener | `top_movers`, `screener_search` |
| 市场环境 | market_temperature | `market_temperature` |

## alpha-thesis

| Section | Bridge Domain | MCP Tool |
|---|---|---|
| 市场定价/估值锚 | consensus, valuation_snapshot | `consensus`, `valuation` |
| 机构观点 | institution_rating | `institution_rating`, `institutional_views` |
| 催化剂日历 | calendar | `finance_calendar` |

## bear-pre-mortem

| Section | Bridge Domain | MCP Tool |
|---|---|---|
| 机构仓位/拥挤度 | institution_rating, shareholder | `institution_rating`, `shareholder`, `shareholder_top` |
| 估值极端假设 | valuation_snapshot, valuation_history | `valuation`, `valuation_history` |
| 空头数据 (HK) | — | `short_positions` |

## industry-landscape

| Section | Bridge Domain | MCP Tool |
|---|---|---|
| 行业估值分布 | industry_peers, industry_valuation_dist | `industry_peers`, `industry_valuation_dist` |
| 市场情绪 | market_temperature | `market_temperature` |

## moat-analysis

| Section | Bridge Domain | MCP Tool |
|---|---|---|
| 行业对标/估值分布 | industry_valuation_dist, valuation_peer | `industry_valuation_dist`, `valuation_comparison` |
| 估值截面 | valuation_snapshot | `valuation` |

## capital-allocation

| Section | Bridge Domain | MCP Tool |
|---|---|---|
| 分红历史 | dividend | `dividend` |
| 回购/股权变化 | financial_snapshot | `financial_report_latest` |

## catalyst-map

| Section | Bridge Domain | MCP Tool |
|---|---|---|
| 催化剂日历 | calendar | `finance_calendar` |
| 催化剂新闻 | news | `news` |

## scenario-model

| Section | Bridge Domain | MCP Tool |
|---|---|---|
| 估值历史/分位 | valuation_history | `valuation_history`, `valuation_rank` |
| 一致预期参照 | consensus, forecast_eps | `consensus`, `forecast_eps` |

## comps-analysis

| Section | Bridge Domain | MCP Tool |
|---|---|---|
| Peer multiples | valuation_peer, industry_valuation | `valuation_comparison`, `industry_valuation` |
| Market data | market_quote | `quote` |

## dcf-model

| Section | Bridge Domain | MCP Tool |
|---|---|---|
| Terminal check / 交叉验证 | consensus | `consensus` |

## 3-statement-model

| Section | Bridge Domain | MCP Tool |
|---|---|---|
| Driver sanity / sell-side 对比 | consensus | `consensus` |

## company-history

| Section | Bridge Domain | MCP Tool |
|---|---|---|
| 申报/披露历史 | filings | `filings` |
| 分红/资本操作历史 | dividend | `dividend` |

## information-impact

| Section | Bridge Domain | MCP Tool |
|---|---|---|
| 消息验证/市场反应 | news, price_action | `news`, `intraday`, `quote` |

## driver-map

| Section | Bridge Domain | MCP Tool |
|---|---|---|
| 估值语境 | valuation_snapshot | `valuation` |

---

## Skills That Do NOT Use Bridge

以下 skill 不涉及市场数据获取，不需要 `[→ Bridge]` 标记：

- `teach-in` — 物理直觉，非数据
- `mechanism-insight` — 工程原理，非价格
- `market-sizing` — TAM 估算，非市场快照
- `meeting-minutes` — 转录结构化，非数据
- `reddit-sentiment` — 独立社交舆情管道
- `primary-research-plan` — 专家访谈设计
- `research-viz` — 消费而非获取
- `research-journal` — 知识沉淀
- `coverage-tracker` — 覆盖管理
- `` — 路由建议
- `financial-data` — Bridge 的上游（CLI 写入 actuals）
- `init-workspace` — operations skill
- `update-agent-runtime` — operations skill
- `ingest` — 文档转换
- `meta-skill` — skill 治理
- `integrate` — 整合
- `trusted-market-bridge` — Bridge 定义本身
