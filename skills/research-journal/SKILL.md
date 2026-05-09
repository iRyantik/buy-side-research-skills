---
name: research-journal
description: Use when summarizing a completed research session, writing topic research notes, preserving solved research insights, or preparing a high-density Boss Brief for a PM or boss.
---

# Research Journal

## Core Principle

Use this skill to preserve **research value that has actually been earned**. Do not log every reminder, detour, or interesting-but-unresearched anomaly. A journal entry is for conclusions, mechanisms, key data, and unresolved questions that the user has genuinely worked through.

Follow `CLAUDE.md §3` for source discipline. Natural-language output should be Chinese unless the user asks otherwise.

## Modes

### Private Research Journal

Use when the user says things like:
- "总结本轮研究"
- "总结本轮行业研究"
- "总结本轮 topic 研究"
- "写进 journal"
- "整理这个 topic"
- "把这次公司 / 行业 / 主题研究沉淀一下"

Before writing, first show a confirmation table:

| 问题 | 建议深度 | Value tags | 判断理由 | 写入位置 |
|---|---|---|---|---|

Depth levels:
- `skim`: 一句话结论 + 为什么暂时不深挖。
- `standard`: 结论 + 关键证据 + 研究含义。
- `deep`: 已经研究清楚的机制、关键数据、结论、剩余疑问。

Value tags:
- `data-anchor`
- `glossary`
- `mechanism`
- `market-structure`
- `model-driver`
- `alpha-view`
- `source-map`
- `open-question`
- `research-edge`
- `disclosure-anomaly`
- `driver-gap`
- `source-conflict`
- `know-how-gap`
- `market-misread`

Write to:

```text
topics/[topic_type]/[topic-slug]/[YYYY-MM-DD]-[session-slug]/research-journal.md
```

Also maintain the topic `index.md` as a natural map of researched questions and session links.

## Journal Writing Style

Do not use a rigid template. Write like a human research note:
- Start with a natural table of contents or short map of what was researched.
- Use headings that match the actual questions.
- Lead each section with the conclusion.
- Keep `skim` items light.
- Let `deep` items include data, terminology, mechanism, and the remaining thing not yet known.
- Do not add a mechanical `## 下一步` section. If useful, write naturally: "我还没搞清楚的是..." or "后面最值得补的是..."

Research Edge Radar reminders do **not** automatically enter the journal. If the anomaly was only noticed, leave it in the conversation. If the user actually researched it and formed a view, write the resulting insight naturally in the relevant section.

`driver-map` results can be absorbed only after they have been checked and understood. In the journal, record the solved driver conclusion, key source / as-of, and remaining uncertainty. Do not write unverified driver guesses as facts; mark weak items `[来源待补]` or keep them out.

`mechanism-map` results can be absorbed only after the mechanism has been genuinely researched and understood. In the journal, record the mechanism conclusion, the key terms, the flow / value-capture logic, source / as-of, and what remains uncertain. Do not write an unverified mechanism guess as settled know-how.

## Boss Brief

Use when the user says:
- "做一版给老板看的"
- "给 PM 的版本"
- "boss brief"
- "发给别人看的研究结论"

Boss Brief is not a short summary. It is a high-density memo whose goal is to communicate the research judgment increment.

Before writing, confirm:
- 核心结论
- 必须保留的关键数据
- 哪些争议 / 风险不能删
- 哪些细节可以牺牲

Then write to:

```text
topics/[topic_type]/[topic-slug]/[YYYY-MM-DD]-[session-slug]/boss-brief.md
```

Use normal memo headings such as:
- `Conclusion`
- `Takeaways`
- `Key Data`
- `Debate`
- `Implications`

Do not force all headings into every brief. Preserve the strongest conclusion, 3-5 final takeaways, critical data with source/as-of, debate or variant view, and the implication for research judgment.

## Common Mistakes

- Writing every interesting reminder into the journal.
- Calling Boss Brief a "简略版" or "轻量摘要".
- Turning the journal into a transcript.
- Recording unsourced numbers as facts.
- Recording a `driver-map` guess as settled business reality before source verification.
- Recording a `mechanism-map` guess as settled industry know-how before source verification.
- Using a rigid template when the research question needs a natural memo.
