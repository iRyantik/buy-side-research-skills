---
name: meta-skill
description: Create review or update buy-side research skills metadata docs manifests and governance.
---

# Meta Skill

Agent and plugin runtime upgrades belong to `update-agent-runtime`; `init-workspace` remains responsible for workspace scaffold and repair only.

`meta-skill` 是本插件唯一的 active skill-authoring guide。它维护 `research / operations` 双轨：research skill 保留严格投研结构，operations skill 使用更轻的执行结构。

写 / 改任何 active skill 时，以 root `CLAUDE.md` 为项目宪法，以本 skill 为 authoring guide。

## 心法

本 skill 的核心不是“把模板填满”，而是防止系统慢慢漂移：research skill 退化成 sell-side 流水账，operations skill 被硬套研究报告结构，metadata、正文、docs 和 manifests 脱节。

设计任何 skill 前，先问：它服务的到底是什么决策时刻？如果它改变研究判断，就是 `research`；如果它处理 workspace、文件、cache、session、路径、工具链或 skill authoring，就是 `operations`。分类错了，后面的结构、source discipline、保存策略和 docs / manifests 都会错。

好 skill 应降低研究员认知负担，而不是增加一套 AI 自嗨流程。用户是亚洲时区的 buy-side LS researcher，痛点是信息太多、单个公司时间被切碎、容易被噪音淹没。任何新 skill 都要说明它如何让研究更快、更准、更可沉淀。

## 职责边界

本 skill 负责：

- 设计、重写、审查 active skill 的 `SKILL.md` 和 `skill.yaml`。
- 判断 `category: research|operations`。
- 为 research skill 指定 `research_layer`：`triage`、`foundation`、`deep-work`、`memory`、`supporting`。
- 维护 artifact policy、version policy、public docs 和 manifests 的一致性。
- 把研究 skill 写作纪律维护在 active runtime skill 中。
- 维护 authority hierarchy、hard gate 和 UTF-8 文本纪律。

本 skill 不负责：

- 不写公司研究、thesis、driver-map、mechanism-insight、Boss Brief 或 topic artifact。
- 不创建 dated topic research artifact。
- 不恢复 `meta.json` 双轨。
- 不恢复 v2 state files、portfolio tracker、decision-journal、thesis-tracker 或 v2 pair state logs。
- 不把 active skills 物理移动进分类嵌套目录；插件 runtime skills 在 payload root 下保持 `plugins/buy-side-research-skills/skills/[skill-name]/SKILL.md` 一层平铺。

## 触发与输入

触发短语包括：

- “写一个新 skill”
- “改这个 skill”
- “重写 meta-skill”
- “skill 分类怎么做”
- “调整 governance”
- “新增 artifact policy”
- “把这个规则分给各 skill”
- “review 当前 skill governance”

执行前确认输入：

- 要创建或修改的 skill 名称。
- 该 skill 是 `research` 还是 `operations`。
- 如果是 research，属于 `triage`、`foundation`、`deep-work`、`memory` 哪一层。
- 是否需要新增脚本、assets、references；没有实际 runtime 需要就不要创建空目录。
- 是否会影响 public docs、manifest keywords 或 release package shape。
- 是否需要同步 README、docs、payload manifests 或 root marketplace metadata。

如果用户需求不清，先问清楚再写。不要凭想象 invent 一个 skill。

## 执行模式

### Mode A: New Skill Design

用于新增 active skill。必须先写清：

- 这个 skill 服务什么“决策时刻”或 operational job。
- `category` 和 `research_layer`。
- `artifact_policy`。
- runtime boundary：做什么、不做什么。
- 上游 / 下游 skill。
- 需要新增或更新哪些 docs / manifests。

### Mode B: Existing Skill Rewrite

用于重写或大改现有 skill。必须保护用户已有改动，不做无关重构；只改与本次目标相关的正文、metadata、docs 和 manifests。若旧 skill 已经有清晰心法、source policy、反模式、保存策略，应继承而不是重写成另一套风格。

### Mode C: Governance Update

用于调整分类、版本策略、artifact policy、global rules、docs 或 manifests。必须同步 public docs、payload manifests 和 root marketplace metadata，避免“规则写了但安装入口没更新”。

