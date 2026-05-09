# META-SKILL.md — Skill Authoring Guide for Buy-Side Research System

> **本文件不是 user-facing skill，是给 AI agent（Codex / Cursor / Gemini / 其他 Claude session）的 prompt + design guide**。
> 拿到本文件 + 用户具体需求 → 应能产出和现有 reference skills 同等或更高质量的新 skill。
> **使用方式**：把本文件 + 现有 plugin 状态（zip / file tree）+ 用户具体需求一起交给 agent，让 agent 按 §11 流程工作。

---

## 0. Before You Write Anything

如果你（agent）正在读这份文档，先确认：

1. **你拿到了用户需求** —— 知道要写什么 skill 吗？要触发什么？解决什么决策时刻？
2. **你拿到了现有 plugin 文件树** —— 看过 `CLAUDE.md`、`FRAMEWORK.md`、3-4 个 reference SKILL.md 吗？
3. **你理解 user 是 LS / 亚洲 / 特定行业** —— 不是 generic equity researcher

如果以上任一为 No，**先回去要这些 inputs**，不要凭想象开始写。

写完后必须按 §11 自检，并主动指出 3 个最不确定的设计决策让 user review —— 不要偷偷做 assumption 就交付。

---

## 1. 用户上下文（必须内化）

### 1.1 身份和工作语境

- **身份**：Buy-side equity researcher（hedge fund / **LS 长短策略**研究语境）
- **坐标**：亚洲（时区影响美股 post-print 工作流）
- **覆盖市场**：大中华（A 股 + 港股 + 中概 ADR）+ 全球（美 / 日 / 韩 / 欧）
- **覆盖行业**：industrials、aerospace and defense、advanced manufacturing、oil and gas、renewable energy、nuclear、emerging tech themes（AI 软件、AI 硬件、人形机器人、商业航天、quantum 等）

### 1.2 LS 工作的本质特征（设计任何 skill 都要内化）

| 特征 | 设计含义 |
|---|---|
| 双向都看 | 任何 thesis-related skill 默认双向考虑（不假设 long-only） |
| Pair trade 是核心工具（v3.1 已恢复独立 active `pair-trade` skill） | 触发 long X 思路时，自然带上 short Y 候选 / hedge 选项，必要时 handoff 到 `pair-trade` |
| Mechanism 拆解是复用原语（v3.3 新增 active `mechanism-map` skill） | 涉及行业机制、工程原理、设备链条、工艺流程、关键术语或 know-how gap 时，优先复用 `mechanism-map` |
| Driver 拆分是复用原语（v3.2 新增 active `driver-map` skill） | 涉及 revenue / margin / backlog / price-volume-mix driver 时，优先复用 `driver-map`，不要各 skill 重写一套拆分 |
| 跨市场惯性 | 同一公司多重上市、跨市场 peer 比较是常态 |
| 时区 disadvantage | 美股财报后才工作；post-print 工具必须高效 |
| 信息淹没 | **核心痛点**：单股时间被切碎；skill 优先服务 noise reduction |

### 1.3 用户最痛的工作

> "信息太多、单个公司花的时间少、容易被淹没"

任何 skill 设计都要回答：**这个 skill 是降低认知负担，还是增加？**

如果增加，你要给出非常充分的理由（这个增加换来了什么不可替代的 value）。

---

## 2. 当前系统设计哲学（v3 Journal-First）

### 2.1 系统已经放弃的设计（不要再造轮子）

v2 走过的弯路 —— 不要重新设计这些东西：

- ❌ **State files for portfolio tracking**（coverage/[ticker]/thesis.md、pairs/[X-Y]/、portfolio/catalyst-pipeline.md）—— 维护成本过重，研究员实际不会回头看
- ❌ **Thesis-tracker / decision-journal / v2 pair state logs** 已 archive —— 不要在新 skill 里假设这些 state 存在
- ✅ **`pair-trade` 是 v3.1 active research skill** —— 可以作为 hedge / LS framing / pair research 工具调用，但不维护 v2 的 `pairs/[X-Y]/spread-log.md` 或 append-only 交易状态
- ✅ **`mechanism-map` 是 v3.3 active research primitive** —— 可以作为 industry mechanism、engineering principle、equipment chain、process flow、know-how gap 的研究工具，但不做 DCF/comps、不替代 driver-map、不写完整 thesis
- ✅ **`driver-map` 是 v3.2 active research primitive** —— 可以作为 financial model、thesis、peer、pair、journal 的上游输入，但不做 DCF/comps、不编辑 workbook
- ❌ **Ticker-centric 组织**（每个 ticker 一个目录）—— 改为 topic-centric

