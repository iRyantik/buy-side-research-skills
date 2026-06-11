# Universal Data Landing — actuals as Single Source of Truth

> 状态: planned | 日期: 2026-06-11 | 目标: v5.26.0

---

## 1. 问题

**actuals-resolved.json 只覆盖 provider pipeline 能抓到的数据。** SEC 有 revenue_split，EDINET 没有。Quartr 有的 FY2026，EDINET 没有。Futunn 爬到的分部利润，任何 provider 都没有。

agent 在 skill 执行中获取的大量数据（Playwright、PDF、WebSearch、Quartr、IR 页面），散落在 artifact 的 md 表格里——没有落回 actuals。下一次 session、下一个 skill 无法复用。

## 2. 设计

### 核心机制

**`_supplement` key**——actuals-resolved.json 中与 `statements` 平级，作为 provider 未覆盖数据的统一落点。

格式与 `statements` 完全同构：

```json
{
  "statements": {
    "income_statement": [{"concept": "net_sales", "values": {"FY2024": 18867}}],
    "revenue_split": [{"split_type": "segment", "member_label": "...", "values": {...}}]
  },
  "market_data": {...},
  "_supplement": {
    "income_statement": [{"concept": "revenue", "values": {"FY2026": 31510}}],
    "revenue_split": [{"split_type": "segment", "member_label": "光計測機器", "values": {"FY2025": 17950}}],
    "consensus": {"fy2027": {"revenue": {"est": 320000}, "analyst_count": 2}},
    "custom_kpi": {"order_backlog_Q2FY2026_JPYm": 1200}
  }
}
```

每条 supplement 必带 `source` + `source_url` + `verified_at`。

### 数据范围

不限 stock、不限 provider、不限数据类型。覆盖：

| 类型 | 示例 | 常用来源 |
|---|---|---|
| income_statement | 补充 FY（Quartr）、补充 margin split | Quartr, Futunn, IR PDF |
| balance_sheet | 补充 BS 行项 | IR PDF, Futunn |
| cash_flow | 补充 CF 行项 | IR PDF |
| revenue_split | 分部/地域/产品/客户/渠道/收入确认 各维度 | Futunn, IR PDF, Playwright |
| consensus | FY estimate, analyst count | MarketScreener, TipRanks |
| custom_kpi | backlog, orders, ASP, utilization, headcount | earnings call, IR PDF |
| 其他 | 任何有 provenance 的数字 | — |

### Merge 逻辑

`statements` U `_supplement`。同 (concept/period) 或同 (split_type, member, concept, period) → `_supplement` 覆盖（agent 最新发现优先）。

provider data 不受影响——supplement 只能覆盖 supplement 自身，不修改 `statements` 内的行。

### Agent 行为

```
任何数据 → Edit actuals._supplement.<type> → 落盘

Edit 前必 Read——old_string 包含当前 _supplement 全文，
保证 merge 准确、防止覆盖。
```

### 消费端

`_build_appendix_format()` `_render_segments()`：先读 `statements`，空则 fallback `_supplement`。agent 不用手动补 appendix。

## 3. 文件改动

| 文件 | 改动 | 行数 |
|---|---|---|
| `actuals-to-appendix.py` | `_render_segments` + `_build_appendix_format` fallback `_supplement` | +8 |
| CLAUDE.md ZH/EN template | §5.6 数据落地规则 | +12 |
| `pre_write_gate.py` | CHECK 16——artifact 数字 ∈ actuals (statements ∪ supplement) | +25 |
| `actuals-resolved.json` | 无改动（`_supplement` 是约定，非 schema 变更） | 0 |

## 4. 泛化性

跨 market（US/HK/CN/JP/KR/TW/EU）、跨 provider（SEC/EDINET/DART/AKShare/FinMind/OpenESEF）、跨数据类型——所有 agent 获取的数据都落盘。

新数据类型只需加到 `_supplement` 下新 key，不改上游逻辑。

新 source 只需 agent 调它，结果 Edit 进 `_supplement`，不改 actuals 结构。

## 5. 不做

- 不写 enrich.py（agent Edit 直接 merge，subprocess 不必要）
- 不改变 `statements` 的写入逻辑（provider pipeline 独立）
- 不要求 `_supplement` 数据通过 completeness matrix（它是补丁，自带 provenance 就是质量声明）
- 不做"智慧 merge"——simple key+period 覆盖，agent 自己判断哪个数据新
