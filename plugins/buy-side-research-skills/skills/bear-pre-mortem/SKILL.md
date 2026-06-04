---
name: bear-pre-mortem
description: Stress test an investment thesis and build the strongest opposing case with sourced risks.
---

# Bear Pre-Mortem

Stress test an investment thesis and build the strongest opposing case with sourced risks.

## Research Runtime Capsule

Follow `_shared/research-runtime.md` — 数据获取链、来源验证链、证据协议、产出合约、保存合约。
Hook-enforced: `pre_write_gate` (source/tables/mermaid), `source_contract`, `table_render_integrity`, `mermaid_syntax`, `skill_structure_contract`, `evidence_ledger_floor`.

## 心法

研究员最容易死在 confirmation bias 上：建立 thesis 后所有信息都往 thesis 这边解释。Pre-mortem 是反向操作——**假设这单 trade 一年后亏了 30%，事后看是因为什么**。

不是问"有什么风险"——这种问题只会得到淡化的、形式化的回答。要问"如果我错了，最可能是哪种错法"——这个问题让大脑去搜索具体场景，得到的答案才有用。

比如你做多 ASML："一年后这单 trade 亏了 30%。回头看——TSMC 把 2026 capex 从 $38bn 砍到 $28bn，EUV 订单直接蒸发。高 NA 太贵了，客户发现用旧 EUV 多 pattering 也能凑合。这不是风险清单——是具体场景。"

## 输入与双向用法

- 默认输入是 `alpha-thesis` 输出、当前对话中的 thesis 草稿，或 topic journal 里已经沉淀的研究结论。
- 如果输入是多头 thesis，本 skill 输出最强空头 pre-mortem。
- 如果输入是空头 thesis，本 skill 反向输出"这单 short 为什么会亏钱"：最强多头 / short squeeze / crowded short / upside catalyst 压测。
- 如果 thesis 文件带 YAML frontmatter，优先读取 `key_assumptions`、`kill_criteria`、`valuation_anchor`、`conviction`、`health_status`，不要只解析自然语言正文。

## Mechanism Assumption Audit

在写最强反方之前，先把 thesis 的隐含机制假设挑出来压测。Pre-mortem 不能只攻击估值和宏观，也要问"这个业务到底是不是按 thesis 说的方式运作"。

| 假设类型 | 要压测的问题 | 不清楚时动作 |
|---|---|---|
| 工程 / 设备链条 | 关键设备、工艺流程、产能单位是否真的支持 thesis 的产量 / 成本假设 | 先 handoff 到 `mechanism-insight` |
| Unit economics | 单台设备、单桶油、单项目、单客户的经济性是否成立 | 机制不清先 `mechanism-insight`；财务 driver 不清先 `driver-map` |
| Value capture | 价值到底被 OEM、供应商、服务商、渠道还是客户捕获 | 先 handoff 到 `mechanism-insight` |
| Driver linkage | 机制变化如何传到 revenue、margin、backlog、price-volume-mix | 先 handoff 到 `driver-map` |

若机制假设不清，不要假装已经完成压力测试。先输出最小 handoff block：

```markdown
## Primitive Handoff Required

- Blocker: [哪个 mechanism assumption / driver assumption 不成立或不清楚]
- Why it blocks pre-mortem: [它会影响空头 pitch / unit economics / path of pain 的哪一节]
- Handoff: `mechanism-insight` / `driver-map`
- Inputs needed: [需要补的技术资料 / filing / call / KPI / segment data]
```

## 输出结构

### 1. The Smartest Short Seller's Pitch（300-500 字）

用最锋利的笔法写一份做空逻辑。这一节**完全不要 hedge、不要"另一方面"、不要"但是"**。空头思路就是空头思路，让它满血输出。

要素：
- 一句话讲清空头逻辑（"这是个 melting ice cube" / "估值脱离基本面" / "存在 [具体] 治理 / 财务问题" / "周期顶部，下行 mean reversion 还没开始" / "故事不可能成立因为 [具体限制]"）
- 关键证据 2-3 条
- 对应的目标价 / 下行幅度

### 2. Unit Economics 拷问

不要被 GAAP 报表带跑——质询单位经济：
- 每一个新增客户 / 每一桶油 / 每一台机器，赚多少钱？这个数字几年来怎么变化？
- 增量利润率（incremental margin）和管理层讲的故事一致吗？
- 如果把"非经常性""调整后""一次性"全部加回去，真实赚钱能力是什么样？
- CAC / LTV 类生意：CAC 在涨吗？LTV 假设可信吗？
- 折旧政策：实际资产寿命真的有这么长吗？capex / D&A 长期比例是否暴露了问题？

