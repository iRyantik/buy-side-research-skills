---
name: meta-skill
description: Use when creating, rewriting, reviewing, or validating buy-side-research-skills plugin skills, skill.yaml metadata, artifact policy, runtime category, validators, or skill governance.
---

# Meta Skill

`meta-skill` 是本插件唯一的 active skill-authoring guide。它维护 `research / operations` 双轨：research skill 保留严格投研结构，operations skill 使用更轻的执行结构。

写 / 改任何 active skill 时，以 root `CLAUDE.md` 为项目宪法，以本 skill 为 authoring guide。

## 心法

本 skill 的核心不是“把模板填满”，而是防止系统慢慢漂移：research skill 退化成 sell-side 流水账，operations skill 被硬套研究报告结构，metadata 和正文脱节，validator 只检查旧世界。

设计任何 skill 前，先问：它服务的到底是什么决策时刻？如果它改变研究判断，就是 `research`；如果它处理 workspace、文件、cache、session、路径、工具链或 skill authoring，就是 `operations`。分类错了，后面的结构、source discipline、保存策略和 validator 都会错。

好 skill 应降低研究员认知负担，而不是增加一套 AI 自嗨流程。用户是亚洲时区的 buy-side LS researcher，痛点是信息太多、单个公司时间被切碎、容易被噪音淹没。任何新 skill 都要说明它如何让研究更快、更准、更可沉淀。

## 职责边界

本 skill 负责：

- 设计、重写、审查 active skill 的 `SKILL.md` 和 `skill.yaml`。
- 判断 `category: research|operations`。
- 为 research skill 指定 `research_layer`：`triage`、`foundation`、`deep-work`、`memory`。
- 维护 artifact policy、version policy、validator 和 public docs 的一致性。
- 把研究 skill 写作纪律维护在 active runtime skill 中。

本 skill 不负责：

- 不写公司研究、thesis、driver-map、mechanism-map、Boss Brief 或 topic artifact。
- 不创建 topic session artifact。
- 不恢复 `meta.json` 双轨。
- 不恢复 v2 state files、portfolio tracker、decision-journal、thesis-tracker 或 v2 pair state logs。
- 不把 active skills 物理移动进嵌套目录；插件 runtime skills 保持 `skills/[skill-name]/SKILL.md` 一层平铺。

## 触发与输入

触发短语包括：

- “写一个新 skill”
- “改这个 skill”
- “重写 meta-skill”
- “skill 分类怎么做”
- “调整 validator”
- “新增 artifact policy”
- “把这个规则分给各 skill”
- “review 当前 skill governance”

执行前确认输入：

- 要创建或修改的 skill 名称。
- 该 skill 是 `research` 还是 `operations`。
- 如果是 research，属于 `triage`、`foundation`、`deep-work`、`memory` 哪一层。
- 是否需要新增脚本、assets、references；没有实际 runtime 需要就不要创建空目录。
- 是否会影响 public docs、manifest keywords、validator expected count、release package validator。
- 是否需要同步 `validate-skill-metadata.ps1`、`validate-skill-structure.ps1`、`validate-artifact-policy.ps1` 或专项 validator。

如果用户需求不清，先问清楚再写。不要凭想象 invent 一个 skill。

## 执行模式

### Mode A: New Skill Design

用于新增 active skill。必须先写清：

- 这个 skill 服务什么“决策时刻”或 operational job。
- `category` 和 `research_layer`。
- `artifact_policy`。
- runtime boundary：做什么、不做什么。
- 上游 / 下游 skill。
- 需要新增或更新哪些 validators。

### Mode B: Existing Skill Rewrite

用于重写或大改现有 skill。必须保护用户已有改动，不做无关重构；只改与本次目标相关的正文、metadata、validator 和 docs。若旧 skill 已经有清晰心法、source policy、反模式、保存策略，应继承而不是重写成另一套风格。

### Mode C: Governance / Validator Update

用于调整分类、版本策略、artifact policy、global rules 或 validator。必须同步 docs 和 release package validator，避免“规则写了但 CI 不管”。如果规则能被机械检查，优先写 validator；文档只负责解释判断型约束。

### Mode D: Review / Gap Audit

用于检查现有 skill 是否漂移。输出以问题和缺口为主，不要直接重写，除非用户明确要求实现。

## 工具资源

本 skill 无独立脚本依赖。修改本 repo 时优先读取：

- `CLAUDE.md`
- `README.md`
- `scripts/validate-*.ps1`
- 2-3 个相邻 reference skill 的 `SKILL.md` 和 `skill.yaml`

必读 reference skills：

