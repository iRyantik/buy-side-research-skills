---
schema_version: 1
document_type: spread_log
pair_id: ETN-CAT
long_ticker: ETN
short_ticker: CAT
spread_definition: "paper long ETN total return - paper short CAT total return from 2026-05-07 close snapshot"
base_currency: USD
created_at: 2026-05-08
entry_schema: spread_observation_v1
trade_ready: false
source_policy: "CLAUDE.md §3"
---

# ETN-CAT Spread Log

```spread_observation_v1
date: 2026-05-08
as_of: "2026-05-07 23:51 UTC"
note: "PAPER REVIEW BASELINE - not a trade entry"
long_price: 399.15
short_price: 895.69
long_weight: 1.0
short_weight: -1.0
spread_value: 0.0
spread_zscore: null
beta_180d: null
correlation_180d: null
pnl_since_entry_pct: 0.0
borrow_rate_annual: null
thesis_health: watch
action: monitor
notes_brief: "Schema smoke only; spread/beta/correlation/borrow 缺 source，不能视为真实 entry。"
sources:
  - title: "Yahoo Finance ETN quote"
    url: "https://finance.yahoo.com/quote/ETN"
  - title: "Yahoo Finance CAT quote"
    url: "https://finance.yahoo.com/quote/CAT"
```

**结论先行**：这条 observation 只是 paper baseline，用来验证 `pair-trade` monitor 能读取 spread-log；`action` 保持 `monitor`，不触发真实 `open`。
