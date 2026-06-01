---
name: teach-in
description: Build zero-to-one physical intuition for an unfamiliar industry — why it exists, what's inside, how it's made, and who does what. Zero investment judgment.
---

# Teach-In

Build physical intuition for an unfamiliar industry from absolute zero. No investment judgment. Pure engineering literacy.

## Research Runtime Capsule

- Hook-enforced legality, source boundary, structure floor, and table rendering rules live in workspace hooks and are not restated here.
- Shared runtime/source baseline lives in `skills/_shared/research-policy-baseline.md` and the installed workspace `CLAUDE.md`.
- This skill MUST NOT make any investment judgment. It is a pure engineering-literacy builder. Hand off to `industry-landscape`, `mechanism-insight`, or downstream research skills for investment conclusions.

## 心法

研究员面对一个全新的行业——尤其是半导体、先进制造、能源设备这类工程密集型赛道——最常见的失败模式不是"判断错了"，而是**根本没搞懂东西怎么运作就开始写 thesis**。

`teach-in` 解决的就是这个问题。它不是研究产出，而是**研究前置条件**——在你跑 `industry-landscape`（行业值不值得投）和 `mechanism-insight`（单机制怎么运作）之前，先把最基本的物理直觉建立起来。

本 skill 的失败标准：输出读完后研究员仍然回答不了"这东西长什么样、用什么做的、怎么造出来的、为什么这样设计"。如果输出变成了投资分析报告，也失败。

## AI 的局限

| 局限 | 影响 | Mitigation |
|---|---|---|
| **缺乏空间直觉** | AI 容易把数据中心描述成"很多服务器"，不讲物理空间拓扑 | 强制逐层缩放（大楼→机柜→端口→芯片），配 ASCII 图 |
| **缺乏尺度直觉** | AI 说"微米级精度"但没有类比 | 强制尺度阶梯图，每级标注日常类比（头发丝、芝麻、pizza） |
| **跳过物理约束** | AI 说"用光因为快"，不讲电信号的物理极限 | 强制从物理约束推导设计动机 |
| **材料学缺失** | AI 说"激光器用 InP"但不讲为什么不能用硅 | 半导体/先进制造类必须讲材料选择背后的物理原因 |
| **把科普写成百科** | 输出变成术语词典，不建认知框架 | 每层必须有"为什么"而不只是"是什么" |
| **投研判断泄露** | 忍不住在格局总览表里写"X 公司值得关注" | 格局总览表只列公司名+定位+精度段，不写任何价值判断 |

## 触发场景

- "从零开始讲这个行业"
- "我完全不懂 XX，给我科普"
- "CPO/wafer/die bonding 是什么"
- "光模块干嘛用的"
- "这个行业到底是什么，先给我补课"
- "teach-in"
- "primer"
- "零基础"

## 输入澄清要求

| 维度 | 含义 | 默认假设 |
|---|---|---|
| **对象** | 行业/主题/产品/技术 | 从全行业入手，不聚焦单公司 |
| **深度** | 物理直觉 vs 工程细节 | 默认到"能看懂产业链每一站在干什么"的深度 |
| **行业类型** | 半导体/制造 vs 消费/软件 | 半导体/先进制造必须讲材料+物理约束；消费品牌可跳过材料层 |
| **保存** | 是否落盘 | 默认对话输出；用户要求保存时落 topic artifact |

## 输出结构

### 6 层认知递进

每层回答一个核心问题，按 WHY → WHERE → WHAT → HOW → WHY NOW → WHO 递进。

```
Phase 1: WHY — 为什么需要这个东西
  Layer 1: 物理约束与设计动机
          电为什么不够用 → 光为什么是必然 → 这个东西解决了什么物理问题

Phase 2: WHERE — 长什么样、装在哪
  Layer 2: 空间拓扑（从大楼到端口，逐层缩放）
          数据中心→机柜→服务器→网卡→端口→这个东西→它连接的另一端

Phase 3: WHAT — 里面是什么、用什么做的
  Layer 3: 内部结构 + 材料
          拆开看里面的每个部件 + 每个部件用什么材料做 + 为什么选这个材料

Phase 4: HOW — 怎么做出来的
  Layer 4: 全链制造（从原材料到出货）
          每一站标注：工序名+设备类型+精度要求+全球/中国玩家+良率瓶颈

Phase 5: WHY NOW — 为什么在升级换代
  Layer 5: 代际驱动力
          物理极限推动升级 + 每一代精度/测试/封装怎么跳 + 下一代范式（如 CPO）

Phase 6: WHO — 谁在做（纯事实，不判断）
  Layer 6: 全链公司站位表 + Routing Handoff
          每一站标注：全球玩家/中国玩家/精度天花板
          末尾显式 handoff 到下游 skill
```

### 每层硬要求

