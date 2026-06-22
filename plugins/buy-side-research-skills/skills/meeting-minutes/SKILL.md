---
name: meeting-minutes
description: 把音频/转录稿转化为结构化研究输出——briefing（对外邮件）和 qa（对外问答实录），双语可选，附录分层便于按需剪裁。
---

# Meeting Minutes

把音频或转录稿转化为结构化研究输出。两个模板：`briefing`（对外邮件）+ `qa`（对外问答实录）。内部使用组件（claim 验证、正名对照、后续跟进）作为 appendix 放在文件后半，发邮件时不粘贴即可。

中文版默认输出中文，可选 `--en` 出英文版，可选 `--qa` 单独出 Q&A。

## 原则

- **内容深度完整优先，不设篇幅上限。**
- **事实直接陈述，不铺叙事层**——不写"管理层开场即给出""这是整场 call 中最坦率的问题"这类句式。
- **英文原文全部翻译**——不保留英文引号句，融入中文正文。
- **正文不挂验证标签**——`[需查证]`、`[讲者观点]` 等仅出现在 appendix 的 Claim 验证区。

## 心法

语音转文字稿有三个致命问题：
1. **名字全错**——公司名、人名、产品名、术语被语音识别乱写
2. **听不懂**——讲者默认听众有背景知识，读者没有
3. **真假难辨**——数字、客户关系、订单数据散落其中，没人验证

本 skill 做三件事：**纠正 → 补背景 → 挂 source**。

## Research Runtime Capsule

- Hook-enforced rules live in workspace hooks.
- Shared runtime baseline: `.references/policy/research-policy-baseline.md` + workspace `CLAUDE.md`.
- **数据管道**：不调用 financial-data。优先复用 workspace 现有 `.cache/` 和 teach-in/quickread 的背景知识。
- **RAG 链**：WebSearch→WebFetch→Playwright→curl→[需查证]。关键 claim 强制 Tier 2，一般 claim Tier 1 即可。
- **转录环境**：whisper API key + endpoint + 默认 model 在 `init-workspace` 中配置，本 skill 直接调用 `.scripts/shared/transcribe.py`。
- Sub-agent outputs: evidence_cards_only; main agent synthesizes, deduplicates, scores, tiers, and ranks.

## 触发场景

- "帮我整理这个会议纪要"
- "这段录音转文字帮我纠错"
- "这个 call 里有什么值得查的"
- "把这段纪要结构化"
- 粘贴语音转文字稿 + 要求结构化
- 直接给音频文件路径

## 输入澄清

| 维度 | 含义 | 默认处理 |
|---|---|---|
| **原始文本 / 音频** | 语音转文字稿 或 mp3/m4a/wav | 音频 → 先转写（Step 1） |
| **会议类型** | 卖方/买方/产业调研/专家访谈/公司IR | 未知标"未注明会议类型" |
| **行业/公司** | 主要讨论的行业和公司 | 从文本推断，未知标 [需确认] |
| **日期** | 会议日期 | 未知用当前日期 + [需确认] |
| **输出语言** | 默认中文，可选 `--en` 出英文版 | 中文 |
| **输出模式** | 默认 --briefing，可选 --qa 出 Q&A、--all 两个都出 | briefing |

---

## 执行流程

### Step 0: 环境检查

转录依赖 `.scripts/shared/transcribe.py` + `.scripts/shared/ffmpeg.exe`。
若不存在 → 提示运行 `/init-workspace` 补全。

### Step 1: 音频转写（仅当输入为音频）

```
audio .mp3/.wav/.m4a
  ↓
① 强制问 language（en/zh/ja/ko/...），不给默认
  ↓
② Bitrate check：<32kbps → block，提示提供 ≥64kbps 版本
  ↓
③ Split（>10min 触发）：ffmpeg 切 ≤540s chunks
  ↓
④ Transcribe：whisper-large-v3-turbo（默认），verbose_json + timestamp_granularities[]=segment
  ↓
⑤ Merge：sort segments by start，shift chunk timestamps，去相邻重叠
  ↓
⑥ 输出 _verbatim.txt + _verbatim.json → 存入 .cache/meeting-minutes/transcripts/
```