Modeling skills (`3-statement-model`, `dcf-model`, `comps-analysis`, `model-update`) use `Model Sub-Agent Protocol`. Do not add them to `Parallel Evidence Pass`, and do not give them `evidence_cards_only`.

### Mode D: Review / Gap Audit

用于检查现有 skill 是否漂移。输出以问题和缺口为主，不要直接重写，除非用户明确要求实现。

## Authority Hierarchy

规则冲突时按以下顺序判断：

1. plugin dev repo root `CLAUDE.md`
   - plugin 开发宪法
2. `init-workspace/assets/CLAUDE.md.template`
   - workspace 高层宪法模板
3. invoked `SKILL.md`
   - runtime executable contract
4. `references/policy/research-policy-baseline.md`
   - authoring baseline only，not runtime authority

runtime 行为上，如果 template 的高层摘要与某个 research skill 的具体执行细则看起来不一致：

- **research `SKILL.md` wins**

## Capsule Policy

### Research skills

Capsule 只做一件事：**强制 agent 在执行前读取共享文件**。所有运行时规则在 `_shared/research-runtime.md` 和 hooks 中，不在 capsule 中重复。

Capsule 格式（不可变）：
- MUST-read 指令 + `_shared/research-runtime.md` § anchor
- Hook 防御清单（一行）

禁止在 capsule 中写：
- Tier 回退链、provider 名、trust chain
- `financial-data --lite` 调用方法
- subagent evidence card 协议
- 任何已在 `_shared/` 或 hooks 中的规则

### Modeling skills

`3-statement-model`、`dcf-model`、`comps-analysis`、`model-update` 使用 separate modeling capsule，不吃 research capsule。

### Supporting visualization skills

`research-viz` 这类 supporting visualization skill 仍属于 research 轨，但不进入主研究 ladder。它们可以生成 topic-side HTML artifact，必须绑定一个基准 markdown 研究产物，默认复用基准 stem，只替换扩展名为 `.html`；如需多图，可在 stem 后追加最小 qualifier。

### EN-CN Sync Policy

每个 skill 的 `SKILL.md`（中文）是 source of truth。`SKILL.en.md` 必须保持同步：