| Skill | 学什么 |
|---|---|
| `information-impact` | 强纪律、500 字硬上限、双 mode、source 判断 |
| `candidate-screener` | AI 局限承认、反编造、Tier 分组、漏斗收口 |
| `stock-quickread` | 数据先行、反向工程、强制结构 |
| `peer-deep-dive` | 行业 lens、cross-cut insight、排序和资源分配 |
| `pair-trade` | LS / hedge / spread 方法论、hard standards、risk / sizing |

如果只是写作或审查 skill，不需要外部网络。只有当用户要求核对 Claude / Codex 插件官方结构时，才查官方文档。

## 文件安全

- 不新建 `meta.json`。
- 不移动 active skill 目录；保持 `skills/[skill-name]/SKILL.md`。
- 不修改 `AGENTS.md`、`.claude/`、`RTK.md` 或本地 planning 文件，除非用户明确点名。
- 不创建空的 `scripts/`、`assets/`、`references/` 目录。
- 不把 examples 当 runtime dependency。
- 不把 root `screens/`、`peers/`、`quickreads/`、`cross-market/` 恢复为 active artifact 默认路径。

## 运行输出契约

默认输出短而可执行：

```markdown
## Meta Skill Result

**结论先行**
[本次应该新增 / 修改什么，以及为什么]

## Required Edits
- [...]

## Validation
- [...]

## Open Risks
- [...]
```

如果用户要求实现，直接改文件并运行 validators。不要输出长篇设计散文代替执行。

如果只是 brainstorm / review，输出应优先列问题、tradeoff、推荐路径，不要提前写完整 `SKILL.md`。

## 失败处理

- 如果 category 不清，先说明两种可能后果；不能猜成 research。
- 如果 skill 会新增 active count，必须同步所有 count-based validators。
- 如果 operations skill 被要求套 research 模板，应改用 operations 结构。
- 如果用户要求恢复 v2 state workflow，必须暂停并说明这是架构回退。
- 如果 validator 和文档冲突，以 validator failure 为准，回头修 docs 或 validator。

## Workflow 联动

### 1. 用户上下文（必须内化）

- **身份**：Buy-side equity researcher，hedge fund / LS 长短策略研究语境。
- **坐标**：亚洲，时区影响美股 post-print 工作流。
- **覆盖市场**：大中华（A 股 + 港股 + 中概 ADR）+ 全球（美 / 日 / 韩 / 欧）。
- **覆盖行业**：industrials、aerospace and defense、advanced manufacturing、oil and gas、renewable energy、nuclear、emerging tech themes（AI 软件、AI 硬件、人形机器人、商业航天、quantum 等）。

LS 工作特征：

| 特征 | 设计含义 |
|---|---|
| 双向都看 | thesis-related research skill 默认双向考虑，不假设 long-only |
| Pair trade 是核心工具 | 触发 long X 思路时，自然带上 short Y 候选 / hedge 选项，必要时 handoff 到 `pair-trade` |
| Mechanism 拆解是复用原语 | 涉及行业机制、工程原理、设备链条、工艺流程、关键术语或 know-how gap 时，优先复用 `mechanism-map` |
| Driver 拆分是复用原语 | 涉及 revenue / margin / backlog / price-volume-mix driver 时，优先复用 `driver-map`，不要各 skill 重写一套拆分 |
| 跨市场惯性 | 同一公司多重上市、跨市场 peer 比较是常态 |
| 时区 disadvantage | 美股财报后才工作；post-print 工具必须高效 |
| 信息淹没 | 核心痛点是单股时间被切碎；skill 优先服务 noise reduction |

任何 skill 设计都要回答：这个 skill 是降低认知负担，还是增加？如果增加，要说明换来了什么不可替代的 value。

### 2. 当前系统设计哲学（v3 Journal-First）

不要重新设计 v2 已放弃的东西：

- 不恢复 state files for portfolio tracking，例如 `coverage/[ticker]/thesis.md`、`pairs/[X-Y]/`、`portfolio/catalyst-pipeline.md`。
- 不恢复 thesis-tracker、decision-journal、v2 pair state logs。
- 不恢复 ticker-centric 组织；研究围绕 topic 展开。

v3 的核心定位：

```text
Senior Analyst Radar -> Better AI Question -> Research -> Journal -> Boss Brief
```

AI 不是 status tracker，而是 senior analyst coach：帮研究员问更好的问题、沉淀已研究的认知增量、发现高价值疑点。

Topic-centric 组织：

```text
topics/
  [topic_type]/
    [topic-slug]/
      index.md
      [YYYY-MM-DD]-[session-slug]/
        research-journal.md
        boss-brief.md
```

