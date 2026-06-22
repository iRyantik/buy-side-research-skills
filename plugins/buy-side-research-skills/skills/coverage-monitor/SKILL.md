---
name: coverage-monitor
description: Generate daily coverage briefs and intraday material-event alerts from workspace coverage state.
---

# Coverage Monitor

`coverage-monitor` turns workspace coverage state into a monitoring loop: normalize `COVERAGE.md`, build the watchlist from researched companies, generate a dashboard-style daily brief, and send email delivery with the full HTML attachment. It is an operations skill, not a research skill.

## 心法

这个 skill 解决的不是“再写一份研究”，而是把已经沉淀在 workspace 里的 coverage 状态变成可执行的监控面板。它默认服务亚洲时区的 buy-side researcher：白天盯本地和欧洲，晚上快速接美股 post-print 和盘中异动。

失败方式通常有两个：一是把它做成持仓/P&L 跟踪器，开始掺 portfolio 管理；二是把 alert 门槛做得太松，最后噪音比信息还多。v1 固定只围绕 `COVERAGE.md`、研究优先级和 material event 提醒，不越界。

## 职责边界

负责：

- 读取 workspace `COVERAGE.md` 的 `## Coverage` 表作为 ticker/company/coverage-status source of truth。
- 用 `industry/*/companies/*` 已有研究产物补充 artifact path、latest artifact、artifact_count。
- 对 `stock-quickread` / deep-work artifact 落盘后的 coverage workflow 做 objective 检查：quickread 进 `Building`，deep-work 只触发 `Core` review，不盲目自动升级。
- 规范化 coverage 表到 canonical 列。Coverage: `Core` / `Building` / `Radar`。Monitor: `Core` / `Daily`。
- 生成 dashboard-style daily coverage brief：4 tabs 固定为 `Movers` / `Core Watch` / `Industry Tape` / `Universe`。
- 用更严格的 mover contract 筛选普通异动与重要异动：普通异动 `5% / 3.0x / 7%`，重要异动 `8% / 4.0x / 10%`。
- Industry Tape 三层新闻采集：RSS feed（Substack `/feed` + trade pub 自动发现）→ Playwright 无头浏览器刮首页 → Agent WebSearch domain 搜索。
- 对无 RSS 的 P1 trade pub 自动 Playwright 刮首页头条，刮不到标记 agent fallback。
- 每个行业 source 池由 `RESEARCH.md` 的 `### Daily Signal Sources` 表定义，按 Tier 区别对待。
- Mover explainer：对所有异动（重要+普通）生成中文 summary + evidence link。普通异动默认收起，点击展开。
- Core Watch 每只股票合成一句话中文总结，显示最近关键事件。
- 日报通过 agent enrichment JSON（`--enrichment`）注入 agent 搜索结果：mover explainers、core_watch_news、industry_summaries、industry_searches。
- `--skip-fetch` 支持缓存重渲染（0.3s），agent 搜完新闻后即时更新日报。
- Universe 表价格按市场格式化（¥/₩/$/€ + 市场规则小数位），Partial 状态用琥珀色圆点`·`轻标记。
- IPO pending / private ticker 自动跳过 yfinance 采集。
- 通过 email 发送摘要正文 + 完整 HTML 附件。
- 缺少行情、新闻或发送凭证时 honest fail，保留 gap。

不负责：

- 不跟踪持仓、成本、PnL、exposure 或 broker 账户。
- 不改写研究结论，不生成 thesis。
- 不依赖 FMP / EODHD / 其他付费 API 才能工作。
- 不做个人微信自动化。
- 不负责安装 OS-level 定时任务；本轮 daily 是手动触发。

## Agent 新闻搜索语言规则

Agent 对 Core Watch / Mover 做 WebSearch 时，按市场使用本地语言：

| 市场 | 搜索语言 |
|---|---|
| CN / HK | 简体中文 |
| TW | 繁体中文 |
| JP | 日本語 |
| KS | 한국어 |
| US / EU / SE / UK / MY | English |

优先搜索本地财经媒体和交易所公告，而非通用新闻聚合。

## 每日标准流程（强制）

Agent 每次调 `daily` 必须走完整 5 步，不允许跳过 agent 搜索直接发报：

