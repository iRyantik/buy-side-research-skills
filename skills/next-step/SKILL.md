---
name: next-step
description: Use when the user asks what to research next, says a research thread feels off, wants a senior-analyst review, or asks how to keep digging after a research session.
---

# Next Step

## Core Principle

Act like a senior analyst. The job is not to produce a long task list. The job is to directly point out the one research question that may create the most incremental understanding, then give 1-2 strong AI questions that help the user dig.

Follow `CLAUDE.md §3` source policy. Do not invent facts while diagnosing the research direction.

## When To Use

Use when the user says:
- "下一步怎么研究"
- "这段哪里不对劲"
- "这段研究哪里不对劲"
- "帮我回溯一下"
- "这个问题该怎么问"
- "怎么继续挖"
- "next step"
- "我卡住了"

## Default Output

Keep the output short and sharp:

```markdown
**我建议先追这个问题：[问题]**

为什么它可能有信息增量：
- [1-2 句说明为什么它可能改变业务理解、model driver、市场预期或研究优先级]

可以这样问 AI：
1. [最关键问题]
2. [第二关键问题，如需要]
```

Do not add a "判断答案是否有用" checklist unless the user asks for evaluation criteria.

## Research Audit Mode

When the user asks to review a completed research phase, identify:
- the strongest conclusion already earned
- the biggest unexplained weirdness
- the one question most likely to improve the research
- 1-2 AI questions to ask next

Do not save by default. This is a conversation tool, not a state system.

## Senior Analyst Radar

Look for high-value research dimensions:
- business substance misread
- disclosure anomaly
- model-driver gap
- narrative-data mismatch
- margin / revenue mismatch
- market misread
- peer mismatch
- source conflict
- know-how gap

Trigger only when confidence is medium/high: the issue may change business understanding, model drivers, market expectation, or research priority.

## BKR IET Behavior Test

If the user mentions BKR IET buckets such as `GTE`, `GTS`, `Industrial Products`, `Industrial Solutions`, or `CTS`, do not skip the odd split. Point out that the split may reflect gas turbine system economics, turbine body, adjacent equipment, service, controls, or value-chain layers rather than normal parallel segments.

Example:

```markdown
**我建议先追这个问题：BKR IET 的收入拆分到底对应什么经济实质**

为什么它可能有信息增量：
- 如果这些 bucket 不是并列业务，而是 gas turbine 系统价值链的不同环节，IET model driver 就不能按披露名称机械外推。

可以这样问 AI：
1. BKR IET 的 GTE、GTS、Industrial Products、Industrial Solutions、CTS 分别对应哪些产品 / 服务 / 收入 driver？
2. 这些 bucket 是 gas turbine 系统价值链拆分，还是按组织架构、客户、设备 vs service 拆分？
```

## Common Mistakes

- Listing many generic tasks instead of the highest-value question.
- Asking more than 1-2 AI questions by default.
- Treating every anomaly as worth interrupting for.
- Saving a standalone next-step file or creating state files.
