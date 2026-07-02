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

Q 列生成由 `build()` 内 **Driver Distribution** 自动完成，无需 agent 手动调参。

### Workflow

```
1. Reconcile: 全 A 财年 → 等比缩放 seg_quarters 使 ΣQ = Annual
2. Blend:     M∈{1,2,3} → 实际 Q 利润率混入年度 GM/OpexRev 假设
              blended = M/4 × actual + (1−M/4) × model
3. Q Driver Distribution:
   vol_asp:   Q_Vol = remaining_Vol × w_i, Q_ASP = remaining_ASP × s_i
              w 从实际 Q 数据或 r 外推，Σw=1; s 归一化到 Σ(w×s)=1
   yoy:       二分搜索 r s.t. ΣQ = Annual，链式公式锚
   backlog:   同上 pattern
4. Render:    Revenue = Driver 公式; GM/OM 实际Q→S1公式
5. U 列 Check: (Annual−ΣQ)/Annual → 目标 0%
6. Build 完成后 COM dump checks.json 含 q_checks + flags
```

### 收敛保证

| 项 | 收敛方式 | 预期 Δ |
|---|---|---|
| Revenue | Driver 分配数学保证 ΣQ_Rev = Annual | **0%** |
| Volume | Σw=1 保证 ΣQ_Vol = Vol_year | **0%** |
| GM/GP/OP | Blend 收窄实际vs模型差异 | 残余 ~5-10%（结构性的） |
| D&A | Q = Annual/4 公式 | 残余来自实际Q D&A ≠ 模型 |

### Agent 行为

- **不再需要**：调 q_history → rebuild → check Δ → 循环
- Revenue 自动收敛，无需干预
- GP/OP/D&A 残余差 → 说明实际 Q 的利润率/费用率与年度假设不同 → 供分析师判断
- 残余差 > 20% → 建议检查 JSON 数据（Q 实际值是否异常大/小）

### Checks.json Flag System

| Flag 类型 | 含义 | Agent 行动 |
|----------|------|-----------|
| Q 任何非 0% | 代码 bug（Annual≠ΣQ） | 报 dev，不调 JSON |
| P&L Check > 阈值 | 模型假设偏离 actuals | 调 JSON 假设，最多 3 轮 |
