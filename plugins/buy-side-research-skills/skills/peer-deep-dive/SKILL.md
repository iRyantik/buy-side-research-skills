---
name: peer-deep-dive
description: Compare companies in one industry with sourced KPI matrices and research ranking.
---

## Research Runtime Capsule

本 skill 独立运行时也必须遵守以下 runtime 规则；详细维护基线在 `skills/_shared/research-policy-baseline.md`，但运行时不能假设会自动读取该文件，因此本 skill 自身必须携带可执行的规则摘要。

- 默认用中文自然语言输出；ticker、公司名、产品名、source title、URL、YAML / JSON key、财务和行业术语可以保留英文。所有分析必须结论先行，不要写 "Great question"、"你说得对"、"It depends" 这类空铺垫。
- 非中文 / 英文公司披露项按最小必要原则保留源语言锚点：首次出现的官方 segment、product、KPI、project、program、披露 bucket、订单 / backlog 分类、监管 / 合同术语、客户 / 终端市场名、source title，以及任何后续可能回源检索的词，写成 `源语言（中文译名）`；后续默认用中文短名，除非同一表内存在多个易混淆原文 bucket。
- 全中文即可：普通分析句、takeaway、通用会计 / 商业概念、已在前文定义过的重复项、非关键 source wording。管理层原话只有在措辞本身影响判断时保留短原文；否则用中文概述并贴 source。
- 表格优先用 `Ev` / `证据` 短列承载 inline clickable short source anchor 和例外状态。默认 `[S1](link)`；例外状态追加 `:REV` / `:GAP` / `:ND` / `:EST` / `:CON`，干净值不写 `OK`；完整 source metadata 不在表后展开，每篇 artifact 文末统一写 `## Resources`，用 `- [S1](link) = source type | source title/provider | as-of/filed | page/location | fallback reason` 保持可追溯。
- 每一条事实声明、数字、引语必须有 source link 或明确 source 描述。财务数字、估值、市场数据、KPI、运营数据、行业数据、管理层引语、专家访谈、监管表态、第三方判断、历史事件和时间点必须有 source。研究员判断本身不需要 source，但判断依据的事实必须有 source。
- 能用一手原始 source 就不用二手；多个 source 冲突时必须标注冲突，不要挑一个顺手的用。不确定时直接说不确定，并标 `[需查证]` 或 `[来源待补]`；不确定 URL 是否存在时写 `[link 待补]`。
- 绝对不能编造 URL、页码、引语、数字、人名、日期。
- Source locality rule: use source quality first (`workspace-local > primary public > reputable provider/news > internet market source`), then prefer `home-market / local-language source` within the same quality tier. News / event evidence should prefer local-language sources for the issuer, main listing venue, regulator, or operating country; market data should prefer the primary listing / trading-market source. Do not maintain market-specific provider whitelists in skill rules; if using a global, English, or non-home-market fallback, state the fallback reason in the final `## Resources` list.
- Sub-Agent Evidence Protocol：本 skill 默认必须启动 sub-agent / delegate worker 并行查 source；sub-agent 只能返回 evidence card，不得写最终结论、ranking、thesis、valuation 或 model treatment；主 agent 必须完成 URL/claim spot check、source conflict handling 和最终 synthesis。若当前 host / runner 真的无法 spawn，必须在 artifact 中明示 `sub-agent unavailable`、原因和 coverage caveat。Runtime cap: no per-skill sub-agent count limit; max 6-8 active sub-agents globally; parallel within one skill but serial across skills; close sub-agents immediately after evidence cards or QA notes return.
- 不要写 sell-side 流水账：公司历史、管理层履历、行业科普、通用 SWOT、无数据定性、表格复述。数据表必须有 takeaway，且 takeaway 必须给结构性洞察，不要复读表格。
- 主动执行 Senior Analyst Radar：当疑点可能改变业务实质理解、model driver、市场预期 / consensus framing、peer group / 估值框架或下一步研究优先级时，直接点破。
- 遇到行业机制、工程原理、设备链条、工艺流程、术语或 know-how gap，先 handoff / 触发 `mechanism-map`；遇到 revenue / margin / backlog / price-volume-mix driver、披露口径异常或 model-driver gap，先 handoff / 触发 `driver-map`。
- 研究启动时先检查 `topics/<topic-slug>/_cache/` 是否存在已 ingest 的材料；如有，优先引用 cache 中的 source-tracked markdown。若是单公司研究，同时检查相关 `topics/company/<company-slug>/_cache/financial-data/financial-data-summary.md`；需要审计或机器输入时再进入 `internal/evidence-pack.json`、`internal/actuals-resolved.json`、`internal/source-map.json`。

