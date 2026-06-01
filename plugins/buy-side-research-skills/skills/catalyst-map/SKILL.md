---
name: catalyst-map
description: Full timeline catalyst chain with probability estimation, asymmetric payoff, and time density analysis.
---

# Catalyst Map

Map every catalyst on a timeline with probability, magnitude, direction, and payoff ratio. Not a calendar — a probability-weighted payoff matrix that tells you which events are worth researching and which are noise.

## Research Runtime Capsule

- Hook-enforced rules (source boundary, structure floor, table render) live in workspace hooks.
- Shared runtime baseline: `skills/_shared/research-policy-baseline.md` + workspace `CLAUDE.md`.
- **数据管道**：调用 `/financial-data --lite <ticker>` 获取 baseline 和 earnings dates。
- Sub-agent outputs: evidence_cards_only; main agent synthesizes.

## 心法

好的 catalyst map 回答的不是"接下来有什么事"——而是"哪些事如果发生了会改变 thesis，哪些即使发生了也无关紧要"。大多数 catalyst 的上下行不对称——miss 跌 5%、hit 涨 20%。payoff ratio >3x 的 catalyst 是你该配研究资源的。ratio <1x 的 catalyst 不值得花时间盯。

第二个误区：把时间点当 catalyst。"Q2 财报"不是 catalyst，Q2 财报里的"GT 订单 >SEK 350M"才是。Agent 必须把每个事件精准化到可验证的具体数字。

第三个误区：概率不是精确的——但也不是瞎拍的。有三个锚：历史 base rate、当前进度 proxy、外部验证信号。好的 catalyst map 会告诉你"这个概率是用哪个锚推出来的"。

## 触发场景

- "画 xxx 的催化剂时间线"
- "xxx 有什么 catalyst"
- "接下来 12 个月哪些事会影响 thesis"
- "哪些 catalyst 最值得盯"

## 方法论

### 概率估计（三个锚，至少标一个）

| 锚 | 做法 | 适用 |
|---|---|---|
| **历史 Base Rate** | 公司/同行业过去类似事件的 hit 率 | 重复事件（季度 beat、产品交付节点） |
| **进度 Proxy** | 公告措辞变化、时间线调整、供应商/客户信号 | 一次性事件（CPO 量产验证） |
| **外部验证** | 行业峰会 demo、客户 capex 指引、供应链 leak | 技术节点、订单、客户导入 |

### 上下行不对称

| 概念 | 说明 |
|---|---|
| **Payoff Ratio** | = 命中时幅度 / 落空时幅度（绝对值）。Ratio >3x → 最值得盯 |
| **Noise** | 命中涨 5%、落空跌 5% → ratio 1x → 不值得盯 |

### 时间密度

催化剂不均匀分布。财报季高密度、其余时间稀疏。高密度时段重配资源。

## 输出结构

~~~markdown
## Catalyst Timeline

| 时间 | 催化剂 | 概率 | 方向 | 幅度 | Payoff Ratio | 锚 | Thesis Impact |
|---|---|---|---|---|---|---|---|
| 2026 Q3 | Q2 GT orders >SEK 350M | 40% | ↑ | +15% | 3.0x | Base rate: 4Q中2Q超 | 验证 1.6T 升级 driver |
| 2026 Q4 | 英伟达 Rubin 含 CPO | 25% | ↑ | +25% | 5.0x | Proxy: 架构泄露信号 | CPO 路线验证 |
| 2027 H1 | 猎奇专利败诉 | 30% | ↑ | +20% | 2.0x | Base rate: plaintiffs ~60% | MRSI 竞争出清 |
| 2026 H2 | FPGA 缺货缓解 | 50% | ↑ | +5% | 1.0x | Proxy: lead time缩短 | 解除瓶颈，已 price in |
| 2026 Q4 | Semi 周期下行 | 20% | ↓ | -15% | — | Base rate: cycle avg | 全行业 de-rate |

## Payoff Matrix

| Rank | Catalyst | Payoff Ratio | Weighted Impact |
|---|---|---|---|
| 1 | Rubin 含 CPO | 5.0x | +6.3% (25% × 25%) |
| 2 | GT >350M | 3.0x | +6.0% (40% × 15%) |
| 3 | 猎奇败诉 | 2.0x | +6.0% (30% × 20%) |

## Visual

**Timeline** (ASCII):

    2026 Q3 ─── Q4 ─── 2027 H1 ─── 2027 H2
   │         │         │           │
   │ GT ▲    │ Rubin ▲│ 猎奇 ▲    │ COUPE?
   │ 40%     │ 25%     │ 30%       │
   │ +15%    │ +25%    │ +20%      │
   │         │         │           │
            │ FPGA ▼  │
            │ 50%     │ ← noise
            │ +5%     │

    Density: Q3-Q4 = HIGH (3 catalysts in 6M) — allocate research time.
~~~

## 反模式

- ❌ "Q2 财报"当 catalyst——精准到具体数字
- ❌ 没有概率——"可能涨"不是 catalyst
- ❌ 没标上下行不对称
- ❌ 只有上行没有下行
- ❌ 概率不标锚——40% 从哪来的
- ❌ 不和 thesis 联动
- ❌ 全是"如果...就..."——至少一半该有进度 proxy
- ❌ 不区分 payoff ratio——权重全一样
- ❌ 下行 catalyst 也标"payoff ratio"——下行谈 severity

## 篇幅基准

500-800 字 + 1 timeline 表 + 1 payoff matrix + ASCII timeline。

## Workflow 联动

| 上游 | 取什么 |
|---|---|
| `consensus-map` | 哪些已经 priced in |
| `financial-data` | 历史 beat rate、earnings dates |
| `earnings-setup` | 单次 pre-print bar |

| 下游 | 场景 |
|---|---|
| `alpha-thesis` | catalyst → conviction |
| `candidate-screener` | §6 catalyst 日历 |
| `post-earnings-quick` | 验证 catalyst 是否触发 |

## 与相邻 skill 的边界

- 不做财报 setup → `earnings-setup`
- 不做 thesis → `alpha-thesis`
- 不做 market expectations → `consensus-map`
