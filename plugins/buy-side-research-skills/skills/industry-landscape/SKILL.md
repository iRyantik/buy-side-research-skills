---
name: industry-landscape
description: Map industry value chain profit pools competitive dynamics and company roster with investment judgment.
---

# Industry Landscape

Map an industry's value chain, profit pools, competitive dynamics, and company roster. Make an industry-level investment judgment. Hand off to candidate-screener for company prioritization.

## Research Runtime Capsule

**执行本 skill 前必须先读取以下文件：**
- `references/runtime/research-runtime.md` §1（数据获取链）§2（来源验证链）§2.1（资料收集）§2.2（Source 纪律）§2.5（图片下载链）§4（产出合约）§5（保存合约）

**自动 Hook 防御：** `pre_write_gate`（source/tables/mermaid/image）`source_contract` `table_render_integrity` `mermaid_syntax` `skill_structure_contract` `evidence_ledger_floor`

## 心法

买方做行业研究不是为了"了解行业全景"——那是卖方 initiation 的活。买方做行业研究是为了回答三个问题：(1) 这个行业现在值不值得投？(2) 钱集中在产业链的哪一段？(3) 哪几家公司最值得先看？

`industry-landscape` 的核心产出不是行业百科，而是**产业链地图 + 价值池分析 + 竞争动态 + 公司注册表 + 行业级投资判断**。它比 `teach-in` 多了一层投资视角，比 `candidate-screener` 多了一层行业全景。

本 skill 的失败标准：输出是行业科普但没有投资判断；value chain 画了但没有标注利润分配；公司注册表变成了推荐排序。

## AI 的局限

| 局限 | 影响 | Mitigation |
|---|---|---|
| 利润池误判 | AI 容易假设"行业在增长 = 每段都在赚钱" | 必须单独写 value capture，标注哪段在吃肥肉、哪段在卷 |
| 产业链边界模糊 | AI 容易把上游原材料、中游设备、下游应用全混在一起 | 先画产业链图，每段标注代表性公司 |
| 竞争动态误读 | AI 容易把"有国产"当成"国产替代" | 标注每段的国产化率、精度差距、导入周期 |
| 概念股记忆污染 | AI 容易把热门 names 当 anchor | 公司注册表必须写 exposure 类型和 source 状态 |

## 触发场景

- "这个行业值不值得投"
- "帮我看看这个行业的产业链"
- "这个行业利润集中在哪一段"
- "这个行业有哪些玩家"
- "行业格局怎么样"
- "industry landscape"
- "行业全景"

不触发：
- 零基础还没建立物理直觉 → `teach-in`
- 已经有公司池需要排序 → `candidate-screener`
- 单机制深挖 → `mechanism-insight`

## 输入澄清要求

| 维度 | 含义 | 默认假设 |
|---|---|---|
| 行业边界 | 产品/服务/value chain stage/下游应用 | 按用户原词的最窄可投边界 |
| 地域 | US/大中华/全球 | 全球，优先标用户常看市场的 anchor |
| 时间窗口 | 3M/12M/24M+ | 12M，兼顾 3M catalyst |
| 方向 | Long/Short/Both | Both |

## 输出结构
```markdown
# <Industry> — Industry Landscape

> DATE | Coverage: N companies | Pipeline: actuals ✅ | [需查证] X

## 1. Verdict
## 2. 产业链地图
## 3. 竞争格局
## 4. 价值池
## 5. 公司注册表
## 6. 投资主题 & 催化剂

---

## Resources
```