# Peer Deep Dive

产出**不是** N 份独立的公司分析拼在一起。如果你写出来的内容是 N 个 stock-quickread 串联，就是失败的。

## 心法

横向研究真正的价值，是**纵向研究做不到**的事：
- 抽出 N 家共享的行业坐标系，避免重复劳动
- 发现 N 家管理层 commentary 互相打脸的地方（矛盾 = alpha 起点）
- 看清估值 spread 和基本面 spread 是否匹配（错配 = 机会或陷阱）
- 排序：先研究谁、给多少深度、哪些适合配对看

如果做完只输出"以下是这几家公司的并排对比"，等于没做横向研究——你只是节约了打字时间。

**核心检验**：把"行业 lens"和"cross-cut insight"两节抽掉，剩下的内容是不是 N 份精简 quickread？如果是，重写。

## Source 政策

- Claim-Level Source Contract：正文里的每个 truth-like claim（peer KPI、valuation、liquidity、business model、segment / disclosure comparison）都必须紧跟 inline clickable short anchor，如 `[S1](link)` / `[I1](link)`，不只横向矩阵 `Ev` 要挂证据。
- No Orphan Truth Claim：输出前检查 peer matrix 外的正文事实、ranking 依据、source conflict 和 market data claim 是否都有 anchor；没有就补 source、降级为 gap，或删除。

全局 source / anti-hallucination 规则已内嵌在 `Research Runtime Capsule`。本节只补充 peer-deep-dive-specific 要求。

快速提醒：
- 横向矩阵每行 / 每个关键数据点必须给 Source；没有可靠 source 就标记 `[需查证]` / `[来源待补]`。
- 横向矩阵里的 market / valuation / liquidity 列允许在本地缺失时补公开网页 market data，但必须显式标 `internet source`、provider、as-of、URL / source location，并在 `Ev` 使用 `[I1](link)`。
- 经营、KPI、机制、客户 / 项目、company-disclosed fact 仍保持原有 source discipline，不因 fallback 放宽。
- 若首次使用 internet fallback，正文加一句：`以下标记为 internet source 的字段为本地 cache 缺失后的公开网页 fallback，不等同于公司披露原文。`
- Cross-cut 矛盾信号必须给两边的具体引语和定位；sub-agent URL 抽查匹配后才可使用。
- 跨公司比较必须确认口径可比；不确定 URL 是否存在时写 `[link 待补]`，不得编造。

- Locality-aware market data: valuation, liquidity, price action, borrow, FX, consensus, and cross-market fields should prefer the primary listing / trading-market source at the same quality tier; global or non-home-market fallback requires a reason in the final `## Resources` list.
## Parallel Evidence Pass

本 skill 默认必须按公司或 source bucket 启动 sub-agent / delegate worker 并行收集 evidence；只能让 sub-agent 产出 evidence card：

- 每个 sub-agent 负责 1 家公司或 1 个明确 source bucket（filing、IR deck、earnings call、KPI table、recent event），返回 claim、source title、URL / source location、quote / metric、as-of、confidence、caveat、suggested use。
- sub-agent 不得写 peer ranking、industry lens、cross-cut insight、resource allocation 或最终结论；这些必须由主 agent 汇总完成。
- 主 agent 必须抽查至少 2-3 个关键 URL / claim，统一口径后再写矩阵、differential profile 和 ranking。
- 如果 sub-agent evidence 之间冲突，主 agent 必须标注冲突并说明暂用口径；不能让 sub-agent 自行裁决。
- 如果当前 host / runner 真的无法 spawn，主 agent 必须在 Evidence Protocol Notes 中写明 `sub-agent unavailable`、失败原因、实际单线程取证范围和 source coverage caveat；不能把未并行执行伪装成已完成并行取证。

## 输出结构（严格按这个走）