### 2.2 v3 的核心定位

**AI 不是 status tracker，是 senior analyst coach**：

- 帮研究员**问更好的问题**（不是回答更多问题）
- 帮研究员**沉淀已研究的认知增量**（不是记录每个想法）
- 帮研究员**发现高价值疑点**（不等用户主动问）

### 2.3 核心循环

```
Senior Analyst Radar (发现 edge)
   ↓
Better AI Question (next-step 给方向)
   ↓
Research (用其他 skills 实际研究)
   ↓
Journal (research-journal 沉淀认知)
   ↓
Boss Brief (boss-brief 高密度 transfer 给 PM)
```

任何新 skill 要回答：**它在这个循环的哪一步？**

### 2.4 组织维度：Topic-centric

```
topics/
  [topic_type]/         # theme / company / event 等
    [topic-slug]/       # 例：ai-data-center-power
      index.md          # topic 主索引
      [YYYY-MM-DD]-[session-slug]/
        research-journal.md
        boss-brief.md
```

研究是围绕主题展开的；同一 topic 多个公司、多个 sessions。

### 2.5 复用优先：Research Primitive Layer

新增或大幅修改 skill 时，能复用现有 skill 内容就复用，不要为了新 skill 重写同一套方法论。

| Primitive | 复用场景 | 边界 |
|---|---|---|
| `mechanism-map` | 行业机制、工程原理、设备链条、工艺流程、关键术语、know-how gap | 不做 DCF/comps、不替代 `driver-map`、不写完整 thesis |
| `driver-map` | revenue、margin、backlog、price / volume / mix、披露口径异常、model-driver gap | 不做 DCF/comps、不生成 workbook、不写完整 thesis |
| `cross-market-compare` | A/H、ADR、跨市场 peer、币种 / 会计 / 流动性 / access normalization | 不替代完整 peer research |
| `next-step` | 把怪异点变成 1-2 个更好的 AI 问题 | 不生成任务清单、不落盘 |

如果一个 skill 需要解释机制、设备链条或 know-how，应 handoff 或 consume `mechanism-map` 的结果；如果需要拆 driver，应 handoff 或 consume `driver-map` 的结果；如果只是要提出下一步问题，用 `next-step`，不要把每个 skill 都写成小型 coach。

---

## 3. 写好 Skill 的 9 个核心原则

每个原则都是 hard rule，违反就重写。

### 原则 1: 服务"决策时刻"，不是"输出文档"

Skill 不应按"输出形式"切（thesis、memo、report），应按"研究员在哪个决策时刻调用"切。

- ❌ "X 公司研究报告" → 模糊
- ✅ "决定要不要建仓 X" / "决定 X 财报后加减仓" / "判断这条传闻是否值得进 portfolio" → 具体

### 原则 2: 反流水账纪律

**绝对禁止**的内容（任何 skill、任何场景）：

- "成立于 X 年" / "总部位于 XX" / 公司发展历史
- "管理层经验丰富" / "技术领先" / "行业领导者"
- 5 年历史财务表罗列（除非有明确趋势分析目的）
- 业务分部按章节平铺（quickread 内只用数据表）
- 通用 SWOT / 行业入门 / 监管科普
- "受益于 X" / "长期看好" / "看情况" / "如果错了就退" 这种空话
- 把表格内容用文字念一遍

skill 必须有"反模式自查"节明确列出这些禁忌。

### 原则 3: 数据先行 / 强制结构化

每个判断 / 结论必须有具体数字或数据表支撑：

- 没数据的直觉判断必须标 `[直觉，需查证]`
- "表格 + Takeaway" 模式：表格不是终点，必须有解读
- 但解读不是把表格念一遍 —— 必须给**结构性洞察**或**方向性判断**

### 原则 4: Source 政策 hard enforcement

每条**事实声明、数字、引语**必须有 source link 或明确 source 描述。

