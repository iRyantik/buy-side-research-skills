# Pitfalls — Agent 自查清单

生成 JSON 前逐项检查。违反任何一项 → JSON 不合格。

## 结构

- [ ] `volume.proj` 长度 = `proj_years`
- [ ] 每个 tier 的 `asp` / `asp_bull` / `asp_base` / `asp_bear` 数组 ≥ `1 + proj_years`
- [ ] `gm.proj` 长度 = `proj_years`
- [ ] `yoy.bull/base/bear` 各数组长度 = `proj_years`
- [ ] `opex_rate` 长度 = `3 + proj_years`
- [ ] `capacity.proj` 长度 = `proj_years`（如有）

## 单位

- [ ] vol_asp 线: `unit_scale` 已设——cn 默认 100（万→M），jp/kr 设为 1
- [ ] vol_asp 线: `asp_unit` 已设——cn 默认 `万/t`，匹配实际 ASP 单位
- [ ] Volume 和 ASP 的单位乘除后能正确锚到 Rev(M)——生成前手动验算

## ASP

- [ ] BBE tier: `bull[0] = base[0] = bear[0]`（FY25 固定值，不随情景变）
- [ ] Simple ASP: 无 `asp_fy0` 时 `asp[0] = FY25`，`asp[1:]` = 投影年
- [ ] **禁止** `asp_fy0` 和 `asp[0]` 写相同值——导致 FY26 锁在 FY25

## Calibration

- [ ] vol_asp 线: 手动验算 FY25 Rev，gap < 1% vs Section 1 anchor

## Capacity

- [ ] 有产能假设的线填了 `capacity` + `ramp_notes`
- [ ] `capacity.proj` 长度 = `proj_years`
- [ ] `ramp_notes` key 格式: `fy26`, `fy27`...（两位数年份）

## SOTP

- [ ] `sotp.method` 在 `{pe, ps, ev_ebitda, ev_ebit, ev_sales}`
- [ ] 旧 `sotp_pe: 40` 写法仍然可用，会自动转换
- [ ] EV 方法需要 `meta.net_debt`

## 生成后

- [ ] 运行 `build-logic-model.py` 无报错
- [ ] 打开 Excel 检查 Section 1 FY25A Rev 与 Check 行一致性
- [ ] toggle B1 Bull/Base/Bear — ASP Active 列应变、Scenario Summary 三个情景数值不同

## 已知坑（不改脚本，Agent 自己避）

| # | 坑 | 避法 |
|---|---|---|
| 1 | for 循环里写 R+=1 | 脚本已修 |
| 2 | exec() 赋值 | 脚本已修 |
| 3 | asp_fy0 重复 asp[0] | 自查 ASP 规则 |
| 4 | P&L Check 用 segment sum | 脚本已修 |
| 5 | Scenario NI = GP×(1-opex) | 脚本已修 |
| 6 | SOTP 依赖 depth | 脚本已修（永算全链）|
| 7 | yfinance 限流 | meta.mcap_m fallback |
| 8 | 股吧/论坛假数据 | 不采纳——优先卖方>公司口径 |
| 9 | 不验算 gap 就交付 | 自查 calibration |
| 10 | ASP 数组长度不够 | 自查结构 |
