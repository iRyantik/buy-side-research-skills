# Valuation Method — Auto-Selection

Agent 写 `logic_lines[].sotp` 时，按业务特征自动选最佳方法。研究员可 override。

## 决策树

```
NI > 0 且最近 2 年 margin 稳定?
  ├─ Yes → PE（默认，市场标准）
  └─ No → 为什么亏 / 不稳定？
            ├─ 高 D&A（制造业/重资产）→ EV/EBITDA
            ├─ 早期/高增长/pre-profit → PS
            ├─ 订单驱动/项目制 → EV/Sales
            └─ 特殊情况 → 标 [需查证]，agent 推荐 + 研究员确认
```

## Per Line 覆写

同一家公司可以混合——成熟业务 PE，新业务 PS，重资产 EV/EBITDA。

## Multiple 预设

Agent 从 actuals TTM PE 或行业估值表推测初始值（蓝格，研究员调）。不确定标 `[估算]`。

## 支持的方法

| method | 公式 | 需要 meta |
|---|---|---|
| `pe` | NI_alloc × PE → MCap | 无额外 |
| `ps` | Revenue × P/S → MCap | 无额外 |
| `ev_ebitda` | EBITDA_alloc × EV/EBITDA − NetDebt_alloc → MCap | net_debt |
| `ev_ebit` | EBIT_alloc × EV/EBIT − NetDebt_alloc → MCap | net_debt |
| `ev_sales` | Revenue × EV/Sales − NetDebt_alloc → MCap | net_debt |

向后兼容：旧 `"sotp_pe": 40` 自动 → `{"method": "pe", "multiple": 40}`。

## SOTP Structure

Per-line chain: **Revenue** -> **[Metric]** -> **[Multiple]** -> **EV/Mkt Cap** (method-dependent). The Metric column depends on the valuation method:
- `pe`: Revenue -> NI_alloc -> PE -> Mkt Cap
- `ps`: Revenue -> Revenue -> P/S -> Mkt Cap
- `ev_ebitda`: Revenue -> EBITDA_alloc -> EV/EBITDA -> EV
- `ev_ebit`: Revenue -> EBIT_alloc -> EV/EBIT -> EV
- `ev_sales`: Revenue -> Revenue -> EV/Sales -> EV

**Net Debt** is placed at the TOTAL level only — never allocated per-line. SOTP line EV/Mkt Cap values sum to a subtotal, then:

```
TOTAL = Σ per-line EV (or Mkt Cap)
Mkt Cap = TOTAL − Net Debt (for EV methods) / TOTAL (for Mkt Cap methods)
```