### 3. Research / Operations 双轨结构

Top-level category 只允许：

- `research`
- `operations`

Research layers：

| Layer | Skills | 用途 |
|---|---|---|
| `triage` | `information-impact`, `candidate-screener`, `stock-quickread`, `next-step` | 过滤信息、找候选、快速判断、识别下一步最高杠杆问题 |
| `foundation` | `company-primer`, `mechanism-map`, `driver-map`, `cross-market-compare` | 打地基：公司基础、行业机制、model driver、跨市场比较 |
| `deep-work` | `peer-deep-dive`, `alpha-thesis`, `bear-pre-mortem`, `earnings-setup`, `pair-trade`, `financial-model` | 深度研究、thesis、财报、pair、建模 |
| `memory` | `research-journal` | 沉淀 earned insight 和 Boss Brief |

Operations skills：

| Skill | 用途 |
|---|---|
| `init` | 创建 / 修复 research workspace scaffold |
| `ingest` | 把 raw material 转成 source-tracked `_cache/` markdown |
| `meta-skill` | 创建 / 修改 / 审查本插件的 skills、metadata、validators 和 governance |
| `new-session` | 创建 / 定位 topic session、解析 artifact save path、轻量更新 topic `index.md` |

Active skills 必须保持一层平铺：`skills/[skill-name]/SKILL.md`。不要物理移动到 `skills/research/` 或 `skills/operations/`。

### 4. 写好 Research Skill 的 9 个核心原则

每个原则都是 hard rule，违反就重写。

1. **服务“决策时刻”，不是“输出文档”**：skill 应按研究员在哪个决策时刻调用来切，而不是按 memo / report 形式切。
2. **反流水账纪律**：禁止公司历史、管理层履历、通用 SWOT、行业科普、无数据定性、表格复述。
3. **数据先行 / 强制结构化**：判断必须有具体数字、表格或 source-backed evidence；表格必须有结构性 takeaway。
4. **Source 政策 hard enforcement**：事实、数字、引语必须有 source；绝对不能编 URL、页码、引语、数字、人名、日期。
5. **反模式自查必填**：每条反模式必须具体到可机械自检。
6. **篇幅基准明确**：写用户可见输出篇幅的下限 / 上限，以及超出时意味着什么。
7. **Hard Standards / Hard Cutoffs**：任何评级必须有 observable indicator，不允许凭感觉。
8. **Workflow 联动明确**：上游、下游、artifact 保存策略必须写清楚。
9. **心法节传递设计意图**：1-3 段说明真正解决什么、最容易失败在哪里。

### 5. Research SKILL.md 必填结构

复杂 research skill 推荐骨架：

1. Frontmatter（短 trigger-only description）
2. 开头定义本 skill 的失败标准
3. `心法`
4. `Global Rules Capsule`
5. `Source 政策`
6. `AI 的局限`
7. `触发场景`
8. `输入澄清要求`
9. `Mode A / Mode B / Mixed Mode`
10. `输出结构`
11. `Artifact / 保存策略`
12. `Workflow 联动`
13. `反模式自查`
14. `篇幅基准`
15. `与相邻 skill 的边界`

短 coach 型 research skill 的用户可见输出可以短，但 runtime 结构不能省：`心法`、`Source 政策`、`Workflow 联动`、`反模式自查`、`篇幅基准` 仍然必填。

Research frontmatter：

```yaml
---
name: skill-name
description: Use when [具体触发场景和用户症状].
---
```

Frontmatter 必须只写触发条件，不总结 workflow。

### 6. Operations SKILL.md 必填结构

Operations skill 使用轻量执行结构：

1. Frontmatter
2. `心法`
3. `职责边界`
4. `触发与输入`
5. `执行模式`
6. `工具资源`
7. `文件安全`
8. `运行输出契约`
9. `失败处理`
10. `Workflow 联动`
11. `安全自查`

Operations skill 不强制：

- 不强制 `Global Rules Capsule`。
- 不强制 `Source 政策`。
- 不强制 `反模式自查`；改用 `安全自查`。
- 不强制 `篇幅基准`；如果需要控制输出长度，在 `运行输出契约` 里轻量说明即可。
- 不设置 `research_layer`。

Operations skill 必须强调文件安全、幂等、fail honestly、不要越权写 research artifact。

### 7. Metadata（skill.yaml，必填）

每个 active skill 必须维护 `skill.yaml`。`skill.yaml` 是 metadata / index truth；`SKILL.md` 是 runtime truth。

必填字段：

