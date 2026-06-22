---
name: meeting-minutes
description: Turn voice-transcribed meeting notes into structured research minutes — briefing (external), internal, or Q&A — with corrected names, background context, and RAG-verified claims.
---

# Meeting Minutes

把语音/转录稿转化为结构化研究输出。三个模板：`briefing`（对外邮件）、`internal`（内用深度）、`qa`（对外问答实录）。

## 原则

**内容深度完整优先，不设篇幅上限。** 精炼但不牺牲信息量。

## 心法

卖方/买方电话会议、产业调研、专家访谈的语音转文字稿有三个致命问题：
1. **名字全错**——公司名、人名、产品名、术语被语音识别乱写
2. **听不懂**——讲者默认听众有背景知识，读者没有
3. **真假难辨**——数字、客户关系、订单数据散落其中，没人验证

本 skill 做三件事：**纠正 → 补背景 → 挂 source**。

失败标准：输出读完后读者仍然不知道哪些 claim 有 source、哪些是讲者一家之言、哪些公司被提到。

## Research Runtime Capsule

- Hook-enforced rules (source boundary, structure floor, table render) live in workspace hooks.
- Shared runtime baseline: workspace `.references/policy/research-policy-baseline.md` + workspace `CLAUDE.md`.
- **数据管道**：不调用 financial-data。优先复用 workspace 现有 `.cache/` 和 teach-in/quickread 的背景知识。
- **RAG 链**：复用现有 Fallback——WebSearch→WebFetch→Playwright→curl→[需查证]。关键 claim 强制 Tier 2，一般 claim Tier 1 即可。
- Sub-agent outputs: evidence_cards_only; main agent synthesizes, deduplicates, scores, tiers, and ranks.

## 触发场景

- "帮我整理这个会议纪要"
- "这段录音转文字帮我纠错"
- "这个 call 里有什么值得查的"
- "把这段纪要结构化"
- 粘贴一段语音转文字稿 + 要求结构化
- 直接给音频文件路径

## 输入澄清

| 维度 | 含义 | 默认处理 |
|---|---|---|
| **原始文本 / 音频** | 语音转文字稿 或 mp3/m4a/wav 文件 | 音频 → 先转写（见 Step 1） |
| **会议类型** | 卖方/买方/产业调研/专家访谈/公司IR | 未知则标"未注明会议类型" |
| **行业/公司** | 主要讨论的行业和公司 | 从文本推断，未知则标 [需确认] |
| **日期** | 会议日期 | 未知则用当前日期 + [需确认] |
| **输出模式** | --briefing / --internal / --qa / --all | 默认 --all（三个都出） |

---

## 执行流程

### Step 1: 音频转写（仅当输入为音频文件时）

```
音频 .mp3/.wav/.m4a
  ↓
① 强制问 language（en/zh/ja/ko/...），不给默认
  ↓
② Bitrate check：<32kbps → block，提示提供 ≥64kbps 版本
  ↓
③ Split（>10min 触发）：ffmpeg 切 ≤540s chunks
  ↓
④ Transcribe：whisper-large-v3-turbo，verbose_json + timestamp_granularities[]=segment
  ↓
⑤ Merge：sort segments by start，shift chunk timestamps，去相邻重叠
  ↓
⑥ 输出 _verbatim.txt + _verbatim.json → 存入 .cache/meeting-minutes/transcripts/
```

Step 1 边界：不改文本、不分 speaker、不加标注。纯原材料。

工具：`.scripts/shared/transcribe.py` + `.scripts/shared/ffmpeg.exe`

### Step 2: 共享预处理

**① 术语纠正**
- 找出现有的 teach-in/quickread 中匹配的行业术语和公司名
- 纠正明显的语音识别错误
- 纠正后保留原始文本（供 internal 的 `五、正名对照` 使用）
- 不确定时标 `[待确认]`

**② 实体提取**
- 列出所有被提及的公司/产品/客户/项目/数字

**③ 背景注入**
- 对每个被提及的公司/技术概念，从现有 cache/teach-in/mechanism-insight 引用背景（≤3 句），融入正文叙事
- 无现有缓存 → WebSearch 补核心信息（≤3 句）

### Step 3: 按 mode 输出

#### briefing（对外邮件）

Topic 编号 → prose 叙事。精炼但不限篇幅。
- **不挂**验证标签、无表格、无正名对照
- 可保留讲者观点 vs 事实的语气区别（"管理层认为" / "据 S1 披露"），但不显式标注

