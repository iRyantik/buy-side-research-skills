# FRAMEWORK.md — Journal-First Buy-Side Research Skills v3.3

> `CLAUDE.md` 是唯一 constitution。本文件是系统设计蓝图，不覆盖 `CLAUDE.md`。

## 1. System Thesis

v3 的价值不是“多写几个文件”，而是投研 value add：像 senior analyst 一样发现高价值研究问题，指导用户下一步怎么挖，并把真正想清楚的认知增量沉淀下来。

核心链路：

```text
Research Edge -> Better AI Question -> Research -> Journal -> Boss Brief
```

## 2. Package Model

This repository is a plugin development repo, not the research workspace itself.

```text
buy-side-research-skills/          # plugin dev repo
release-package/                   # zip or marketplace payload
Research-AI-Power/                 # user workspace created later by init
```

Plugin runtime skills live in `skills/`. Example research artifacts live under `examples/` and must not become runtime dependencies.

## 3. Active Skills

| Module | Skills |
|---|---|
| Signal / Funnel | `information-impact`, `candidate-screener`, `stock-quickread` |
| Company Foundation | `company-primer` |
| Research Primitives | `mechanism-map`, `driver-map`, `cross-market-compare`, `next-step` |
| Deep Research | `peer-deep-dive`, `alpha-thesis`, `bear-pre-mortem`, `earnings-setup`, `pair-trade`, `financial-model` |
| Synthesis / Memory | `research-journal` |

The v2 state workflow has been archived outside active `skills/`.

## 4. Senior Analyst Radar

Global rule lives in `CLAUDE.md`; reusable runtime prompt patterns should live in the user workspace at `topics/_meta/edge-radar.md`. The compact example copy lives under `examples/workspaces/ai-data-center-power/`.

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

## 5. Skill Contracts

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

### `company-primer`

Company foundation skill for mapping what a company sells, who pays, how the business evolved, and how segment / KPI disclosure changed over time. It does not do quick triage, driver modeling, valuation, peer ranking, or thesis writing.

It should feed `driver-map` when disclosure evolution blocks revenue, margin, backlog, price / volume / mix, or model-driver interpretation. It should feed `mechanism-map` when product, equipment-chain, process, or know-how understanding is still missing.

### `driver-map`

Research primitive for mapping `Reported Bucket -> Business Reality -> Model Driver`. It handles revenue, margin, backlog, price / volume / mix, weird segment buckets, and model-driver gaps. It does not do DCF/comps, create workbooks, or write full thesis.

Downstream skills consume it:
- `financial-model` turns driver-map into operating model, DCF, comps, reverse DCF, and update maps.
- `alpha-thesis` uses it to anchor variant view, scenario, and kill criteria.
- `peer-deep-dive` uses it to normalize KPI and business reality across peers.
- `pair-trade` uses it to test whether long / short legs share or diverge on real drivers.

### `mechanism-map`

Research primitive for mapping industry mechanisms, engineering principles, equipment chains, process flows, technical terms, and know-how gaps to investment research implications. It explains how something works, where value is captured, and what not to infer.

It does not do DCF/comps, create workbooks, or write full thesis. When mechanism understanding affects revenue, margin, backlog, price / volume / mix, it should feed `driver-map`; when it affects operating model or valuation, it should feed `financial-model`.

### `pair-trade`

Journal-first pair research tool. It keeps the full builder / monitor methodology from the original pair workflow: independent long and short theses, spread history, beta / correlation, sizing, risk matrix, and P/L attribution. It does not maintain trade state, append logs, or depend on the archived v2 workflow.

## 6. File Model

Plugin dev repo:

```text
.claude-plugin/
.codex-plugin/
skills/
scripts/
docs/
examples/
archive/
```

Future research workspace:

```text
_inbox/
_raw/
_cache/
_models/
topics/
  _meta/
    edge-radar.md
  [topic_type]/
    [topic-slug]/
      index.md
      [YYYY-MM-DD]-[session-slug]/
        company-primer.md
        mechanism-map.md
        driver-map.md
        research-journal.md
        boss-brief.md
```

No topic-level edge signal file. No standalone next-step file. A weird signal enters the journal only after it has been researched.

## 6.1 Artifact Save Policy

New research artifacts use topic-session storage by default:

```text
topics/[topic_type]/[topic-slug]/[YYYY-MM-DD]-[session-slug]/[artifact].md
```

Legacy root artifact directories such as `screens/`, `peers/`, `quickreads/`, and `cross-market/` may appear in examples or archived material, but active skills should not use them as default save targets.

Policy classes:
- `none`: conversation-only; no standalone files.
- `optional_topic_session`: save to current topic session only when user asks.
- `default_topic_session`: save to current topic session by default; ask for path confirmation if session is unclear.
- `earned_memory`: write only researched insight that passes the journal gate.
- `external_workbook`: write to user-provided workbook or workspace `_models/`, not a topic markdown artifact.

## 7. BKR IET Behavior Test

When encountering `GTE / GTS / Industrial Products / Industrial Solutions / CTS`, the system should not summarize and move on. It should point out that this may reflect gas turbine system economics, turbine body, adjacent equipment, service, controls, or value-chain layers.

Expected behavior:
- route the mechanism / equipment-chain question through `mechanism-map` when needed
- directly say this is worth digging
- offer 1-2 strong AI questions
- do not create a state file
- let journal capture the insight only after the user actually researches it

## 8. Validation

Required checks:
- active `skills/` count is 15
- active docs and metadata list the same 15 skills
- archived v2 state skills are outside active `skills/`
- example workspaces live under `examples/`, not at repo root
- `Senior Analyst Radar`, `edge-radar.md`, `boss-brief`, `next-step`, `company-primer`, `mechanism-map`, and `driver-map` appear in public docs

**版本**：v3.3.0
**最后更新**：2026-05-10
