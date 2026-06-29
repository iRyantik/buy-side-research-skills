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

- §1 Segments: FY0 Rev / Cost / GP / OP / NI + history
- §3 P&L: Total Rev/GP/Opex/OP/D&A/Tax/NI FY-2~FY0
- **自动规则**: gray fill 格在 data 列自动加粗

## Input 格 (I) 应用位置

- §2 Logic Lines: Volume, Share%, ASP, YoY, GM (非1:1线全列), opex_rate, tax_rate
- Global: Opex rate (proj), Tax rate (proj)
- Nameplate Capacity
- SOTP multiples
- **注意**: per-line history Volume/ASP 也是 I()——这些是分析师估计值，不是公司披露

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
- C 列 key labels 自动加粗（Revenue/GP/GM/Total/Opex/OP/Tax/NI 等）
- Volume/ASP/MCap/Shares/Price C 列标签深红白字
- C1: `(CUR millions)` 或 `(CUR bn)`，italic
- 冻结 D2，B1 下拉切换场景
- build 后跑 `audit_style.py` 检查 General format / font / fill violation

## Check Column (X col)

完整 4Q FY 自动生成。每行 `=Annual − QSum`。跳过 margins/YoY/rates/BBE/empty。格式 `#,##0.0`，column group 折叠。

## Q 列

Q 和 Y 之间空 2 列（width=5），QoQ 行折叠隐藏。

## Chinese sub-rows

Section header 和 segment names 下一行 italic gray 中文翻译。