Step 1 边界：不改文本、不分 speaker、不加标注。纯原材料。

### Step 2: 共享预处理 → scratchpad

产物：`_scratchpad.json`，存入 `.cache/meeting-minutes/`。语言中立（key 用英文，values 保留原语言）。

**① 术语纠正**：找出现有 teach-in/quickread 匹配术语，纠正明显错误。保留原始文本供 appendix 正名对照使用。不确定标 `[待确认]`。

**② 实体提取**：公司/产品/客户/项目/数字。

**③ 背景注入**：从现有 cache/teach-in/mechanism-insight 引用背景（≤3 句），融入正文叙事。无缓存 → WebSearch 补核心信息（≤3 句）。

**④ 逐段读取、累积 scratchpad，确认到底**
- Transcript 可能很长（50min+、600+ segments）。**不允许扫几段就开写最终文件。**
- 读取协议：
  ```
  Read chunk 1 (L1–200)   → 提取实体、数字、claim、topic → 写入 scratchpad
  Read chunk 2 (L201–400) → 同上，追加
  Read chunk 3 (L401–600) → 同上，追加
  Read chunk N (L601–end) → 同上，确认末尾是 Q&A 收尾 / 道谢 / 结束语
  ```
- **验证到底**：最后一个 Read 的内容必须与开头无重复（不是循环 hallucination），且语义上是结尾。
- scratchpad 凑齐后才进 Step 3。不读到底绝不开写 briefing / qa。

### Step 3: 按 template 输出

**模板数量：2 个。** briefing + qa。每个模板出 ZH 和（可选）EN 两个版本。internal 的组件作为 appendix 嵌入。

**语言风格**：
- 事实直接陈述，不写"管理层表示/坦言/强调/承认"开头的叙事句
- 英文原文全部翻译融入正文，不保留 `"English quote"` 格式
- 不设"关键点"独立段落，实质性分析融入 prose 末尾
- 跨公司对比需有上下文和逻辑支撑，不抛一句孤立判断

---

## 输出结构

### briefing

```
# <会议主题>

> <日期> | <会议类型> | <行业/公司>

## 1. <Topic 1>

<prose 叙事，融入背景>

## 2. <Topic 2>

<prose 叙事>

...
## N. <Topic N>

---

## Company Profile                                         ← appendix 起点

仅在公司级 meeting 出现（earnings call / IR / expert call on a single company）。行业级跳过，直接进 Listed Companies。

核心维度（必填）：

| Dimension | Detail |
|---|---|
| Company | |
| Ticker | |
| Business | <一句话> |
| Key Platforms / Products | |
| End Markets | |

可选维度（有则填，无则省略）：

| Dimension | Detail |
|---|---|
| Revenue & Growth | |
| Margin Profile | |
| Key Customers | |
| Key Suppliers | |
| Competitive Position | |

有 stock-quickread → 直接引用，不重新查。

## Industry Context

有 teach-in / industry-landscape → 直接引用，不重新查。

## Listed Companies

纪要中提到的所有上市公司（不含主体公司 Profile）。业务描述详细，1-2 句，含关键产品或市场地位。最后一列按会议上下文命名。

| Company | Ticker | Business | <Context Column> |
|---|---|---|---|
| 联讯仪器 | 688808 CH | 光通信测试仪器国产 #1：采样示波器、误码仪、光功率计 | 全球唯二量产 1.6T 采样示波器 |

第四列命名按会议主题：如"光测试/CPO 布局""航空供应链定位""AI 服务器相关业务"等。

## Technical / Industry Background

对会议涉及的关键技术概念或行业背景做解释。有机制洞察类 artifact → 引用。

## Claim Verification

### Key Claims (Tier 2)

| # | Claim | Category | Source | Status |
|---|---|---|---|---|
| C1 | | | | |

### General Claims

| # | Claim | Category | Source | Status |
|---|---|---|---|---|

### Speaker Opinions (Unverified)

- <opinion>

## Name Corrections

| Transcript | Corrected | Ticker | Notes |
|---|---|---|---|

## Follow-Up

- <actionable item>

## Resources

- `.cache/meeting-minutes/...`
```

