# Financial-Data Lite/Full 边界重划

> 状态: draft
> 日期: 2026-06-08
> 版本: v5.13.10

## 1. 背景

当前 `--mode lite` 和 `--mode latest_core` 几乎一样，full 模式不存在。SKILL.md 描述 lite/full 有 evidence-pack 等死文件区别——没人用。

## 2. 目标

重划 lite/full 边界，让代码和文档对齐实际消费场景：

- **Lite**：stock-quickread/candidate/peer 用的最少必要数据（~46 field）
- **Full**：modeling/DCF 用的完整数据（~72 field，多期+全字段）

## 3. 字段边界

### Lite（~46 field）

```
IS (12): revenue, cogs, gross_profit, sg_and_a, r_and_d, operating_income,
         ebit, ebitda, interest_expense, income_tax, net_income, eps
BS (6):  cash, accounts_receivable, inventory, total_assets, total_equity, total_debt
CF (3):  operating_cf, capex, dividends_paid
MKT (12): price, mcap, pe_ttm, pe_ntm, pb, ps, ev_ebitda, ev_sales, div_yield, beta, 52w_h/l
SEGMENTS: revenue, op_income, margin per segment
SUPP (3): order_backlog, orders, employees
期间:     latest FY + latest Q/H
```

### Full（lite + 18 补充字段 + 多期）

```
IS (+4):  pre_tax_income, sbc, d_and_a, amortization
BS (+8):  short_term_debt, long_term_debt, goodwill, intangible_assets,
          total_current_assets, total_current_liabilities, bonds_payable
CF (+3):  d_and_a, buybacks, fcf (derived)
SUPP (+8): installed_base, arr, nrr, grr, churn, customer_count,
           production_volume, utilization_pct
期间:     FY-2/FY-1/FY0 + sub-0/1/2/3
```

## 4. 产出

统一产出 **actuals-resolved.json**（lite 和 full 写同一个文件，full 只是字段更多、期间更多）。

删死文件：evidence-pack.json、full-filing.md、completeness.json、cross-check.json、source-map.json 不写入 actuals 目录。provider 的 `_raw/` 和 `_cache/datasets/` 路径保留不删（provider 证据留存）。

## 5. CLI

```
/financial-data <ticker>                  → --mode lite (default)
/financial-data <ticker> --mode full      → --mode full
/financial-data <ticker> --periods 3Y     → --mode full, 多期提取
```

## 6. 文件变更

| 文件 | 动作 |
|---|---|
| `financial_data.py` | 加 `--mode full`、lite/full 字段过滤器、多期逻辑（future） |
| `financial-data/SKILL.md` | lite/full 文档对齐新边界 |
| `stock-quickread/SKILL.md` | 确认 `--lite` 引用 -> `/financial-data <ticker>` |
| `3-statement-model/SKILL.md` | 改为 `--mode full` |
| `dcf-model/SKILL.md` | 改为 `--mode full` |
| `comps-analysis/SKILL.md` | 改为 `--mode full` |