```yaml
metadata_schema_version: 1
name: skill-name
id: skill-name
display_name: Skill Name
version: 1.0.0
system_generation: 3.5.0-dev
author: buy-side-research-system
namespace: research.equity
category: research
research_layer: triage
summary: ...
description: ...
trigger: ...
capabilities: ...
artifact_policy:
  save_policy: optional_topic_session
  default_artifact: skill-name.md
  canonical_location: topics/[topic_type]/[topic-slug]/[YYYY-MM-DD]-[session-slug]/skill-name.md
  save_trigger: save only when user asks
```

Rules：

- `category` 只能是 `research` 或 `operations`。
- Research skill 必须有合法 `research_layer`。
- Operations skill 不得有 `research_layer`。
- `meta.json` 已 retired；不要新建、恢复或维护。
- `version` 是单个 skill 自身 semver，不是系统代际。
- `system_generation` 记录该 skill 当前对齐的系统代际。

Artifact policy：

- `save_policy` 只能是 `none`、`optional_topic_session`、`default_topic_session`、`earned_memory`、`external_workbook`、`workspace_scaffold`、`cache_artifact`、`topic_session_scaffold`。
- 不落盘的 skill 写 `conversation-only`。
- Topic artifact 必须落在 `topics/[topic_type]/[topic-slug]/[YYYY-MM-DD]-[session-slug]/`。
- `research-journal` 只写 earned insight / Boss Brief / topic index update，不当作所有 skill 的普通保存目标。
- `init` 使用 `workspace_scaffold`，只创建 / 补齐 workspace。
- `ingest` 使用 `cache_artifact`，只写 `_cache/` operational markdown。
- `new-session` 使用 `topic_session_scaffold`，只创建 / 定位 topic session 和轻量更新 `index.md`，不写研究结论。

### 8. Source 政策（runtime shared rules 摘要）

Research skill 的通用 source / anti-hallucination 规则放在 `Global Rules Capsule (v1)`，`Source 政策` 节只写 skill-specific 增量。

必须有 source：

- 财务数字、估值、市场数据、价格、as-of 数据。
- KPI / 运营数据：产量、客户数、ARR、库存、orders、backlog 等。
- 行业数据：市占率、价格、产能、需求量、TAM。
- 管理层引语、专家访谈、监管表态、第三方判断。
- 历史事件和时间点。

Source 质量：

1. 一手原始：SEC filings、交易所公告、IR、监管 / 政府数据。
2. 二手权威：transcripts、Bloomberg / CapIQ / FactSet、行业研究机构、专家访谈平台。
3. 三手解读：Reuters、Bloomberg News、FT、WSJ、卖方研究。
4. 谨慎使用：推特 / 论坛 / 个人博客 / 公司新闻稿。

反幻觉硬规则：

- 绝对不能编造 URL、页码、引语、数字、人名、日期。
- 没找到具体 source 的事实，标 `[需查证]` 或 `[来源待补]`。
- 不确定 URL 是否存在时写 `[link 待补]`。
- Sub-agent 返回的 URL 视为 `[agent-provided, 未验证]`，关键 link 必须人工抽查。

### 9. 反模式 Catalog

通用反模式：

- 出现“成立于 / 总部位于 / 管理层经验丰富”。
- 5 年历史财务表罗列。
- 通用 SWOT。
- 行业入门 / 监管科普。
- “受益于 / 长期看好 / 看情况 / 有待观察”作为判断。
- 数据表无 takeaway / takeaway 复述表格。

Source 类反模式：

- 具体数字 / 引语无 source link。
- “据报道 / 有传言 / 有人说”当 source。
- 编造 URL。
- Sub-agent URL 直接当 verified。
- 多 source 冲突时挑一个用，不标注冲突。
- 引用 “10-K” 而不是 “10-K 2024 p.42”。

LS 视角缺失：

- Thesis 默认 long-only，不考虑 short / pair / hedge。
- Variant view 只 vs long consensus，不 vs short consensus。
- Pair trade 但 long thesis 和 short thesis 不能各自独立 sound。
- Short-only kill criteria 和 long 一样，没考虑 squeeze 风险。

数据空话：

- “估值偏贵 / 偏便宜”但不做反向工程。
- “Spread 偏离历史”但不给 z-score / percentile。
- 强度 = “High because 这是大新闻”。
- Catalyst 都是“长期”。
- Kill criteria = “如果错了就退”。
- Bear case 回报 -2%，bear 太弱。

AI 编造类：

- 编造业务关联，例如 “X 是 Y 供应商”但没有 source。
- 用已知市场概念股代替真实分析。
- Tier-2/3 关联只写“供应链相关”无具体 supplier link。
- 把卖方“概念股归类”当作业务关联依据。
- AI 推测 candidate 但不标 `[需查证]`。