- **Capsule**：必须完全一致（除了语言）。
- **输出结构**：围栏 ` ```markdown ` 骨架必须完全一致。
- **必填 section**：`心法`、`反模式自查`、`篇幅基准`、`Artifact/保存策略` 必须在 EN 中存在。
- **允许差异**：反模式自查的具体条目数可不同（CN ≥10 条，EN 可按需调整）。
- **检查方式**：写/改 CN 后立即改 EN，不同步不合并。

### Operations skills

operations skills 不嵌 research capsule。

## Hooks-First Runtime Law

跨宿主 deterministic runtime law 优先落到 workspace hooks，而不是继续堆进 skill prose。正式加载面是：

- workspace `.claude/settings.json`
- workspace `.claude/hooks/`
- workspace `.codex/hooks.json`

plugin dev repo 中的 hook 配置与脚本通过 `init-workspace` 交付到 workspace；plugin-local docs 不是宿主自动 hook discovery surface。

hook 只负责 binary / machine-checkable guardrails，例如 source legality、subagent boundary、workspace path safety、明显 narrative drift。判断密度高、依赖研究品味或需要主观裁判的规则，继续留在 `SKILL.md`、`skill.yaml` 与 authoring governance 中。

`information-impact` 的 claim qualification 与 `primary-research-plan` 的 compliance floor 也属于 hook-first binary rules。
`reddit-sentiment` 的 social clue-only boundary 也属于 hook-first binary rules。
`peer-deep-dive` 的 cross-market parity（上市身份 / 货币 / as-of）由 skill 自身的 §4.1 列定义强制（≥2 市场时必填 5 cross-market 列），不另设 hook。
modeling workbook artifacts 在范围内时，`3-statement-model`、`dcf-model`、`comps-analysis`、`model-update` 的 statement presence、balance integrity、formula discipline、missing-actuals floor、valuation-basis floor、actuals_cross_check、driver_cross_check、internal_consistency、dcf_linked_to_3sm、dcf_input_sourcing、comps_sourced、meta_sheet 也属于 xlsx-aware hook-first binary rules。
`research-journal` 的 earned-insight gate 与 topic index map-only boundary 也属于 hook-first binary rules。
`research-viz` 的 stem-binding、self-contained delivery 和 source-line contract 也属于 hook-first binary rules。
定量事实治理层（`fact_provenance`：Tier 0-3 验证，`claim_source_proximity`：强声明必有 source 锚点）也属于 hook-first binary rules。

如 hook 与 prose 在 binary legality 上冲突，以 hook enforcement 为准。`research-policy-baseline.md` 继续只是 authoring baseline，不是 runtime authority。

## Hard Gate

任何公共 research 规则变更，必须在同一个 change 里同步：

1. `references/policy/research-policy-baseline.md`
2. 所有受影响的 active research `SKILL.md`
3. 如影响 workspace 高层摘要，再改 `CLAUDE.md.template`
4. 如影响 public behavior / package language，再改 `README.md`、`docs/release.md`、payload manifests / marketplace manifests

不允许只改 baseline / template 而不改 skills 就合并或发版。

hooks-first 补充 hard gate：

5. 新的 deterministic runtime rule，如能脚本化，优先进 workspace hooks，而不是继续堆进 `SKILL.md` prose。
6. 规则一旦 hook 化，对应 `SKILL.md` 中的同类 binary rule prose 必须在同一个 change 删除。
7. hooks 共享脚本与宿主 adapter 必须同步维护；不允许只改 Claude 或只改 Codex 一侧配置。
8. hooks 的正式交付面是 `init-workspace` scaffold；不允许把 plugin dev repo 局部文件误当成宿主自动加载面。
9. skill-specific hook 新增后，review 仍保留旧 prose 的，视为治理失败。
10. 新增 runtime hook / repair script / install command 时，禁止再硬编码 `powershell ... .ps1`；必须走跨平台 launcher，或明确给出 Windows `powershell` 与 macOS `pwsh` 双写命令。

命名规则补充 hard gate：

9. 如变更 research topic artifact 命名规则，必须同步 `references/policy/research-policy-baseline.md` §11。
10. 每个会落 topic markdown 的 research skill 必须在 `skill.yaml` 的 `artifact_policy` 下声明 `naming_mode`。
11. 不允许只改某个 skill 的 prose / examples，而不改 `skill.yaml`。
12. supporting visualization skill 若生成 topic-side HTML artifact，必须把 stem-binding save contract 写进 `skill.yaml` 与 `SKILL.md`，不要另造一套平行 dated naming 体系。

## UTF-8 文本纪律

中文或多语言文本资产统一使用 **UTF-8 无 BOM**。

- `.md` / `.yaml` / `.json` 默认按 UTF-8 无 BOM 维护。
- 修改中文文件时必须显式使用 UTF-8 写回。
- 批量脚本改写文本时必须指定 UTF-8，避免 mojibake。
- 不对 `SKILL.md` 做整文件重排或批量格式化；frontmatter、顶层 `# H1`、空行结构和 parser-sensitive 顺序只做本次字段所需的最小编辑。
- JSON 只做键值级最小编辑，不重排整个对象；YAML 保持现有缩进和引号风格，不为美化做全量重写。

## 工具资源

本 skill 无独立脚本依赖。修改本 repo 时优先读取：

- `CLAUDE.md`
- `README.md`
- `docs/`
- root `.claude-plugin/marketplace.json`
- 2-3 个相邻 reference skill 的 `SKILL.md` 和 `skill.yaml`

必读 reference skills：

| Skill | 学什么 |
|---|---|
| `information-impact` | 强纪律、500 字硬上限、双 mode、source 判断 |
| `candidate-screener` | AI 局限承认、反编造、Tier 分组、漏斗收口 |
| `industry-landscape` | 行业 first-pass、value pool、KPI/source map、routing 边界 |
| `consensus-map` | sell-side consensus、buy-side bar、priced-in assumptions、variant-view gap |
| `primary-research-plan` | 合规 primary research、expert call、channel check、survey、decision gates |
| `stock-quickread` | 数据先行、反向工程、强制结构 |
| `peer-deep-dive` | 行业 lens、cross-cut insight、排序和资源分配 |
| `pair-trade` | LS / hedge / spread 方法论、hard standards、risk / sizing |

如果只是写作或审查 skill，不需要外部网络。只有当用户要求核对 Claude / Codex 插件官方结构时，才查官方文档。

## 文件安全