- 必须 source：财务数字、KPI、行业数据、引语、第三方判断、历史事件
- 不需要 source：研究员自己的判断、推断、合成结论
- 反幻觉硬规则：**绝对不能编造** URL、页码、引语、数字、人名、日期
- 不确定 URL 时写 `[link 待补]`，不要造链接
- Sub-agent 返回的 URL 视为 `[agent-provided, 未验证]`，要抽查

详细规则见 §5。

### 原则 5: 反模式自查必填

每个 skill 必须有"反模式自查"节，列出该 skill 最容易犯的具体错误。

**好的反模式**（具体可自检）：
- ❌ Catalyst 都是"长期" → 没有具体时间，重列
- ❌ Bear case 回报 -2% → bear 太弱
- ❌ Kill criteria = "如果错了就退" → 没有可观察信号

**坏的反模式**（空话）：
- ❌ "不要写得太长"
- ❌ "要客观"
- ❌ "注意 source"

每个反模式必须能机械自检（看到这个 pattern 就重写）。

### 原则 6: 篇幅基准明确

每个 skill 必须明确：

- **输出篇幅**（不是 SKILL.md 篇幅）：低于下限 / 超过上限各意味着什么
- 不同模式 / 不同场景的篇幅基准

例（来自 information-impact）：

> 单条完整 Mode A + Mode B：400-500 字（**500 硬上限**）
> 超过 500 字 → 越权，应该触发其他 skill

### 原则 7: Hard Standards / Hard Cutoffs

**不允许 AI 凭感觉打分**。任何评级 / 等级必须有 hard standard：

例（information-impact 的强度评级）：
- ❌ "Medium because: 看起来影响中等"（凭感觉）
- ✅ "High because: thesis §5.1 第 1 条假设是 'EUV bookings > $5B'，本次数据 $3.2B 直接反向"（link 到具体 thesis 字段）

例（pair-trade 的 spread z-score 阈值）：
- z-score > +1.5σ 或 < -1.5σ：可建仓
- z 在 ±0.5σ 内：太接近 mean，等
- z > ±3σ：警惕 regime change

Hard standards 防止输出退化为"感觉对就对"。

### 原则 8: Workflow 联动明确

skill 不能是孤岛。每个 skill 明确：

- **上游**（什么 skill 的产出 feed 进来）
- **下游**（产出 feed 到哪个 skill）
- **状态文件**（写什么 / 读什么）

写一个表格列出"这种场景 → 触发哪个下游 skill"。

### 原则 9: 心法节传递设计意图

每个 skill 顶部有"心法"节，**用 1-3 段话**传递这个 skill 真正要解决什么、最容易失败的地方在哪。

心法不是描述功能，是传递设计意图 —— 让用户和未来的 agent 都明白 *为什么* 这样设计。

---

## 4. SKILL.md 必填结构（template）

复杂研究型 skill 默认参考 `candidate-screener` / `peer-deep-dive` / `pair-trade` 这三个 Claude 原生感最强的 reference。它们的共同特征不是"标题多"，而是把研究员最容易偷懒或 AI 最容易瞎编的地方写成硬约束。

### 4.0 Claude 原生参考模板

| Reference skill | 应学习的东西 |
|---|---|
| `candidate-screener` | 机制拆解、AI 局限前置、输入澄清、mode 输出模板、漏斗收口 |
| `peer-deep-dive` | 结论先行、行业 lens、cross-cut insight、排序和资源分配 |
| `pair-trade` | 硬判断标准、builder / monitor、risk / sizing、反模式自查 |

复杂研究型 skill 的推荐骨架：

1. Frontmatter（短 trigger-only description）
2. 开头定义本 skill 的失败标准
3. `心法`
4. `Source 政策`
5. `AI 的局限`
6. `触发场景`
7. `输入澄清要求`
8. `Mode A / Mode B / Mixed Mode`
9. `输出结构`
10. `Workflow 联动`
11. `反模式自查`
12. `篇幅基准`
13. `与相邻 skill 的边界`

短 coach 型 skill（如 `next-step`）可以保持短而尖，不必硬拉长；但只要一个 skill 涉及 web search、复杂判断、多 mode、估值、模型、跨市场、供应链 claim，就应尽量使用上述骨架。

每个新 skill 的 SKILL.md 必须包含以下章节（顺序可调，但不能缺）：

### 4.1 Frontmatter（YAML）

```yaml
---
name: skill-name              # 用 kebab-case
description: Use when [具体触发场景和用户症状]。
---
```