### 0. 任务定义

研究员先明确：
- **公司列表**：3-8 家（数量超过 8，先自由对话预筛，或按子行业 / business model 分子组；当前发布版不包含独立 `peer-scan` skill）
- **研究目的**：建核心仓 / 找 hedge / 找 pair trade / 主题暴露 / 其他（这决定研究深度的分配）
- **时间预算**：用于第 5 节的资源分配

如果用户没说研究目的，主动问一句——目的不同会导致 cross-cut 关注重点和资源分配完全不同。

### 0A. 横向比较 Preflight（先判断能不能比）

横向比较之前先确认这些公司真的能放进同一张机制 / driver / KPI 坐标系。不能因为 tickers 同行业就硬做矩阵。

| 检查项 | 通过标准 | 不通过时动作 |
|---|---|---|
| Mechanism / value-capture 可比 | N 家公司处在同一机制链条，或已明确各自在哪个环节捕获价值 | 先 handoff 到 `mechanism-map` 统一 mechanism / value-capture |
| KPI 定义可比 | 核心 KPI 定义一致，或差异能 footnote / normalize | 先 handoff 到 `driver-map` 拆 KPI / disclosure 口径 |
| Driver 口径可比 | revenue、margin、backlog、price-volume-mix 能映射到可比 driver | 先 handoff 到 `driver-map` |
| Peer group 合理 | business model、商业化阶段、周期性和政策暴露没有大到让 cross-cut 失真 | 先重分组；机制不清时用 `mechanism-map` |

若任一项不通过，不要硬做 ranking / matrix。先输出最小 handoff block：

```markdown
## Primitive Handoff Required

- Blocker: [mechanism / KPI / driver / peer group 哪一项不可比]
- Why it blocks peer-deep-dive: [它会污染行业 lens / 横向矩阵 / ranking 的哪一节]
- Handoff: `mechanism-map` / `driver-map`
- Inputs needed: [需要补的 filing / call / KPI definition / mechanism source]
```


### 结论先行（放在行业 Lens 之前，~200-400 字）

**这是给 PM 看的 — 这个版块必须足够完整，让读者不需要翻后面的第 1-7 节就能做出方向性判断。** 后面各节是支撑论据。

必含：

**一句话总判断**（1 句）
- 这批公司作为一个 group，当前阶段的整体方向性判断
- 例：「韩国军工板块处于出口 super-cycle，但五家之间基本面 spread 远大于估值 spread — Rotem 最便宜却最赚钱，Hanwha Systems 最贵却亏损扩大」

**优先级排名（微型表）**
| 公司 | 方向 | 一句话理由 |
|---|---|---|
| X | 多 | PER 最低 + ROIC 最高 + 隐藏资产被市场忽略 |
| Y | 多 | 规模最大 + moat 最清晰，但需等回调 entry |
| ... | ... | ... |

注意：这张表和后面第 5 节不冲突 — 这里是结论高度浓缩（每家公司仅一行），第 5 节才是完整排序+时间分配+研究深度

**2-3 个最核心的 cross-cut 发现**（每条 1-2 句）
- 从第 4 节提前提取的最关键 insight — 矛盾信号 / 估值错配 / 极端值中的最 decisive 发现
- 例：「Hyundai Rotem 的 Greenblatt ROC ~44% 但 PER 仅 23.5x — 是板块内唯一同时满足『最便宜+最赚钱』的；Hanwha Systems 的 PA 109x 对应 OP -46% — 估值和基本面方向完全相反」

**第一优先行动**（1 句）
- 基于上述结论，最迫切的下一步是什么
- 例：「本周优先拆解 Rotem defense vs rail standalone 估值，验证 rail 19T 隐藏资产的真实价值」

**反模式**：
- ❌ 写「详见后面第 X 节」 — 结论先行必须自包含，不能当「预览目录」
- ❌ 每个发现都加解释和 caveat — 这是浓缩结论，论据留给后面
- ❌ 排名没有方向（「有待观察」）— 必须给方向
- ❌ 排名表缺乏理由（只列公司名+方向但不说为什么）— 必须有一句话理由


### 1. 行业 Lens（共享坐标系，~300-400 字）

**这是 skill 的灵魂之一**——这部分写**一次**，N 家公司**共享**这套坐标系，避免在每家公司里重复行业背景。