### 3. 会计 / 财务红旗清单

## 会计红旗公式

科目多语对照见 `references/policy/statement-line-items.md`。

| # | 红旗 | 公式 | 输入来源 | 报表位置 | 警戒阈值 |
|---|---|---|---|---|---|
| 1 | DSO 恶化 | 应收 × 365 ÷ Revenue | FS, FS | BS + IS | YoY +30% / > 同业 2x |
| 2 | 存货积压 | COGS ÷ 平均存货 | FS, FS | IS + BS | YoY 显著下降 |
| 3 | 利润无现金支撑 | OCF ÷ NI | FS, FS | CF + IS | 持续 < 0.7 |
| 4 | 资产老化 | CapEx ÷ D&A | FS, FS | CF | 持续 < 0.7 |
| 5 | M&A 减值风险 | Goodwill ÷ Equity | FS, FS | BS | > 50% |
| 6 | 股权稀释 | SBC ÷ Revenue | FS, FS | 附注 + IS | > 10% |

逐项扫，每条要给：当前数 / 警戒阈值 / 状态 / Ev。有问题的那几条单独展开论证。

| 红旗项 | 当前数 | 警戒阈值 | 状态 | Ev |
|---|---|---|---|---|
| DSO / 应收账款增速 vs 收入增速 | DSO 78 天 | > 收入增速 1.5x | 🚩 | [S1](./_cache/sources/ar-aging-note.md) |

