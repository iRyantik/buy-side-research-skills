---
name: thesis-tracker
description: Use when checking whether an existing thesis still holds, updating thesis health, reviewing kill criteria, or maintaining a catalyst pipeline across positions.
---

# Thesis Tracker

读取已有 thesis、decision log 和 pair thesis，判断 thesis health、assumption drift、kill criteria、catalyst urgency。它是状态维护工具，不是重新写一篇 thesis。

## Source 政策

遵守 `CLAUDE.md §3`；若冲突，以 `CLAUDE.md` 为准。任何新事实、新数字、新事件都必须有 source。`health_status` 是研究判断，不需要单独 source，但支撑这个判断的事实必须有 source。

## 触发场景

- "X thesis 还成立吗"
- "帮我更新 thesis health"
- "本周 catalyst pipeline"
- "哪些持仓需要 review"
- "把 VRT 加入 tracker / 更新 health-log"

## 读取 / 写入

读取：

- `coverage/[ticker]/thesis.md`
- `pairs/[LONG_TICKER]-[SHORT_TICKER]/thesis.md`
- `journal/decisions.md`
- `portfolio/catalyst-pipeline.md`
- 已存在的 `coverage/[ticker]/health-log.md`

写入或建议更新：

- append `coverage/[ticker]/health-log.md`
- replace `portfolio/catalyst-pipeline.md`
- 必要时建议修改 `coverage/[ticker]/thesis.md` frontmatter 的 `health_status`, `updated_at`, `next_catalyst`

默认只改状态文件。除非用户明确要求，不重写旧 thesis 正文。

## 工作流

1. 先读 thesis frontmatter。优先使用 `ticker`, `trade_structure`, `direction`, `conviction`, `health_status`, `next_catalyst`, `key_assumptions`, `kill_criteria`, `sources`。
2. 再读正文摘要，确认 thesis one-liner、当前论点和缺口。
3. 读取 `journal/decisions.md`，区分 `open/add/trim/close/review`。`review` 不等于建仓；`position_gross_pct: 0` 的条目只能当 watchlist / research queue。
4. 判断三件事：assumption drift、distance to kill、catalyst urgency。
5. 输出结论先行的 health table 和 catalyst pipeline。
6. 如果需要落盘，append `health_observation_v1` 到 health-log，并重写 `portfolio/catalyst-pipeline.md`。

## Health 判断边界

| Health | 定义 | Action |
|---|---|---|
| `active` | 核心假设仍被新事实支持，kill criteria 远，catalyst 正常推进 | monitor |
| `watch` | 论点未失效，但出现估值、数据缺口、catalyst 临近或关键假设未验证 | monitor / review |
| `impaired` | 核心假设被新事实动摇，或 distance to kill 已接近 | trigger `bear-pre-mortem` or `decision-journal review` |
| `killed` | kill criteria 已触发，或 thesis 关键前提被反证 | trigger `decision-journal close` |

`Distance to Kill` 必须量化；可以用价格、spread z-score、margin threshold、order growth、event miss。不能只写"远 / 中 / 近"。拿不到数据时写 `[来源待补]`，并把 health 至少降到 `watch`。

## health_observation_v1 写入契约

每次 tracker 落盘时，append 一个 fenced block：

```health_observation_v1
date: 2026-05-08
as_of: "2026-05-08"
ticker: VRT
linked_thesis: coverage/VRT/thesis.md
linked_decision: 2026-05-08-VRT-review-001
previous_health_status: null
health_status: watch
distance_to_kill: "未量化；kill criteria 依赖后续 orders / margin / revisions。"
changed_assumption: "无新事实变化；这是从 AI 电力 fixture 初始化的 tracker baseline。"
action: monitor
next_review_trigger: "Q2 2026 earnings release or earlier guidance/order commentary"
sources:
  - title: "Vertiv Q1 2026 results"
    url: "https://investors.vertiv.com/news/news-details/2026/Vertiv-Reports-Strong-First-Quarter-with-Diluted-EPS-Growth-of-136-Adjusted-Diluted-EPS-Growth-of-83-Raises-Full-Year-Guidance/default.aspx"
```

字段要求：

- `linked_thesis` 必须指向实际 thesis 文件。
- `linked_decision` 如果来自 journal，必须写 decision id；没有就填 `null`。
- `previous_health_status` 来自上一条 health-log 或 thesis frontmatter。
- `health_status` 只能是 `active`, `watch`, `impaired`, `killed`。
- `action` 只能是 `monitor`, `review`, `update_thesis`, `trigger_earnings_setup`, `trigger_decision_journal`, `close`.

## 输出格式

第一段必须给结论：哪个 thesis 需要 action，哪个只是 monitor。

### 1. Health Table

| Ticker / Pair | Direction | Position State | Health | Distance to Kill | Changed Assumption | Next Catalyst | Action |
|---|---|---|---|---|---|---|---|
| VRT | Long review | watchlist, 0% gross | watch | 未量化 `[来源待补]` | valuation support 未验证 | Q2 2026 earnings `[来源待补]` | monitor |

### 2. Catalyst Pipeline

| Date | Ticker / Pair | Event | Importance to Thesis | Prep Done? | Next Skill |
|---|---|---|---|---|---|
| 2026-Q2 date `[来源待补]` | VRT | Q2 earnings | high | no | `earnings-setup` |

### 3. Takeaway

最多 3 条：

- 最需要 review 的标的。
- 未来 14 天内的 catalyst。
- 最接近 kill 的标的。

### 4. State Writes

明确说明写了什么：

- `coverage/VRT/health-log.md`: appended `health_observation_v1`
- `portfolio/catalyst-pipeline.md`: replaced current pipeline
- `coverage/VRT/thesis.md`: no body rewrite; optional frontmatter update only

## VRT Fixture 示例

如果读到 `coverage/VRT/thesis.md` 和 `journal/decisions.md` 中的 `2026-05-08-VRT-review-001`：

- 这是 `review`，不是 `open`。
- `position_gross_pct: 0.0`，所以不能把它写成真实持仓。
- health 初始应为 `watch`，因为基本面强但 valuation / consensus revision work 未完成。
- catalyst-pipeline 应写成 watchlist catalyst，而不是 portfolio exposure。

## 规则

- 先读 YAML frontmatter，再读正文；不要靠自然语言猜字段。
- 缺 `key_assumptions`, `kill_criteria`, `next_catalyst` 时标记 schema gap，不要硬编。
- 新事实必须有 source；找不到就写 `[来源待补]`。
- `review` 不等于 `open`；watchlist 不等于 portfolio。
- 除非用户明确要求，不重写 thesis 正文。
