# CLAUDE.md - Buy-Side Research Skills 插件开发宪法

> 本文件只服务 `buy-side-research-skills` plugin dev repo。
> 它是插件开发与发布治理的 source of truth，不是用户 research workspace 的运行时宪法。

---

## 1. 定位

- 本文件负责 **plugin 开发宪法**：authoring governance、metadata / manifest / packaging / release sync、authority hierarchy、hard gate。
- 用户 workspace 的高层宪法模板维护在 `plugins/buy-side-research-skills/skills/init-workspace/assets/CLAUDE.md.template`。
- Claude / Codex hooks 通过 `init-workspace` 下发到用户 workspace 的 project-level config（`.claude/settings.json`、`.codex/hooks.json`）；plugin dev repo 文档本身不是宿主自动 hook discovery surface。
- 被调用的 active skill 运行时行为，以对应的 `plugins/buy-side-research-skills/skills/*/SKILL.md` 为准。
- `_shared/research-policy-baseline.md` 只做 authoring baseline / review baseline，不是假定会自动加载的 runtime authority。

---

> Agent/plugin runtime upgrade flow belongs to `update-agent-runtime`; `init-workspace` remains workspace scaffold-and-repair only.

## 2. Authority Hierarchy

规则冲突时按以下顺序判断：

1. root `CLAUDE.md`
   - plugin 开发宪法
2. `init-workspace/assets/CLAUDE.md.template`
   - workspace 高层宪法模板
3. invoked research `SKILL.md`
   - runtime executable contract
4. `_shared/research-policy-baseline.md`
   - authoring baseline only，not runtime authority

如果 workspace template 的高层摘要与某个 research skill 的具体执行细则看起来不一致：

- **research `SKILL.md` wins**
- template 只提供高层约束，不覆盖 skill procedure

---

## 3. 各层职责

### 3.1 Root `CLAUDE.md`

负责：
- plugin repo 的目标、边界、authoring governance
- metadata / manifest / release / packaging 同步规则
- 哪些文件是 runtime truth，哪些只是维护基线
- hard gate 维护纪律

不负责：
- 详细 research runtime procedure
- 完整 source / fallback / sub-agent playbook
- 每个 research artifact 的写作模板正文

### 3.2 `CLAUDE.md.template`

负责：
- workspace 语境与高层原则
- 默认中文、结论先行、data first、anti sell-side
- workspace file rules / topic structure / routing
- 高层 source stance

不负责：
- 完整 claim-level source contract 全文
- 完整 fallback taxonomy
- 完整状态码字典
- skill-specific section-level 细则

### 3.3 Research `SKILL.md`

负责：
- 真正 runtime 会用到的执行合同
- canonical medium capsule
- skill-specific delta
- 输出结构、fallback 边界、默认单线 / 默认并行、routing handoff

### 3.4 `research-policy-baseline.md`

负责：
- 完整研究规则 baseline
- 维护者 review / batch sync 的对照底稿
- 关键原文规则的集中保存，包括多语言披露规则、本地语言 / 本地市场 source 优先、claim-level source contract、clickable short anchors + `## Resources`

不负责：
- 单独决定 runtime 行为

---

## 4. Skill Families

### 4.1 Research skills

Research skills 必须内嵌 **canonical medium capsule + skill-specific delta**。

公共 capsule 至少覆盖：
- 默认中文、结论先行
- truth-like claim 必须挂 clickable short anchor
- 文末唯一 `## Resources`
- 无 source 就 honest degrade
- source quality first
- 同层优先 local-language / home-market source
- `internet source` 只补 market / consensus / valuation / liquidity / price-action 缺口
- `internet source` 不冒充 company-disclosed fact
- 本 skill 默认单线或默认并行的一句话规则
- 主 agent 负责最终 synthesis

### 4.2 Modeling skills

`3-statement-model`、`dcf-model`、`comps-analysis`、`model-update` 使用 **separate modeling capsule**，不吃 research capsule。

公共 modeling capsule 至少覆盖：
- actuals completeness
- source-map verification
- no silent zeros
- bounded QA 型 sub-agent
- 主 agent 负责 final workbook、valuation treatment、delivery

### 4.3 Operations skills

Operations skills 不嵌 research capsule，只保留各自操作边界、文件安全、输入输出和必要 source discipline。

---

## 5. Hard Gate

任何公共 research 规则变更，必须在**同一个 change**里同步完成：

1. 修改 `_shared/research-policy-baseline.md`
2. 同步所有受影响的 active research `SKILL.md` capsules
3. 如影响 workspace 高层原则，再修改 `CLAUDE.md.template`
4. 如影响 public behavior / package language，再同步 `README.md`、`docs/release.md`、plugin manifests / marketplace manifests

不允许只改 baseline / template 而不改 skills 就合并或发版。

---

## 6. UTF-8 文本纪律

中文或多语言文本资产统一使用 **UTF-8 无 BOM**。

至少适用于：
- `.md`
- `.yaml`
- `.json`

硬规则：
- 修改含中文或多语言文本的文件时，必须显式以 UTF-8 写回。
- 批量脚本改写文本时，必须显式指定 UTF-8，避免 mojibake。
- 不要依赖终端默认编码去“碰运气”写文件。
- 如果发现中文显示异常，先判断是控制台渲染问题还是文件内容真的被写坏；不要把 mojibake 当成“只是终端问题”直接带进提交。

---

## 7. Authoring Rules

- active runtime skills 保持平铺在 `plugins/buy-side-research-skills/skills/[skill-name]/`。
- 不恢复 retired `meta.json`、v2 state workflow、ticker-centric tracker 结构。
- 任何新 skill 或重大 skill rewrite，如果影响 public positioning、skill map、keywords、release payload，必须同步 docs / manifests。
- “尽量用已有原文”优先于“为了结构好看而重写腔调”。尤其是多语言披露规则、source contract、本地语言 source 优先等已验证过的规则，默认沿用原文，只做最小改写。

---

## 8. Release Shape

runtime release zip 继续保持扁平 payload：

- `.claude-plugin/`
- `.codex-plugin/`
- `skills/`
- `README.md`

repo docs、authoring baseline、release notes 是否进 zip，以当期 release policy 为准；不要默认把所有 repo 文档塞进运行时包。

---

## 9. 双语同步规则

本插件同时维护中文源文件与英文翻译副本。英文研究员依赖 `SKILL.en.md`、`CLAUDE.en.md.template`、`*.en.md` 等翻译文件。

**同步铁律**：

- 修改中文源文件（`SKILL.md`、`CLAUDE.md.template`、`research-policy-baseline.md`、`actuals-data-catalog.md`、KPI driver `.md` 等）→ **必须同步修改对应的 `.en.md` 文件**。
- 发布前检查：`docs/release.md` pre-release checklist 含 `[ ] 中文源码变更已同步到所有对应 .en.md`。
- 中文版为 source of truth；英文版必须内容密度对齐——中文有的每个 section、每条规则、每个表、每个约束，英文必须有。不压缩、不概括。
- 代码、路径、YAML key、ticker、财务术语、CLI 命令 **不翻译**，保留原样。
- 如变更仅涉及中文措辞风格优化且不改变规则语义，英文版可跳过。
