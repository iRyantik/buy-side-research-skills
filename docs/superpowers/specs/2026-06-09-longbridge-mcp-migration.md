# Longbridge Plugin → MCP 迁移

> 状态: spec → 实现
> 日期: 2026-06-09
> 目标: v5.15.0

---

## 背景

长桥 MCP Server (`https://openapi.longbridge.com/mcp`) 提供 145 个工具，覆盖行情、财务、估值、新闻、日历、机构评级等全部能力。现有 80+ skill 的长桥插件可以被完全替代。

MCP 全局安装：
```bash
claude mcp add --transport http --scope user longbridge https://openapi.longbridge.com/mcp
```

---

## 改动清单

### 1. `trusted-market-bridge` SKILL.md + SKILL.en.md

**现状**：引用 Longbridge skill 插件调用（`Skill("longbridge:quote")` 等）

**改为**：
- 所有数据调用改用 MCP 工具：`mcp__longbridge__quote`、`mcp__longbridge__company`、`mcp__longbridge__financial_statement` 等
- Source 标签从 `[LBG#]` 改为 `[I#](longbridge)` 或保留 `[LBG#]` 但目标改为 MCP 来源
- 信任链更新：`MCP > yfinance > WebSearch > Google Finance`

### 2. `financial-data` SKILL.md + SKILL.en.md

**现状**：Market data fill engine Layer 2 引用 "Bridge" 层

**改为**：
- Layer 2 从 "Bridge(覆盖 US/HK/SH/SZ)" 改为 "MCP 长桥 (覆盖 US/HK)"
- Trust 排名：`MCP (longbridge) > yfinance > WebSearch > Google Finance`
- 删除对 Bridge skill 调用的依赖

### 3. `research-runtime.md` + `research-runtime.en.md`

**现状**：§1 数据获取链提到 "Bridge"、§2.2 提到 trust chain

**改为**：
- `Bridge > yfinance > ...` → `MCP (longbridge) > yfinance > ...`
- 市场快照轨：`MCP (longbridge US/HK) > yfinance > WebSearch > Google Finance`

### 4. 安装文档

**现状**：需要安装 `longbridge-skills.zip`

**改为**：
```bash
claude mcp add --transport http --scope user longbridge https://openapi.longbridge.com/mcp
# 然后 /mcp → longbridge → Authenticate
```

### 5. `init-workspace` assets

**`.claude/mcp.json` 模板**：不加 longbridge 条目（用户全局安装，不绑 workspace）

**CLAUDE.md template**：§5.5 删除对 longbridge plugin 的引用，改为 MCP

### 6. Release package

`longbridge-skills.zip` 从 repo root 删除，不再作为 companion asset 发布。

---

## 不改

- 现有 `longbridge@longbridge-skills` 插件不卸载——用户如果装了继续能用，不强删
- `[LBG#]` source label 格式保留（已有 source_contract 支持）
- `trusted-market-bridge` skill 本身不删除——它仍是 market data 的 routing 层，只是底层从 plugin 切到 MCP

---

## 执行

```
1. trusted-market-bridge SKILL.md + SKILL.en.md — 工具引用更新
2. financial-data SKILL.md + SKILL.en.md — Bridge → MCP
3. research-runtime.md + research-runtime.en.md — trust chain
4. CLAUDE.md.template + CLAUDE.en.md.template — 删 longbridge plugin 引用
5. init-workspace docs — MCP 配置指引
6. 删 longbridge-skills.zip
7. CPR v5.15.0
```