必含：
- **当前 regime**：今年市场在 trade 这个行业的什么变量？（例：能源股是 capital discipline + 资本返还；半导体是 cycle + 库存；A&D 是国防预算 + commercial recovery）
- **Capital cycle 整体阶段**：行业层面是重投资 / 维持 / 收割？这决定后续公司层估值锚点的选择
- **行业层面实证驱动因素**：当前 regime 下行业整体股价主要跟着哪些**外部变量**动（不是公司层 KPI）
- **行业 base rate**：这种估值 / 周期位置历史上演变路径是什么？最近一次类似阶段是哪几年？

**反模式**：
- ❌ 行业入门 / 监管科普 / 历史发展（这是百科，不是 lens）
- ❌ 罗列行业有多少玩家 / 市占率前五（这是数据，不产生 insight）
- ❌ "受益于 / 不利于"这种空话

### 2. 横向矩阵（核心数据表）

N 家公司 × 关键维度的并排数据。**必须有 `Ev` 列；完整 source metadata 放文末 `## Resources`**。分两层：

#### 2A. 通用维度（所有行业都列）

| 公司 | 市值 | 收入(LTM) | 收入 YoY | EBITDA margin | ROIC（除现金） | 净负债/EBITDA | Capex/D&A | FCF yield | EV/EBITDA(当前 vs 5Y 中位) | 资本返还/FCF | Ev |
|---|---|---|---|---|---|---|---|---|---|---|---|

每行 `Ev` 标注主要数据来源（典型：`[S1](link) [S2](link)`）；文末 `## Resources` 统一展开：`- [S1](link) = local source | 10-K FY2025 | filed [date]`、`- [S2](link) = market data source | Bloomberg/CapIQ | as-of [date]`。

正文 claim 示例：`Peer A has the highest service mix at 42%, while Peer B still discloses services only inside the equipment segment. [S1](link) [S2](link)`


**ROIC（除现金）计算公式**：NOPAT / (Invested Capital - 现金及等价物)。闲置现金不参与经营但会拉低分母，剔除后反映经营业务的真实投入回报。口径说明：如现金超过总资产的 20%，差异可能显著，需在表下单独标注各家的现金占比。

#### 2B. 行业特定维度（先查后建逻辑）

通用维度（2A）远不足以判断 N 家公司的差异——每个行业都有自己的核心 KPI。**用错 KPI 的横向比较是误导**。

**核心原则**：先查现成模板（省时间），没有就用元方法论现场推导（覆盖任何新行业）。**不依赖穷举行业**——商业航天、合成生物、空中出行、稀土永磁、core SMR 等任何冒出来的新行业都能处理。

**Step 1: 检查现成模板**

`references/industries/` 目录下有现成 KPI 模板的行业（这些是 crystallized knowledge，作为高质量 reference）：

| 行业 / 板块 | 模板文件 | 覆盖范围 |
|---|---|---|
| Aerospace & Defense | `aerospace-defense.md` | Defense primes、commercial aero、engines、space、suppliers |
| Oil & Gas | `oil-gas.md` | Upstream (E&P)、midstream、downstream、OFS、integrated |
| Renewable Energy | `renewable-energy.md` | Solar、wind、battery storage、green hydrogen、IPP/developer |
| Nuclear | `nuclear.md` | Utilities、SMR developers、fuel cycle、uranium miners |
| Advanced Manufacturing | `advanced-manufacturing.md` | Industrial automation、机器人 (非人形)、capital equipment |
| Humanoid Robotics | `humanoid-robotics.md` | Pure-play、supply chain、ecosystem |
| Software / AI Applications | `software-ai-applications.md` | SaaS、AI-native 应用、AI infra、cybersecurity |
| EPC | `epc.md` | 大型 infrastructure、energy EPC、specialty contractors |
| Quantum | `quantum.md` | Pure-play、enterprise spillover |

**如果 N 家公司主要属于上述行业之一**：
- 直接读取对应模板
- 使用模板中的 KPI 列表 + cross-cut 注意事项
- 注意子细分匹配（A&D 模板要按 Defense primes / Commercial aero / Engines / Suppliers 选；O&G 按 Upstream / Midstream / Downstream 选）

