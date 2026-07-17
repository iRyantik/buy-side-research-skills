# Unified Data Routing

> 从 CLAUDE.md §4 引用的数据路由细则。

本 workspace 的数据路由由 `capability-matrix.json` 统一管理。Agent 不手动判断优先级——每个数据请求前调 `route.py`，按序执行 chain，第一个成功的源直接用。

```bash
python .scripts/shared/route.py <TICKER.MARKET> <capability>
```

## Capability 列表（常用）

| 类别 | capability |
|---|---|
| 市场实时 | `market_quote`, `price_action`, `price_intraday`, `price_history` |
| 估值 | `valuation_snapshot`, `valuation_peer`, `valuation_history`, `valuation_rank`, `industry_valuation` |
| 基本面 | `financial_snapshot`, `financial_statement`, `financial_report`, `business_segments` |
| 一致预期 | `consensus`, `forecast_eps` |
| 事件 | `news`, `filings`, `calendar` |
| 股东/管理 | `shareholder`, `shareholder_top`, `executive` |
| 机构 | `institution_rating`, `institutional_views` |
| 结构化 | `income_statement`, `balance_sheet`, `cash_flow`, `revenue_split` |

完整列表：`cat .references/routing/capability-matrix.json | python -c "import json,sys; d=json.load(sys.stdin); print('\n'.join(sorted(d['chains'].keys())))"`

## 路由决策

Agent 收到数据请求时，按三重判断：

1. **问的是哪种数据？**——市场快照 / 财务快照 / 结构化三表
2. **actuals 是否已缓存？**——先扫 `industry/*/companies/<ticker>/.cache/financial-data/actuals-resolved.json`
3. **上下文是什么？**——日常对话（秒回优先）/ 写 artifact（准确性优先）

## 路由表

| 问什么 | actuals 已有 | actuals 没有 |
|---|---|---|
| **报价/K线/日内** | Bridge → yfinance → WebSearch | Bridge → yfinance → WebSearch |
| **估值/新闻/评级/日历/汇率/异动** | Bridge → yfinance → WebSearch | Bridge → yfinance → WebSearch |
| **财务快照**（收入/EPS/ROE） | Read actuals → Bridge `financial_report_latest` → yfinance | Bridge `financial_report_latest` → yfinance |
| **结构化三表**（artifact Step 1） | Read actuals → `/financial-data --lite` 增量 | `/financial-data --lite`（强制） |
| **多期FY对比** | Read actuals → 过期>180天提醒 | `/financial-data --lite --periods FY20-FY25` |

## Source Chain

```
actuals_cache → Bridge（Longbridge MCP）→ yfinance → WebSearch/WebFetch
```

- Bridge = Longbridge MCP（145 工具，US/HK/SH/SZ/SG）
- 不可用时自动 fallback 到 yfinance（15min 延迟，全球覆盖）
- yfinance 也失败 → WebSearch 兜底

## 架构

```
capability-matrix.json  ← 单一真理源（字段→源→优先级）
route.py                ← 查矩阵 + 条件判断
各 skill [→ Bridge: x]  ← 标记 capability 名
```

新 Bridge 源加入时只改 `capability-matrix.json` 一个文件。
