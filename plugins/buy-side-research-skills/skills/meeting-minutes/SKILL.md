---
name: meeting-minutes
description: Turn raw voice-transcribed meeting notes into structured research minutes with corrected names, background context, and RAG-verified claims.
---

# Meeting Minutes

把语音转录的会议纪要转化为结构化、可追溯、可验证的研究笔记。

## 心法

卖方/买方电话会议、产业调研、专家访谈的语音转文字稿有三个致命问题：
1. **名字全错**——公司名、人名、产品名、术语被语音识别乱写
2. **听不懂**——讲者默认听众有背景知识，读者没有
3. **真假难辨**——数字、客户关系、订单数据散落其中，没人验证

本 skill 做三件事：**纠正 → 补背景 → 挂 source**。输出不是"会议记录"，是"会议里有什么值得信、什么需要查、什么可以扔"。

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

## 输入澄清

| 维度 | 含义 | 默认处理 |
|---|---|---|
| **原始文本** | 语音转文字稿 | 原样粘贴 |
| **会议类型** | 卖方/买方/产业调研/专家访谈/公司IR | 未知则标"未注明会议类型" |
| **行业/公司** | 主要讨论的行业和公司 | 从文本推断，未知则标 [需确认] |
| **日期** | 会议日期 | 未知则用当前日期 + [需确认] |

## 执行流程

### Phase 1: 清洗与纠正

**Step 1: 术语纠正**
- 找出现有的 teach-in/quickread 中匹配的行业术语和公司名
- 检查 `references/company-name-alias.yaml` 常见语音识别错误对照表
- 纠正明显的语音识别错误（中英文混合时尤其注意）
- 纠正后必须保留原始文本作为对照

**Step 2: 提取结构化信息**
- 列出所有被提及的公司/产品/客户/项目
- 产出 **正名对照表**——语音转录 → 正名 + 代码

### Phase 2: Claim 提取与分类

**Step 3: 提取所有可验证 claim**

| 分类 | 示例 | 验证优先级 |
|---|---|---|
| **关键 claim**（市场份额、客户关系、订单/收入数据、价格/ASP、产能/产量、并购/合作） | "联讯份额从 15%→40%" "跟华为有深入合作" "Keysight 交期 6 个月" | **强制 Tier 2**（必须跑 Playwright） |
| **一般 claim**（行业趋势、技术路线、竞争格局定性、时间线） | "1.6T 是 Pluggable 极限" "单通道速率提升驱动升级" | Tier 1 即可（WebFetch/WebSearch） |
| **观点/判断**（讲者的投资建议、估值判断、预测） | "罗博特科市值可能超越联讯" "明年收入 100 亿" | 不验证——保留为"讲者观点"，原样标注 |

**Step 4: Claim 验证（RAG Fallback 链）**

复用的优先顺序与降级逻辑：

```
Tier 0: workspace 现有 .cache/ —— teach-in/quickread/actuals → 直接引用
Tier 1: WebSearch → WebFetch(url) → 提取原文
Tier 2: Playwright MCP browser_navigate + browser_snapshot → 提取原文
Tier 3: curl -sL url → 提取正文
Tier 4: [需查证] —— honest degradation
```

**关键 claim**：Tier 2 必须尝试。Tier 1+2 全失败才能标 [需查证]。
**一般 claim**：Tier 1 即可。失败标 [需查证]。
**观点**：不验证，标注"讲者观点"。

### Phase 3: 背景补充

**Step 5: 补充公司和行业背景**

对每个被提及的公司，从以下来源自动拉取背景（不新建，只引用已有缓存和 artifact）：
- `industry/<industry>/companies/<ticker>/.cache/` → actuals, quickread
- `industry/<industry>/` → teach-in, industry-landscape
- 无现有缓存 → WebSearch 补核心信息（≤ 3 句）

**Step 6: 补充技术/行业背景**

如果会议涉及技术概念（如 CPO、PAM4、interposer），从现有 teach-in/mechanism-insight 中引用解释。没有则写 1-2 句补充。

### Phase 4: 输出

按固定结构输出。

## 输出结构