```
1. python run_coverage_monitor.py daily --dry-run
2. 读 agent_work gap → 获取 pending_movers / pending_core / pending_industries
3. Agent 基于脚本已搜好的 news items 写中文总结（不再搜原始新闻）:

   **脚本已做**: DDG 双语搜索 → 每只 Core Watch/Mover 返回 3-8 条 news items
   **Agent 做**: 读 news items → 写:
     - Core Watch: stock summary (一句话中文)
     - Mover explainer: summary + ≥2 条 evidence 引用
     - Industry summary: 基于 RSS + WebSearch 结果的中文段落

4. 写入 enrichment-YYYY-MM-DD.json
5. python run_coverage_monitor.py daily --enrichment <.json>
```

**硬门**：
- `agent_work` 的 `pending_*` 数字必须归零才算完成
- enrichment 文件名按日期——每天新文件，不重用
- Dry-run 不算完成——必须有 enrichment + 正式输出

**DDG 搜索**：脚本通过 `.scripts/shared/search.py` 自动搜，双语（Company Native + Company EN），其他 research skill 可复用。

## 触发与输入

触发短语包括：

- “coverage monitor”
- “daily coverage brief”
- “monitor my coverage”
- “send today's coverage brief”
- “覆盖日报”
- “盘中提醒”

输入：

| 输入 | 作用 |
|---|---|
| `workspace` | 可选。默认当前 workspace 根目录。 |
| `mode` | `doctor` / `normalize-coverage` / `daily` / `intraday` |
| `today` | 可选。覆盖日报日期；格式 `YYYY-MM-DD` |
| `dry_run` | 可选。渲染和检查，但不写文件、不发送 |

依赖输入：

- `COVERAGE.md` 为 coverage source of truth。
- `coverage-tracker` 维护 `Coverage` / `Monitor` / `Last Review` / `Next Trigger`。
- `industry/*/companies/*` 目录只补充已注册公司的 artifact metadata；有 `COVERAGE.md` 时未注册目录只进入 gap。
- 可选 delivery env：`SMTP_HOST`、`SMTP_PORT`、`SMTP_USER`、`SMTP_PASSWORD`、`COVERAGE_EMAIL_TO`。脚本会读取 workspace `.env`，不覆盖用户环境变量。

## 执行模式

### Mode A: `doctor`

检查 workspace 可见性、coverage 条目数和 delivery env 缺口。不写文件。

### Mode B: `normalize-coverage`

把旧版或混乱列头的 `COVERAGE.md` 规范成 canonical 表头。`--dry-run` 只打印结果。

### Mode C: `daily`

生成 dashboard-style 日报。HTML 固定为 4 个 tabs：

1. `Movers`
2. `Core Watch`
3. `Industry Tape`
4. `Universe`

其中 `Coverage Gaps` 不再单独占一个 tab，而是收进 `Universe` tab 的 contract / gap 区块。

正常模式写入：

```text
daily/YYYY-MM-DD-brief.md
daily/YYYY-MM-DD-brief.html
```

### Mode D: `intraday`

只对 `Core Watch` 名单扫描 material event。默认一轮运行；`--interval-minutes` 可循环。已发送事件去重，不重复轰炸。

## 工具资源

- Workspace script entrypoint: `python .scripts/coverage-monitor/run_coverage_monitor.py`
- Provider path: optional `yfinance` quote/news snapshot
- Search path: live web search first, then direct fetch / HTML parse, with Playwright as JS-heavy fallback only
- Delivery path: Python stdlib `smtplib` email only

示例命令：

```bash
python .scripts/coverage-monitor/run_coverage_monitor.py doctor
python .scripts/coverage-monitor/run_coverage_monitor.py normalize-coverage --dry-run
python .scripts/coverage-monitor/run_coverage_monitor.py daily --dry-run
python .scripts/coverage-monitor/run_coverage_monitor.py intraday --once --dry-run
```

## 文件安全

- 不直接修改用户 topic 研究产物。
- `normalize-coverage` 之外不改 `COVERAGE.md`。
- `daily` 只写 `reports/coverage-monitor/` 和 `.cache/coverage-monitor/state.json`。
- 不覆盖用户自定义 `.env` 内容，只读取 env。
- 不触碰 plugin dev repo 之外的 runtime 配置文件。

## 运行输出契约

默认输出短而可执行：

```markdown
## Coverage Monitor Result

**结论先行**
[本次运行做了什么：doctor / normalization / daily brief / intraday alerts]

## Coverage
- [watchlist 条目数]
- [Core Watch / Daily Watch 分布]

## Delivery
- [email sent / skipped]

## Gaps
- [...]
```

