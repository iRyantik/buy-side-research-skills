# Buy-Side Research Skills v3.1.0

Journal-first buy-side research skill suite for Claude/Cowork and Codex. v3 的重点不是维护交易状态，而是帮助研究员像 senior analyst 一样发现高价值问题、继续深挖，并把真正想清楚的研究沉淀到 topic journal。

## Core Idea

```text
Senior Analyst Radar → better AI questions → research → research-journal → Boss Brief
```

- `Senior Analyst Radar`：发现中高置信的高价值疑点，直接提醒。
- `next-step`：把疑点变成 1-2 个最值得问 AI 的问题。
- `research-journal`：只沉淀已研究清楚的认知增量。
- `boss-brief`：给老板 / PM 的高密度判断输出，不是简略摘要。

## Active Skills

| Skill | 用途 |
|---|---|
| `candidate-screener` | 从主题、假设或筛选条件找候选股票 |
| `stock-quickread` | 快速搞清楚一家公司值不值得继续看 |
| `peer-deep-dive` | 多家公司横向研究，找 cross-cut 信号 |
| `pair-trade` | 判断 Long / Short pair 是否成立，拆 spread 逻辑和 hedge 候选 |
| `alpha-thesis` | 构建 long / short thesis 和 variant view |
| `bear-pre-mortem` | 反向压力测试 thesis |
| `earnings-setup` | 财报前 setup / 财报后 quick read |
| `financial-model` | 搭新模型或更新已有模型，重点拆 revenue driver |
| `information-impact` | 验证消息 / 传闻 / 供应链 claim 是否靠谱 |
| `cross-market-compare` | A/H、ADR、跨市场估值和可交易性比较 |
| `research-journal` | 写 topic journal 或 Boss Brief |
| `next-step` | 指导下一步该怎么研究 |

## Senior Analyst Radar

遇到以下中高置信信号时，系统应主动提醒“这里值得深挖”：

- 业务实质错读
- 披露口径异常
- model-driver gap
- narrative-data mismatch
- margin / revenue mismatch
- market misread
- peer mismatch
- source conflict
- know-how gap

提醒只出现在对话中，不自动写入 journal。只有当用户实际研究并形成认知增量后，才由 `research-journal` 沉淀。

## Topic Layout

```text
topics/
  _meta/
    edge-radar.md
  [topic_type]/
    [topic-slug]/
      index.md
      [YYYY-MM-DD]-[session-slug]/
        research-journal.md
        boss-brief.md
```

同一个 topic 的不同时间研究都落在同一个 topic folder 下，用日期 session 隔离。`index.md` 是演进式地图，记录研究过的问题、核心结论、重要数据口径和历史 session。

## Research Journal

`research-journal.md` 格式要自然，不强制死板标题。它记录的是已经研究过、想清楚的东西：

- 关键结论
- 关键数据和 source / as-of
- 机制理解
- 名词 / know-how
- 剩余没搞清楚的问题

不要把单纯提醒、未研究的怪异信号、对话流水账写进去。

## Boss Brief

`boss-brief.md` 是老板 / PM 版高密度研究输出。它不是“简略版”，目标是让读者看到你比市场多理解了什么。

常用标题可以很正常：
- `Conclusion`
- `Takeaways`
- `Key Data`
- `Debate`
- `Implications`

生成前必须确认核心结论、关键数据、不能删的争议 / 风险、可以牺牲的细节。

## Archived v2 State Workflow

v2 的状态 workflow 已退出 active skills，归档在：

```text
archive/v2-state-skills/
archive/v2-state-fixtures/
```

它们保留历史参考，但不属于 v3 active workflow。

`pair-trade` 已在 v3.1 以 journal-first 研究工具形式恢复：它保留完整 pair builder / monitor 方法论，但不维护 v2 状态日志，只输出 pair research / monitor 判断。

## Version History

### v3.1.0
- Restored `pair-trade` as a journal-first active skill.
- Kept v2 state workflow archived; `pair-trade` no longer depends on state logs.

### v3.0.0
- Pivoted to journal-first research system.
- Added `research-journal` and `next-step`.
- Added Senior Analyst Radar and global `topics/_meta/edge-radar.md`.
- Archived v2 state workflow skills and fixtures.

### v2.2.0
- Added `candidate-screener`.

### v2.1.0
- Added `financial-model`.

### v2.0.0
- Added state workflow scaffolds.

### v1.2.0
- Aligned original research skills with buy-side workflow.