- 不新建 `meta.json`。
- 不移动 active skill 目录；保持 `plugins/buy-side-research-skills/skills/[skill-name]/SKILL.md`。
- 不修改 `AGENTS.md`、`.claude/`、`RTK.md` 或本地 planning 文件，除非用户明确点名。
- 不创建空的 `scripts/`、`assets/`、`references/` 目录。
- 不把 examples 当 runtime dependency。
- 不把 root `screens/`、`peers/`、`quickreads/`、`cross-market/` 恢复为 active artifact 默认路径。

## Skill Directory Spec

每个 skill 目录下允许以下子目录。这是收口——新 skill 只能创建这里列出的目录，init-workspace 和 update-agent-runtime 的 auto-discovery 也只处理这些。

### 目录定义

| 目录 | 职责 | 部署行为 | 策略 |
|---|---|---|---|
| `scripts/` | 可执行代码（.py, .js） | `_scripts/<skill>/` | 覆盖 |
| `assets/` | 数据文件、配置、requirements、模板 | `_scripts/<skill>/` | 覆盖 |
| `assets/templates/` | 用户可改的模板文件 | `_scripts/<skill>/` | 缺时补 |
| `references/` | 该 skill 自己的参考文档 | **不部署** — agent 直接从 plugin cache 读取 | — |
| `examples/` | 示例产物、示例 HTML | **不部署** — agent 直接从 plugin cache 读取 | — |
| `.platform` | 空标记文件。有此文件 → skill 是平台级（init-workspace, update-agent-runtime），资产走 A类部署到 workspace root，不参与 B类 auto-discovery | — | — |

### 规则

1. **不部署 ≠ 不重要** — `references/` 和 `examples/` 是该 skill 的 canonical 参考和示例，agent 执行 skill 时能直接从 plugin cache 读。不能因为不落地 workspace 就删。
2. **没有 runtime 需求不创建空目录** — 如果 skill 不需要脚本或 assets，就不建 `scripts/` / `assets/`。
3. **不要在此清单外新增目录** — 如果有新需求，先来改这个 spec，再建目录。
4. **B类 auto-discovery** — init-workspace 和 update-agent-runtime 的 B类规则就是遍历 `skills/*/scripts/` + `skills/*/assets/`。加新文件到这些目录 → 自动部署，零改动。

### Deployment 矩阵总览

```
skills/<skill>/scripts/          →  _scripts/<skill>/          覆盖
skills/<skill>/assets/           →  _scripts/<skill>/          覆盖
skills/<skill>/assets/templates/ →  _scripts/<skill>/          缺时补
skills/<skill>/references/       →  (不部署，agent 读 cache)
skills/<skill>/examples/         →  (不部署，agent 读 cache)
skills/<skill>/.platform         →  A类，部署到 workspace root
```

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

如果用户要求实现，直接改文件。root `scripts/` 开发校验层已删除；不要引用或恢复旧 validator / build-release 入口，除非用户另行要求重新设计工具链。不要输出长篇设计散文代替执行。

如果只是 brainstorm / review，输出应优先列问题、tradeoff、推荐路径，不要提前写完整 `SKILL.md`。

## 失败处理

