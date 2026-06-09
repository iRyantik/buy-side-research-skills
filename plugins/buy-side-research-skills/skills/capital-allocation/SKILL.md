---
name: capital-allocation
description: Score management capital allocation — buyback timing, dividend, M&A ROI, capex efficiency with 10Y record and anchored scoring.
---

# Capital Allocation

Score management's capital allocation quality over a 10-year window. The biggest wealth creation or destruction doesn't happen in operations — it happens in the CFO's office.

## Research Runtime Capsule

**执行本 skill 前必须先读取以下文件：**
- workspace `.references/runtime/research-runtime.md` §1（数据获取链）§2（来源验证链）§2.1（资料收集）§2.2（Source 纪律）§2.5（图片下载链）§4（产出合约）§5（保存合约）

**自动 Hook 防御：** `pre_write_gate`（source/tables/mermaid/image）`source_contract` `table_render_integrity` `mermaid_syntax` `skill_structure_contract` `evidence_ledger_floor`

**GATE**: Read workspace `.references/runtime/research-runtime.md` BEFORE any action. All runtime rules in that file + hooks — capsule only states what is unique to this skill.

## 心法

管理层最重要的决策不是战略——是钱怎么花。同一个行业、同一条赛道，资本配置好和差的管理层可以导致 3-5x 的长期股东回报差距。判断资本配置不是看"花了多少钱"——是看"每一块钱赚回多少"。buyback 在股价低位时是 value-accretive，在高位时是价值破坏。M&A 宣布时涨 5% 没用——要看 3-5 年后这条业务是 independent growth engine 还是 write-off。

核心问题只有四个：他们怎么花 surplus cash？花的时候价钱对不对？花完以后回报怎么样？这种行为在 strengthen 还是 deplete 护城河？

## 触发场景

- "xxx 管理层钱花得怎么样"
- "分析 xxx 的资本配置"
- "xxx 的 buyback 是创造价值还是毁灭价值"
- "xxx 的 M&A track record"

## 四维度评分

### 1. Buyback（回购）[→ Bridge: financial_snapshot, dividend]

| 分数 | 标准 | 怎么看 |
|---|---|---|
| 9-10 | 持续在低位回购，高位不回购；buyback yield > dividend yield | 查 10 年回购量和股价的 overlay——回购集中在低谷期 = 加分 |
| 7-8 | 回购稳定但 timing 一般 | |
| 5-6 | 回购和股价不相关——像自动程序 | |
| 3-4 | 高位大幅回购、低位不回购 | |
| 1-2 | Buyback 用途是 offset SBC dilution，不是 return capital | 如果 shares outstanding 没变——buyback 全被 SBC 吃掉了 = 负分 |

### 2. Dividend（分红）

| 分数 | 标准 |
|---|---|
| 9-10 | Payout ratio 30-40% 持续 10 年，从未削减 |
| 7-8 | Payout <30% 但稳定增长 |
| 5-6 | Payout 波动大，随利润摇摆 |
| 3-4 | Dividend > FCF——借钱发股息 |
| 1-2 | 从未分红，且 surplus cash 被浪费 |

### 3. M&A ROI（并购回报）

这是最难的一项——不能只看 announcement return，要看 3-5 年后的真实 ROI。

| 分数 | 标准 | 怎么看 |
|---|---|---|
| 9-10 | 有一个 transformative deal，3-5 年后贡献了公司 30%+ 的收入且有独立 moat | Mycronic 买 MRSI: $125M → 现在 GT 部门年收入 SEK 2B+ |
| 7-8 | 多个 small tuck-in，整合成功，无明显 write-off | |
| 5-6 | M&A 积极但回报看不清 | |
| 3-4 | 有大 write-off 或 goodwill impairment | |
| 1-2 | Empire building——为规模而买、买贵了、文化冲突 | |

**关键数据**：每个 >5% market cap 的 deal，查 3 年后那条业务的 revenue/profit contribution。如果 disclosure 不够，标 [披露不足]。

### 4. Capex 效率

| 分数 | 标准 |
|---|---|
| 9-10 | ROIC >20% 持续 5 年+，capex/revenue 稳定且产生 organic growth |
| 7-8 | ROIC 15-20% |
| 5-6 | ROIC 10-15% |
| 3-4 | ROIC <10% |
| 1-2 | CapEx > operating CF——在烧钱，且无 revenue acceleration |