```markdown
# <会议主题> — 会议纪要

> <日期> | 来源：<会议类型> | 主要覆盖：<行业/公司>

## 一、核心结论

4-8 条。每条一句——这场会到底讲了什么新信息。
结论必须区分：**有 source 支撑的** vs **讲者观点，未经独立验证的**。

## 二、正名对照

| 语音转录 | 正名 | 代码 | 备注 |
|---|---|---|---|

## 三、Claim 验证

### 关键 Claim（Tier 2 验证）

| # | Claim | 分类 | Source | 验证方法 | 状态 |
|---|---|---|---|---|---|
| C1 | <原始 claim> | 市场份额/客户/订单/价格 | [S1](url) | Playwright ✅ | 已验证 |
| C2 | <原始 claim> | 客户关系 | — | WebFetch ❌ Playwright ❌ | [需查证] |

### 一般 Claim

| # | Claim | 分类 | Source | 状态 |
|---|---|---|---|---|
| I1 | <原始 claim> | 行业趋势 | [I1](url) | 已验证 |

### 讲者观点（未验证）

- <观点 1>
- <观点 2>

## 四、公司背景补充

| 公司 | 代码 | 主营业务 | 光测试布局 / 会议相关业务 |
|---|---|---|---|

## 五、技术/行业背景

对会议涉及的关键技术概念做 1-3 句解释。引用现有 teach-in/mechanism-insight。

## 六、后续跟进建议

- <具体可验证的下一步问题 1>
- <具体可验证的下一步问题 2>

## Resources

- [S1](url) — source 描述
- [I1](url) — source 描述
```

## Artifact / 保存策略

**Artifact（可见）**——落在公司目录，与其它研究产出并列：

```
industry/<industry>/companies/<ticker>/YYYY-MM-DD-<call-type>_summary.md
```

**Raw 数据（隐藏）**——原始录音和转写稿落在公司 cache：

```
industry/<industry>/companies/<ticker>/.cache/meeting-minutes/
  raw/                              ← 原始录音 .mp3（隐藏）
     YYYY-MM-DD-<call-type>.mp3
  transcripts/                      ← 转写稿 .txt/.json（隐藏）
     YYYY-MM-DD-<call-type>_verbatim.txt
     YYYY-MM-DD-<call-type>_verbatim.json
```

- `<call-type>` = `earnings-call` / `ir-call` / `expert-interview` / `industry-call` / `sellside-call`
- 路径不明 → agent 按 policy baseline §11 自动创建。

## Workflow 联动

| 场景 | 下一步 |
|---|---|
| 会议中某条 claim 需要深度验真伪 | `/information-impact` |
| 会议提到的新公司需要 first pass | `/stock-quickread <ticker>` |
| 会议的产业观点需要验证 | `/mechanism-insight` 或 `/industry-landscape` |
| 会议的判断沉淀为认知 | `/research-journal` |

## 反模式自查

### 纠错类
- ❌ 纠正术语时不留原始文本对照——读者无法判断纠正是否合理
- ❌ 凭猜测纠正公司名——不确定时标 `[待确认]`
- ❌ 把讲者的简称当作独立公司（如"K"→需注明指 Keysight）

### 验证类
- ❌ 关键 claim（市场份额/客户/订单）只跑到 Tier 1 就停
- ❌ 把 WebSearch 摘要当原文——必须打开页面读
- ❌ 编造 source URL
- ❌ 多 source 冲突时不标注——必须标注"source A 说 X，source B 说 Y"

### 输出类
- ❌ 把讲者观点写成事实（"收入 100 亿" vs "讲者认为收入可达 100 亿"）
- ❌ 输出纯流水账——没有优先级、没有可操作建议
- ❌ 没有正名对照表
- ❌ 背景补充凭空编公司介绍——必须引用现有 cache 或 web source
- ❌ 敏感内容（"不要录音"、"未公开"）未标注或公开发布

## 篇幅基准

- 标准纪要：130-260 行（含表格和 source link）
- <100 行：Claim 提取不全或验证不足
- >400 行：在替 `information-impact` 或 `industry-landscape` 干活

## 与相邻 skill 的边界

| | meeting-minutes | information-impact | research-journal |
|---|---|---|---|
| **入口** | 整场会议转录 | 单条信息/传闻 | 已想清楚的认知 |
| **问题** | 这场会讲了什么、哪些能信 | 这条信息靠谱吗 | 我学到了什么 |
| **深度** | 全量浅度——提 claim + 挂 source | 单条深挖——给 verdict | 沉淀 insight |
| **验证** | 关键 claim Tier 2，一般 Tier 1 | 每条跑满 fallback 链 | 不验证 |
| **产物长度** | 2000-4000 字 | 300-700 字 | 100-500 字 |
