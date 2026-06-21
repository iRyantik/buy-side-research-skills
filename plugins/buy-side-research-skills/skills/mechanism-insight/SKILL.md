---
name: mechanism-insight
description: Deep-dive a single industry mechanism engineering principle or equipment chain — explain how it works and where value is captured.
---

# Mechanism Insight

Deep-dive a single industry mechanism, engineering principle, or equipment chain. The core value is not writing an encyclopedia entry — it's producing an insight that can change an investment judgment.

## Research Runtime Capsule

**执行本 skill 前必须先读取以下文件：**
- workspace `.references/runtime/research-runtime.md` §1（数据获取链）§2（来源验证链）§2.1（资料收集）§2.2（Source 纪律）§2.5（图片下载链）§4（产出合约）§5（保存合约）

**自动 Hook 防御：** `pre_write_gate`（source/tables/mermaid/image）`source_contract` `table_render_integrity` `mermaid_syntax` `skill_structure_contract` `evidence_ledger_floor`

**GATE**: Read workspace `.references/runtime/research-runtime.md` BEFORE any action. All runtime rules in that file + hooks — capsule only states what is unique to this skill.

## 心法

很多工业、能源、核电、航天和先进制造研究的真正 edge，不在"知道一个名词"，而在知道这个名词背后的系统怎么工作、瓶颈在哪里、谁捕获价值、哪些环节会传导到 revenue / margin / backlog driver。

`mechanism-insight` 的工作是把 know-how gap 变成可研究、可追问、可沉淀的结构。核心价值不是写科普，而是**产出能改变投资判断的洞察**。

本 skill 是 `driver-map` 的上游补充：`mechanism-insight` 解释"机制怎么运作、价值在哪里捕获"；`driver-map` 再解释"这些机制如何进入收入、利润率、backlog、price / volume / mix driver"。不要用机制解释替代 driver-map，也不要在本 skill 里直接做 DCF、comps、workbook 或完整 thesis。

如果输出只是百科解释，或者讲完以后不能说明它会改变什么研究判断，本 skill 就失败了。

## AI 的局限

| 局限 | 影响 | Mitigation |
|---|---|---|
| 相似术语混淆 | AI 容易把 train、turbine、compressor、generator 等概念混在一起 | 强制做 `Terms that matter`，逐一说明 plain meaning 和边界 |
| 流程过度简化 | 复杂系统被压成一句"设备驱动增长"，丢掉瓶颈和价值捕获点 | 必须画轻量流程图 / 链条图 |
| 把 capability 写成 adoption | "产品可以用于 LNG / data center / nuclear" 被误写成已经供货 | 客户 / 项目 / 供应链 claim 必须标 source 或 `[需查证]` |
| 技术事实过时 | 工艺路线、设备方案、监管要求可能变化 | 涉及最新项目、标准、装机、成本时标 as-of |
| 百科化 | 输出变成泛科普，不服务投资判断 | 每个机制解释必须落到 value capture / thesis read-through |

## 触发场景

### Mode A: Mechanism Explainer
- "这个行业术语到底是什么意思"
- "这个设备链条是怎么连接的"
- "这个设备链条为什么这样设计"
- "这个工艺流程怎么运作"
- "为什么这个系统要这样设计"
- "瓶颈 / control point 在哪里"
- "这个 process step 在系统里做什么"
- "这个机制为什么重要"

### Mode B: Mechanism-to-Research Map
- "这个机制对哪些公司有价值"
- "这个工程约束会怎么影响 revenue driver"
- "为什么这个设备链条会影响 margin / service mix"
- "这个 know-how gap 会不会影响 thesis"
- "这个机制能不能解释 peer 估值差"

### Mixed Mode
- "这个业务 bucket 背后的机制是什么，为什么这么拆"
- "先讲清楚这个机制，再告诉我哪些公司类型可能受益"
- "这个设备链条怎么运作，哪些环节最可能捕获价值"

### 不应触发
- 完全零基础没建立物理直觉 → `teach-in`
- 全行业产业链和价值池 → `industry-landscape`
- "这家公司收入 driver 是什么" → `driver-map`
- "帮我搭 model / DCF / comps" → `3-statement-model / dcf-model / comps-analysis / model-update`

## 输入澄清要求

| 维度 | 含义 | 默认假设 |
|---|---|---|
| 对象 | 术语 / 设备 / 工艺 / 系统 / value chain | 用户给具体名词时按单一机制；给主题时先缩到最关键机制 |
| 研究目的 | 理解机制 / feed driver-map / feed model / feed thesis / peer compare | 默认服务后续 driver-map 和 thesis |
| 技术深度 | 直觉解释 / 工程链条 / 商业约束 | 默认用研究员能建模和问问题的深度，不写教材 |
| 行业范围 | 用户指定的行业 / 设备链 / 工艺链 | 按用户覆盖行业，不扩展到无关行业 |
| 保存需求 | 是否落盘 | 默认对话输出；用户要求保存时写入 topic root |

## Mode A: Mechanism Explainer

### Step 1: Insight in one sentence

用一句话讲清楚这个机制最重要的投研含义。

### Step 2: Terms that matter

| Term / part | Plain meaning | Boundary / not this | Why it matters | Ev |
|---|---|---|---|---|

### Step 3: How it works

默认用轻量流程图 / 链条图：

```
input / fuel / feedstock -> core equipment/process -> output -> bottleneck / control point
```

随后用 3-6 个步骤解释，不要超过机制本身所需的深度。

### Step 4: Bottleneck and control point

明确系统中哪里最可能决定：capacity / throughput、uptime / reliability、efficiency、capex intensity、service intensity、regulatory / safety constraint。

## Mode B: Mechanism-to-Research Map

### Step 1: Where value is captured

