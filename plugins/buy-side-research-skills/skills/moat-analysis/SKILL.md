---
name: moat-analysis
description: Scorecard-based competitive moat analysis with anchored scoring, evidence grading, peer comparison, and moat trajectory.
---

# Moat Analysis

Quantify competitive moat — not with adjectives, but with anchored scores, graded evidence, peer comparison, and a trajectory judgment. Every score must answer: why not one point higher or lower? Every moat must answer: is it getting wider or narrower?

## Research Runtime Capsule

- Hook-enforced rules (source boundary, structure floor, table render) live in workspace hooks.
- Shared runtime baseline: `references/policy/research-policy-baseline.md` + workspace `CLAUDE.md`.
- **数据管道**：调用 `/financial-data --lite <ticker>` 获取 baseline。
- **数据验证**：Claim Fill Pipeline — Tier 0(actuals)→1(WebFetch)→2(Playwright)→3(curl)→4([需查证])。见  §3.2。
- **Actuals-only**: ROIC, margins, and all moat scorecard financial metrics use actuals-resolved.json disclosed data only.
- Sub-agent outputs: evidence_cards_only; main agent synthesizes.

## 心法

Moat analysis 最容易写成赞美诗——"技术领先"、"品牌强"、"客户粘性高"。区分好坏 moat analysis 的标准很简单：读完以后，你知不知道**哪个变量一旦变了，护城河就破了**？如果不知道，分析没做完。

第二个死穴：moat 是相对的。MYCR 的技术壁垒 9 分是因为猎奇是 5 分、Besi 是 8 分。如果猎奇明天突破了 1μm 精度，MYCR 的壁垒不会自动变——但你的 9 分必须变。moat scorecard 必须包含 peer 对标。

第三个死穴：moat 是动态的。CPO 时代，引线键合这个工艺本身可能消失——K&S 的 moat 不是变窄，是直接没了。每个 moat 分析必须回答：下一代技术/产品/范式下，这个壁垒是加强、不变、削弱还是消失？

## 触发场景

- "分析 xxx 的护城河"
- "xxx 和 yyy 谁壁垒深"
- "xxx 能守住现有份额吗"
- "xxx 的竞争地位在变好还是变差"

## 五维度评分

每维 1-10 分，必须有 peer 对标，必须有 observable evidence。

### 1. 技术壁垒

不是"技术好"——是新技术进入者要花多长时间、多少钱才能追到你的当前水平。而且你在他们追的时候又往前跑了多远。

| 分数 | 标准 | 例 |
|---|---|---|
| 9-10 | 全球只有你+1 家能做。进入需要 3 年+ $100M+ | ASML EUV: 只有一家。光模块固晶 1μm: 只有 MRSI/Besi/ASMPT |
| 7-8 | 3-5 家能做，但你有代际优势（比第二名领先一代） | ficonTEC CPO 耦合: 有 2-3 家在追，但有 18 个月领先 |
| 5-6 | >5 家能做，你是 top 3 但差距不大 | 中端贴片: 猎奇/博众等都行，精度差距不显著 |
| 3-4 | 技术 learned within 12 months, no IP protection | 自动化整线: 3C 自动化公司都能做 |
| 1-2 | 技术被替代方案威胁，你的技术路线可能被跳过 | 引线键合在 CPO 时代可能直接消失 |

**关键问题**：如果你想领先一代需要多少研发投入？$10M? $100M? 这个数除以公司年研发费用 = 追赶者需要几年的研发预算。比值越大，壁垒越深。

### 2. 客户锁入

不是"客户关系好"——是客户如果换供应商，需要花多少钱、多少时间、冒多大风险。

| 分数 | 标准 | 例 |
|---|---|---|
| 9-10 | 替换需要 1 年+ requalification，可能影响客户交付 | 航空发动机: 要重新 cert，客户不会为省 5% 冒这个险 |
| 7-8 | 替换需 3-12 月，有 real cost 但不是 impossible | 固晶+耦合成套: 换了固晶机耦合参数要重跑，但客户会試 second source |
| 5-6 | 替换 <3 月，主要是关系/习惯不是真锁入 | 大多数工业品 |
| 3-4 | 几乎无切换成本 | 标准件、commodity |
| 1-2 | 客户主动寻找替代，你的产品是 pain point | |

**关键问题**：上次有大客户换供应商是什么时候？花了多久？如果从没发生过，可能不是锁入——可能只是没人试过。

### 3. 规模效应

不是"收入大"——是 unit cost 随规模下降的速度。

| 分数 | 标准 |
|---|---|
| 9-10 | Unit cost 每 doubling 下降 >15%，且有 evidence（毛利率 trend 持续上升） |
| 7-8 | 下降 10-15% |
| 5-6 | 下降 5-10% |
| 3-4 | 下降 <5% |
| 1-2 | 无规模效应，或 diseconomies（规模越大越难管） |

**关键数据**：过去 5 年 revenue 翻了多少倍，gross margin 变化了多少。

### 4. 监管/认证

| 分数 | 标准 |
|---|---|
| 9-10 | 法定准入门槛，5 年+认证周期，只有你和 1-2 家有 |
| 7-8 | 行业强制认证 1-3 年，不是谁想做就能做 |
| 5-6 | 有认证但不是准入条件 |
| 3-4 | 自愿性标准 |
| 1-2 | 无任何监管 |

### 5. 品牌/转换成本/网络效应

品牌不是"有名"——是能不能 charge premium。转换成本不是"不方便"——是"换了会丢数据/业务中断"。