**Step 2: 没有现成模板时——用元方法论推导**

读取 `references/industry-kpi-framework.md`，按 5 步推导：

1. **定位 4 个维度**：商业模式（commodity / capital equipment / project / SaaS / IP licensing / platform / pre-commercial deep tech / hybrid）+ 周期性 + 政策依赖 + 商业化阶段
2. **填空 5 个问题**：收入来源 / unit economics / capital cycle / 风险结构 / 商业化进度
3. **加入行业 idiosyncratic KPI**（如不确定，主动询问研究员——AI 不应假装领域专家）
4. **精炼到 5-10 个 KPI**
5. **告知用户思路 + 请校准**

**Step 3: 用户确认后选择是否保存为新模板**

推导完成后告知用户：
> "[行业] 暂无现成模板。我根据 [4 维度] 推导出 [N 个 KPI]。你想要：
> (a) 用这套继续  (b) 调整  (c) 重新讨论  (d) 推导后保存为 `references/industries/[name].md` 以便复用"

如果用户选 (d)，新模板就**作为研究副产品累积**——不是主动维护负担。

**Step 4: 现成模板"接近但不完全匹配"的情况**

经常遇到：用户研究的行业**部分**重叠现有模板（例：LNG carriers 不在 O&G 模板，但 midstream 提供部分参考）。

处理：
- 明确告知"现有 [X] 模板提供部分参考（覆盖 Y 部分），但 [行业] 还需补 [Z]，建议结合元方法论补充"
- 不要硬套不匹配的模板

**Step 5: N 家公司维度差异巨大时**

如果 N 家公司在 4 个维度上差异显著（例：long X 是 early-scale + long Y 是 mature；或 N 家分散在不同子细分）：
- 警告用户这不是合理的对比组
- 建议重新分组（按子细分 / 维度 cluster）
- 不要强行做 cross-cut——会得到无意义结论

#### 2C. 跨公司可比性提示

每个 KPI 必须确认 N 家**口径一致**。常见陷阱：
- EBITDA 调整项不同（一家加回 SBC、一家不加）
- ROIC 的 invested capital 算法不同
- Production / 收入的口径不同（gross vs net、含/不含某子公司）
- Capex 含/不含 acquisition

**有口径差异时必须在表下脚注明确**，不能假装可比。

### 3. 各公司 Differential Profile（每家 ~250-400 字）

**关键警告**：这不是 mini stock-quickread。这是"和共同坐标系 / 同业相比，这家有什么特殊的"。如果你在写这家公司的业务模式 / 历史 / 管理层背景——停。那是后续 stock-quickread 的事。

每家用如下模板：

#### [公司名]

**一句话定位**：在同业里的位置（10-15 字）
> 例："同业里成本最低生产商，但增长最慢"
> 例："唯一一家把 60% 收入投回 capex 的，其他都在收割"
> 例："估值便宜但 ROIC（除现金）同业最低——typical value trap 候选"

**关键 differential**（3-5 条，**只列和同业不同的**）
- 用具体数字描述这家**偏离同业**的地方，每条要给 Source
- 例："EBITDA margin 32% vs 同业 24% [10-K 2024 segment data](url)，来自 X 区块成本优势"
- ❌ 不要列这家自己的全貌（"收入构成 60% A、40% B"——不是 differential）

**特有驱动因素**（1-3 条）
除了第 1 节列的行业共同 driver 之外，这家**独有的**驱动因素。
- 例："这家有 30% 收入来自一个客户的 long-term contract，其续约结果是 idiosyncratic 风险"

**当前最大争议**（1-2 句）
市场在为这家纠结什么。

**Thesis 苗头**：基于上面观察，给出方向性判断
- **多 / 空 / 中性 / 不感兴趣** 之一
- 1 句具体理由
- 例："多——估值最便宜但 ROIC（除现金）同业最高，明显错配，需要查市场为什么折价"
- 例："不感兴趣——同业平均水平，无明显 setup"

**反模式**：
- ❌ 复述业务模式 / 收入构成（quickread 的事）
- ❌ "管理层经验丰富 / 团队稳定"（不是 differential）
- ❌ Thesis 苗头给"看情况" / "有待观察"（必须给方向，没方向就写"不感兴趣"）