**Frontmatter 写法**：
- 必须短而准，只写触发条件，不总结 workflow。
- 以 `Use when...` 开头，使用第三人称。
- 不要把完整流程、输出结构、状态文件、边界说明塞进 description；这些放正文。
- 具体触发短语写在正文 `触发场景` 里，不放 frontmatter。

### 4.2 心法（必填）

1-3 段，传递设计意图。直击这个 skill 真正解决什么、最容易失败的地方。

### 4.3 Source 政策（必填，引用 CLAUDE.md）

```markdown
本 skill 不维护独立 source policy。执行时必须遵守 `CLAUDE.md §3`；
若局部说明与 `CLAUDE.md` 冲突，以 `CLAUDE.md` 为准。

特别强调：
- [skill-specific 的 source 注意事项]
```

不要在 skill 里复制完整 source policy —— 引用 CLAUDE.md。

### 4.4 触发场景（必填）

列出具体触发短语（不是抽象描述）。如有多个 mode，按 mode 分组。

### 4.5 AI 的局限（复杂 / 高风险 skill 必填）

凡是依赖 web search、供应链关系、估值数据、Excel workbook、跨市场换算、AI universe recall 或复杂 source 判断的 skill，必须前置说明 AI 会在哪里失败：

- 会漏什么
- 会编什么
- 哪些数据可能 stale
- 哪些关系必须 source corroboration
- 用户该如何二次验证

### 4.6 输入澄清要求（复杂 / 多 mode skill 必填）

用表格列出关键维度、含义、默认假设。不要在关键输入缺失时硬猜。

### 4.7 Mode 设计（如有）

如果 skill 有多种使用 mode（如 Builder vs Monitor），明确：
- 每个 mode 的触发场景
- 每个 mode 的工作流
- mode 之间的关系（顺序 / 并列 / 互斥）

### 4.8 输出结构（必填）

具体到章节级别。给出：
- 章节顺序
- 每节必填字段
- 数据表格的列定义
- Hard standards（如评级 / 阈值）

### 4.9 状态文件 schema（如有）

如果 skill 写 / 读状态文件，明确：
- 文件路径
- Frontmatter schema（YAML）
- Entry schema（如果是追加式日志）
- Append-only / replace-only / hybrid

v3 journal-first 默认不维护 v2 状态库。除非用户明确要求，否则不要重新引入 `coverage/`、`pairs/[X-Y]/spread-log.md`、`portfolio/` 这类状态闭环。

### 4.10 Workflow 联动（必填）

表格列出"什么场景 → 触发哪个下游 skill"。

### 4.11 反模式自查（必填）

按问题类型分组（如 Source 类、Logic 类、流水账类）。每条必须可机械自检。

### 4.12 篇幅基准（必填）

输出篇幅的下限 / 上限 + 超出时的含义。

---

## 5. Source 政策（必读，CLAUDE.md §3 摘要）

### 5.1 必须有 source 的内容

- 财务数字（收入、利润、margin、ROIC、leverage 等）
- KPI / 运营数据（产量、客户数、ARR、库存、orders、backlog 等）
- 行业数据（市占率、价格、产能、需求量、TAM）
- 引语（管理层 commentary、卖方观点、专家访谈）
- 第三方判断（"Wood Mac 认为 X"）
- 历史事件 / 时间点

### 5.2 不需要 source 的内容

- 研究员自己的判断
- 基于已 sourced 事实的合成结论
- 行业常识 / 教科书原理

### 5.3 Source 质量分级

1. **一手原始**：SEC filings、交易所公告、IR、监管 / 政府数据
2. **二手权威**：transcripts、Bloomberg / CapIQ / FactSet、行业研究机构、专家访谈平台
3. **三手解读**：Reuters、Bloomberg News、FT、WSJ、卖方研究
4. **谨慎使用**：推特 / 论坛 / 个人博客 / 公司新闻稿

能用一手就不用二手。多个 source 冲突时，一手优先并明确标注冲突。

### 5.4 反幻觉硬规则（最重要）

- **绝对不能编造** URL、页码、引语、数字、人名、日期
- 没找到具体 source 的事实，标记 `[需查证]` 或 `[来源待补]`
- 不要凭印象写"管理层之前说过..."—— 找到具体出处或删
- 引用具体数字 / 引语必须给具体定位（"10-K 2024 p.42" ✓ vs "10-K" ❌）
- 不确定 URL 是否存在时**不要写 URL** —— 写描述加 `[link 待补]`