- 如果 category 不清，先说明两种可能后果；不能猜成 research。
- 如果 skill 会新增 active count，必须同步 README / CLAUDE / docs / manifests 中的 skill 列表和路径说明。
- 如果 operations skill 被要求套 research 模板，应改用 operations 结构。
- 如果用户要求恢复 v2 state workflow，必须暂停并说明这是架构回退。
- 如果旧文档和当前 payload 结构冲突，以 root `CLAUDE.md` 和 `plugins/buy-side-research-skills/` 当前结构为准；不要为了兼容旧流程恢复已删除的 root `scripts/` 或 root `skills/`。

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
| Mechanism 拆解是复用原语 | 涉及行业机制、工程原理、设备链条、工艺流程、关键术语或 know-how gap 时，优先复用 `mechanism-insight` |
| Driver 拆分是复用原语 | 涉及公司 / segment / 产品线 / 披露 bucket 的 revenue / margin / backlog / price-volume-mix driver 时，优先复用 `driver-map`，不要各 skill 重写一套拆分；泛行业 first-pass 用 `industry-landscape`，机制不清用 `mechanism-insight` |
| 市场空间测算 | TAM/SAM/SOM 估算和 scenario sizing 优先复用 `market-sizing` → `scenario-model`，不要在 thesis 里临时拍数 |
| 竞争壁垒 / 管理层 / 催化剂 | 深挖前先复用到 `moat-analysis`、`capital-allocation`、`catalyst-map`，不靠 stock-quickread 拼凑 |
| 财报后快速判断 | post-print verdict 用 `post-earnings-quick`，读最近的 `earnings-setup` bar 做基准对比 |
| 覆盖跟踪 | 已覆盖公司状态更新和优先级重排用 `coverage-tracker`，与 `research-journal` 分工：前者管状态，后者管认知 |
| Consensus framing 是 foundation 原语 | 涉及 sell-side consensus、buy-side bar、priced-in assumptions、market-implied expectations 或 variant-view gap 时，优先复用 `consensus-map`，不要在 thesis 或 quickread 里临时重写 |
| Primary evidence 需要合规计划 | 涉及 expert call、customer / supplier channel check、survey、fieldwork 或 ex-employee interview 验证关键假设时，优先复用 `primary-research-plan`，不要生成假访谈结果 |
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
industry/
  [topic-namespace]/[topic-slug]/
    index.md
    [YYYY-MM-DD]-research-journal.md
    [YYYY-MM-DD]-boss-brief.md
```

### 3. Research / Operations 双轨结构

Top-level category 只允许：

- `research`
- `operations`

Research layers：

| Layer | Skills | 用途 |
|---|---|---|
| `triage` | `information-impact`, `stock-quickread`, `post-earnings-quick`, `reddit-sentiment`, `next-step` | 过滤信息、快速判断、财报后快速反应、social sentiment、识别下一步最高杠杆问题 |
| `foundation` | `teach-in`, `industry-landscape`, `financial-data`, `market-sizing`, `company-history`, `consensus-map`, `mechanism-insight`, `driver-map` | 打地基：零基础物理直觉、行业全景、结构化财务+市场数据、TAM 估算、公司业务/披露历史、市场预期、行业机制、model driver |
| `deep-work` | `candidate-screener`, `peer-deep-dive`, `moat-analysis`, `catalyst-map`, `capital-allocation`, `alpha-thesis`, `bear-pre-mortem`, `earnings-setup`, `pair-trade`, `primary-research-plan`, `scenario-model`, `3-statement-model`, `dcf-model`, `comps-analysis`, `model-update` | 深度研究：分场景 L/S 排序、横向比较（同市场/跨市场）、竞争壁垒、催化剂链、管理层资本配置、thesis、赔率 memo、建模 |
| `supporting` | `research-viz` | 可视化后处理 |
| `memory` | `research-journal`, `coverage-tracker` | 沉淀 earned insight、跟踪已覆盖公司状态和优先级 |

Operations skills：

| Skill | 用途 |
|---|---|
| `init-workspace` | 创建 / 修复 research workspace scaffold |
| `ingest` | 把 raw material 转成 source-tracked `_cache/` markdown |
| `meta-skill` | 创建 / 修改 / 审查本插件的 skills、metadata、docs、manifests 和 governance |

Active skills 必须在 payload root 下保持一层平铺：`plugins/buy-side-research-skills/skills/[skill-name]/SKILL.md`。不要物理移动到 `skills/research/` 或 `skills/operations/`。

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

所有 research skill 统一使用以下 section 顺序。标 `[必填]` 的不可省略，标 `[可选]` 的按需加。

```
1. Frontmatter（短 trigger-only description，≤140 字符）[必填]
2. # 标题 [必填]
3. Research Runtime Capsule [必填] — 强制读 _shared/ 格式（见 §5.1）
4. 心法 [必填] — 1-3 段，解决什么、最容易失败在哪
5. 触发场景 [必填]
6. 输入澄清要求 [可选] — 有复杂输入时加
7. 执行模式（Mode A/B/C）[可选] — 多模式 skill 加
8. 输出结构 [必填] — 含围栏 ```markdown artifact 骨架 + Source contract
9. Artifact / 保存策略 [必填]
10. 与相邻 skill 的边界 [必填] — 本 skill 和相似 skill 的区别
11. 反模式自查 [必填] — ≥10 条，每条可机械自检
12. 篇幅基准 [必填] — 下限/上限，超出意味着什么
```

