# Edge Radar

> 本文件是 research workspace 的问题雷达，不是状态库，也不是交易日志。

## 使用原则

- 只记录能改变研究优先级的问题类型。
- 不记录 raw reminders、未验证灵感、交易状态或 daily todo。
- 每个问题都应能 handoff 到一个更具体的 skill。

## 高价值问题类型

| Signal | 典型症状 | 下一步 |
|---|---|---|
| Business reality gap | 披露名称和真实经济实质不一致 | `company-history` |
| Know-how gap | 工艺、设备链、工程原理或术语没搞清楚 | `mechanism-insight` |
| Driver gap | revenue / margin / backlog / price-volume-mix 没拆清 | `driver-map` |
| Consensus gap | 市场预期、priced-in assumptions 或 buy-side bar 没拆清 | `consensus-map` |
| Primary evidence gap | 关键假设需要 expert call、channel check、survey 或 fieldwork 验证 | `primary-research-plan` |
| Source conflict | filing、IR deck、call、新闻或卖方口径冲突 | `information-impact` |
| Peer mismatch | 市场把公司放进错误 peer group | `peer-deep-dive` |
| Thesis fragility | variant view、catalyst 或 kill criteria 不成立 | `alpha-thesis` / `bear-pre-mortem` |

## 提醒格式

```markdown
**这里值得深挖**
- 怪异点：[哪里不自然]
- 可能说明：[1-2 个解释]
- 可以问 AI：[1-2 个最关键问题]
```