```
# <会议主题>

> <日期> | <会议类型> | <行业/公司>

## 1. <Topic 1>

<prose 叙事，融入背景>

## 2. <Topic 2>

<prose 叙事>

...
```

#### internal（内用深度）

按五段结构，内容完整。验证状态、来源、不确定性全部保留。

```
# <会议主题> — 内部纪要

> <日期> | <会议类型> | <行业/公司>

## 一、核心结论

4-8 条。每条一句，区分有 source 支撑 vs 讲者观点。

## 二、Claim 验证

### 关键 Claim（Tier 2 验证）

| # | Claim | 分类 | Source | 验证方法 | 状态 |
|---|---|---|---|---|---|
| C1 | | 市场份额/客户/订单/价格 | | Playwright ✅ | 已验证 |
| C2 | | | | | [需查证] |

### 一般 Claim

| # | Claim | 分类 | Source | 状态 |
|---|---|---|---|---|---|
| I1 | | | | |

### 讲者观点（未验证）

- <观点>

## 三、背景补充

融入正文叙事，不取表格。引用现有 cache/teach-in。

## 四、后续跟进

- <具体可验证的下一步>

## 五、正名对照（放最后）

| 语音转录 | 正名 | 代码 | 备注 |
|---|---|---|---|

## Resources
```

#### qa（对外问答实录）

Q1: / A1: 精简，去 filler（uh/um/yeah），保留全部数据。

```
# <会议主题> — Q&A

> <日期> | <会议类型>

Q1: <问题精简>
A1: <回答精简，保留数字>

Q2: <问题精简>
A2: <回答精简>
```

---

## Artifact / 保存策略

```
行业级（行业 panel / sell-side call）：
  industry/<slug>/panorama/meeting-minutes/
  ├── YYYY-MM-DD-<topic>_briefing.md
  ├── YYYY-MM-DD-<topic>_internal.md
  └── YYYY-MM-DD-<topic>_qa.md

公司级（earnings call / IR / expert interview）：
  companies/<ticker>/
  ├── .cache/meeting-minutes/
  │   ├── raw/YYYY-MM-DD-<call>.mp3
  │   └── transcripts/YYYY-MM-DD-<call>_verbatim.{txt,json}
  ├── YYYY-MM-DD-<call>_briefing.md
  ├── YYYY-MM-DD-<call>_internal.md
  └── YYYY-MM-DD-<call>_qa.md
```

- 路径不明 → agent 按 workspace structure 自动创建。

## Workflow 联动

| 场景 | 下一步 |
|---|---|
| 会议中某条 claim 需要深度验真伪 | `/information-impact` |
| 会议提到的新公司需要 first pass | `/stock-quickread <ticker>` |
| 会议的产业观点需要验证 | `/mechanism-insight` 或 `/industry-landscape` |
| 会议的判断沉淀为认知 | `/research-journal` |

## 反模式自查

### 纠错类
- ❌ 纠正术语时不留原始文本对照——internal 必须有正名对照表
- ❌ 凭猜测纠正公司名——不确定时标 `[待确认]`
- ❌ 把讲者的简称当作独立公司（如"K"→需注明指 Keysight）

### 验证类
- ❌ 关键 claim（市场份额/客户/订单）只跑到 Tier 1 就停
- ❌ 把 WebSearch 摘要当原文——必须打开页面读
- ❌ 编造 source URL
- ❌ 多 source 冲突时不标注——必须标注"source A 说 X，source B 说 Y"

### 输出类
- ❌ 把讲者观点写成事实
- ❌ briefing 挂验证标签
- ❌ internal 缺正名对照
- ❌ 背景补充凭空编公司介绍——必须引用现有 cache 或 web source
- ❌ 敏感内容（"不要录音"、"未公开"）未标注或公开发布

## 与相邻 skill 的边界

| | meeting-minutes | information-impact | research-journal |
|---|---|---|---|
| **入口** | 整场会议转录 | 单条信息/传闻 | 已想清楚的认知 |
| **问题** | 这场会讲了什么、哪些能信 | 这条信息靠谱吗 | 我学到了什么 |
| **深度** | 全量浅度——提 claim + 挂 source | 单条深挖——给 verdict | 沉淀 insight |
| **验证** | 关键 claim Tier 2，一般 Tier 1 | 每条跑满 fallback 链 | 不验证 |