已删除的段：
- `Global Rules Capsule` — 不再需要。全局纪律在 `_shared/research-runtime.md` §2.2 和 hooks。
- `Source 政策` / `Source Contract` 独立 section — 并入输出结构 blockquote（一句话）。
- `资料收集与 Source 验证` 独立 section — 并入 `_shared/research-runtime.md` §2。skill 只保留特有执行流程。

Research frontmatter：

```yaml
---
name: skill-name
description: Use when [具体触发场景和用户症状].
---
```

Frontmatter 必须只写短单行 UI 摘要，不总结 workflow；`description` 必须是纯文本单行，建议少于 140 个字符，不使用 `|` / `>` block scalar、Markdown、列表或长触发规则。

为了避免 skill card description 再次空白，active `SKILL.md` 除了正确 frontmatter 外，还必须保留一个顶层 `# ...` 标题；不要让 frontmatter 后直接进入 `## Research Runtime Capsule` 或 `## Modeling Runtime Capsule`。

#### §5.1 Research Runtime Capsule 标准模板

所有 research skill 必须使用以下强制读格式。核心 3 行不可变：

```markdown
## Research Runtime Capsule

**执行本 skill 前必须先读取以下文件：**
- `_shared/research-runtime.md` §1（数据获取链）§2（来源验证链）§2.1（资料收集）§2.2（Source 纪律）§2.5（图片下载链）§4（产出合约）§5（保存合约）

**自动 Hook 防御：** `pre_write_gate`（source/tables/mermaid/image）`source_contract` `table_render_integrity` `mermaid_syntax` `skill_structure_contract` `evidence_ledger_floor`
```

**规则**：
- 核心 3 行不可变。§ anchor 根据 skill 需要调整（如不用图片的 skill 可去掉 §2.5）。
- 禁止在此段复述 Tier 链、provider 名、trust chain、subagent 流程。
- 禁止写 `数据管道：调用 /financial-data --lite`——已在 `_shared/` §1。
- 禁止写 `Sub-agent outputs: evidence_cards_only`——已在 `_shared/` §3。
- skill-specific 定制放在 `心法` 或 `执行模式` 段，不放在 Capsule。

#### §5.2 Modeling Runtime Capsule 标准模板

建模 skill 使用以下模板。核心 4 行不可变，skill-specific 定制最多 2 行。

```markdown
## Modeling Runtime Capsule

- Hook-enforced modeling rules (missing_actuals_not_zero, balance_integrity, structure_floor, etc.) live in workspace hooks.
- Shared modeling protocol: `references/policy/research-policy-baseline.md` §6.
- **数据源**：从 `actuals-resolved.json` 取 historical actuals，从 `_cache/driver-map/` 取 driver assumptions。缺失 actuals 不填零。
- Sub-agent QA bounded; main agent owns the final workbook.

[如有 skill-specific 建模规则，≤2 行]
```

**建模 capsule 自检**：
- [ ] Capsule 是否 ≤ 6 行？
- [ ] 是否删除了 Research Workspace Adapter 段（缓存路径列表）？
- [ ] 是否删除了 Model Sub-Agent Protocol 段（已在 shared baseline §6）？
- [ ] 是否删除了 consumer trust contract？
- [ ] 是否有重复 hook 的内容（missing_actuals_not_zero 等）？

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
system_generation: 3.10.0
author: buy-side-research-system
namespace: research.equity
category: research
research_layer: triage
summary: ...
description: ...
trigger: ...
capabilities: ...
artifact_policy:
  save_policy: optional_topic_result
  default_artifact: skill-name.md
  canonical_location: industry/<industry>/companies/<ticker>/[YYYY-MM-DD]-skill-name.md
  naming_mode: plain
  save_trigger: save only when user asks
```

Rules：

- `category` 只能是 `research` 或 `operations`。
- Research skill 必须有合法 `research_layer`。
- Operations skill 不得有 `research_layer`。
- `meta.json` 已 retired；不要新建、恢复或维护。
- `version` 是单个 skill 自身 semver，不是系统代际。
- `system_generation` 记录该 skill 当前对齐的系统代际。
- `SKILL.md` frontmatter 后第一个非空正文标题必须是顶层 `# ...`，再进入 capsule 或其它二级标题。

Artifact policy：