### 5.5 Sub-agent URL 验证

Sub-agent 返回的 URL 视为 `[agent-provided, 未验证]`：
- 不能直接当 verified source 用
- 关键 link 必须人工抽查 URL 和 claim 是否匹配
- URL 不匹配 claim 时标 `[link mismatch]`，找真实 source 或标 `[需查证]`

任何依赖 web search 的 skill（如 information-impact、candidate-screener）必须明确这条规则。

---

## 6. 反模式 Catalog（学习的负空间）

写新 skill 时，确保你的"反模式自查"节涵盖该 skill 类型的常见失败。

### 6.1 通用反模式（任何 skill 都要避免）

- ❌ 出现 "成立于" / "总部位于" / "管理层经验丰富"
- ❌ 5 年历史财务表罗列
- ❌ 通用 SWOT
- ❌ 行业入门 / 监管科普
- ❌ "受益于" / "长期看好" 等空话
- ❌ "看情况" / "有待观察" 作为判断
- ❌ 数据表无 takeaway / takeaway 复述表格

### 6.2 Source 类反模式

- ❌ 具体数字 / 引语无 source link
- ❌ "据报道" / "有传言" / "有人说" 当 source
- ❌ 编造 URL（看似合理但不存在）
- ❌ Sub-agent 返回的 URL 直接当已验证
- ❌ 多 source 冲突时挑一个用，不标注冲突
- ❌ 引用 "10-K" 而不是 "10-K 2024 p.42"
- ❌ Wikipedia / 推特 / 论坛作为关键事实依据

### 6.3 LS 视角缺失反模式

- ❌ Thesis 默认 long-only，不考虑 short / pair / hedge
- ❌ Variant view 只 vs long consensus，不 vs short consensus
- ❌ Pair trade 但 long thesis 和 short thesis 不能各自独立 sound
- ❌ Short-only 的 kill criteria 写法和 long 一样（没考虑 squeeze 风险）
- ❌ 候选股推荐只给 long basket，没 short basket（即使方向 = both）

### 6.4 数据空话反模式

- ❌ "估值偏贵 / 偏便宜" 但不做反向工程
- ❌ "Spread 偏离历史" 但不给 z-score / percentile
- ❌ 强度 = "High because 这是大新闻"（凭感觉）
- ❌ Catalyst 都是"长期"
- ❌ Kill criteria = "如果错了就退"（无可观察信号）
- ❌ Bear case 回报 -2%（bear 太弱）

### 6.5 AI 编造类反模式（最危险）

- ❌ AI 编造业务关联（"X 是 Y 供应商"但其实不是）
- ❌ AI 列已知"市场概念股"代替真实分析（NVDA / MSFT 当万能答案）
- ❌ Tier-2/3 关联只写"供应链相关"无具体 supplier link
- ❌ 把卖方研报的"概念股归类"当作业务关联依据
- ❌ AI 推测 candidate 但不标 `[需查证]`

### 6.6 Workflow 孤岛反模式

- ❌ 不读 / 不写状态文件的新 skill（孤岛）
- ❌ 没说明触发哪个下游 skill
- ❌ 输出膨胀（默认 < 500 字的 skill 写到 2000 字）
- ❌ Trigger keywords 和现有 skill 冲突

---

## 7. 篇幅基准（不同 skill 类型）

### 7.1 SKILL.md 文件本身

- 简单 skill：200-300 行（如 next-step）
- 标准 skill：300-450 行（如 information-impact、cross-market-compare）
- 复杂 skill（多 mode + 高判断密度）：300-500 行（如 pair-trade）

超过 600 行通常是 over-engineering —— 拆开或精简。

### 7.2 Skill 输出篇幅（用户看到的产出）

- **Filter / Quick judgment skills**：< 500 字硬上限（如 information-impact）
- **Single-stock research**：1200-1800 字（如 stock-quickread）
- **Multi-stock research**：N 线性 scale，1500-5000 字（如 peer-deep-dive）
- **Thesis building**：800-1500 字（如 alpha-thesis）
- **Coaching**：< 300 字（如 next-step —— 短而尖）

每个 skill 必须明确自己的篇幅基准 + 超出 / 不足时的含义。