## 与 Moat 的关系

这是 agent 必须回答的关键桥接：**这管理层是在加强还是在削弱护城河？**

- 好 moat + 好 capital allocation = compounder（MYCR 式：精度壁垒 + 聪明并购）
- 好 moat + 差 capital allocation = 价值陷阱（高 ROIC 但 surplus cash 被浪费）
- 差 moat + 好 capital allocation = 也救不了（好 CFO 改变不了行业底层）
- 差 moat + 差 capital allocation = 不研究

## 输出结构

> **Source contract**：Scorecard 评分、ROIC/FCF/conversion 数字、buyback yield 等每行必须带 source anchor。
>
> **密度表**：
>
> | Section | 强制标 source | 豁免 |
> |---|---|---|
> | Scorecard 表 | 每行 10Y Evidence 列的 scoring basis 数字 | 评分本身 |
> | 资本配置历史 | 每笔 M&A/repo/dividend 的金额+时间 | 定性描述 |
> | ROIC/FCF 趋势 | 每个年份的 ROIC/FCF/conversion 值 | 趋势方向解读 |
>
> **完成 Gate**：写完扫 scorecard → 每行 anchor 列有 [S#]/[I#] 或 `[待查]` → `[待查]` ≤3。

```markdown
## Capital Allocation Scorecard

| 维度 | Score | 10Y Evidence | Anchor |
|---|---|---|---|
| Buyback | 7 | 2020/2023 低位回购，2025 高位未回购；buyback yield avg 2% | Shares outstanding -8% in 10Y; SBC dilution ~1%/yr → net -7% |
| Dividend | 8 | 10 年连续增长，payout ratio 30-40% | Never cut; yield 1.5-2% |
| M&A ROI | 9 | MRSI $125M → GT division now 30%+ revenue | 3-5Y post-deal ROI estimate: 15x+ |
| Capex | 6 | ROIC 15-18%，capex/revenue 8-10% | Cycle-dependent; high capex years ROI dips to 12% |
| **Total** | **7.5** | — | — |

## Visual

**10Y Capital Flow** (ASCII bar or research-viz):
Buyback:   $800M
Dividend:  $600M
M&A:       $500M  (incl. MRSI $125M)
Capex:     $1.2B
─────────────────
Total deployed: $3.1B
```

Market cap created: $4.5B (10Y ago $1.5B → today $6B)
ROI on deployed capital: ~145%

## Moat Bridge

- MRSI 并购 → 固晶+耦合成套 → moat 加深（技术壁垒 8→9, 客户锁入 6→7）
- 分红稳定 → 没有削弱 moat（没有因为钱不够少投研发）

## 反模式

- ❌ 只看最近两年 buyback——timing 需要 10 年视角
- ❌ 不看 SBC dilution——buyback 被 SBC 吃掉的等于没回购
- ❌ M&A 看 announcement return 而不是 3-5Y ROI
- ❌ 不打分、不标 anchor
- ❌ 不做 moat bridge——资本配置和护城河脱节
- ❌ 不比较 surplus cash 的其他用途（比如不回购能不能多投研发）
- ❌ dividend > FCF 不标红色（借钱发股息）
- ❌ 只看金额不看 ROI——$5B capex 不重要，ROIC 才重要

## 篇幅基准

30-50 行 + 1 scorecard + 1 capital flow 图 + 1 moat bridge。

## Workflow 联动

| 上游 | 取什么 |
|---|---|
| `Skill("buy-side-research-skills:financial-data", "<TICKER> <market> --periods FY2010-FY2025")` 或 CLI fallback | 10 年 CF：buyback/dividend/capex/M&A |
| `company-history` | 并购整合记录 |
| `moat-analysis` | Moat scorecard → bridge |

| 下游 | 场景 |
|---|---|
| `alpha-thesis` | 管理层可信度 → thesis conviction |

## 与相邻 skill 的边界

- 不做 moat → `moat-analysis`
- 不做 thesis → `alpha-thesis`
- 不做估值 → `dcf-model` / `comps-analysis`


