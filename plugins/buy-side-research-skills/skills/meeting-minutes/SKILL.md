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

**仅当输入为音频时执行。** 输入是文本 → 跳过 Step 0。

检查转录依赖，缺什么装什么：

```bash
# 1. whisper deps（幂等，已装跳过）
pip install requests

# 2. ffmpeg（不可用时自动下载 BtbN portable）
python -c "
import urllib.request, zipfile, io, shutil, os, tempfile
from pathlib import Path
ff = Path('.scripts/shared/ffmpeg.exe')
if ff.exists(): exit()
print('Downloading ffmpeg...')
url = 'https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip'
with urllib.request.urlopen(url) as r: data = r.read()
tmp = Path(tempfile.gettempdir()) / 'ffmpeg_install'
shutil.rmtree(tmp, ignore_errors=True); tmp.mkdir()
with zipfile.ZipFile(io.BytesIO(data)) as z: z.extractall(tmp)
inner = next(tmp.iterdir())
shutil.copy2(inner / 'bin' / 'ffmpeg.exe', ff)
shutil.rmtree(tmp, ignore_errors=True)
print('ffmpeg ready')
"
```

**whisper API key**：从环境变量 `WHISPER_API_KEY`、`WHISPER_API_BASE`、`WHISPER_MODEL` 读取。未配置时提示用户提供。

### Step 1: 音频转写（仅当输入为音频）

```
audio .mp3/.wav/.m4a
  ↓
① Language detection + confirmation：先根据文件名/来源路径/用户消息语言推断，然后向用户确认 "检测到音频语言为 X，用 X 转录？" 确认后再跑。不给默认、不过自己猜
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

### Step 1.5: Workspace 感知（可选，在 workspace 内时执行）

```bash
python .scripts/shared/workspace-locate.py <公司名或行业关键词>
```

- 命中已有公司目录 → artifact 存到该公司目录下
- 命中已有行业 → artifact 存到行业 `panorama/meeting-minutes/`
- 命中已研究过的背景 → 注入到 Step 3 briefing
- 未命中 → 当前目录输出

### Step 2: 共享预处理 → scratchpad

产物：`_scratchpad.json`，存入 `.cache/meeting-minutes/`。语言中立（key 用英文，values 保留原语言）。

**① 术语纠正**：找出现有 teach-in/quickread 匹配术语，纠正明显错误。**所有 fact 声明写入最终文件前，至少走一次 WebSearch 核实**——不留死角。核实范围：
- 公司：名/代码/上市状态/行业归类/地域分布/股权关系
- 产品：名/技术路线/迭代节奏/市场定位/竞争格局
- 技术：术语解释/标准/路线图/物理极限
- 财务：数字/增长率/margin 区间/与实际披露的一致性
- 行业：趋势/格局/市场份额/上下游关系
- 宏观：政策/地缘/贸易限制
- 易混淆：首字母缩写（CPU/CPO/GPU）、同音/近音词

保留原始文本供 appendix 正名对照使用。不确定标 `[待确认]`。

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

**⑤ 验证日志（verification_log）——强制 gate**

scratchpad 必须包含 `verification_log` 字段，每条 fact 挂一个 web search URL。Step 3 入口检查：`verification_log` 为空或覆盖率 < 实体的 80% → 退回 Step 2 补查。不凑齐不进 Step 3。

格式：`{"claim": "盛合晶微已上市", "source_url": "https://...", "verified": true}`

### Step 3: 按 template 输出

**模板数量：2 个。** briefing + qa。每个模板出 ZH 和（可选）EN 两个版本。internal 的组件作为 appendix 嵌入。

> 文件命名按 CLAUDE.md §3.2：`YYYYMMDD-[skill]-[Company-Name]_<variant>.md`

**语言风格**——以下一律禁止，违者重写：

| # | 禁止 | 例 |
|---|---|---|
| ① | 叙事句开头 | "管理层开场即给出""分析师花了几分钟做行业普及" |
| ② | 英文引号原文 | "the company is actually older than the United States" |
| ③ | 独立"关键点"段落 | pros 末尾单独一段"关键点：..." |
| ④ | 孤立的跨公司判断 | "比 DPC Holdings 温和得多" |
| ⑤ | 替读者下判断 | "这是投资中最关键的变量之一""值得高度关注" |
| ⑥ | 修辞比喻 | "皇冠上的明珠""真正的护城河""掌控自己的命运""像做蛋糕杯一样" |
| ⑦ | 口语化/评价性措辞 | "deal 很热""签了就是好事""小玩家""至今仍很差" |
| ⑧ | 对会议本身行为的元描述 | "分析师追问了一个关键问题""分析师用了一个珠宝比喻""分析师举例" |
| ⑨ | 情绪化/画面化措辞 | "比美国还老""侮辱性报价""最极端证明""艰难持有赶上好时机变现" |
| ⑩ | 程度副词和编辑定性 | "远超""近乎垄断""必然很低""极高的杠杆率压缩了所有" |

可保留：分析师/讲者观点的中性归因（"分析师的判断是""管理层认为"）、买方提问的上下文。

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

## Listed Companies Mentioned

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
- ❌ verification_log 为空或覆盖率不足 → 退回补查
- ❌ fact 声明无 web search URL 支撑就写入最终文件

### 输出类（语言风格）
- ❌ 叙事句开头——"管理层/分析师 + 动词"作为段落起手式
- ❌ 英文引号原文——即使贴原话也不保留
- ❌ 独立"关键点"段落
- ❌ 孤立的跨公司比较判断
- ❌ 替读者下判断（"这是最关键的""值得高度关注"）
- ❌ 修辞比喻（"皇冠明珠""护城河""掌控命运"等）
- ❌ 口语化/评价性措辞
- ❌ 对会议行为的元描述（"分析师花了几分钟""做了一个比喻""举例"）
- ❌ 情绪化/画面化措辞（"比美国还老""侮辱性""最极端证明"）
- ❌ 程度副词和编辑定性（"远超""近乎垄断""必然很低"）
- ❌ 背景补充凭空编公司介绍
- ❌ 正文字段挂 `[需查证]` / `[讲者观点]` 标签
- ❌ 敏感内容未经标注发布
