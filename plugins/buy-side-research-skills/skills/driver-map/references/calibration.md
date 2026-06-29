# Calibration — Gap < 1%

vol_asp 和 capacity_util 线需要校准：公式算出的 FY25A Revenue 必须 ≈ Section 1 的 anchor 值。

## 验算公式

**vol_asp**: `Rev = Σ(Vol × Share% × ASP) / 100`

用 FY25A (FY0) 列的值手动验算，必须与 Section 1 的 `logic_line FY25A Rev` anchor 差距 < 1%。

## 调参优先级

Gap > 1% 时，按以下顺序调整：

1. **ASP** — 优先。价格有市场锚，调整最直观
2. **Volume** — 其次。产能/出货有公开数据支撑
3. **Share%** — 最后。从 segment split 反推，改得越少越好

## 禁止

- 带着 gap 交付 JSON
- 只调一个 tier 的 ASP 而不验算 blended 是否仍然锚住
- 用精确到小数第 3 位的数（假精度）—— round 到合理 sig fig

## 工具

`validate_json()` 只检查结构，不检查 gap。Agent 必须 **手动验算**；

```python
# 验算示例
vol = 7000  # t
ai = 0.05 * vol    # AI tier volume
auto = 0.09 * vol  # Auto tier volume  
cons = vol - ai - auto
rev = (ai * 26 + auto * 10 + cons * 4.9) / 100  # 万元 → M
print(f"Rev={rev:.0f}M, Anchor=450M, Gap={abs(rev-450)/450*100:.2f}%")
# → Rev=450M, Anchor=450M, Gap=0.02% ✓
```

## Quarterly Calibration

Q→FY Check column 显示 Δ = Annual − QSum。Δ ≠ 0 时按 module 调整：

| Module | 调整目标 | 不调 |
|---|---|---|
| vol_asp | Q Volume | ASP |
| yoy | Q YoY Active | Revenue chain |
| 其他 | 比例缩放 Q values | margin 结构 |

流程：build → audit → check Q column Δ → Δ > 阈值 → 调 JSON q_history driver → rebuild → loop until Δ < 阈值。