| Value capture point | Who captures value | Revenue / margin channel | Evidence quality | Research read-through |
|---|---|---|---|---|

### Step 2: Insight → Driver-map bridge

| Mechanism implication | Driver-map link | Model / thesis implication | Confidence |
|---|---|---|---|

Rating hard standards：

| Rating | Hard standard |
|---|---|
| **High** | 有一手或权威 source，且可直接映射到 driver |
| **Medium** | 机制和商业关系合理，但公司层面披露不完整 |
| **Low** | 主要是研究员推断或主题关联，必须标 `[来源待补]` / `[需查证]` |

### Step 3: What not to infer

- `product can be used` vs `customer adopted`
- `equipment exposure` vs `recurring service exposure`
- `industry bottleneck` vs `company-specific revenue driver`
- `technical importance` vs `pricing power`

## 输出结构

> **Source contract**：本文所有事实 claim（数字、公司名、行业判断、竞争格局描述）句尾必须带 [S#](url) 或 [I#](url) 短链锚。解读性句子（"我觉得""我的判断"）不强制。连续 3 句以上事实 claim 中间无 source → 密度不够。
>
> **密度表**：
>
> | Section | 强制标 source | 豁免 |
> |---|---|---|
> | 物理原理/机制描述 | 每个物理常数、关键技术参数、材料属性 | 公认物理定律 |
> | 设备/工艺细节 | 设备型号、精度数字、产能数据、价格 | — |
> | 产业链站位 | 每家公司名称+产品名+定位 | — |
> | 价值捕获分析 | 市占率/利润率/定价权数字 | 定性判断 |
>
> **完成 Gate**：写完逐段扫 → 物理常数有 [P#]、设备数字有 [S#]/[I#] → `[待查]` ≤8 → Resources 展开所有 source。

```markdown
## 结论先行
[一句话说明这个机制最重要的投研含义]

## Insight in one sentence
[这个机制是什么 + 在系统里做什么 + 影响哪个投研变量]

## Terms that matter
| Term / part | Plain meaning | Boundary / not this | Why it matters | Ev |

## How it works
[轻量流程图 + 3-6 步解释]

## Where value is captured
| Value capture point | Who captures value | Revenue / margin channel | Evidence quality | Research read-through |

## Research read-through
| Mechanism implication | Driver-map link | Model / thesis / peer implication | Confidence |

## What not to infer
- [不能外推的结论]

## Routing
- 拆解公司 driver → `/driver-map`
- 形成 thesis → `/alpha-thesis`
```

## 图片要求

**产品/设备实物图必须**。来源优先级：公司产品页 hero image → web search → `[缺图]`。

**下载方法**：`python .scripts/shared/download-image.py <url> --output <slug> --topic mechanism-insight` — HTTP Tier 1 → Playwright Tier 2 `--base64` → `[缺图]` if all tiers fail。
artifact 引用：`![描述](../../../../_cache/images/mechanism-insight/<slug>.png)`

## Artifact / 保存策略

写入行业 topic：
```
industry/<industry-slug>/panorama/mechanism-insight/YYYY-MM-DD-mechanism-insight-<qualifier>.md
```

`naming_mode = required_qualifier`，qualifier 按具体机制/设备/工艺命名。

## Workflow 联动

| 场景 | 下一步 |
|---|---|
| 机制已讲清，需拆 revenue / margin / backlog driver | `driver-map` |
| 机制影响 model | `3-statement-model / dcf-model / comps-analysis / model-update` |
| 机制暴露高价值疑点但不知道怎么问 | `` |
| 机制解释了 peer 差异或 KPI 不可比 | `peer-deep-dive` |
| 机制形成 long / short variant view | `alpha-thesis` |
| 零基础需要先建立物理直觉 | `teach-in` |
| 需要行业全景和投资判断 | `industry-landscape` |

## 反模式自查

### Source 类
- ❌ 产能、成本、效率、订单、价格、客户、装机量没有 source / as-of
- ❌ 把行业常识写成公司披露事实
- ❌ 多个 source 冲突但不标冲突

### Logic 类
- ❌ 只写百科解释，没有 value capture 或 research read-through
- ❌ 把 `product can be used` 写成 `customer adopted`
- ❌ 把技术重要性直接外推成 pricing power
- ❌ 没画流程图 / 链条图
- ❌ 解释了设备功能但没说瓶颈、control point 或 service intensity

### Workflow 类
- ❌ 用户只是问机制，却输出 DCF / comps / price target
- ❌ 没有产品/设备实物图
- ❌ 机制仍是 Low confidence，却被当作核心事实
- ❌ 在 mechanism-insight 里做了 industry-landscape 级别的产业链全景

## 篇幅基准

- Quick check：30-60 行 + 1 张流程图/表
- Full insight：65-120 行 + 2-4 张表
- 超过 130 行：范围过大，应拆成多个机制或转入 `peer-deep-dive`

## 与相邻 skill 的边界

| | teach-in | industry-landscape | mechanism-insight | driver-map |
|---|---|---|---|---|
| **入口** | 零基础 | 知道基础概念 | 知道行业术语 | 知道机制 |
| **问题** | 这东西是什么 | 行业值不值得投 | 机制怎么运作 | 收入/利润怎么拆 |
| **覆盖** | 全链科普 | 全行业 | 1-2 个机制 | 单家公司/segment |
| **图片** | 实物图 | 产品实物图 | 产品实物图 | 无 |
| **产物长度** | 6000-8000 | 2000-3000 | 1000-1800 | 800-1500 |

> 产品图：每个涉及物理设备/产品的单元必须配 1 张实物图。下载优先级：公司官网 Media Kit → 产品页 hero → web search → [缺图]。下载到 topic 。