- `save_policy` 只能是 `none`、`optional_topic_result`、`default_topic_result`、`earned_memory`、`external_workbook`、`workspace_scaffold`、`cache_artifact`、`topic_scaffold`。
- 不落盘的 skill 写 `conversation-only`。
- Topic artifact 必须落在 `industry/<industry>/companies/<ticker>/[YYYY-MM-DD]-[artifact].md`。
- 只有会落 topic markdown 的 research skill 才声明 `artifact_policy.naming_mode`；可选值只允许 `plain`、`optional_qualifier`、`required_qualifier`。
- `none`、`external_workbook`、`cache_artifact`、`workspace_scaffold`、`topic_scaffold` 不声明 `naming_mode`。
- `research-journal` 只写 earned insight / Boss Brief / topic index update，不当作所有 skill 的普通保存目标。
- `init-workspace` 使用 `workspace_scaffold`，只创建 / 补齐 workspace。
- `ingest` 使用 `cache_artifact`，只写 `_cache/` operational markdown。

默认 naming tier：
- `plain`：`stock-quickread`、`company-history`、`alpha-thesis`、`bear-pre-mortem`、`earnings-setup`、`pair-trade`、`research-journal`、`moat-analysis`、`catalyst-map`、`capital-allocation`、`post-earnings-quick`
- `optional_qualifier`：`consensus-map`、`industry-landscape`、`peer-deep-dive`、`candidate-screener`、`primary-research-plan`、`scenario-model`、`market-sizing`
- `required_qualifier`：`mechanism-insight`、`teach-in`、`reddit-sentiment`

### 8. Shared Runtime / Source Baseline

Research skill 的通用 source / anti-hallucination 规则现在由 shared baseline + workspace hooks 承接，不再要求每个 skill 本地复制 `Source 政策`。

authoring hard rules：
- research skill 必须默认依赖 shared source hierarchy：披露事实轨 `topic-local evidence cache > primary public > trusted third-party > web`；市场快照轨统一由 `/financial-data --lite` 的 trust-based fill 链（Bridge → yfinance → WebSearch → Google Finance）获取，不再各自调 `trusted-market-bridge`。
- 示例必须展示正文短锚点与文末 `## Resources` 双写同 target；不允许再写 `S1` / `I1` 等短锚点代码后接 `(link)` 或 `(url)` 占位符——此类写法会被 source_contract hook 拦截。
- 一旦某条 binary source / structure / boundary 规则进入 hook，对应 `SKILL.md` 中同类规则 prose 必须删除，而不是继续双份保留。
- `Source 政策` 若保留，只能写 skill-specific non-binary edge；不能复述 shared legality。

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
- 若保留 `Source 政策`，只能写 skill-specific non-binary 增量；shared legality 不得回流。
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
- 不强制 research capsule / skill-local Source 政策 / 篇幅基准。
- Validator、docs、manifest count 同步。

Supporting visualization skill：

- `category: research`，但 `research_layer: supporting`，不混进主 research ladder。
- 有完整 frontmatter、顶层 `# H1`、runtime capsule 和清晰 output contract。
- 保存到 topic 时必须绑定一个基准 markdown research artifact，并复用同一 stem 输出 `.html`。
- 不把安装器、拖拽 `.skill` 包说明或外部分发层 manifest 搬进 plugin runtime skill。
- 只做 source-backed visualization，不创造新的公司事实或 thesis。

### 13. 不要做的事

- 不要让 research skill 只引用 `CLAUDE.md`；插件运行时可能不读 `CLAUDE.md`。
- 不要给 operations skill 硬加 research capsule、skill-local Source 政策或篇幅基准。
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
- ❌ 忘记更新 docs / manifests，导致规则只存在于单个文件里。
- ❌ 新增 active skill 但 active count 仍是旧值。
- ❌ 新增 skill 后没加入 README / CLAUDE / manifests。
- ❌ 恢复 `meta.json`。
- ❌ 把 active skills 物理嵌套进分类目录。
- ❌ 把 `research-journal` 当作所有 skill 的普通保存目标。
- ❌ 把 `_cache/` 当作 earned memory 或 original source。

## 文档版本

- **版本**：v2.0
- **基于**：buy-side-research-skills v5.0.0
- **最后更新**：2026-06-01
- **维护者**：用户（user）