---

## 8. Reference Exemplars（标杆 skills）

### 8.1 必读的 reference skills

写新 skill 前，仔细阅读以下 SKILL.md 作为质量基准：

| Skill | 学什么 | 路径 |
|---|---|---|
| `information-impact` | **极强纪律 + 500 字硬上限 + 双 mode 设计** | `skills/information-impact/SKILL.md` |
| `candidate-screener` | **AI 局限承认 + 反编造 + Tier 分组 + 漏斗收口** | `skills/candidate-screener/SKILL.md` |
| `stock-quickread` | **数据先行 + 反向工程 + 8 节强制结构** | `skills/stock-quickread/SKILL.md` |
| `alpha-thesis`（LS 改造版） | **Trade Structure 子流程 + 双向 LS** | `skills/alpha-thesis/SKILL.md` |

### 8.2 标杆设计的具体特征

读 reference exemplars 时观察以下设计模式：

1. **Frontmatter 的 description 写法**：触发场景具体、列举 5-8 个用户实际会说的短语
2. **心法的力度**：1-3 段直击设计意图，不是功能描述
3. **Mode 设计**：如何把不同使用场景拆成 mode、mode 之间关系
4. **Hard standards 的写法**：阈值 / 等级如何 link 到具体可观察 indicator
5. **反模式分组**：按问题类型（source / logic / 流水账 / LS / workflow）分组
6. **Workflow 联动表格**：场景 → 下游 skill 的清晰映射
7. **YAML schema 设计**：状态文件如何结构化（参考 information-impact 的 information_v1）

---

## 9. 测试标准（写完 skill 后必做的自检）

写完一个 SKILL.md 后，对照以下 checklist 自检。每条都要 yes，否则重写。

### 9.1 必填结构检查
- [ ] Frontmatter 有 name + description？
- [ ] description 包含 5-8 个触发短语？
- [ ] 心法节有 1-3 段传递设计意图？
- [ ] Source 政策节引用 CLAUDE.md（不重复全文）？
- [ ] 触发场景列出具体短语？
- [ ] 输出结构明确到章节级 + 字段级？
- [ ] Workflow 联动表格存在？
- [ ] 反模式自查节存在且条目可机械自检？
- [ ] 篇幅基准明确（下限 + 上限 + 超出含义）？

### 9.2 设计哲学检查
- [ ] 这个 skill 服务于具体的"决策时刻"，不是"输出文档"？
- [ ] 输出篇幅符合 §7 的 skill 类型基准？
- [ ] 任何评级 / 等级有 hard standard，不允许凭感觉？
- [ ] Source 要求清晰（必须 source 的字段标明了）？
- [ ] LS 视角默认（如适用 thesis 类工作）？

### 9.3 反模式覆盖检查
- [ ] 反模式自查涵盖 §6 中该类型 skill 的常见失败？
- [ ] 至少有 10 条具体反模式？
- [ ] 每条反模式可机械自检（不是 "要客观" 这种空话）？

### 9.4 Workflow 集成检查
- [ ] 这个 skill 在 v3 核心循环（Edge → Question → Research → Journal → Brief）的哪一步？
- [ ] 上游和下游 skills 明确？
- [ ] 状态文件读 / 写规则清晰？
- [ ] Trigger keywords 和现有 active skills 不冲突？

### 9.5 用户特征匹配检查
- [ ] 例子 / 场景符合 LS 亚洲研究员的覆盖（不出现消费 / 医药例子）？
- [ ] 跨市场场景（A/H、ADR、跨市场 peer）有覆盖（如适用）？
- [ ] 中文输出习惯遵守（专业术语英文）？

---

## 10. 写作过程中的常见陷阱

### 10.1 第一稿就过长

新手 agent 常常一上来写 700+ 行 SKILL.md。**先写 outline + 必填章节标题 → review → 再填内容**。

### 10.2 章节质量不均

通常"心法"和"反模式"写得最差（被当成填空）。**这两节是 skill 灵魂**，要花最多时间打磨。

### 10.3 Hard standards 凭感觉

写"Low / Medium / High"等级时，agent 容易给空话定义。强制要求每个等级 link 到 specific observable indicator。

### 10.4 反模式空泛

"不要写得太长" / "要客观" / "注意细节" 都不是反模式 —— 是空话。每条反模式必须**具体到可机械自检**：看到这个 pattern 就触发重写。