appendix 从上到下越来越内部：
- `Company Profile` + `Listed Companies` + `Industry Context` + `Technical Background`：外发可保留
- `Claim Verification`：内用，含 `[需查证]` 标签
- `Name Corrections`：内用
- `Follow-Up`：内用
- `Resources`：内用，含本地路径

发邮件时从 `Claim Verification` 起不粘贴。

### qa

```
# <会议主题> — Q&A

> <日期> | <会议类型>

**Q1: <精简问题>**
A: <精简回答，去 filler，保留全部数据>

**Q2: ...**

---

## Company Profile
...

## Claim Verification
...
```

appendix 分层规则同 briefing。

---

## Artifact / 保存策略

```
.cache/meeting-minutes/                        ← 全部隐藏
├── raw/YYYYY-MM-DD-<call>.mp3                 ← Step 0: 原始音频
├── transcripts/YYYY-MM-DD-<call>_verbatim.txt  ← Step 1: 纯转录
├── transcripts/YYYY-MM-DD-<call>_verbatim.json
└── YYYY-MM-DD-<call>_scratchpad.json          ← Step 2: 预处理中间件

公司级 artifact（露出）：
  companies/<ticker>/
  ├── YYYY-MM-DD-<call>_briefing_zh.md          ← 中文 briefing
  ├── YYYY-MM-DD-<call>_briefing_en.md          ← 英文 briefing（可选）
  ├── YYYY-MM-DD-<call>_qa_zh.md                ← 中文 qa
  └── YYYY-MM-DD-<call>_qa_en.md                ← 英文 qa（可选）

行业级（行业 panel / sell-side call）：
  industry/<slug>/panorama/meeting-minutes/
  ├── YYYY-MM-DD-<topic>_briefing_zh.md
  └── YYYY-MM-DD-<topic>_qa_zh.md
```

- `_briefing_en.md` 和 `_qa_en.md` 仅在用户要求时输出。
- 路径不明 → agent 按 workspace structure 自动创建。

## Workflow 联动

| 场景 | 下一步 |
|---|---|
| 某条 claim 需要深度验真伪 | `/information-impact` |
| 新公司需要 first pass | `/stock-quickread <ticker>` |
| 产业观点需要验证 | `/mechanism-insight` 或 `/industry-landscape` |
| 判断沉淀为认知 | `/research-journal` |

## 反模式自查

### 认读类
- ❌ 没读完完整 transcript 就开始输出——必须读到末尾再写
- ❌ 凭猜测纠正公司名——不确定标 `[待确认]`
- ❌ 把讲者简称当作独立公司

### 验证类
- ❌ 关键 claim 只跑到 Tier 1 就停
- ❌ 把 WebSearch 摘要当原文——必须打开页面读
- ❌ 编造 source URL

### 输出类
- ❌ 出现英文引号原文——全部翻译融入中文
- ❌ 出现"管理层开场/坦言/强调"叙事句——事实直接陈述
- ❌ 独立"关键点"段落——融入 prose
- ❌ 抛孤立判断句的跨公司对比（"X 比 Y 温和得多"无上下文支撑）
- ❌ 背景补充凭空编公司介绍
- ❌ 正文字段挂 `[需查证]` / `[讲者观点]` 标签——仅 appendix 使用
- ❌ 敏感内容（"不要录音"、"未公开"）未经标注发布
