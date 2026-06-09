# stock-quickread Pipeline Bug Fixes

> 状态: spec
> 日期: 2026-06-09
> 目标版本: v5.14.3

---

## Fixable（插件可控）

### #1 Skill 工具无法识别 namespace skill

**修**: stock-quickread SKILL.md Step 1 从 `/financial-data <ticker>` 改为直接命令：

```
python .scripts/financial-data/financial_data.py
  --market us --identifier <TICKER> --company-slug <slug> --mode lite
```

不再依赖 `Skill("financial-data")` 调用。加一个简化的 agent 指令："如果 `Skill` 工具可用则调 `/financial-data`，否则跑上面的直接命令。"

### #2 CLI 参数名是 --identifier 不是 --ticker

**修**: SKILL.md 中所有示例从 `--ticker <TICKER>` 改为 `--identifier <TICKER>`。

**范围**: stock-quickread + financial-data SKILL.md 中所有 CLI 示例。

### #4 actuals-to-appendix.py 扫不到 actuals

**修**: 脚本内搜索路径更新。现在 `actuals-resolved.json` 在 `_cache/financial-data/actuals-resolved.json`（v5.13.13 改的），脚本可能还在扫 `_cache/datasets/` 或 `internal/`。更新搜索逻辑。

### #5 actuals-to-appendix.py 不在 workspace

**修**: 脚本在 `skills/financial-data/scripts/actuals-to-appendix.py`，需确认 init-workspace 的 C2 规则会把它部署到 `.scripts/financial-data/actuals-to-appendix.py`。确认 financial-data skill 没有 `.platform` 标记（scripts 会被自动部署）。

如果路径是 `.scripts/financial-data/actuals-to-appendix.py`，skill 文档就用这个路径。

### #6 evidence_ledger auto 缺少 -t TICKER

**修**: SKILL.md pipeline Step 7 写完整命令：

```
python .scripts/evidence_ledger.py auto <artifact> -t <TICKER>
```

### #7 evidence_ledger lint 参数

**修**: 同上，lint 命令也补全：

```
python .scripts/evidence_ledger.py lint <artifact> -t <TICKER>
```

---

## Won't Fix（平台/环境限制）

### #3 lite mode market_data 缺失
yfinance 在中国可能被墙或限速。不是代码 bug，是网络环境。可以在 SKILL.md 加 fallback 指令但不改代码。

### #8 图片下载跳过
v5.14.0 已修复 `sys.stdout.reconfigure`。如果最新版仍然跳过，那是 Agent 纪律问题——v5.14.2 的 pipeline discipline 应该覆盖。

### #9 WebSearch API 400
deepseek-v4-pro 模型跟 WebSearch 工具不兼容。这是 Claude Code 平台问题，插件管不到。

### #10 Playwright MCP 不稳定
MCP server 连接问题是 Claude Code 基础设施，插件管不到。

---

## 改动清单

| 文件 | 改动 |
|---|---|
| `stock-quickread/SKILL.md` Step 1-8 | #1 直接命令 + #2 --identifier + #6 #7 补全参数 |
| `stock-quickread/SKILL.en.md` | 同上英文 |
| `financial-data/scripts/actuals-to-appendix.py` | #4 搜索路径更新到 `_cache/financial-data/` |
| 确认 `financial-data/.platform` 不存在 | #5 确保脚本自动部署 |

---

## 执行

```
1. 确认 financial-data/.platform 不存在
2. 修 actuals-to-appendix.py 搜索路径
3. 修 stock-quickread SKILL.md Step 1-8 全链
4. 修 SKILL.en.md 同步
5. CPR v5.14.3
```