> **Source contract**：本文所有事实 claim（数字、公司名、行业判断、竞争格局描述）句尾必须带 [S#](url) 或 [I#](url) 短链锚。解读性句子（"我觉得""我的判断"）不强制。连续 3 句以上事实 claim 中间无 source → 密度不够。
>
> **密度表**：
>
> | Section | 强制标 source | 豁免 |
> |---|---|---|
> | §1 Verdict | 利润池占比数字、方向判断依据 | 方向判断本身 |
> | §2 产业链地图 | 每段价值池占比 %、市占率数字、产能数字 | ASCII 图 |
> | §3 竞争格局 | 每家公司市占率/定位、行业集中度 (CR3/CR5) | — |
> | §4 利润池 | 每个 pool 的利润率/占比数据 | — |
> | §6 公司注册表 | 每家公司 ticker+MCap+暴露类型 | — |
>
> **完成 Gate**：写完逐段扫 density → `[待查]` ≤10 → Resources 段必须有所有 [S#]/[I#] 展开。

### 1. Verdict（~200 字）

结论先行：这个行业当前该不该投、为什么、利润在哪里、最大的风险是什么。

### 2. 产业链地图（~800 字 + ASCII 图）

```
上游 → 中游 → 下游 → 终端客户
```

每段标注：
- 这段在做什么（一句话）
- 价值池占比（占行业总利润的 X%）
- 代表公司（3-5 个）+ **公司 logo 图**
- 集中度趋势（分散→集中？被替代？）
- 国产替代程度（如适用）

**产业链图之后必须跟一张价值分配总结**：哪段在吃最肥的肉、哪段在卷、利润池在往哪迁移。

### 3. 竞争格局（~600 字 + 表格）

| 环节 | 格局 | 进入壁垒 | 替代威胁 | 买家议价力 | 供应商议价力 |
|---|---|---|---|---|---|
| — | 集中/分散 | — | — | — | — |

**产品实物图**：关键设备/产品的实物照片（如光模块、固晶机、耦合设备）。

Takeaway：这个行业的竞争在往什么方向变。

### 4. 行业驱动力（~400 字）

- 需求端：什么在推动增长（具体 KPI，不写"AI 驱动"——写"每 GPU 带宽需求从 400G→800G"）
- 供给端：瓶颈在哪（产能/capex/人才/上游芯片）
- 代际升级：什么在改变行业结构（如 800G→1.6T→CPO 的精度跳变）
- 政策/地缘：有没有出口管制/国产替代强制推动

### 5. 投资判断（~300 字）

- 行业当前 regime：扩张/收缩/整合/替代
- 多空分歧在哪
- 什么时候这个判断会错（kill criteria）
- 行业级的 variant view（和 consensus 差在哪）

### 6. 公司注册表（~500 字 + 表格）

| 公司 | 市场 | 产业链位置 | Exposure 类型 | 为什么在表里 | Ev |
|---|---|---|---|---|---|
| — | — | — | direct/indirect/thematic | — | — |

**不排序。** 排序是 `candidate-screener` 的事。这里只列"这个行业有哪些值得知道的公司"。

**公司 logo 图**：每段产业链的代表公司配 logo。

### 7. Routing（~150 字）

| 下一步 | Skill |
|---|---|
| 需要深挖某个设备段/机制 → | `/mechanism-insight <具体>` |
| 需要公司优先级排序 → | `/candidate-screener` |
| 需要横向比较 3-8 家公司 → | `/peer-deep-dive` |
| 快速看某家公司 → | `/stock-quickread <ticker>` |
| 拆公司 revenue/margin driver → | `/driver-map` |
| 需要市场预期/priced-in 分析 → | `/consensus-map` |

## 图片要求

**下载方法**：`python _scripts/shared/download-image.py <url> --output <slug>`。Logo 模式：`--logo <TICKER>`。图片来源优先级：① 公司 Media Kit → ② 产品页 hero → ③ web search → ④ `[缺图]`。

| 图片类型 | 必须 | 来源 |
|---|---|---|
| 公司 logo 图 | **必须**（每个产业链环节的代表公司） | 官网 media kit → favicon → web search → `[缺图]` |
| 产品实物图 | **必须**（关键设备/产品） | 官网产品页 → web search → `[缺图]` |

## Artifact / 保存策略

写入行业 topic 根：
```
industry/<industry-slug>/YYYY-MM-DD-industry-landscape.md
```

`naming_mode = optional_qualifier`：完整行业全景用默认名；只覆盖某段 value chain slice 时追加 qualifier。

## Workflow 联动

| 场景 | 下一步 |
|---|---|
| 零基础需要先建立物理直觉 | `teach-in` |
| 深挖某段设备/机制 | `mechanism-insight` |
| 公司优先级排序 | `candidate-screener` |
| 横向公司比较 | `peer-deep-dive` |
| 单家公司快速判断 | `stock-quickread` |
| 公司 driver 拆解 | `driver-map` |
| 市场预期分析 | `consensus-map` |
| 形成投资 thesis | `alpha-thesis` |

## 反模式自查

- ❌ 产业链图没有利润分配标注——画了等于没画
- ❌ 竞争格局只列名字不写趋势（在集中？在被替代？）
- ❌ 公司注册表变成了推荐排序——那是 candidate-screener 的事
- ❌ 投资判断写"长期看好"没有具体 regime
- ❌ 没有产品实物图
- ❌ 没有公司 logo 图
- ❌ 把 teach-in 的内容照搬（物理科普），跳过价值池和投资判断
- ❌ 把 mechanism-insight 的内容照搬（单机制深挖），跳过行业全景
- ❌ 公司注册表超过 30 家——太多了，这不是数据库
- ❌ 不标 exposure 类型（direct vs indirect vs thematic）

## 篇幅基准

- 标准 industry-landscape：2000-3000 字
- 低于 1800 字：产业链地图或竞争格局展开不足
- 超过 3500 字：在替 teach-in 或 mechanism-insight 干活

## 与相邻 skill 的边界

| | teach-in | industry-landscape | mechanism-insight | candidate-screener |
|---|---|---|---|---|
| **入口** | 零基础 | 知道基础概念 | 知道行业术语 | 有公司池 |
| **问题** | 这东西是什么 | 行业值不值得投 | 机制怎么运作 | 先看哪家 |
| **投研判断** | 零 | 行业级 | 机制级 | 公司级 |
| **覆盖** | 全链科普 | 全行业产业链+价值池 | 1-2 个机制 | 公司池排序 |
| **图片** | 实物图 | 公司 logo + 产品实物图 | 产品实物图 | 无 |
| **产物长度** | 6000-8000 字 | 2000-3000 字 | 1000-1800 字 | 500-1500 字 |

> 产品图：每个涉及物理设备/产品的单元必须配 1 张实物图。下载优先级：公司官网 Media Kit → 产品页 hero → web search → [缺图]。下载到 topic 。
