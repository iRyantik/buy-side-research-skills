# Unified Data Routing

> 从 CLAUDE.md §4 引用的数据路由细则。

## 路由决策

Agent 收到数据请求时，按三重判断：

1. **问的是哪种数据？**——市场快照 / 财务快照 / 结构化三表
2. **actuals 是否已缓存？**——先扫 `industry/*/companies/<ticker>/.cache/financial-data/actuals-resolved.json`
3. **上下文是什么？**——日常对话（秒回优先）/ 写 artifact（准确性优先）

## 市场路由

| 市场 | 结构化三表 | 市场数据 | IR 补充分部 |
|---|---|---|---|
| US | edgartools API (XBRL) | yfinance / Bridge | SEC EDGAR 10-K PDF（仅 commentary） |
| CN | AKShare API | yfinance / Bridge | CNINFO PDF（仅验证） |
| HK | AKShare API → **缺 segment** | yfinance / Bridge | **Company IR PDF → pymupdf4llm → table-dump** |
| JP | **TDnet PDF → pymupdf4llm → table-dump** | yfinance | PDF 自带 segment |
| KR | **DART PDF → pymupdf4llm → table-dump** | yfinance | PDF 自带 segment |
| TW | **English MOPS PDF → pymupdf4llm → table-dump** | yfinance | PDF 自带 segment |
| EU | **Company IR PDF → pymupdf4llm → table-dump** | yfinance | PDF 自带 segment |

- Field schema：`.references/policy/statement-line-items.md`（117 concepts）
- 路由脚本：`python .scripts/financial-data/financial_data.py --market <mkt> --identifier <TICKER> --mode lite`

## 路由表

| 问什么 | actuals 已有 | actuals 没有 |
|---|---|---|
| **报价/K线/日内** | Bridge → yfinance → WebSearch | Bridge → yfinance → WebSearch |
| **估值/新闻** | Bridge → yfinance → WebSearch | Bridge → yfinance → WebSearch |
| **结构化三表** | Read actuals（全字段） | `/financial-data --mode lite` |
| **多期对比** | Read actuals | `/financial-data --mode full` |

## Source Chain

```
actuals_cache → API provider (US/CN/HK) / IR PDF→MD (JP/KR/TW/EU) → yfinance (market data)
```

- US/CN/HK: API primary, no PDF needed unless segment/commentary missing
- JP/KR/TW/EU: PDF primary via pymupdf4llm + table-dump extraction
- Bridge = Longbridge MCP（US/HK/SH/SZ/SG 市场数据）
- 不可用时自动 fallback 到 yfinance
