---
name: init
description: Use when setting up or repairing a buy-side research workspace folder before research begins, especially when the user asks to initialize, scaffold, bootstrap, or create the standard workspace layout.
---

## Global Rules Capsule (v1)

本 skill 独立运行时也必须遵守以下全局规则；维护源是 `skills/_shared/global-rules.md`，该文件尽量使用 `CLAUDE.md` 原文。

- 默认用中文自然语言输出；ticker、公司名、产品名、source title、URL、YAML / JSON key、财务和行业术语可以保留英文。所有分析必须结论先行，不要写 "Great question"、"你说得对"、"It depends" 这类空铺垫。
- 每一条事实声明、数字、引语必须有 source link 或明确 source 描述。财务数字、估值、市场数据、KPI、运营数据、行业数据、管理层引语、专家访谈、监管表态、第三方判断、历史事件和时间点必须有 source。研究员判断本身不需要 source，但判断依据的事实必须有 source。
- 能用一手原始 source 就不用二手；多个 source 冲突时必须标注冲突，不要挑一个顺手的用。不确定时直接说不确定，并标 `[需查证]` 或 `[来源待补]`；不确定 URL 是否存在时写 `[link 待补]`。
- 绝对不能编造 URL、页码、引语、数字、人名、日期。sub-agent 或其他 AI 给出的 URL 一律视为 `[agent-provided, 未验证]`，关键 link 必须人工抽查 URL 和 claim 是否匹配。
- 不要写 sell-side 流水账：公司历史、管理层履历、行业科普、通用 SWOT、无数据定性、表格复述。数据表必须有 takeaway，且 takeaway 必须给结构性洞察，不要复读表格。
- 主动执行 Senior Analyst Radar：当疑点可能改变业务实质理解、model driver、市场预期 / consensus framing、peer group / 估值框架或下一步研究优先级时，直接点破。
- 遇到行业机制、工程原理、设备链条、工艺流程、术语或 know-how gap，先 handoff / 触发 `mechanism-map`；遇到 revenue / margin / backlog / price-volume-mix driver、披露口径异常或 model-driver gap，先 handoff / 触发 `driver-map`。

# Init

`init` 只负责把一个普通文件夹变成可用的 buy-side research workspace。它创建 workspace scaffold、写入 workspace `CLAUDE.md`、`.gitignore` 和 `topics/_meta/edge-radar.md`，让同事在正确的地方开始研究，而不是把研究材料塞回 plugin dev repo。

如果本 skill 开始 ingest 文件、研究公司、写 topic artifact、创建 git repo、改插件源码、覆盖用户已有文件，或者把 workspace scaffold 写进当前 plugin repo，它就失败了。`init` 是开工前的脚手架，不是研究 skill。

## 心法

`init` 解决的是“同事装好插件以后，第一步到底在哪里开始”的问题。一个好的 workspace 比一个更长的说明文档更有用：目录边界清楚，raw material、cache、models 和研究产物各有位置，后续 skill 才不会把所有东西混在一起。

这个 skill 的核心不是多建目录，而是防止污染：不要把用户研究 workspace 和 plugin dev repo 混用；不要把 raw PDF、Excel model、缓存 markdown 和可沉淀的 research memory 混用；不要让 workspace 一开始就背上 v2 state tracking 的维护负担。

默认行为必须保守、幂等、可重复运行。已有文件不覆盖，缺什么补什么；不主动 `git init`；可以复制 `ingest` helper scripts 到 `_scripts/`，但不执行 ingest。

## Source 政策

全局 source / anti-hallucination 规则已内嵌在 `Global Rules Capsule (v1)`。本节只补充 init-specific 要求。

特别强调：
- 本 skill 不产出公司事实、行业事实、财务数字或投资判断，因此通常不需要外部 source。
- 若解释 workspace 规则，只引用本 skill 的本地模板和脚本：`skills/init/assets/`、`skills/init/scripts/init-research-workspace.ps1`。
- 不要编造 Claude / Codex 安装路径或用户机器环境；路径来自用户输入或当前命令输出。
- 如果用户要求把已有研究材料搬进 workspace，只能建议放入 `_inbox/` 或 `_raw/`，不要推断材料内容。

## AI 的局限

| 局限 | 影响 | Mitigation |
|---|---|---|
| **路径误判** | 可能把当前 plugin repo 当成 research workspace | 脚本检测 `.claude-plugin/`、`.codex-plugin/`、`skills/`、`META-SKILL.md`，命中即退出 |
| **覆盖用户文件** | 可能破坏已有 workspace 规则 | 已存在的 `CLAUDE.md`、`.gitignore`、`topics/_meta/edge-radar.md` 一律不覆盖 |
| **越界做 ingest** | 可能提前处理 PDF / Excel / PPTX | 只复制 ingest scripts；不执行转换 |
| **误开 git** | 研究 workspace 默认不启用 git | 不 git init，只写 `.gitignore` 供用户未来自行决定 |
| **把 scaffold 当 artifact** | 可能写入 topic session | `init` 的 artifact 是 workspace scaffold，不是 research artifact |

## 触发场景

- “init research workspace”
- “初始化研究工作区”
- “创建研究文件夹”
- “setup research”
- “bootstrap workspace”
- “给同事初始化一个 workspace”
- “我装好插件后第一步怎么开工”
- “帮我补齐 research workspace 目录”

### 不应触发

- 用户要处理 PDF、Excel、PPTX、DOCX 或 `_inbox/` 材料 → 等未来 `ingest`，当前只建议先放入 `_inbox/`。
- 用户要研究公司业务基础 → `company-primer`。
- 用户要写研究笔记 / Boss Brief → `research-journal`。
- 用户要保存某个 skill 产物 → 按该 skill 的 `artifact_policy` 进入 topic session。