### 10.5 Workflow 联动写完就忘

写"和其他 skill 的关系"时容易写完就忘。**回头实际去那些 skill 的 SKILL.md 检查**：你声称的下游 skill 真的支持这种调用吗？还是你想象的？

### 10.6 没承认 AI 局限

AI 在以下任务上不可靠（必须在 SKILL.md 里明确承认）：
- 编造业务关联（特别是供应链 tier-N）
- Universe 偏差（mid/large cap 主导，small cap 缺失）
- 知识 cutoff（最近 6-12 个月数据）
- 估值数据 stale
- 概念股堆砌惯性

如果你的新 skill 涉及以上任一，必须有明确的 caveat 节。

---

## 11. 给 Agent 的 Final Workflow

按以下 5 步工作：

### Step 1: 理解需求（10-20% 时间）

- 用户具体要写什么 skill？解决什么决策时刻？
- 用户给的现有 plugin 是什么版本？v3 journal-first 还是更新？
- 这个 skill 在 v3 核心循环（Edge → Question → Research → Journal → Brief）哪一步？

如果以上任一不清楚 —— **回去问 user**，不要自己脑补。

### Step 2: 阅读 reference（15-20% 时间）

- 必读：CLAUDE.md（项目宪法）+ FRAMEWORK.md（系统设计）+ 本文件
- 至少读 3 个 reference SKILL.md（建议 information-impact + 一个最相关的现有 skill + active pair-trade；只有在用户明确要比较 v2 状态 workflow 时才读 archived pair-trade）
- 观察这些 skill 的设计模式（§8.2）

### Step 3: 写 outline（5-10% 时间）

先写 SKILL.md 的章节标题 + 每节 1-2 句要点，**不要直接写完整内容**。outline 长度应在 30-50 行。

把 outline 给 user review —— 等 user 确认方向再展开。

### Step 4: 填充内容（50-60% 时间）

按 §4 必填结构填充。重点打磨：

- **心法**（最容易写差的章节，花 15+ 分钟）
- **反模式自查**（按 §6 catalog 分组，至少 10-15 条具体可自检反模式）
- **Hard standards**（任何评级必须 link 到 specific indicator）

### Step 5: 自检 + 主动 flag（10-15% 时间）

- 按 §9 checklist 逐条自检
- **写完后必须主动指出 3 个最不确定的设计决策让 user review**：
  - 不要 silently 做 assumption
  - 例：阈值定多少（z-score 1.5σ vs 2σ）、章节是否合并、Mode 划分是否合理

输出到 user 的格式：

```
## [Skill Name] SKILL.md

[完整 SKILL.md 内容]

---

## 我做的关键设计决策

1. [决策点 1] —— 选项 A / B / C，我选了 X，理由是 ...
2. [决策点 2] —— ...
3. [决策点 3] —— ...

## 我最不确定的 3 个地方

1. [不确定点 1] —— 可能 alternative：...
2. [不确定点 2] —— ...
3. [不确定点 3] —— ...

## 自检结果（§9 checklist）

[逐条勾或不勾，不勾的解释为什么]
```

---

## 12. 一个完整范例：写 information-impact 时该问的问题

如果用户说"帮我写一个 information-impact skill"，按 §11 你应该问：

**Step 1（理解需求）**：
- "Information impact" 解决什么决策时刻？—— 信息淹没情况下快速判断哪条值得行动
- 输入是什么？—— 一条新闻 / 卖方报告 / 数据点 / 传闻
- 输出是什么？—— 影响判断 + 是否需要后续 action
- 在 v3 核心循环哪步？—— 事件 / 信号响应（不是 Edge → Question 这条主线）

**Step 2（reference）**：
- 读 CLAUDE.md §3（source 政策）+ §4（senior analyst radar）
- 读现有 information-impact SKILL.md（如果有 v3 版本）
- 读 alpha-thesis 看它如何处理"对 thesis 的影响"

**Step 3（outline）**：

```
- 心法（防淹没核心 + 500 字硬上限）
- Source 政策
- 触发场景（具体短语）
- 信息类型 → 处理路径 Map
- Mode A: Claim Check
- Mode B: Research Relevance（v3 简化后没有 Portfolio Impact）
- 状态文件 schema
- Workflow 联动
- 反模式自查
- 篇幅基准
```

