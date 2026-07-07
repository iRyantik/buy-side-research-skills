# Visual Hierarchy — Excel 格类型约定

## 格类型表

| 类型 | 函数 | 字体 | 填充 | 含义 |
|---|---|---|---|---|
| **输入假设** | `I()` | Blue `#0000CC` | Yellow `#FFFFCC` | 研究员可调的模型假设 |
| **实际值** | `A()` | Black | Light Gray `#F0F0F0` | 财报披露 hardcode |
| **公式** | `CF()` | Black | 无 | 模型计算——**强制 number_format** |
| **通用** | `C()` | Black | 无 | 标签/通用值 |
| **重点 driver** | `HL()` | White Bold | Deep Red `#963634` | Volume/ASP/MCap/Shares/Price 标签 |
| **关键指标** | `BOLD()` | Black Bold | 无 | 需加粗的财务行标签 |

## Actual 格 (A) 应用位置

- **§1 Segments**: FY0 Rev / GP / OP / EBITDA + history（gray fill）
- **§3 P&L**: **无 A() 在 P&L 数据行中**——所有数据行都是 F 或 gap 推导（EBITDA depth 模式）。A() 只在 Rate Bridge 和 Check 行出现
- **Rate Bridge**: 存 FY-2 / FY-1 / FY0 actuals（`A()` 值，collapsed）
- **自动规则**: gray fill 格在 data 列自动加粗

## Rate Bridge（P&L 前，collapsed）

Rate Bridge 位于 P&L header 之前，是一个 collapsed section，用于存储历史 actuals 以便公式引用：

- 内容：FY-2 / FY-1 / FY0 actuals for Rev, GP, OI, EBITDA, NI, Tax, D&A（per depth）
- **EBITDA depth 模式**：`gap_gp` / `gap_oi` / `gap_ni` + `tax_rate` = Excel 公式引用 FY0 actuals 计算（**非 Python hardcoded**）
- 所有 bridge 行 collapsed：`outline_level=1`, `hidden=True`
- C 列 label 使用 `itf`（italic）字体

Bridge 用途：P&L 中的 gap 推导公式引用 Rate Bridge 中的 FY0 actuals 计算 gap 值，确保所有历史推演可从 actuals 复算。

## C 列字体规则

C 列标签字体按行类型决定，不再使用统一的 key-labels 自动加粗规则：

| 字体 | 缩写 | 适用范围 |
|---|---|---|
| **Bold** | `bf` | Revenue, Cost, GP, Opex, OI, D&A, EBITDA, Tax, Net Income（P&L $ amounts）；SOTP Revenue / EV / Mkt Cap / Net Debt / TOTAL |
| **Normal** | `nf` | 所有 YoY, GM, OPM, EBITDA margin, NPM（ratios / growth rates）；SOTP multiples；Overall items |
| **Italic** | `itf` | 所有 QoQ, Check 行, Bridge items, S2 split labels, residual % |

## Input 格 (I) 应用位置

- §2 Logic Lines: Volume, Share%, ASP, YoY, GM（非1:1线全列）, opex_rate, tax_rate
- Global: Opex rate (proj), Tax rate (proj)
- Nameplate Capacity
- SOTP multiples
- SOTP gap cells（EBITDA depth）
- Rate Bridge actuals（FY-2 / FY-1 / FY0）
- Check 行 actuals（historical years）
- **注意**: per-line history Volume/ASP 也是 I()——这些是分析师估计值，不是公司披露

## Check 行（P&L 底部，collapsed）

- 不再使用 inline Q-check column。Check 行统一放置在 P&L 底部，collapsed
- 每行存储 actuals（`I()`）for historical years（FY-2 / FY-1 / FY0）
- Check formula：`= (P&L − actuals) / ABS(actuals)`；projected years 留空
- Check label 在 C 列使用 `itf` 字体
- 覆盖项：Rev, GP, OI, EBITDA, NI, Tax, D&A（per depth）

## P&L 行顺序

P&L section 内统一行顺序如下：

```
Revenue → Rev YoY → Cost → GM → GP → GP YoY → Opex → OI → OI YoY →
OPM → D&A → EBITDA → EBITDA YoY → EBITDA margin → Tax → Net Income →
NI YoY → NPM
```

## SOTP Section

SOTP 估值 section 的 per-line 结构：

```
Revenue → [Metric] → [Multiple] → EV 或 Mkt Cap（method-dependent）
```

- **无 per-line Net Debt**——Net Debt 仅在 TOTAL 级别出现
- Revenue 行 C 列使用 `bf`（bold）
- Multiple 行 C 列使用 `nf`（normal）
- TOTAL 行汇总所有 line 的 EV / Mkt Cap，减去 Net Debt 得出 Equity Value

## 格式常量

| 常量 | 格式 | 用途 |
|---|---|---|
| `NUM` | `#,##0.0` | Revenue, GP, OP, NI, Cost, Opex, MCap |
| `DEC` | `#,##0.00` | ASP, 价格 |
| `INT` | `#,##0` | Volume, Capacity, Shares count |
| `PCT` | `0.0%` | GM, YoY, Margins, Opex rates, Tax rates |
| `0.0x` | | SOTP multiples |

## 其他规范

- 无网格线、全 Calibri 11
- C1: `(CUR millions)` 或 `(CUR bn)`，italic
- 冻结 D2，B1 下拉切换场景
- build 后跑 `audit_style.py` 检查 General format / font / fill violation

## Q 列

Q 和 Y 之间空 2 列（width=5），QoQ 行折叠隐藏。

## Chinese sub-rows

Section header 和 segment names 下一行 italic gray 中文翻译。