## 输入澄清要求

| 输入 | 必需性 | 默认处理 |
|---|---|---|
| **WorkspacePath** | 必需 | 用户未给路径时先要求一个明确路径，不猜测 |
| **Workspace name** | 可选 | 由路径 basename 推断 |
| **是否已有内容** | 可选 | 脚本幂等补齐，不覆盖已有核心文件 |
| **是否启用 git** | 不支持 | 本 batch 不 git init，只写 `.gitignore` |
| **是否 ingest 材料** | 不支持 | `init` 不 ingest，只创建 `_inbox/`、`_raw/`、`_cache/` 并复制 helper scripts |

如果用户给的是当前 plugin repo、`.claude/plugins/...` 插件安装目录或任何包含 plugin manifest 的目录，必须拒绝初始化并要求换一个 research workspace 路径。

## 模式设计

### Mode A: New Workspace Scaffold

用户给一个不存在或空的新路径时使用。

动作：
- 创建固定 workspace scaffold。
- 写入 workspace `CLAUDE.md`、`.gitignore`、`topics/_meta/edge-radar.md`。
- 创建 `_scripts/` 并复制 `init-research-workspace.ps1`、`init-assets/` 与 ingest helper scripts，方便用户以后自检 / 转换材料。
- 返回 created / skipped summary 和下一步建议。

### Mode B: Repair Existing Workspace

用户给一个已有 research workspace，需要补齐缺失项时使用。

动作：
- 只创建缺失目录。
- 只写缺失的核心文件。
- 对已有 `CLAUDE.md`、`.gitignore`、`topics/_meta/edge-radar.md` 标记 skipped。
- 不试图重写用户本地规则。

### Mode C: Dry Explanation

用户只是问“最后文件夹长什么样”或“init 会做什么”时使用。

动作：
- 不运行脚本。
- 只展示目标目录树和边界。
- 明确说明不 git init、不 ingest、不研究公司、不创建 topic session artifact。

## 输出结构

### 初始化完成后

````markdown
## Init Result

**结论先行**
已初始化 / 已补齐 research workspace：[path]

## Created
- [...]

## Skipped
- [...]

## Workspace Shape
```text
[workspace]/
├── _inbox/
├── _raw/
├── _cache/
├── _models/
├── _scripts/
└── topics/
    ├── _meta/
    │   └── edge-radar.md
    ├── company/
    ├── theme/
    └── event/
```

## 下一步
1. 把待处理材料放进 `_inbox/` 或 `_raw/`。
2. 如果要研究公司基础，用 `company-primer`。
3. 如果要转换材料，用 `ingest`。
4. 如果只是想开始问下一步研究问题，用 `next-step`。
````

### 被阻止时

```markdown
## Init Blocked

**结论先行**
不能在这个路径初始化 research workspace。

- 路径：[path]
- 原因：[命中 plugin repo / plugin install dir / 路径不明确]
- 建议路径：[user-owned research workspace path]
```

## Workflow 联动

| 场景 | 下一步 |
|---|---|
| 用户刚装好插件，不知道从哪开始 | `init` 创建 workspace scaffold |
| 用户已有 workspace，但缺 `_raw/`、`_cache/`、`topics/_meta/` | `init` repair missing scaffold |
| 用户把材料放入 `_inbox/` 后想转换 | `ingest` |
| 用户开始研究某家公司 | `company-primer` 或 `stock-quickread` |
| 用户已经研究清楚并想保存认知 | `research-journal` |
| 用户问下一步怎么研究 | `next-step` |

Artifact policy：
- `save_policy`: `workspace_scaffold`
- `default_artifact`: `workspace scaffold`
- `canonical_location`: 用户指定 research workspace
- 不创建 topic artifact，不写 `research-journal.md`，不写 `boss-brief.md`。

## 反模式自查

- ❌ 在 plugin repo 内初始化 workspace → 立刻停止。
- ❌ 覆盖已有 `CLAUDE.md`、`.gitignore` 或 `edge-radar.md` → 违反幂等原则。
- ❌ 自动 `git init` → 本 batch 禁止。
- ❌ 自动 ingest PDF / XLSX / PPTX / DOCX → `init` 只复制脚本，不执行转换。
- ❌ 创建 `research-journal.md` 或 topic session artifact → 越界。
- ❌ 把 `_raw/`、`_cache/`、`_models/` 当成可提交研究成果 → 边界错误。
- ❌ 生成 v2 state folders，如 `coverage/`、`portfolio/`、`pairs/` → 架构倒退。

## 篇幅基准

- 成功初始化：150-250 字 + created / skipped 列表。
- Repair existing workspace：120-220 字，重点说明补了什么、跳过什么。
- Dry explanation：200-350 字，展示目录树和边界即可。
- 被阻止：80-150 字，直接说明原因和替代路径。

超过 400 字通常说明开始解释研究方法或文档消化，应该 handoff 到相邻 skill 或 `ingest`。

## 边界

- `init` vs `ingest`：`init` 建 workspace 并复制 helper scripts；`ingest` 才负责把 raw 文件转成 LLM-friendly markdown。
- `init` vs `research-journal`：`init` 创建空 workspace scaffold，`research-journal` 只沉淀 earned insight。
- `init` vs `company-primer`：`init` 不研究公司；公司基础研究交给 `company-primer`。
- `init` vs plugin release scripts：`init` 面向用户 research workspace；root `scripts/` 面向 plugin dev / release validation。