**Step 4（填充）**，写完后...

**Step 5（自检 + flag）**：

```
我做的关键设计决策：
1. Mode B 是 "Research Relevance" 不是 "Portfolio Impact" —— v3 已不维护 portfolio 状态
2. Source quality 直接引用 CLAUDE.md 4 级，不重新搞 A/B/C/D
3. 500 字硬上限保留 —— 这是 skill 灵魂

我最不确定的 3 个地方：
1. 是否保留 Mode A claim verdict 的 5 级（Confirmed/Likely/Plausible/Unsupported/Contradicted），还是简化到 3 级？
2. "卖方观点本身不是 catalyst" 这条结论是否过强？
3. 状态文件 schema 是否还需要（v3 不强调状态）？
```

---

## 13. 不要做的事

最后强调几条**绝对不要做**的事：

- ❌ **不要复制 CLAUDE.md 内容到 skill 里** —— 引用即可
- ❌ **不要给所有 skill 都加 LS 改造** —— bear-pre-mortem 本身已是 LS 思维（设想错了 + 对手是聪明的）
- ❌ **不要为消费 / 医药行业设计任何 example** —— 用户不看
- ❌ **不要默认 long-only** —— LS 工作要求双向
- ❌ **不要把 skill 设计成 sell-side report 模板** —— 我们反流水账
- ❌ **不要写完就交付** —— 必须按 §11 Step 5 自检 + flag
- ❌ **不要 silently 做 assumption** —— 不确定就 flag
- ❌ **不要重新设计 v2 已废弃的东西**（state files、decision-journal、thesis-tracker、v2 pair state logs）—— 除非 user 明确要回退
- ✅ `pair-trade` 本身是 active research skill；能复用其 LS / hedge / spread 方法论，但不要恢复强制落盘状态系统

---

## 14. 文档版本

- **版本**：v1.0
- **基于**：buy-side-research-skills v3.3.0
- **最后更新**：2026-05-09
- **维护者**：用户（user）

如果用户的 plugin 版本号变化（如 v4.0、v5.0），本文件需要同步更新核心循环、active skills 列表、archive 状态。

---

# 附录 A: 给 Agent 的 Quick-Start Prompt

如果你（agent）想最快上手，复制以下 prompt 作为对话开端：

```
我要为 buy-side-research-skills (v3.0.0) plugin 写一个新 skill。

我的需求：[用户具体需求]

我已读：
- META-SKILL.md（本文件）
- CLAUDE.md
- FRAMEWORK.md
- 以下 reference SKILL.md：[列出读了哪几个]

按 META-SKILL.md §11 流程：
1. 我对需求的理解：[复述一遍]
2. 这个 skill 在 v3 核心循环的位置：[Edge / Question / Research / Journal / Brief 哪步]
3. 我准备先写 outline 给你 review，确认方向后再展开

如果上述理解有偏差，请纠正后再开始。
```

# 附录 B: 自检 Checklist 速查

写完 SKILL.md 后逐条勾选：

**结构（10 条）**
- [ ] Frontmatter name + description
- [ ] description 含 5-8 个触发短语
- [ ] 心法节 1-3 段
- [ ] Source 政策引用 CLAUDE.md
- [ ] 触发场景具体短语
- [ ] 输出结构章节级 + 字段级
- [ ] 状态文件 schema（如有）
- [ ] Workflow 联动表格
- [ ] 反模式自查 ≥ 10 条
- [ ] 篇幅基准明确

**设计（5 条）**
- [ ] 服务具体决策时刻
- [ ] 输出篇幅符合 §7 基准
- [ ] Hard standards（不凭感觉）
- [ ] LS 视角默认（如适用）
- [ ] AI 局限明确承认（如适用）

**反模式覆盖（3 条）**
- [ ] 涵盖 §6 该类型常见失败
- [ ] 每条可机械自检
- [ ] 至少 10-15 条

**集成（4 条）**
- [ ] 在 v3 核心循环位置明确
- [ ] 上下游 skills 明确
- [ ] 状态文件规则清晰
- [ ] Trigger 不冲突

**用户特征（3 条）**
- [ ] 例子覆盖 LS / 亚洲 / 工业 + AI / 不含消费医药
- [ ] 跨市场场景（如适用）
- [ ] 中文输出习惯

**总分**：25 条全部勾选才算合格。