### 4. Cross-Cut Insight 层（核心，500-800 字）

**Skill 的灵魂之二**——做不到这一节就是失败。如果你 cross-cut 真的找不到任何东西，必须明确写"未发现 X / Y / Z"，并解释为什么没有（同业同质化太强 / 数据不足 / 时点问题等）—— 不能装作有内容。

#### 4A. 矛盾信号（管理层互相打脸）

N 家管理层 commentary 哪里**互相对立**？这是 alpha 最丰沃的土壤——因为一定有一边错了。

格式：
> **[矛盾点]**：X 公司 [具体引语] [Q3 2024 call 时间戳](url)；Y 公司同期说 [对立引语] [Y Q3 2024 call 位置](url)。
> **背景**：两家终端市场重叠 X% [10-K segment overlap](url) / 都属于上游 Permian / 都做某细分应用 — 解释为什么这两家应该说同一件事
> **解读**：可能解释（一边在 sandbagging？区域差异？时点错位？）+ 哪边的位置更可信 + 怎么验证

如果**完全没有**矛盾信号，明确说"未发现明显矛盾——N 家在 [核心 narrative] 上保持高度一致，可能意味着行业 commentary 被锚定在 X，或者真实差异要从数据而非言论中找"。

#### 4B. 共识信号（多家说同一件事）

N 家都在强调什么？高度一致信号可信度高，是行业层面判断的基石。
> 例："X / Y / Z 三家 H2 不约而同上调 OpEx 指引 [三家 Q3 call 各自引用 + url]——说明行业层成本通胀加速，不是单家问题。这个信号意味着第 1 节'行业 regime'里的成本敏感度判断需要加权"

共识信号的用法：用来**校准对行业 lens 的理解**，并识别哪些公司还**没认怂**（异常值，可能是 best-in-class 或下一份财报的 disappointment 候选）。

#### 4C. 估值 Spread vs 基本面 Spread（错配点）

回看第 2 节矩阵：估值 spread 和基本面 spread **匹配吗**？错配处是机会或陷阱。

格式：
> **错配点**：X EV/EBITDA 12x，Y 8x [Bloomberg 同时点](url)——X 增长 18% / Y 14% [各自 LTM 收入](url)
> **预期 spread**：增速差 ~30%，估值正常 spread 应该多少
> **实际 spread**：50%
> **解读**：可能（市场担心 Y 的某具体问题 / X 有非可比的优势 / 时点定价不充分）。研究方向是验证哪个解释最对

至少给 2-3 个最显眼的 spread 错配。

#### 4D. 极端值的故事

第 2 节矩阵里每个维度的 max / min 是谁？**极端值是研究起点不是结论**——为什么这么极端、是机会还是陷阱。

格式：
> **[维度] 极端值**：max 是 X（具体数 + Source），min 是 Y（具体数 + Source）
> **驱动**：X 这么高是因为 [基本面理由 + 是否 sustainable]
> **判断**：是机会（市场没认识到）还是陷阱（基本面真的差，估值已合理）

挑 3-5 个最有信息量的极端值——不是把每个维度的 max/min 都念一遍。

### 5. 研究排序 & 资源分配

**这一节强制具体**——含糊的"建议先看 X"等于没排序。

#### 5A. 优先级矩阵

| 公司 | 优先级 | 研究深度建议 | 时间分配 | 排序理由 |
|---|---|---|---|---|
| X | 1 | 全套：stock-quickread → alpha-thesis → bear-pre-mortem | 2 天 | 信息密度最高（cross-cut 命中 2 个错配点）+ 临近财报（catalyst 时间敏感） |
| Y | 2 | 简化：stock-quickread + alpha-thesis 简版 | 1 天 | hedge 候选，重点跟 spread 演变 |
| Z | 3 | 仅 stock-quickread | 半天 | 同业 typical，无明显 setup，先建 mental model 进 watchlist |
| ... | ... | ... | ... | ... |

排序的判断维度：
- **信息密度**：cross-cut 命中越多，优先级越高
- **时间敏感度**：临近财报 / 临近其他 catalyst 的优先
- **现有覆盖深度**：从零开始的 vs 已有 mental model 的，前者更耗时
- **估值 setup**：是否处于 asymmetric 的位置（max upside / 极端折价）

