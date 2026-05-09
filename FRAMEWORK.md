# FRAMEWORK.md — Journal-First Buy-Side Research Skills v3.1

> `CLAUDE.md` 是唯一 constitution。本文件是系统设计蓝图，不覆盖 `CLAUDE.md`。

## 1. System Thesis

v3 的价值不是“多写几个文件”，而是投研 value add：像 senior analyst 一样发现高价值研究问题，指导用户下一步怎么挖，并把真正想清楚的认知增量沉淀下来。

核心链路：

```text
Research Edge → Better AI Question → Research → Journal → Boss Brief
```

## 2. Active Skills

| Module | Skills |
|---|---|
| Discovery | `candidate-screener`, `stock-quickread`, `peer-deep-dive` |
| Pair Research | `pair-trade` |
| Thesis / Challenge | `alpha-thesis`, `bear-pre-mortem` |
| Event / Claim | `earnings-setup`, `information-impact` |
| Model / Market Structure | `financial-model`, `cross-market-compare` |
| Journal / Coach | `research-journal`, `next-step` |

The v2 state workflow has been archived outside active `skills/`.

## 3. Senior Analyst Radar

Global rule lives in `CLAUDE.md`; reusable prompt patterns live in `topics/_meta/edge-radar.md`.

High-value dimensions:
- business substance misread
- disclosure anomaly
- model-driver gap
- narrative-data mismatch
- margin / revenue mismatch
- market misread
- peer mismatch
- source conflict
- know-how gap

Trigger only when the issue may change business understanding, model driver, market framing, peer group, or research priority.

Default reminder:

```markdown
**这里值得深挖**
- 怪异点：[哪里不自然]
- 可能说明：[1-2 个解释]
- 可以问 AI：[1-2 个最关键问题]
```

## 4. Skill Contracts

### `next-step`

Research coach, not task list. It gives:
- the highest-value next research question
- why it may create information gain
- 1-2 AI questions to ask next

It does not save files by default.

### `research-journal`

Captures solved research insight:
- `Private Research Journal`
- `Boss Brief`

Private journal is natural, not a rigid template. It records the conclusion, data, mechanism, terminology, and remaining question that the user actually researched.

Boss Brief is a high-density memo for a boss / PM. It optimizes judgment transfer, not brevity.

### `information-impact`

Claim Check + Research Relevance. It verifies whether a claim is credible, then decides whether it creates a research question. It does not write portfolio impact or state files.

### `pair-trade`

Journal-first pair research tool. It keeps the full builder / monitor methodology from the original pair workflow: independent long and short theses, spread history, beta / correlation, sizing, risk matrix, and P/L attribution. It does not maintain trade state, append logs, or depend on the archived v2 workflow.

## 5. Files

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
screens/
peers/
quickreads/
cross-market/
archive/
  v2-state-skills/
  v2-state-fixtures/
```

No topic-level edge signal file. No standalone next-step file. A weird signal enters the journal only after it has been researched.

## 6. Edge Radar Document

`topics/_meta/edge-radar.md` only contains:

1. **识别信号**
2. **可以怎么问 AI**

It is not a state log, status tracker, case library, or hypothesis database.

## 7. BKR IET Behavior Test

When encountering `GTE / GTS / Industrial Products / Industrial Solutions / CTS`, the system should not summarize and move on. It should point out that this may reflect gas turbine system economics, turbine body, adjacent equipment, service, controls, or value-chain layers.

Expected behavior:
- directly say this is worth digging
- offer 1-2 strong AI questions
- do not create a state file
- let journal capture the insight only after the user actually researches it

## 8. Validation

Required checks:
- active `skills/` count is 12
- active docs and metadata list the same 12 skills
- archived v2 state skills are outside active `skills/`
- old brief naming, topic-level edge signal files, and standalone next-step files do not appear
- `Senior Analyst Radar`, `edge-radar.md`, `boss-brief`, and `next-step` appear in public docs

**版本**：v3.1.0
**最后更新**：2026-05-09