Daily brief 的 HTML 固定为 4-tab dashboard，风格参考 `today` 原型但内容按 coverage workflow 重构；Markdown 仍保留摘要和 universe 表，不再把 Markdown 包进 `<pre>`。`intraday` 只输出命中的 alert 名单和事件说明，不追加长篇研究分析。

关键 daily contract：

- `Movers` 只展示命中 mover threshold 的名字，不再因为 `near 20d high/low` 单独入选。
- 重要异动卡片默认并入 news + filing / official release 证据层。
- `Core Watch` 默认每天搜公司级 news，不等价格异动。
- `Industry Tape` 先扫 `Daily Signal Sources`，source 没有新东西时再 fallback general news。
- `Universe` 默认不显示 `OK`；quote freshness / data status 只在 `Partial` / `No Data` / `Stale` 时 exception-only 呈现。
- `Data Health` 只做轻量汇总，不做 appendix，不让状态系统抢正文版面。

Artifact policy：

- `save_policy`: `cache_artifact`
- `default_artifact`: `daily-coverage-brief.md`
- `canonical_location`: `daily/YYYY-MM-DD-coverage.md`

## 失败处理

- `COVERAGE.md` 缺失：继续从 `industry/*/companies/*` 发现已研究公司，并显式报告 gap。
- ticker 缺失 / `IPO pending` / `private`：保留在 coverage gaps，不做行情抓取。
- 多 ticker（如 `002487 CH / 1081 HK`）：第一个作为 quote primary，全部作为 search alias。
- `yfinance` 不可用：继续生成报告，标注 `yfinance_unavailable`。
- `search_link` 不算成功结果；没有结构化结果时必须保留 gap，而不是伪装“搜到了”。
- email 凭证缺失：继续生成报告，标注 delivery gap，不伪装成功发送。
- workspace 路径不存在：退出并返回非零状态。

## Workflow 联动

| 上游 | 作用 |
|---|---|
| COVERAGE.md (agent rule) | agent 产出 artifact 后自动维护，monitor 脚本跑前扫文件系统纠正 |
| `stock-quickread` | 首次出现自动注册 `Building Coverage` + `Daily Watch` |
| `alpha-thesis` / `peer-deep-dive` / `earnings-setup` / `scenario-model` / `driver-map` / `catalyst-map` | 产出后 `compute_coverage_tier()` 从文件系统自动判断是否 Core |
| `research-journal` | 解释 coverage 状态变化的原因 |

| 下游 | 作用 |
|---|---|
| researcher 日常工作流 | 每日收日报；Core Watch 名单盘中接提醒 |
| `/update-agent-runtime` | 把本 skill 的脚本同步到 workspace `.scripts/coverage-monitor/` |

## 安全自查

- ❌ 把这个 skill 写成研究报告模板。
- ❌ 把 `Coverage` 和 `Monitor` 绑定到主观 conviction。
- ❌ 引入 broker、PnL 或持仓字段。
- ❌ 缺 delivery env 还汇报“已发送”。
- ❌ 把定时发送说成已实现。
- ❌ 对 `Daily Watch` 默认发盘中轰炸。
- ❌ 无 workspace artifact 却凭空造 watchlist。
正常模式还会尝试发送 email：正文为摘要，完整 HTML dashboard 作为附件。`--dry-run` 只渲染到 stdout，不写文件、不发送。

## 邮箱配置

在 workspace `.env` 中设置（`init-workspace` 自动生成 `.env.template`）：

```
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=your-email@example.com
SMTP_PASSWORD=your-app-password
COVERAGE_EMAIL_TO=recipient@example.com
```

`doctor` 命令会检查缺失并提示。

## Workflow 联动

本 skill 已吸收原 `coverage-tracker` 的职责：
- `normalize-coverage` 命令规范 COVERAGE.md
- `build_universe` 从文件系统自动判断 Coverage/Monitor 状态
- agent 产出 artifact 后直接更新 COVERAGE.md 字段，不再需要独立 tracker skill

| 下游 | 作用 |
|---|---|
| researcher 日常工作流 | 每日收日报；Core Watch 名单盘中接提醒 |
| `/update-agent-runtime` | 把本 skill 的脚本同步到 workspace `.scripts/coverage-monitor/` |
