# Pitfalls — Agent 自查清单

生成 JSON 前逐项检查。违反任何一项 → JSON 不合格。

## 结构

- [ ] `volume.proj` 长度 = `proj_years`
- [ ] 每个 tier 的 `asp` / `asp_bull` / `asp_base` / `asp_bear` 数组 ≥ `1 + proj_years`
- [ ] `gm.proj` 长度 = `proj_years`
- [ ] **非 1:1 线必须填 `gm.fy-2` / `gm.fy-1`**——缺 history GM → GP=0 → OP 为负
- [ ] `yoy.bull/base/bear` 各数组长度 = `proj_years`
- [ ] `opex_rate` 长度 = `3 + proj_years`

## 单位

- [ ] vol_asp 线: `unit_scale` 已设——cn 默认 100（万→M），jp/kr B mode 需要匹配显示单位
- [ ] vol_asp 线: `asp_unit` 已设——cn 默认 `万/t`，匹配实际 ASP 单位
- [ ] Volume 和 ASP 的单位乘除后能正确锚到 Rev(M)——生成前手动验算
- [ ] 数值格式已对：B mode `#,##0.0`，Volume `#,##0`，ASP `#,##0.00`

## 跨市场

- [ ] 非 cn 市场: `meta.yf_ticker` 是否有效？默认 ticker 可能失败
- [ ] 非 cn 市场: 数值格式——B mode 自动 `#,##0.0`（一位小数）
- [ ] 非 cn 市场: `logic_lines[].unit_scale` 是否匹配？cn=100, jp/kr B mode=1000

## ASP

- [ ] BBE tier: `bull[0] = base[0] = bear[0] = asp_fy0`（FY0 固定值，不随情景变）
- [ ] Simple ASP: 有 `asp_fy0` 时 `asp[0..]` = 投影年；无 `asp_fy0` 时 `asp[0]` = FY0
- [ ] **禁止** `asp_fy0` 和 `asp[0]` 写相同值——导致 FY+1 锁在 FY0

## Calibration

- [ ] vol_asp 线: 手动验算 FY0 Rev，gap < 1% vs Section 1 anchor
- [ ] 非 1:1 线: 验算 FY0 GP = Rev × GM，与 Check GP 对比
- [ ] 有 seg OP: 验算 FY0 per-line OP vs Check OP

## Segment 数据

- [ ] segment 填了 `fy-2`/`fy-1`（如果公司有历史披露）
- [ ] seg 有 op 披露 → 填 `op`，max_seg_depth 自动升到 op
- [ ] seg 有 ni 披露 → 填 `ni`
- [ ] `name_cn` 已填（中文翻译，独占一行）

## Profit 链

- [ ] 每条非 1:1 line 的 GM history 都有值
- [ ] 如果 seg 有 op：验证 Section 1 OP 投影列 = Σ per-line OP
- [ ] 如果 seg 有 ni：同上验证

## SOTP

- [ ] `sotp.method` 在 `{pe, ps, ev_ebitda, ev_ebit, ev_sales}`
- [ ] 旧 `sotp_pe: 40` 写法仍然可用，会自动转换
- [ ] EV 方法需要 `meta.net_debt`

## Non-GAAP

- [ ] 如果用 non-GAAP：`meta.basis` 已设，`meta.basis_note` 说明调整项
- [ ] actuals 数字 = non-GAAP 口径（分析师手动填入，不来自 CLI）

## 生成后

- [ ] 运行 `build-logic-model.py` 无报错
- [ ] 运行 `audit_style.py` — 0 errors
- [ ] 打开 Excel 检查 Section 1 FY0 Rev 与 Check 行一致性
- [ ] toggle B1 Bull/Base/Bear — ASP Active 列应变、Scenario Summary 三个情景数值不同
- [ ] Section 1 OP 投影列 = Σ per-line OP（如有）
- [ ] 列映射 print 确认 D/FY0/LC/SC 正确

## 已知坑