Workflow 孤岛：

- 不声明 `artifact_policy`。
- 把 research material 直接写进 `research-journal`，跳过 Earned Insight Gate。
- 新产物继续默认写 root `screens/`、`peers/`、`quickreads/`、`cross-market/`。
- 没说明触发哪个下游 skill。
- Trigger keywords 和现有 skill 冲突。

### 10. 篇幅基准

Research SKILL.md 文件本身：

- 简单 skill：200-300 行。
- 标准 skill：300-450 行。
- 复杂 skill：300-500 行。
- 超过 600 行通常是 over-engineering，应拆开或精简。

Research 用户可见输出：

- Filter / Quick judgment skills：< 500 字硬上限。
- Single-stock research：1200-1800 字。
- Multi-stock research：N 线性 scale，1500-5000 字。
- Thesis building：800-1500 字。
- Coaching：< 300 字。

Operations 输出篇幅不强制使用研究篇幅基准；只需在 `运行输出契约` 中说明默认输出短而可执行。

### 11. 给 Agent 的 Final Workflow

按以下 5 步工作：

1. **理解需求**：用户要写什么 skill？解决什么决策时刻或 operational job？属于 v3 核心循环哪一步？
2. **阅读 reference**：必读 root `CLAUDE.md`、本 skill；至少读 2-3 个相邻 active skill。
3. **写 outline**：先写章节标题 + 每节 1-2 句要点；复杂新增 skill 先给 user review。
4. **填充内容**：重点打磨心法、反模式 / 安全自查、hard standards、artifact policy。
5. **自检 + flag**：按 checklist 自检，并主动指出最不确定的设计决策。

输出给 user 时：

```markdown
## [Skill Name] Result

**结论先行**
[完成了什么 / 建议什么]

## 关键设计决策
- [...]

## 验证
- [...]

## Open Risks
- [...]
```

### 12. 自检 Checklist

Research skill：

- Frontmatter name + trigger-only description。
- `skill.yaml` 有 `category: research` 和合法 `research_layer`。
- 心法 1-3 段。
- 包含当前版本 `Global Rules Capsule`。
- Source 政策只写 skill-specific 增量。
- 触发场景具体。
- 输出结构章节级 + 字段级。
- Artifact / 保存策略与 `skill.yaml` 一致。
- Workflow 联动表格。
- 反模式自查至少 10 条，且可机械自检。
- 篇幅基准明确。
- 在 v3 核心循环位置明确。
- 上下游 skills 明确。
- Trigger 不冲突。
- 例子符合 LS / 亚洲 / 工业 + AI，不用消费 / 医药例子。

Operations skill：

- Frontmatter name + trigger-only description。
- `skill.yaml` 有 `category: operations`，且没有 `research_layer`。
- 使用 operations 结构。
- 文件安全、幂等、fail honestly、边界清楚。
- Artifact policy 与正文一致。
- 不创建 research artifact，除非该 operations skill 的职责就是创建 scaffold / cache。
- 不强制 research capsule / Source 政策 / 篇幅基准。
- Validator、docs、manifest count 同步。

### 13. 不要做的事

- 不要让 research skill 只引用 `CLAUDE.md`；插件运行时可能不读 `CLAUDE.md`。
- 不要给 operations skill 硬加 research capsule、Source 政策或篇幅基准。
- 不要默认 long-only。
- 不要把 skill 设计成 sell-side report 模板。
- 不要 silently 做 assumption；不确定就 flag。
- 不要恢复 v2 state files、decision-journal、thesis-tracker、v2 pair state logs。
- 不要恢复 `meta.json`。
- 不要把 active skills 物理嵌套进分类目录。

## 安全自查

- ❌ 把 operations skill 写成 research report 模板。
- ❌ 给 operations skill 强制 `篇幅基准`、Senior Analyst Radar 或 primitive routing。
- ❌ 忘记更新 `skill.yaml`，只改 `SKILL.md`。
- ❌ 忘记更新 validators，导致规则只存在于文档里。
- ❌ 新增 active skill 但 active count 仍是旧值。
- ❌ 新增 skill 后没加入 README / CLAUDE / manifests。
- ❌ 恢复 `meta.json`。
- ❌ 把 active skills 物理嵌套进分类目录。
- ❌ 把 `research-journal` 当作所有 skill 的普通保存目标。
- ❌ 把 `_cache/` 当作 earned memory 或 original source。

## 文档版本

- **版本**：v1.1
- **基于**：buy-side-research-skills v3.5.0-dev
- **最后更新**：2026-05-10
- **维护者**：用户（user）
