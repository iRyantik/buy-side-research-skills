---
name: thesis-tracker
description: Use when checking whether an existing thesis still holds, updating thesis health, reviewing kill criteria, or maintaining a catalyst pipeline across positions.
---

# Thesis Tracker

读取已有 thesis 和 decision log，判断 thesis health、catalyst pipeline、kill criteria 是否变化。它是维护系统，不是重新写一篇 thesis。

## Source 政策

遵守 `CLAUDE.md §3`；若冲突，以 `CLAUDE.md` 为准。任何新事实、新数字、新事件都必须有 source。对 health 的判断是研究员判断，不需要单独 source。

## 触发场景

- "X thesis 还成立吗"
- "帮我更新 thesis health"
- "本周 catalyst pipeline"
- "哪些持仓需要 review"

## 读取 / 写入

读取：
- `coverage/[ticker]/thesis.md`
- `pairs/[LONG_TICKER]-[SHORT_TICKER]/thesis.md`
- `journal/decisions.md`
- `portfolio/catalyst-pipeline.md`

写入或建议更新：
- `coverage/[ticker]/health-log.md`
- `portfolio/catalyst-pipeline.md`
- 必要时建议修改 `coverage/[ticker]/thesis.md` frontmatter 的 `health_status`, `updated_at`, `next_catalyst`

## 输出格式

### 1. 持仓健康度表（必填）

| Ticker / Pair | Direction | Entry / 当前价 | P/L vs Bench | Health | Distance to Kill | Changed Assumption | Next Catalyst | Action |
|---|---|---|---|---|---|---|---|---|
| XOM | Long | 110 / 145 | +12% (vs +5% SPX) | active | 远（kill@$95） | none | Q3 print 11/15 | no action |
| ASML-AMAT | Pair | -1.5σ / -0.3σ | +8% spread converge | watch | 中（kill@+0.5σ） | AMAT memory better than expected | ASML Q3 10/22 | review |
| TSLA | Short | 280 / 305 | -8% (vs +5% SPX) | impaired | 近（kill@$320） | demand resilience higher than thesis | Q3 10/19 | review or close |

字段说明：
- **Health**: `active`（thesis OK） / `watch`（出现 weakening 信号） / `impaired`（关键假设动摇但未 kill） / `killed`（已触 kill criteria）
- **Distance to Kill**: 用具体距离表达（百分比 / σ / 美元），不接受"远 / 中 / 近"无量化
- **P/L vs Bench**: 必须 vs 适当 benchmark（SPX / 沪深 300 / sector ETF），不只看绝对回报

### 2. Catalyst 时间线（按日期排序，未来 8 周）

| Date | Ticker / Pair | Event | Importance to Thesis | Pre-print prep done? |
|---|---|---|---|---|
| 2026-10-19 | TSLA (Short) | Q3 财报 | high (确认 demand resilience or break) | no — 需触发 earnings-setup pre-print |
| 2026-10-22 | ASML (Pair long) | Q3 财报 | high (EUV bookings) | yes — setup 已 ready |
| 2026-10-30 | XOM (Long) | Q3 + investor day | medium | no |
| 2026-11-15 | OPEC+ | 减产决定 | high (XOM thesis) | n/a (政策事件) |

### 3. Takeaway（≤ 3 条）

明确指出：
- **最需要 review 的标的**（health 是 impaired 或 watch 的）—— 触发 thesis 重审 / bear-pre-mortem
- **最近的 catalyst**（未来 14 天内的）—— 触发 earnings-setup pre-print
- **最接近触 kill 的标的**（distance to kill < 10%）—— 优先关注

### 4. 自动联动建议

每个 health 异常 / catalyst 临近的标的，明确建议下一步触发哪个 skill：
- Health = impaired → 触发 `bear-pre-mortem` 重做
- Health 变化触发 thesis 文件 frontmatter 更新（`health_status`、`updated_at`）
- 即将到来的 catalyst → 触发 `earnings-setup` pre-print
- Distance to kill < 5% 或已触 → 触发 `decision-journal`（review or close action）

## 规则

- 先读 YAML frontmatter，再读正文；不要靠自然语言猜字段。
- 如果缺 `key_assumptions` / `kill_criteria` / `next_catalyst`，先标记 schema gap，不要硬编。
- 只建议改状态；除非用户明确要求，不直接重写旧 thesis 正文。