| # | 坑 | 避法 |
|---|---|---|
| 1 | 非 1:1 line 缺 history GM → GP=0 → OP 负 | 自查: 每条非 1:1 线填 `gm.fy-2/fy-1` |
| 2 | B mode 忘了改 unit_scale → Revenue 量级错 1000x | 验算: unit_scale = div（B mode=1000, M mode=1） |
| 3 | D/E 列 OP 公式被清 | 脚本已加 protected_rows |
| 4 | P&L actuals 没加粗 | 脚本 post-format 自动处理 |
| 5 | vol_asp 投影 Q ASP 用年度值未除 4 | 脚本 driver 分配自动处理（remaining_ASP） |
| 6 | 1:1 线 GM/OM 实际 Q 没用 S1 公式 | 脚本渲染自动处理（is_1to1 → S1 reference） |
| 7 | Q D&A 公式与 Annual 不一致 | 脚本: Q D&A = Annual_D&A/4 |
| 8 | 实际 Q 利润率拉偏年度假设 | Blend 步骤自动收窄（M/4 权重） |
| 9 | yoy 投影 Q YoY 率用年度值（非 QoQ） | 脚本 driver 分配自动二分搜索 QoQ rate r |
| 5 | yoy line FY0 Implied YoY 空白 | 脚本已修 |
| 6 | residual D/E 列空白 | 脚本已修 |
| 7 | Section 1 OP 投影列空白 | 脚本已加 OP fill |
| 8 | 裸 `ws.cell().value` → 无 number_format | 用 `CF()` 替代；CHECK 17 拦截 |

## Q 列

- [ ] Q columns Q actual data 从 yfinance/financial-data 拉取，不手填
- [ ] Q actual 值 A() 来自 quarters.segments，agent 不要编
- [ ] vol_asp: unit_scale 已设——ASP 和 Volume 单位乘除后 = Revenue 单位
- [ ] **unit scale gate**: gap >10% → 报警，检查 ASP 单位
- [ ] **4Q complete FY**: Quarterly Check column Δ = Annual − QSum。Δ≠0 → 进入 calibration 调整

## Q 已知坑

| # | 坑 | 避法 |
|---|---|---|
| Q1 | unit_scale 导致 Rev 偏差 10x | 验算: Vol×ASP/scale ≈ anchor，gap>10% 检查 ASP 单位 |
| Q2 | ASP 用 万 导致 scale 错 | ASP 和 Rev 同单位，避免 K/M 混淆 |
| Q3 | Q actual 和 Q proj 混合 FY | Check column 显示 Δ，进入 calibration |

## EBITDA Depth Pitfalls

### 1. gap_gp=0 trap

如果 actuals 缺 `gp` 字段，`gap_gp` 退化为 0，导致 GP = EBITDA，Cost / GM / Opex 无意义。必须在 actuals 补全 GAAP `gp` 字段。EBITDA depth 的 P&L 全部走公式链（F/F），GP 依赖 gap 从 EBITDA 反推——gap 本身需要 actuals 里的 gp 对位锚定。

### 2. FY0-only gap vs multi-year avg

gap 公式用 FY0 单年锚（`gap_gp = FY0_EBITDA - FY0_GP`），时间漂移会在历史年（FY-2、FY-1）Check 行显为 gap。Agent 应审视是否需要调整为多年平均 gap，尤其是当 GP/EBITDA 关系在历史年有明显趋势变化时。

### 3. Check reading

历史年 Check 非零 = 模型假设偏离 actuals。检查对应 line assumptions（GM、Opex rate、D&A assumptions）是否需调整。**注意**：FY0 年 Check 接近 0% 不意味着模型正确——FY0 是 gap 的计算基年，gap 公式天然锚在 FY0，FY0 Check 只能验证公式实现正确性，不能验证 gap 假设的合理性。

### 4. 1:1 lines in EBITDA depth

Section 2 不引用 Section 1（即使用了 I() 假设而非 S1 formula）。确保每条 1:1 line 有正确的 EBITDA margin 历史假设（`fy-2`/`fy-1`/`fy0`），否则 EBITDA 投影失去历史锚定。1:1 lines 在 EBITDA depth 下独立渲染完整 EBITDA margin -> EBITDA -> EBITDA YoY 链，不依赖 Section 1 的聚合结果。
