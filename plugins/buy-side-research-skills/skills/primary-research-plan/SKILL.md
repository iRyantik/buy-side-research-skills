---
name: primary-research-plan
description: Design an expert call, channel check, survey, or fieldwork plan to verify a key investment hypothesis.
---

# Primary Research Plan

Design an expert call, channel check, survey, or fieldwork plan to verify a key investment hypothesis.

## Research Runtime Capsule

**执行本 skill 前必须先读取以下文件：**
- `_shared/research-runtime.md` §1（数据获取链）§2（来源验证链）§2.1（资料收集）§2.2（Source 纪律）§2.5（图片下载链）§4（产出合约）§5（保存合约）

**自动 Hook 防御：** `pre_write_gate`（source/tables/mermaid/image）`source_contract` `table_render_integrity` `mermaid_syntax` `skill_structure_contract` `evidence_ledger_floor`

## 心法

Primary research 的价值不是"多问几个人"，而是把 desk research 里最脆弱、最可能改变判断的假设拿到现实世界验证。

三个核心问题比二十个 interview question 更重要：
1. **哪个假设最值得验证？**——不是所有 gap 都需要 primary research，选那个会让你的 thesis 变方向的
2. **谁有答案？**——customer 知道需求、supplier 知道产能、ex-employee 知道内部运营、distributor 知道价格
3. **看到什么结果就该停？**——confirm/mixed/weaken/kill 四 gate，提前写好，避免事后 cherry-pick

合规红线必须标——不能问 non-public orders、客户名单、未公开价格、contract terms、未来 guidance。但合规是 guardrail 不是 centerpiece。好计划的核心是研究设计，不是合规检查表。

## 触发场景

- "这个假设应该找哪些人验证"
- "帮我设计专家访谈计划 / channel check"
- "怎么问客户 / 供应商才合规"
- "这个 thesis 哪些部分需要 primary research"
- "设计 survey / fieldwork 验证计划"

**不应触发**：验证单条 claim 可信度 → `information-impact`；拆 driver → `driver-map`；写 thesis → `alpha-thesis`。

## 输入澄清要求

| 维度 | 含义 | 默认假设 |
|---|---|---|
| 研究对象 | ticker / 公司 / 行业 / segment | 按用户原词 |
| 要验证的假设 | consensus gap / driver gap / thesis assumption | 从上下文抽取 |
| 受访对象 | customer / supplier / competitor / ex-employee / expert | 默认多 persona |
| 时间窗口 | next print / 3M / 12M | 默认 12M |
| 合规约束 | 内部 restricted list / expert network rules | 默认 unknown，写 "follow firm compliance" |

## Mode A: Standard Plan

用于把多个关键假设转成完整 fieldwork plan。

### 输出结构

```markdown
## Verdict

[2-3 句：最值得验证的假设是什么，找哪种 persona，看到什么结果会改变 decision]

## 1. 验证什么

| Hypothesis | 已有证据 | 缺什么 | 改变什么决策 | 优先级 |
|---|---|---|---|---|
| [假设] | [现有 source] | [什么信息能填 gap] | [thesis / model / sizing / ranking] | High / Med / Low |

> 挑 1-2 个 High 优先级的进入 §2-§4。中低优先级的标 "后续"。

## 2. 找谁问

| Persona | 能知道什么 | 找几个 | 为什么是他们 |
|---|---|---|---|
| [customer / supplier / ex-employee / expert / distributor] | [process / historical / directional / aggregated] | [n≥3] | [验证 §1 哪个假设] |

## 3. 怎么判断

| 结果 | 什么样的 evidence | 做什么 |
|---|---|---|
| ✅ 确认 | [具体 threshold] | advance thesis / model |
| ⚠️ 含混 | [不够清晰] | 追加一轮 / cross-check |
| ❌ 减弱 | [反向 evidence] | lower conviction / revise |
| 💀 推翻 | [假设直接失效] | drop thesis |

**三角验证**：[同一个 claim 从哪 2-3 个不同 persona 或 public source 交叉验证]

## 4. 怎么问

### [Persona A]

必问（2-3 条）：
1. [open-ended, non-leading question]
2. [...]

红线：不能问 [non-public orders / customer names / pricing / contract terms / guidance / confidential pipeline]。需改写为 [public / historical / directional proxy]。

### [Persona B]

[同上]
```

### Mode A 篇幅：1000-1600 字

---

## Mode B: Expert Call Guide

用于单次 expert call。输出压缩为 600-1000 字——§1 一行 hypothesis + §2 一个 persona + §3 decision gate + §4 必问 3-5 条 + 红线。不写 triangulation。

## Mode C: Channel Check / Survey

用于客户/供应商/分销商批量验证。在 Mode A 基础上加 sample plan（目标 n≥10、persona split、地域 split）和 bias controls（不只看 happy customers / recent buyers）。篇幅 800-1400 字。

## Artifact / 保存策略

写入行业 topic：
    industry/<industry>/companies/<ticker>/YYYY-MM-DD-<artifact>.md

路径不明 → agent 按 policy baseline §11 自动创建。

## 反模式自查

- ❌ 问题清单很长但没有 hypothesis register——不知道每个问题验证什么。
- ❌ 没有 decision gate——看到什么结果都算 "interesting"。
- ❌ 只找一种 respondent，没有 triangulation。
- ❌ 问题是 leading question，诱导专家确认 thesis。
- ❌ 暗示去问 MNPI（订单、价格、客户名单、合同、guidance）。
- ❌ 把 planned call 写成 actual expert feedback。
- ❌ 用 small-N anecdote 直接推翻或确认 thesis。
- ❌ 选错 persona——问了 10 个 expert 但没人能回答核心假设。

## 篇幅基准

| Mode | 字数 |
|---|---|
| Standard | 1000-1600 |
| Expert Call | 600-1000 |
| Channel Check | 800-1400 |

低于下限通常漏了 hypothesis 或 decision gate；超过上限在写 execution handbook。