| Layer | ASCII 架构图 | 实物图 | 术语表 | 尺度比较 | Source |
|---|---|---|---|---|---|
| 1 | 必须（物理对比） | 不需要 | 不需要 | 必须（数量级对比） | IEEE/物理标准/教材 |
| 2 | 必须（空间缩放） | **必须**（产品实物+安装位置） | 必须（端口/接口标准） | 必须 | 产品页/MSA 规范/数据中心架构 |
| 3 | 必须（爆炸图） | **必须**（拆解实物） | 必须（每个部件） | **必须**（尺度阶梯） | 产品页/teardown/BOM 分析 |
| 4 | 必须（全链流程图） | **必须**（关键设备实物） | 必须（每道工序） | 不需要 | 官网设备页/招股书/行业报告 |
| 5 | 必须（代际对照图） | 不需要 | 必须（新技术名词） | 不需要 | 标准组织/代际 roadmap |
| 6 | 不需要（纯表格） | **必须**（代表公司 logo 图） | 不需要 | 不需要 | 招股书/公司官网/行业报告 |

### 图片要求

**实物图下载优先级**：公司官网 Media Kit → 产品页 hero image → web search 产品图 → 行业代表性图 → `[缺图]`

下载到 `_cache/images/teach-in/`；产物内嵌 `![描述](相对路径)`。

**ASCII 架构图**：我来画。每层至少 1 张。

### Routing Handoff（Layer 6 末尾必填）

```markdown
## 下一步

- 判断行业是否值得投资、产业链利润分配 → `/industry-landscape`
- 深挖某个设备段/机制的运作和价值捕获 → `/mechanism-insight <具体机制>`
- 筛选公司优先级 → `/candidate-screener`
- 快速扫单家公司 → `/stock-quickread <ticker>`
```

## Artifact / 保存策略

写入行业 topic 根：
```
industry/<industry-slug>/YYYY-MM-DD-teach-in-<qualifier>.md
```

路径解析优先复用 `new-session` 的 topic 解析结果。`qualifier` 必填——例如 `optical-module`、`die-bonding-equipment`。

## Workflow 联动

| 场景 | 下一步 |
|---|---|
| 建立了物理直觉，需要判断行业投资价值 | `industry-landscape` |
| 需要深挖某个设备段/机制 | `mechanism-insight` |
| 多个候选公司需要排序 | `candidate-screener` |
| 直接看某家公司 | `stock-quickread` |
| 拆解公司收入/利润 driver | `driver-map` |
| 查市场预期/priced-in gap | `consensus-map` |

## 反模式自查

### 结构类
- ❌ 输出变成了投资分析报告（出现"值得投""估值合理""推荐关注"）
- ❌ 跳过了材料层但这是半导体/先进制造行业
- ❌ 尺度对比只写数字没有日常类比
- ❌ 没有一张 ASCII 架构图——纯文字科普必定失败
- ❌ 6 层中任何一层完全缺失且无说明

### 物理直觉类
- ❌ 只说"用光因为快"，不讲电信号的带宽-距离乘积极限
- ❌ 只说"芯片很小"，不给尺度对比
- ❌ 只说"精度很高"，不讲为什么高精度是物理上必须的

### 图片类
- ❌ 产品实物图用了厂商 logo 而不是设备/产品本体
- ❌ 找不到图就跳过——必须标 `[缺图]`
- ❌ 用了整页网页截图而不是产品 hero image

### Source 类
- ❌ 物理常数无 source
- ❌ 术语解释无 source
- ❌ 公司名单无 source

### Routing 类
- ❌ Layer 6 末尾没有 Routing Handoff
- ❌ 在 teach-in 里做了 industry-landscape 或 mechanism-insight 该做的事

## 篇幅基准

- 标准 teach-in：6000-8000 字（含 ASCII 图和图片链接）
- 低于 5000 字：Layer 3（制造链）或 Layer 4（代际驱动力）展开不足
- 超过 10000 字：在替 `mechanism-insight` 或 `industry-landscape` 干活，应拆分

## 与相邻 skill 的边界

| | teach-in | industry-landscape | mechanism-insight |
|---|---|---|---|
| **入口** | 零基础 | 知道基础概念 | 知道行业术语 |
| **问题** | 这东西是什么 | 行业值不值得投 | 机制怎么运作 |
| **投研判断** | **零** | 行业级 | 机制级 |
| **覆盖** | 全链科普 | 全行业产业链+价值池 | 1-2 个机制深挖 |
| **图片** | 实物图（必须） | 公司 logo + 产品实物图（必须） | 产品实物图（必须） |
| **产物长度** | 6000-8000 字 | 2000-3000 字 | 1000-1800 字 |

- `teach-in` 是 `industry-landscape` 和 `mechanism-insight` 的**前置条件**，不是替代品。
- `teach-in` 不做投资判断；`industry-landscape` 做行业级投资判断；`mechanism-insight` 做机制级价值捕获判断。
- 不要把 teach-in 的 Layer 4（全链制造）当成 mechanism-insight——teach-in 每步只写 100-200 字，mechanism-insight 单段可以写 1000+ 字。
