---
name: post-earnings-quick
description: Post-earnings 5-min verdict — three-dimension beat/miss judgment with thesis impact decision.
---

# Post Earnings Quick

Five-minute post-print verdict. Not a full review — a rapid three-dimension check: did they beat or miss versus the pre-print bar? Did guidance move? Does the thesis still hold?

## Research Runtime Capsule

**执行本 skill 前必须先读取以下文件：**
- workspace `.references/runtime/research-runtime.md` §1（数据获取链）§2（来源验证链）§2.1（资料收集）§2.2（Source 纪律）§2.5（图片下载链）§4（产出合约）§5（保存合约）

**自动 Hook 防御：** `pre_write_gate`（source/tables/mermaid/image）`source_contract` `table_render_integrity` `mermaid_syntax` `skill_structure_contract` `evidence_ledger_floor`

**GATE**: Read workspace `.references/runtime/research-runtime.md` BEFORE any action. All runtime rules in that file + hooks — capsule only states what is unique to this skill.

## 心法

财报后第一件事不是读财报——是找基准。没有基准的 beat/miss 判断是噪音。基准按优先级：earnings-setup 的 pre-print bar → consensus range → prior year same-quarter trend。找不到基准就直说"没有基准，不做判断"。

第二个陷阱：beat 了 2% 但 guidance 下来了——是好还是坏？机械判断 beat=好会漏掉最重要的信号。**三维判断**：actuals vs bar、guidance vs prior guidance、quality of beat（是一次性 gain 还是 recurring 改善）。

500 字硬上限。这不是深度分析——是快速的 thesis 方向性检查。做完 5 分钟该出 verdict。

## 触发场景

- "xxx 出财报了 快速看下"
- "MYCR 刚出了 Q2 怎么样"
- "这个 quarter 的财报对 thesis 有什么影响"

## 基准优先级

```
1. 同 ticker 最近的 earnings-setup artifact（pre-print bar 最准）
2. Consensus range（从 /financial-data market_data 或 WebSearch）
3. Prior year same-quarter growth trend（最弱的 proxy——去年有 COVID/M&A 就不准）
4. 都没有 → "没有基准，不判断方向，只列数字和 guidance 变化"
```

## 三维判断

| 维度 | 问题 | 怎么看 |
|---|---|---|
| **Actuals vs Bar** | Revenue/EPS beat or miss? | 2%+ = beat, -2% = miss, between = in-line |
| **Guidance** | Guidance vs prior guidance / consensus | Guidance raise > actuals beat。Guidance cut > actuals beat——管未来的指导比管过去的数字重要 |
| **Quality** | Beat 是一次性的还是 recurring 的？ | 税收 benefit、asset sale、FX gain = 一次性。Organic growth beat、margin expansion from scale = quality |

综合：如果 beat 了 revenue 但 guidance cut → thesis 要 re-examine。如果 miss 了但 guidance raise（cost cutting 生效、order pipeline 加速）→ thesis 可能 strengthen。

## 输出结构

```markdown
## Verdict [→ Bridge: financial_snapshot_detail]

**Beat — thesis unchanged** （或其他组合）

| Metric | Actual | Pre-Print Bar | Consensus | Beat/Miss |
|---|---|---|---|---|
| Revenue | $1.2B | $1.15B | $1.18B | Beat +4% |
| EPS | $0.45 | $0.42 | $0.43 | Beat +7% |

## Guidance

| Guidance | Prior | Consensus | Direction |
|---|---|---|---|
| FY revenue | $5.0-5.2B | $4.8-5.0B | $5.1B | Raised |

## Quality Check

- Revenue beat: +4%, driven by GT orders +8% QoQ — organic, recurring
- EPS beat: +7%, FX tailwind ~2% — partially non-recurring
- No one-time items of concern

## Thesis Impact

**Thesis: unchanged.** 1.6T upgrade driver intact. GT orders beat supports thesis. Guidance raise consistent with our base case.

**Next**: update coverage-tracker. No need to re-do stock-quickread. Monitor next catalyst: Q3 GT orders (Oct 2026).

> Hard cap: 500 words. Do not write a full earnings review. If you need more space, handoff to `stock-quickread` or `driver-map`.
```

## 反模式
    
    - ❌ 没有基准就说 beat/miss——必须找到 bar
    - ❌ beat/miss 只看 actuals 不看 guidance——guidance 更重要
    - ❌ 不分一次性 vs recurring
    - ❌ 超过 500 字——写成 full review
    - ❌ thesis 状态不判断——"有待观察"不是判断
    - ❌ 不更新 coverage-tracker
    
    ## 篇幅基准
    
    20-33 行硬上限。超了就是做错了。
    
    ## Workflow 联动
    
    | 上游 | 取什么 |
    |---|---|
    | `earnings-setup` | pre-print bar |
    | `financial-data` | actuals + consensus |
    | `consensus-map` | 如果没有 earnings-setup |
    
    | 下游 | 场景 |
    |---|---|
    | `stock-quickread` | thesis needs full review |
    | `coverage-tracker` | 更新 stage/priority |
    | `driver-map` | guidance 改变 driver 假设 |
    
    ## 与相邻 skill 的边界
    
    - 不做财报前准备 → `earnings-setup`
    - 不做深度财报分析 → `stock-quickread`
    - 不做 thesis 改写 → `alpha-thesis`
    