#### 5B. Pair / Cluster 建议

- **适合放在一起继续研究的几家**：基于业务重叠 / 估值错配 / driver 差异，哪几家适合一起跟踪。
- **相对错配候选**：如果有 Long / Short 的研究苗头，只说明错配逻辑和需要继续验证的问题，不生成交易状态。
- 默认必须输出 cluster 判断；如果**没有合适的 cluster**，明确说"无明显 cluster 机会——同业同质化高 / 估值已 priced / N 家相关性过高"。
- 若 cross-cut 暴露业务实质错读、peer mismatch 或 market misread，触发 Senior Analyst Radar，并建议用 `next-step` 继续拆。

### 6. 跨公司的关键问题

这次扫描产生的问题，分两类：

#### 6A. 公司层面问题（每家单独研究时要重点回答）

按公司分组列出。这些问题会成为后续每家 stock-quickread 的"下一层要问的具体问题"输入。
- **X 公司**：
  1. 具体问题 1（基于 cross-cut 4A 矛盾信号产生的）
  2. 具体问题 2
- **Y 公司**：...

#### 6B. 行业层面问题（任一家答出都影响所有 N 家）

- 例："如果北美页岩 break-even 在 H2 真的回升到 $X，这套行业 lens 整体需要重新校准——X / Y / Z 都受影响"
- 例："如果 OpEx 通胀是结构性的（不是周期），所有 N 家的中长期 margin 假设都偏高"

这些问题是**未来主动找信息**的方向，不是被动等的。

### 7. 下一步

明确指出：
- **第一个进 stock-quickread 的公司**（具体名字 + 为什么是这家）
- **行业层面要追的具体研究方向**（基于第 6B）
- **本次 peer-deep-dive 可能需要重做的时机**：例如 N 家集中财报后、行业某个数据节点、政策事件后
- 如果横向比较暴露行业机制、工程原理、设备链条或术语口径不清，明确先用 `mechanism-map` 统一 mechanism / value-capture 理解，再继续比较。
- 如果横向比较暴露 revenue / margin / backlog / price-volume-mix 口径不可比，明确先用 `driver-map` 统一业务实质和 driver，再继续比较。

## Workflow 联动

| 场景 | 下一步 |
|---|---|
| peer group 机制、value-capture 或 KPI 口径不可比 | 先 `mechanism-map` 或 `driver-map`，再回到本 skill |
| 横向比较暴露单一公司的 variant view | `alpha-thesis` |
| 横向比较暴露 long / short cluster 或 hedge candidate | `pair-trade` |
| 需要把 peer 差异量化进 operating model 或 valuation | `3-statement-model / dcf-model / comps-analysis / model-update` |
| 已经形成可复用行业 lens、peer map 或研究排序 | `research-journal` |
| 仍不知道下一轮最值得追哪个问题 | `next-step` |

## 可选保存

默认输出到对话。用户明确要求保存时，写入当前日期化保存路径：

```text
topics/[topic-namespace]/[topic-slug]/[YYYY-MM-DD]-peer-deep-dive.md
```

如果当前日期化保存路径不明确，先 handoff 到 `new-session` 解析路径；不要临时发明目录或未解析路径就写入。

## 输出篇幅基准（线性 scale）

| N | 目标字数 | 矩阵表数量 | Cross-cut 字数 |
|---|---|---|---|
| 3 | ~2500 字 | 2 张 | 400-600 |
| 4 | ~3000 字 | 2 张 | 500-700 |
| 5 | ~3500 字 | 2-3 张 | 500-800 |
| 6 | ~4000 字 | 3 张 | 600-900 |
| 7 | ~4500 字 | 3 张 | 600-900 |
| 8 | ~5000 字 | 3 张 | 700-1000 |
| >8 | — | — | 先自由对话预筛，或按子行业 / business model 分子组 |

各节字数大致分配：
- 行业 lens：300-400（不随 N 变）
- 矩阵表：本身字数小（数据为主）
- Differential profiles：250-400 × N（线性增长）
- **Cross-cut**：500-1000（轻度增长——N 大不一定 insight 多）
- 排序 + 问题 + 下一步：300-500（不随 N 显著变）