| 分数 | 标准 |
|---|---|
| 9-10 | Brand premium >20% vs #2, 且可量化 |
| 7-8 | Premium 5-20% |
| 5-6 | 同价，品牌是 tiebreaker |
| 1-2 | 必须打折才能竞争 |

## 证据强度

每条证据必须标注强度。Hard evidence = 公开数字。好 moat 分析至少有一个 Hard。

| 强度 | 定义 | 怎么找 |
|---|---|---|
| **Hard** | 可量化，公开可查 | 毛利率 vs peer 10 年、客户集中度、替换 case study、ROIC 历史 |
| **Medium** | 可观察但未量化 | 行业访谈提到导入周期、客户 RFQ 频率、供应商 list 变化 |
| **Soft** | 只能定性 | "业内公认"、"据说"、agent 推断 |

## 输出结构

> **Source contract**：以下所有表格中涉及估值、概率、评分、回报、市场规模数字的列，每行必须带 source anchor（[S#](url) 或 [I#](url)）。
>
> **密度表**：
>
> | Section | 强制标 source | 豁免 |
> |---|---|---|
> | Moat Scorecard | 每行 Evidence 列的具体数字/事件+source | 评分本身 |
> | 竞争格局对比 | 每家 peer 的市占率/利润率/定价数据 | — |
> | Switching cost/Barrier | 每个 barrier 的量化证据（合同期限/替换成本/认证周期） | — |
>
> **完成 Gate**：写完扫 scorecard → 每行 Evidence 有 [S#]/[I#] → `[待查]` 行 ≤3 → Resources 展开。

~~~markdown
## Moat Scorecard

| 维度 | Score | Evidence | Strength | Peer A | Peer B |
|---|---|---|---|---|---|
| 技术壁垒 | 9 | 贴片精度 1m，只有 Besi/ASMPT 能跟；R&D/$rev = 15% vs peer 8% | Hard | 8 | 5 |
| 客户锁入 | 7 | 固晶+耦合成套捆绑，替换需 6-12 月；但目前没有大客户真换过的 case | Medium | 6 | 4 |
| 规模效应 | 5 | Rev doubled in 3Y, gross margin +300bp | Hard | 6 | 4 |
| 监管/认证 | 3 | — | Soft | 3 | 3 |
| 品牌 | 4 | 瑞典品牌，中国市场无溢价 | Soft | 6 | 3 |
| **Total** | **5.6** | — | — | **5.8** | **3.8** | Ev |

## Moat Trajectory

| 维度 | 当前 | 3 年后 | 驱动 |
|---|---|---|---|
| 技术壁垒 | 9 | → 9 (stable) | 1.6T 精度要求继续筛人 |
| 客户锁入 | 7 | → 8 (widening) | CPO 耦合成套进一步加深绑定 |
| 规模效应 | 5 | → 6 (widening) | GT 订单规模增长 |
| 监管 | 3 | → 3 (stable) | — |
| 品牌 | 4 | → 5 (widening) | CPO 量产验证提升行业认知 |

## Visual

**Moat Radar** (description; actual chart via research-viz):
        技术壁垒 (9)
            ▲
           /|\
          / | \
品牌  |  |  客户锁入
(4) --+-- (7)
          | 
          |
        规模 (5) ---- 监管 (3)

## Killer Question

如果一家 PE fund 给你 $2B 让你 3 年内复制这个业务：
- 最难的环节是什么？（= 最深壁垒）
- 需要多少人和时间？（= 规模效应+技术壁垒的量化）
- 你第一年会从哪里挖人？（= 人才壁垒）
- 客户为什么不换？即使你便宜 20%？（= 客户锁入的真实强度）
~~~

## 反模式
    
    - ❌ 没有评分 anchor——8 分和 7 分的区别说不清
    - ❌ 不做 peer 对标——moat 不能自言自语
    - ❌ 证据不标强度，全是 Soft
    - ❌ 没有 Hard 证据却有 9 分以上
    - ❌ 不做 moat trajectory——只给 snapshot
    - ❌ 不出 killer question
    - ❌ 不看毛利率 trend vs peer——看毛利率绝对值没用，看 dispersion
    - ❌ 把 market share 当 moat（份额高可能是价格战抢来的）
    - ❌ 把一代产品的优势当结构壁垒
    - ❌ 不在下一代范式下重新评估
    
    ## 篇幅基准
    
    600-1000 字 + 1 scorecard + 1 trajectory 表 + radar chart + killer question。
    
    ## Workflow 联动
    
    | 上游 | 取什么 |
    |---|---|
    | `mechanism-insight` | 技术壁垒的工程基础 |
    | `driver-map` | 规模/成本证据 |
    | `company-history` | 历史竞争位演变 |
    | `peer-deep-dive` | 同行对标数据 |
    
    | 下游 | 场景 |
    |---|---|
    | `alpha-thesis` | moat → thesis conviction |
    | `peer-deep-dive` | moat 评分嵌入 §4.3 |
    
    ## 与相邻 skill 的边界
    
    - 不做技术原理 → `mechanism-insight`
    - 不做管理层评估 → `capital-allocation`
    - 不做完整 thesis → `alpha-thesis`
    

## Appendix: actuals-resolved.json

完整字段清单 -> `references/actuals-data-catalog.md`。

结构：`meta` / `market_data` (15 field) / `statements.income_statement` (13 field) / `statements.balance_sheet` (10 field) / `statements.cash_flow` (4 field) / `segments` / `supplementary` / `source_map`。

消费规则：先读 actuals -> source_map 取 [S#]/[I#] 标签（不写 [actuals]）-> ratio 只用 actuals 真实值（不用 forward estimate）。
