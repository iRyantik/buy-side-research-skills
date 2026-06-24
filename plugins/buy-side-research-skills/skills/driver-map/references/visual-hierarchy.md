# Visual Hierarchy — Excel 格类型约定

| 类型 | 字体 | 填充 | 含义 | 写格函数 |
|---|---|---|---|---|
| **输入假设** | Blue `#0000CC` | Yellow `#FFFFCC` | 研究员可调的模型假设 | `I()` |
| **实际值** | Black | Light Gray `#F0F0F0` | 财报披露 hardcode | `A()` |
| **公式/计算值** | Black | 无 | 模型输出 | `C()` |

## Actual 格 (A) 应用位置

- §1 Segments: FY25A Rev / Cost / GP / GM
- §3 P&L: Total Rev FY23-25, Total GP FY23-25, Opex/OP/D&A/Tax/NI FY23-25
- Check rows: FY25A anchors

## Input 格 (I) 应用位置

- §2 Logic Lines: Volume, Share%, ASP, YoY, GM 投影, SOTP multiples
- Global: Opex rate FY26+, Tax rate
- Nameplate Capacity

## 其他规范

- 无网格线、全 Calibri 11
- C 列选择性加粗（Revenue/GP/GM/Total/Opex/OP/Tax/NI/MCap 等财务条目）
- C1: `(CUR millions)` 或 `(CUR bn)`，italic
- 冻结 D2，B1 下拉切换场景
- ASP 用 `#,##0.0`，Revenue 用 `#,##0`，GM/YoY 用 `0.0%`