| 库存增速 vs 收入增速 | ... | ... | ... | [S1](./_cache/sources/inventory-vs-revenue.md) |
| Capex vs D&A 长期比例 | 1.8x | 持续 > 1.5x 警惕过投 | ... | [S2](./_cache/sources/capex-da-history.md) |
| 经营性现金流 vs 净利润长期匹配度 | OCF/NI 0.6 | < 0.7 持续是警告 | 🚩 | [S3](./_cache/sources/ocf-ni-bridge.md) |
| 商誉 / 无形资产占比、近期减值历史 | ... | ... | ... | [S4](./_cache/sources/goodwill-impairment-note.md) |
| 关联交易 / 表外项目 | ... | ... | ... | [S5](./_cache/sources/related-party-note.md) |
| 分部合并、披露口径变化 | ... | 任何变化都警惕 | ... | [S6](./_cache/sources/segment-disclosure-history.md) |
| 股权激励真实成本（加回去后还赚钱吗） | ... | SBC > 净利润 30% 警惕 | ... | [S7](./_cache/sources/sbc-note.md) |
| 管理层 / 内部人最近的减持 | ... | 集中减持是信号 | ... | [I1](https://example.com/form4-disclosure) |
| 审计 / 会计政策近期变化 | ... | 任何变化都警惕 | ... | [S8](./_cache/sources/audit-policy-note.md) |

每个 🚩 状态的项必须单独展开，引用具体数据点和对比基准。

### 4. 多头 thesis 在淡化什么（3-5 条）

回到原始多头 thesis，找出每一处"长期来看不重要""短期扰动""一次性影响"——空头的工作是论证这些不是扰动而是趋势。

### 5. Base Rate / 历史相似情境

这种"故事"（高估值 + 高增长预期 / 周期顶部 + 资本支出潮 / 类似商业模式 + 类似阶段）**历史上的样本结果如何**？拉 3-5 个可比案例，每个给具体公司 / 时间窗口 / 结局 / Ev。

| 可比情境 | 时间窗口 | 公司 / 标的 | 结局 | Ev |
|---|---|---|---|---|
| 类似估值 + capex cycle 顶 | 2014 Q3 - 2016 Q1 | Whiting Petroleum | 股价从 $X 跌到 $Y，-90% | [S1](./_cache/sources/whiting-10k-2014.md) [S2](https://example.com/whiting-price-history) |

| ... | ... | ... | ... | ... |

Base rate 是反 narrative 最强的武器——管理层永远讲"这次不一样"，base rate 告诉你"通常不"。**但 base rate 的力度全在 source 真实**——编造的可比案例反而削弱压力测试。

### 6. 行为偏差自检

这个 thesis 的研究员（"我"）可能有哪些偏差让我看不见空头逻辑？
- 我是不是 anchored 在某个买入价 / 历史高点？
- 我是不是因为最近读了利好新闻在 echo chamber 里？
- 我对管理层有没有 personal affection / 反感？
- 我有没有 sunk cost——花了很多时间研究，不愿意承认错？
- 我是不是 framing 问题就让 thesis 看起来对（"它会涨多少" vs "它有多大概率亏 30%"）？
- 我是不是 social proof 中——某个我尊敬的投资人 / 朋友也持有？

### 7. The Path of Pain

如果空头逻辑对，股价的下跌路径会是什么样？
- 第一个 leg：什么 catalyst 触发，跌多少？
- 第二个 leg：什么后续事件加速？
- 长期均衡：哪里是支撑？

这一节让你提前知道**亏损路径**长什么样，避免到时候被叙事 reframe（"这只是技术性回调""市场情绪过度"）。

## Artifact / 保存策略

写入行业 topic：
    industry/<industry>/companies/<ticker>/YYYY-MM-DD-<artifact>.md

路径不明 → agent 按 policy baseline §11 自动创建。

## Growth Break Scenario

如果 revenue growth 从 X% 跌到 Y%：
- Margin impact: EBIT margin Z% → Z'%（fixed cost leverage reverse）
- Multiple impact: PE Xx → Yx（growth de-rate）
- Implied downside: −A%

最可能触发 growth break 的信号：[1-2 个 leading indicator]

## Source Contract

> 空头压测对 source 真实性要求最高——"可能出问题"必须有具体的 filing/page/数字，不能只靠"看起来可疑"。

**密度表**：

| Section | 强制标 source | 豁免 |
|---|---|---|
| §1 空头 narrative | 每个指控对应的具体数字/事件 | narrative 本身 |
| §3 红旗 walk | 每行 DSO/库存/OCF/Capex/SBC 的 filing source+页码 | 红旗判断 |
| §4 Base rate | 每个历史可比案例的 ticker+年份+跌幅+source | — |
| §5 Kill criteria | 每条触发条件的阈值出处（filing/IR/history） | — |

**完成 Gate**：写完扫 §3 → 每行有 filing source → §4 每个案例有 ticker+source → `[待查]` ≤5 → Resources 展开。

## 反模式自查

- ❌ 第 1 节读起来像"另一方面也有人认为"——重写，把空头当成你
- ❌ 第 3 节走过场，每条都写"无明显问题"——你没真看，回去看
- ❌ 第 5 节没有具体可比案例，只有"很多公司这样" → 拉具体例子
- ❌ 整篇没有具体数字、具体时间、具体事件 → 太空洞，重写
- ❌ 每个空头点都立刻被一个对应的多头反驳"挽回"了 → 这不是 pre-mortem 是辩论赛，重写
- ❌ thesis 依赖工程机制、设备链条、产能单位或 value capture，但没有先做 Mechanism Assumption Audit → 先触发 `mechanism-insight`。
- ❌ 最强反方攻击的是 revenue / margin / backlog / price-volume-mix，但原 thesis 没拆 driver → 先触发 `driver-map`。

**Source 专项（空头压测对 source 真实性要求最高）**
- ❌ 第 3 节红旗项有数字但无 filing source / 页码 → 补
- ❌ 第 5 节 base rate 案例无具体公司名 / 时间 / 链接 → 编造的可比削弱压测，必须补
- ❌ 引用了"听说" / "据传" / 推特 / 论坛作为做空依据 → 法律风险高，必须找一手 source 或删
- ❌ 出现具体数字 / 引语但无 source link → 标记 `[需查证]` 或删
- ❌ 用了管理层减持 / 内部人交易作为论据但无 Form 4 / 披露 source → 补
- ❌ URL 不确定真实存在 → 写描述加 `[link 待补]`，不要假装

## 篇幅基准

- Quick pre-mortem：600-900 字，适合快速检查一个 thesis 是否有明显盲点。
- Full bear pre-mortem：1000-1800 字，适合 IC 前完整压测，必须包含 unit economics、会计红旗、base rate 和 path of pain。
- 超过 2000 字通常说明在写完整 short thesis，应转入 `alpha-thesis` 的 short-only 结构或拆成多个风险模块。

## 用法说明

本 skill 在 `alpha-thesis` 写完之后、IC memo 提交之前使用。如果压力测试之后原 thesis 还站得住，conviction 是真的；如果发现明显盲点，回去修 thesis、降低 sizing，或者直接放弃这单 trade。

