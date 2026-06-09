# Bridge Priority Routing — Scenario-Based Data Pipeline

> 状态: implemented
> 日期: 2026-06-09
> 版本: v5.16.0

---

## 背景

v5.15.0 引入了 Longbridge MCP 作为 trusted third-party 市场数据层，但 CLAUDE.md §4.1 的路由逻辑是一刀切——所有公司在所有场景下走同一条链。实际场景有两个关键维度：

1. **actuals 是否已缓存**（有的公司拉过了，有的没有）
2. **上下文是什么**（日常对话 vs 写 artifact）

## 设计

### 概念层级

```
Source-of-record 层：actuals-resolved.json（本地，已缓存的公司财务事实）
Bridge 层：           Bridge（抽象，当前实现 = Longbridge MCP，覆盖 US/HK/SH/SZ/SG）
                     ↓ 未来扩展更多 source 不改上层路由
市场兜底层：          yfinance → WebSearch / WebFetch
```

### 三重判断

1. 问的是哪种数据？── 市场快照 / 财务快照 / 结构化三表
2. actuals 是否已缓存？── 先扫 `industry/*/companies/<ticker>/_cache/financial-data/actuals-resolved.json`
3. 上下文是什么？── 日常对话（秒回优先）/ 写 artifact（准确性优先）

### 路由表

| 数据类别 | actuals 已有 | actuals 没有 |
|---|---|---|
| 市场快照（报价/K线/估值/新闻/评级/日历/汇率/资金/股息/情绪） | Bridge → yfinance → WebSearch | Bridge → yfinance → WebSearch |
| 财务快照（日常对话：收入/EPS/ROE） | ① Read actuals → ② Bridge latest Q → ③ 不一致 prefer Bridge 时效性 | Bridge financial_report_latest → yfinance snapshot → 追问建议 CLI |
| 结构化三表（artifact Step 1） | 读 actuals → /financial-data --lite 增量更新 | /financial-data --lite（强制） |
| 多期FY对比 | 读 actuals → 过期 >180天 提醒 | /financial-data --lite --periods |

### Fallback 链

```
Bridge（US/HK/SH/SZ/SG 首选）
  ↓ 不可用 / 超时 / 未覆盖
yfinance
  ↓ 也不可用
WebSearch / WebFetch
```

### Bridge 抽象

- Bridge 是 trusted third-party 市场数据聚合层，不绑定具体实现
- 当前实现 = Longbridge MCP（145 工具，验证 34 domain）
- 覆盖：US/HK/SH/SZ/SG
- 以后扩展新 source 加入 Bridge 层，上层路由不改变

## 与现有系统关系

- `trusted-market-bridge` skill：Bridge 层的 MCP 工具映射（已验证）
- `financial-data` CLI：source-of-record，仅在写 artifact / 需要多期 actuals / 需要 primary public provider 时调用
- CLAUDE.md §4.1：路由规则（本文）
- init-workspace Step 8：Longbridge MCP 安装（skippable）

## 不做

- 不让 yfinance 成为用户可见的独立 tier（是 CLI 内部细节）
- 不自动在每日对话触发 financial-data CLI
- 不在 Bridge 层做实际数据缓存（由 actuals 和 _cache 负责）