如果产出**显著超过**上限，通常是落入"N 份 quickread 拼贴"陷阱——回头删 differential profile 节里复述的内容。

## 反模式自查

写完后必须自检：

**通用**
- ❌ 抽掉"行业 lens"和"cross-cut"两节后，剩下的是 N 份精简 quickread → 失败的 peer-deep-dive，重写
- ❌ 任何一节有"成立于 / 总部位于 / 管理层经验丰富" → 删
- ❌ 出现行业入门 / 监管科普 / 行业历史 → 删
- ❌ 结论埋在后半部分，需要翻好几页才能看到方向判断 → 「结论先行」节没写或写得像「预览目录」

**第 1 节（行业 lens）专项**
- ❌ 描述行业有多少玩家 / 市占率结构（不是 lens 是数据）
- ❌ "受益于 X" 这种万能空话
- ❌ 没说当前 regime 在 trade 什么变量

**第 2 节（矩阵）专项**
- ❌ 表格无 `Ev` 列或文末 `## Resources` 缺失 → 加上
- ❌ 跨公司口径不一致但没标注（EBITDA 调整项不同等）→ 标 footnote 或 normalize
- ❌ 行业特定 KPI 列了通用项但没列对应板块的特定 KPI → 补
- ❌ 没有 ROIC（除现金）/ Capex 强度 / 估值 vs 自身历史 等关键判断指标
❌ 只看标准 ROIC 就说资本效率差 — 可能是现金拖累，必须同时看 ROIC（除现金）
- ❌ 没做横向比较 Preflight 就直接 ranking / matrix → 先确认 mechanism、KPI、driver、peer group 可比。
- ❌ 工程机制 / 设备链条不清楚却硬比较 KPI → 先用 `mechanism-map` 统一 mechanism / value-capture 口径
- ❌ 各公司 driver 口径明显不同却硬做矩阵 → 先用 `driver-map` 统一 business reality / model driver

**第 3 节（differential profile）专项**
- ❌ 在写公司业务模式 / 收入构成 / 历史 → 那是 quickread 的活
- ❌ "Differential" 内容其实是这家自己的全貌（不是和同业的差异）
- ❌ Thesis 苗头是"看情况" / "有待观察" → 没决断，必须给方向
- ❌ 每家长度差不多 → 重要的 / 复杂的应该更详细，简单的应该更短

**第 4 节（cross-cut）专项 — 最容易失败的节**
- ❌ 整节没有任何具体引语 / 数字对比 → 是空想，重写
- ❌ 矛盾信号没给两边的具体引语和定位 → 力度 = 0
- ❌ 估值 spread 错配只写了"XX 估值高 / 低"，没说"应该多少 vs 实际多少 vs 解读"
- ❌ 极端值的故事只罗列 max/min，没解释为什么这么极端、是机会还是陷阱
- ❌ 找不到 cross-cut 但假装有 → 必须明确说"未发现 X" 并解释为什么没有

**第 5 节（排序）专项**
- ❌ 每家研究深度都给"全套" → 资源没分配
- ❌ "建议先看 X" 但没给具体时间分配和理由 → 含糊 = 没排序
- ❌ Pair trade 找不出却硬凑 → 明确说"无明显 pair 机会"

**第 6 节（问题）专项**
- ❌ 公司层面问题 = 一般性的"看一下管理层"，不是 cross-cut 产生的具体问题
- ❌ 行业层面问题 = "看看行业景气" 这种空话

**Source 专项**
- ❌ 矩阵表的数据无 source link → 标记或补
- ❌ Cross-cut 引用的管理层 commentary 无具体 call / Q&A 位置 → 力度受损，必须补
- ❌ Source 是"据报道""有传言""有人说" → 不是 source，找出处或删
- ❌ URL 不确定真实存在 → 写描述加 `[link 待补]`，不要假装
- ❌ 把 sub-agent evidence card 直接粘成最终 peer ranking / cross-cut conclusion → 必须由主 agent 抽查、统一口径、重新 synthesis
- ❌ 把 sub-agent 返回的 URL 直接当作已验证 source → 必须先抽查至少 2-3 个 link，确认 URL 和 claim 匹配
- ❌ 跨公司比较的数字来自不同口径但没标注 → 是错误，必须修正
