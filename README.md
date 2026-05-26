# Buy-Side Research Skills —— 零基础完全上手指南

> 当前版本：`4.0.0`
>
> 仓库地址：[iRyantik/buy-side-research-skills](https://github.com/iRyantik/buy-side-research-skills)

---

## Beginner 入口

- [Beginner 先看：Skill 分层图（HTML 可视化）](docs/beginner-skill-map.html)

---

## Current Workspace Rules

This section is the canonical v3.9 workspace rule.

```text
research-workspace/
  _inbox/                 # global staging only
  _scripts/
  edge-radar.md
  topics/
    industry/<slug>/
      index.md
      _inbox/             # created by new-session
      2026-05-18-industry-quickread.md
      2026-05-18-rklb-stock-quickread.md

    company/<slug>/
      index.md
      _inbox/             # created by new-session or promote-company
      2026-05-18-stock-quickread.md
      _cache/             # created on demand by financial-data / driver-map / ingest
      _raw/               # created on demand by ingest
      _models/            # created on demand by modeling skills
```

- `new-session` creates only `index.md` and `_inbox/`.
- `ingest` creates `_raw/` and `_cache/` on first conversion.
- Industry/theme topics can temporarily hold company research as `YYYY-MM-DD-<company-slug>-<artifact>.md`.
- Use `promote-company` to move company-scoped files into `topics/company/<company-slug>/`.
- `integrate` is unchanged and remains the legacy whole-topic directory merge skill.
- Industry topics do not get `_models/` by default; model folders are created only when explicitly needed.

### 本地缺数时的 market data fallback

- research skills 默认先查本地 `_cache/`、`financial-data` 和已 ingest 的 source-tracked markdown。
- 市场/快照类字段默认走双轨顺序：先 `workspace-local / financial-data`，再 `trusted third-party`，最后才是 web / internet fallback。
- 如果对象是 A股 / 港股 / 美股，且当前 skill 显式借用 `trusted-market-bridge`，则 market-snapshot track 可先通过 Longbridge 拉取 `market_quote`、`price_action`、`valuation_snapshot`、`fx_snapshot`、`adr_ah_premium`、`news`、`filings`、`consensus`、`financial_snapshot` 或高层 `market_screen` 信号；这类字段必须显式保留 `Longbridge Securities`、symbol、market、as-of 和 fallback reason，不冒充公司披露原文。
- 如果 Longbridge 对某个域 `scope_restricted`，默认自动降级到现有 web / internet market source fallback；正文不必额外展开，最终只需在 `## Resources` 写明 `fallback reason`。
- 当前显式消费这层 bridge 的 skill 包括：`consensus-map`、`earnings-setup`、`peer-deep-dive`、`pair-trade`、`cross-market-compare`、`stock-quickread`、`candidate-screener`、`alpha-thesis`、`bear-pre-mortem` 和 `industry-quickread`。 
- 如果本地缺失，只有部分 market / consensus / valuation / liquidity / price-action section 会自动 fallback 到公开互联网 market data。
- 这类字段会显式标成 `internet source`，并写明 provider、as-of、URL / source location；若使用全球 / 非本地市场 fallback，还要写明 fallback reason；不会冒充公司披露原文。
- 业务事实、segment 利润、公司披露 KPI、客户 / 项目事实、管理层原话、未披露 driver 等缺口，仍然保持 `[需查证]` / `[来源待补]` / `not disclosed`。

### 本地语言 / 本地市场 source 优先

- source 不是单行总顺序，而是双轨：披露事实轨 `workspace-local > primary public > trusted third-party > web`；市场快照轨 `workspace-local / financial-data > trusted third-party > web`。
- 同一可信度层级内，研究和新闻默认优先 home-market / local-language source；市场数据默认优先主要上市地 / 交易市场的数据源。
- 不维护任何市场专属 provider 白名单；如果使用全球、英文或非本地市场 fallback，必须在文末 `## Resources` 写明 fallback reason。

---

### Claim-level source contract

- 新 research output 默认把每个可验证的 truth-like claim 都挂 inline clickable short source anchor，例如 `[S1](./source.md)` / `[P1](https://...)` / `[I1](https://...)`。
- 正文不堆长链接；正文和表格只显示短码，但短码本身必须可点击。provider、as-of / filed date、page / location 统一放在文末 `## Resources`；不要在表格下方默认展开完整 source metadata。
- 多个 source 写成 `[S1](./source.md) [I1](https://...)`，不要写成 `[S1][I1]`。
- 判断句可以不逐句挂 source，但它依赖的事实、数字、引语、市场数据和业务关系必须已经有 anchor。
- 没有 source 的事实只能写成 `[需查证]` / `[来源待补]` / `not disclosed` / `working hypothesis`，不能写成确定事实。

---

## 目录

- [0. 这个插件是什么？我能用它做什么？](#0-这个插件是什么我能用它做什么)
- [1. 我完全不会编程，能用吗？](#1-我完全不会编程能用吗)
- [2. 安装：跟 Claude 说几句话就搞定](#2-安装跟-claude-说几句话就搞定)
- [3. 准备工作：全用对话完成](#3-准备工作全用对话完成)
- [4. 第一次研究：从零到写出第一份分析](#4-第一次研究从零到写出第一份分析)
- [5. 每个 Skill 做什么、什么时候用](#5-每个-skill-做什么什么时候用)
- [6. 完整研究流程示例](#6-完整研究流程示例)
- [7. 文件放在哪里？Workspace 结构详解](#7-文件放在哪里workspace-结构详解)
- [8. 常见问题与排错](#8-常见问题与排错)
- [9. 进阶：自定义与维护](#9-进阶自定义与维护)

---

## 0. 这个插件是什么？我能用它做什么？

### 用一句话说

**这个插件把专业股票研究员（buy-side analyst）的工作流程，变成了一套你在 Claude Code 或 Codex 里可以直接用中文对话触发的「技能」。**

### 源码与安装包结构

当前源码仓库是 wrapper + nested payload 结构：真正的 plugin payload 在 `plugins/buy-side-research-skills/`，active skills 在 `plugins/buy-side-research-skills/skills/[skill-name]/`。

用户下载的 Release zip 仍是扁平运行时结构，解压后直接包含 `.claude-plugin/`、`.codex-plugin/`、`skills/` 和 `README.md`。源码 root 的 `CLAUDE.md`、`AGENTS.md`、`docs/`、`examples/` 不进入安装包。

### 用人话说

想象你雇了一个非常聪明的研究助理。你跟他说：

- "帮我看一下 Vertiv 这家公司值不值得深入研究"
- "市场现在对 GE Vernova 的预期是什么？有没有哪里可能错了？"
- "帮我把 Rocket Lab 的财务数据拉出来，我要搭模型"
- "我下周要看 GE 的财报，帮我准备一下关键问题"
- "我想做多 Vertiv、做空西门子能源，帮我分析这个 pair trade 合不合理"

这个插件就是让 Claude / Codex 听得懂这些指令，并且按照专业研究员的标准来执行和输出。

### 你能做什么（不写一行代码）

| 你想做的事 | 跟 Claude 说什么 |
|---|---|
| 快速看一家不熟的公司 | "用 stock-quickread 看 Vertiv" |
| 快速了解一个陌生行业 | "用 industry-quickread 看核电行业" |
| 搞清楚一家公司到底靠什么赚钱 | "用 driver-map 拆 Rocket Lab 的收入 driver" |
| 搞懂一个行业的工程/技术原理 | "用 mechanism-map 解释燃气轮机产业链" |
| 拉美股/A股/港股/日股/韩股/欧股的财务数据 | "用 financial-data 拉 AAPL 美股数据" |
| 搭三表财务预测模型 | "用 3-statement-model 给 GE 搭模型" |
| 做 DCF 估值 | "用 dcf-model 给 Rocket Lab 做 DCF" |
| 看市场对一只股票的预期 | "用 consensus-map 看市场对 IONQ 的预期" |
| 写一份完整的做多/做空 thesis | "用 alpha-thesis 写 GE Vernova 做多逻辑" |
| 找 thesis 的漏洞 | "用 bear-pre-mortem 打我 GEV 做多 thesis 的逻辑" |
| 准备财报季 | "用 earnings-setup 准备下周 GE 的财报" |
| 设计一对 pair trade | "用 pair-trade 分析做多 VRT 做空 SMCI" |
| 比较几家同行业公司 | "用 peer-deep-dive 比较 VRT、GEV、SMCI" |
| 看 Reddit 上的情绪和高信号帖子 | "用 reddit-sentiment 查 IONQ 在 Reddit 上怎么看" |
| 把一篇研究文做成 memo-ready HTML 图 | "用 research-viz 把这篇 mechanism-map 做成 capability map" |
| 把研究结论沉淀下来 | "用 research-journal 总结这轮研究" |
| 判断一条新闻值不值得追 | "用 information-impact 看这条消息" |

### 你不能做什么（重要边界）

- 插件不会替你买卖股票，不会替你下单。
- 插件给的是分析框架和判断依据，不是投资建议。
- 所有财务数据来自公开源（SEC、交易所公告等），插件不做数据造假，也不会替你核实每一条第三方数据。

---

## 1. 我完全不会编程，能用吗？

**能。** 你不需要会写代码。你需要会的是：

1. **打字** —— 用自然语言跟 Claude Code 或 Codex 对话。
2. **知道你要研究什么** —— 知道公司名或股票代码，知道你想回答什么问题。
3. **有基本的文件操作能力** —— 新建文件夹、把 PDF/Excel 拖进文件夹。

### 你需要先装好的东西

| 你需要什么 | 怎么装 | 要不要钱 |
|---|---|---|
| **Claude Code** 或 **Codex** | 去官网下载安装即可 | Claude Code 需要 Anthropic 账号和 API 额度；Codex 取决于你的授权 |
| **Python**（仅 `ingest` 和 `financial-data` 需要） | 去 python.org 下载，安装时勾选 "Add Python to PATH" | 免费 |
| **本插件** | 看下一节，全程用对话安装 | 免费，开源 |

> **如果你只做对话类研究**（让 Claude 帮你分析、写 thesis、做 peer comparison），你甚至不需要装 Python。只有当你需要**消化 PDF/Excel 文件**、**拉取结构化财务数据**或**抓取 Reddit sentiment 数据**时，才需要 Python。

### 三个概念先搞清楚

```
插件源码仓库（本 repo）
    ↓ 发布为扁平 Release zip 后安装
Claude Code / Codex（你的 AI 助手）
    ↓ 你对它说话，它加载本插件的 skills
研究 Workspace（你电脑上一个普通文件夹）
    ↓ 所有研究产物（分析报告、财务数据、模型）都存在这里
```

**简单记：本仓库是"说明书和工具"，Claude Code 是"执行者"，Workspace 是"你的笔记本"。**

---

## 2. 安装：跟 Claude 说几句话就搞定

### 第一步：确认 Claude Code 或 Codex 已装好

打开你的 Claude Code，随便跟它说句话（比如"你好"）。如果能正常回复，说明已装好。

如果还没装，去 Claude Code 官网下载安装。安装过程就是普通的"下一步→下一步"，跟装微信没有区别。

### 第二步：安装本插件

1. 打开 [GitHub Release 页面](https://github.com/iRyantik/buy-side-research-skills/releases)
2. 下载最新版本的 `buy-side-research-skills-X.X.X.zip`
3. 解压到你电脑上的一个文件夹（记下路径）
4. 在 Claude Code 里说：**"帮我安装本地插件，路径是 xxx"**（把 xxx 换成你解压的文件夹路径）

Claude 会帮你完成安装。你只需要确认即可。

> 如果你用的是 Codex，把上面对话里的 "Claude" 换成 "Codex" 即可，操作完全一样。

### 第三步：验证安装成功

在 Claude Code 里说：

> "帮我检查 buy-side-research-skills 插件是否正确安装了"

如果 Claude 回复说能看到一列 skill 名字（如 `stock-quickread`、`financial-data`、`driver-map` 等），说明安装成功。

---

## 3. 准备工作：全用对话完成

以下所有步骤都**不需要你手动敲任何命令**。你只需要在 Claude Code 里用中文说一句话，Claude 会帮你完成。

### 3.1 创建你的研究 Workspace

**关键原则：不要在本插件文件夹里做研究。** 你需要另外建一个空文件夹作为你的"研究笔记本"。

在你的电脑桌面或文档文件夹里，新建一个空文件夹。名字随意，比如 `我的研究`。

然后打开 Claude Code，把工作目录切到这个新文件夹（在 Claude Code 界面里选择打开文件夹即可）。接着对 Claude 说：

> "帮我初始化研究 workspace"

Claude 会自动帮你创建如下结构：

```
我的研究/
├── CLAUDE.md              # workspace 的配置说明
├── AGENTS.md              # 给 AI agent 的指针
├── _inbox/                # 临时存放待处理的文件
├── _scripts/              # 辅助脚本（自动复制过来）
├── edge-radar.md          # 跨主题的研究雷达，记录你关注的问题
└── topics/                # 所有研究主题都放在这里（目前是空的）
```

> **注意**：`init-workspace` 不会安装 Python 依赖。它只创建文件夹骨架。

### 3.2 配置 EDGAR 身份（拉美股数据需要）

美国 SEC（证监会）要求访问 EDGAR 数据库的人自报身份。这不是注册账号，只是告诉 SEC "谁在查数据"。

在 Claude Code 里说：

> "我的 EDGAR 身份是 张三 zhangsan@email.com，帮我配置好美股数据访问"

Claude 会帮你写入环境变量配置。**不需要注册任何账号，也不需要密码。** SEC 只是要求你声明你是谁。

### 3.3 配置其他市场的数据源（按需）

| 你想拉哪个市场的数据 | 需要什么 | 获取方式 |
|---|---|---|
| 美股（US） | `EDGAR_IDENTITY` | 见上一步，告诉 Claude 你的姓名+邮箱即可 |
| A 股（CN） | 无 | 不需要任何 key，直接用 |
| 港股（HK） | 无 | 不需要任何 key，直接用 |
| 日股（JP） | `EDINET_API_KEY` | 去 https://disclosure2.edinet-fsa.go.jp/ 注册申请，拿到 key 后告诉 Claude："帮我配置日股 EDINET key：xxx" |
| 韩股（KR） | `DART_API_KEY` | 去 https://opendart.fss.or.kr/ 注册即可，拿到 key 后告诉 Claude："帮我配置韩股 DART key：xxx" |
| 欧股（EU） | 通常无 | 需要提供 filing URL 或本地 ESEF 文件，直接告诉 Claude 文件在哪 |

对于大多数用户来说，**美股和 A 股就够用了**，美股只需告诉 Claude 你的姓名+邮箱，A 股零配置。

### 3.4 安装 Python 依赖（仅当你需要消化文件或拉财务数据时）

**如果你只做对话类研究（分析、写 thesis、做 peer comparison），跳过这一步。**

只有当你要处理 PDF/Excel 文件，或拉取结构化财务数据时，才需要安装依赖。

**你不需要手动敲任何命令。** 在 Claude Code 里说：

> "帮我检查 ingest 和 financial-data 的 Python 依赖是否齐全，缺什么就帮我装上"

Claude 会自动检查、列出缺失项、并在你确认后安装。如果中途遇到问题，Claude 会告诉你具体怎么解决。

> 这是一次性的。装好之后就不用再管了。

---

## 4. 第一次研究：从零到写出第一份分析

假设你想快速看一家公司：**Vertiv（VRT）**。你听说过这家公司是做数据中心电力和冷却的，但不熟。

### 完整对话示例

**你**：
> 帮我新建一个 Vertiv 的研究 session

Claude 会帮你在 workspace 里创建 `topics/company/vertiv/` 文件夹和所有子目录。

**你**：
> 用 stock-quickread 快速看一下 VRT

Claude 会输出一份快速公司分析，包含：公司做什么、核心业务线、关键财务数字、市场怎么看、值得深挖的问题。

**你**：（看完后觉得有意思，想深入了解收入从哪里来）
> 用 driver-map 拆一下 VRT 的收入 driver

Claude 会按 segment 拆解收入驱动因素（量、价、mix），标注哪些数据有、哪些需要补。

**你**：（觉得需要看市场预期）
> 用 consensus-map 看市场现在对 VRT 的预期是什么

Claude 会摊开 sell-side consensus、buy-side bar、priced-in assumptions，标注哪里有 variant-view 机会。

**你**：（研究完了想沉淀）
> 用 research-journal 总结这轮 VRT 的研究发现

Claude 会把你的 earned insight 写成 topic journal，并生成一份 Boss Brief。

**整个过程你没有写一行代码，也没有敲任何命令。你只是在用中文跟 Claude 对话。**

---

## 5. 每个 Skill 做什么、什么时候用

### 5.1 运维类 Skills（Operations）—— 管理你的研究环境

#### `init-workspace` —— 创建研究笔记本

**什么时候用**：第一次用这个插件，或者你的 workspace 文件夹丢了/坏了需要重建。

**你跟 Claude 说**：*"帮我初始化研究 workspace"*

**会发生什么**：在当前文件夹创建标准研究 workspace 结构（`_inbox/`、`_scripts/`、`topics/`、`edge-radar.md`）。

**不会发生什么**：不会安装 Python 依赖，不会拉取数据，不会创建 git 仓库。

---

#### `update-agent-runtime` —— 更新当前宿主插件并同步当前 workspace

**什么时候用**：插件已经装好了，但你要把 **当前宿主**（Claude Code 或 Codex）里的 buy-side 插件更新到最新 GitHub release，并把当前 workspace 的 hooks、`_scripts/`、根目录 `CLAUDE.md` / `AGENTS.md` 的 managed runtime sections 同步到最新模板。

**你跟当前宿主说**：*"用 update-agent-runtime 更新当前宿主插件并同步这个 workspace"*。

**会发生什么**：只更新当前宿主，不碰另一个宿主；自动取最新 release zip；修复 `.claude/settings.json`、`.claude/hooks/*.ps1`、`.codex/hooks.json`、`_scripts/`，并定向升级当前 workspace 的 `CLAUDE.md` / `AGENTS.md` managed sections。

**不会发生什么**：不会整份覆盖你自定义的 `CLAUDE.md` / `AGENTS.md`，不会直接按固定机器路径手改 cache，也不会默认同时更新 Claude 和 Codex 两边。

---

#### `new-session` —— 新建一个研究主题

**什么时候用**：你准备开始研究一个新公司、新行业、新主题、或一对 pair trade。

**你跟 Claude 说**：*"帮我新建一个 IONQ 的研究 session"* 或 *"帮我新建一个核电行业的研究 session"*

**会发生什么**：在 `topics/` 下创建或定位对应的 topic 文件夹，只确保 `index.md` 和 `_inbox/`；`_raw/`、`_cache/`、`_models/` 由后续 skill 按需创建。

**不会发生什么**：不会写任何研究结论。它只建骨架，不做研究。

---

#### `ingest` —— 把 PDF/Excel/PPT 转成可搜索的文本

**什么时候用**：你下载了公司财报 PDF、卖方报告 PPT、行业数据 Excel，想让 Claude 能读它们。

**操作步骤**：
1. 把文件拖进对应 topic 的 `_inbox/` 文件夹
2. 对 Claude 说：*"帮我用 ingest 处理刚才放进 VRT 文件夹 _inbox 里的文件"*

**会发生什么**：
- PDF → 可搜索的 markdown 文本
- Excel → 保留表格结构的 markdown
- PPT/Word → 带结构的文本
- 原始文件自动移到 `_raw/` 下对应类别存档

**需要什么**：Python + 依赖已安装（见 3.4 节，让 Claude 帮你装）。

---

#### `financial-data` —— 拉取结构化财务数据

**什么时候用**：你需要公司的三表数据（利润表、资产负债表、现金流量表）来搭模型或做分析；如果该市场能结构化抓收入拆分，`financial-data` 会一并写入。

**你跟 Claude 说**：
- 美股：*"用 financial-data 帮我拉 AAPL 的美股财务数据"*
- A 股：*"用 financial-data 帮我拉 600519 贵州茅台的财务数据"*
- 日股：*"用 financial-data 帮我拉 7203 丰田的日股财务数据"*
- 韩股：*"用 financial-data 帮我拉 005930 三星电子的韩股财务数据"*
- 台股：*"用 financial-data 帮我拉 2330 台积电的台股财务数据"*

**会发生什么**：输出 `financial-data-summary.md`（人类可读的财务概览）+ `internal/` 下的结构化 JSON（给建模 skill 和 `driver-map` 用）。`actuals-resolved.json` 默认放三表；A 股等可结构化拆分的市场还会包含 `statements.revenue_split`。抓不到收入拆分时不编造，`driver-map` 会用 `full-filing.md` 从原文抽。

**需要什么**：Python + 依赖已安装（见 3.4 节）；对应市场的 key 已配置（见 3.2-3.3 节）。

---

#### `integrate` —— 合并子 topic

**什么时候用**：你把一个主题拆成几个子主题分别研究，现在想合并。

**你跟 Claude 说**：*"帮我把某某子 topic 合并到某某父 topic 下面"*

---

#### `promote-company` —— 把行业里的公司研究沉淀到 company 目录

**什么时候用**：你先在行业 / 主题 topic 里研究了一家公司，现在决定把它作为长期跟踪对象。

**你跟 Claude 说**：*"把 space-launch topic 里的 RKLB 研究 promote 到 company/rklb"*

**会发生什么**：把 `2026-05-18-rklb-*.md` 这类确定属于公司的文件移动到 `topics/company/rklb/`，文件名去掉 `rklb-` 前缀；行业级 peer / industry 文件留在原 topic，并在 company index 里 backlink。

---

#### `meta-skill` —— 修改本插件

**什么时候用**：你想修改本插件的某个 skill 的行为，或新增一个 skill。

> 普通用户**不需要用这个**。这是给插件维护者用的。
> 维护口径：root `CLAUDE.md` 管 plugin 开发宪法，`CLAUDE.md.template` 管 workspace 高层宪法，invoked `SKILL.md` 管 runtime 行为，`skills/_shared/research-policy-baseline.md` 只做 authoring baseline。

---

### 5.2 研究类 Skills（Research）—— 做真正的投资研究

Skills 按研究深度分为四层。越往下越深入。

#### 第一层：筛选与快速判断（Triage）

| Skill | 一句话 | 什么时候用 | 你跟 Claude 说 |
|---|---|---|---|
| `stock-quickread` | 快速看一家不熟的公司 | 听到一个新名字，想判断值不值得深挖 | *"用 stock-quickread 快速看 VRT"* |
| `industry-quickread` | 快速了解一个行业 | 遇到陌生行业，想搞清格局和关键问题 | *"用 industry-quickread 看核电行业"* |
| `candidate-screener` | 从主题出发找受益股 | 有个主题想法，想知道哪些公司受益 | *"用 candidate-screener 找 AI 数据中心电力的受益股"* |
| `information-impact` | 判断一条消息重不重要 | 看到一条新闻/传闻，想判断是否值得追 | *"用 information-impact 分析这条消息靠不靠谱"* |
| `reddit-sentiment` | 抓取并总结 Reddit 情绪 | 想知道某只股票、IPO、财报或主题在 Reddit 上怎么被讨论 | *"用 reddit-sentiment 查 SpaceX IPO 在 Reddit 上怎么看"* |
| `next-step` | 研究卡住了，问下一步怎么做 | 不确定接下来该研究什么 | *"用 next-step 帮我判断下一步研究什么"* |

---

#### 第二层：打地基（Foundation）

| Skill | 一句话 | 什么时候用 | 你跟 Claude 说 |
|---|---|---|---|
| `company-primer` | 深度拆解一家公司的业务 | 决定认真看某家公司，需要搞清楚它到底卖什么、客户是谁、历史怎么演变 | *"用 company-primer 深度看 GE Vernova"* |
| `consensus-map` | 拆解市场现在相信什么 | 想知道 sell-side 共识、buy-side bar、市场隐含预期是什么，哪里可能错了 | *"用 consensus-map 看市场对 IONQ 的预期"* |
| `earnings-setup` | 做财报前 setup 或财报后快读 | 想看 print 前后的预期、price action、revisions、news / filings fallback | *"用 earnings-setup 准备 RKLB 下周财报"* |
| `peer-deep-dive` | 横向深比一组同行 | 想比较 market / valuation / consensus / recent event context，并允许 bridge 补 A / 港 / 美市场证据 | *"用 peer-deep-dive 比较 RKLB、LUNR、SPIR"* |
| `pair-trade` | 评估 long / short pair 的 spread 逻辑 | 想比较两腿的价格、估值、consensus、news，并在 bridge 受限时自动退回 web source | *"用 pair-trade 分析做多 VRT 做空 SMCI"* |
| `trusted-market-bridge` | 拉取 A / 港 / 美市场证据包 | 想用 Longbridge 拉市场数据、价格数据、FX、ADR/AH premium、filings、news、consensus、financial snapshot 或 `market_screen` 信号，或给 research skill 提供统一 bridge | *"用 trusted-market-bridge 拉 NVDA.US 的市场数据和 FX"* |
| `mechanism-map` | 搞懂一个行业的技术和物理机制 | 行业有工程/技术/工艺/设备链条不懂，需要搞清"东西到底怎么运作" | *"用 mechanism-map 解释燃气轮机"* |
| `driver-map` | 拆一家公司的收入/利润由什么驱动 | 想知道公司业绩由量、价、mix、产能利用率等哪些因素决定 | *"用 driver-map 拆 Rocket Lab 的 revenue driver"* |
| `cross-market-compare` | 跨市场估值比较 | A/H 股、ADR、多地上市的估值差异 | *"用 cross-market-compare 比较比亚迪 A 股和 H 股"* |

---

#### Supporting：研究配套可视化

| Skill | 一句话 | 什么时候用 | 你跟 Claude 说 |
|---|---|---|---|
| `research-viz` | 把已有研究文做成 memo-ready HTML 图 | 已经有一篇 markdown 研究主文，想补 capability map、peer scatter、valuation band、timeline 或其它 HTML 图表 | *"用 research-viz 把这篇 mechanism-map 做成 capability map"* |

---

#### 第三层：深度研究（Deep Work）

| Skill | 一句话 | 什么时候用 | 你跟 Claude 说 |
|---|---|---|---|
| `peer-deep-dive` | 横向比较几家同行业公司 | 想看一个行业里几家公司的相对优劣 | *"用 peer-deep-dive 比较 VRT、GEV、SMCI"* |
| `alpha-thesis` | 写一份做多或做空的完整逻辑 | 已经有了足够的认知，想系统化写出投资逻辑，并允许 bridge 补 priced-in / valuation / consensus / price-action 这类市场快照输入 | *"用 alpha-thesis 写 IONQ 做空 thesis"* |
| `bear-pre-mortem` | 用最强反方视角压测 thesis | 想检验 downside、crowding、估值反证和 price setup，bridge 只补市场快照层，不放宽 short-side 事实纪律 | *"用 bear-pre-mortem 压测我对 RKLB 的多头 thesis"* |
| `industry-quickread` | 30-45 分钟看懂一个行业值不值得继续研究 | 想快速判断行业 current regime、value pool 和下一步研究入口，并允许 bridge 补板块表现、valuation anchor、FX / premium framing | *"用 industry-quickread 看 AI 电力基础设施"* |
| `earnings-setup` | 准备一份财报 | 下周有财报，想知道该关注什么、什么数字会改变故事 | *"用 earnings-setup 准备下周 GE 的财报"* |
| `pair-trade` | 分析一对多空组合 | 有做多 X 做空 Y 的想法，想分析逻辑是否自洽 | *"用 pair-trade 分析做多 VRT 做空 SMCI"* |
| `primary-research-plan` | 设计专家访谈或渠道调研计划 | 需要验证一个关键 thesis 假设，想约专家聊 | *"用 primary-research-plan 设计验证 IONQ 客户 adoption 的方案"* |
| `research-viz` | 把基准研究文做成 HTML 图表 | 已经有一篇研究主文，想把核心信息变成 memo-ready capability map、peer scatter、valuation band 或 timeline | *"用 research-viz 把这篇 mechanism-map 做成 capability map"* |
| `3-statement-model` | 搭三表财务预测模型 | 需要先填历史 actuals，再建立利润表、资产负债表、现金流量表的预测模型 | *"用 3-statement-model 给 Rocket Lab 搭模型"* |
| `dcf-model` | 做 DCF 估值 | 需要基于自由现金流折现算 intrinsic value | *"用 dcf-model 给 GE Vernova 做估值"* |
| `comps-analysis` | 做可比公司估值 | 需要看 peer group 的 multiples 来判断贵不贵 | *"用 comps-analysis 做核电行业的可比公司分析"* |
| `model-update` | 更新已有模型 | 财报出来了，需要把新数据 plug 进已有的模型 | *"用 model-update 更新 GE 的模型"* |

---

#### 第四层：沉淀（Memory）

| Skill | 一句话 | 什么时候用 | 你跟 Claude 说 |
|---|---|---|---|
| `research-journal` | 把本轮研究的认知增量写下来 | 一轮研究做完了，需要沉淀那些"真正搞清楚了、有 source 支撑、会改变判断"的结论 | *"用 research-journal 总结这轮 VRT 研究"* |

**research-journal 不是日记**，不要每看一份材料就写一条。只写 earned insight：你进来时不知道、出去时知道了、而且这个认知会改变你对这只股票的看法。

---

## 6. 完整研究流程示例

> 以下示例中，用户说的话都很短。**不需要在对话里写长篇要求**——每个 skill 内部已经有完整的执行规范，你只需要用简短的自然语言触发即可。

### 场景 A：你听到一个股票代码，想快速判断值不值得看

> 你：帮我新建一个 VRT 的研究 session
>
> 你：用 stock-quickread 快速看一下 VRT
>
> 你：（看完觉得有意思）用 consensus-map 看 VRT 的市场预期
>
> 你：用 driver-map 拆 VRT 的 revenue driver
>
> 你：用 research-journal 总结这轮 VRT 的发现

---

### 场景 B：你有一个主题想法，想找受益股

> 你：帮我新建一个 AI 数据中心电力的研究 session
>
> 你：用 industry-quickread 看 AI 数据中心电力行业
>
> 你：用 mechanism-map 解释数据中心电力架构
>
> 你：用 candidate-screener 找 AI 数据中心电力的受益股
>
> 你：（筛选出几家后）用 peer-deep-dive 比较 VRT、GEV、SMCI、EATON
>
> 你：用 research-journal 总结这轮主题研究

---

### 场景 C：你决定认真看一家公司，要搭模型

> 你：帮我新建一个 Rocket Lab 的研究 session
>
> 你：用 financial-data 拉 RKLB 美股数据
>
> 你：用 company-primer 深度看 RKLB
>
> 你：用 driver-map 拆 RKLB 的 revenue driver
>
> 你：用 3-statement-model 给 RKLB 搭历史 + 预测三表模型
>
> 你：用 dcf-model 给 RKLB 做估值
>
> 你：用 consensus-map 看 RKLB 的市场预期
>
> 你：用 alpha-thesis 写 RKLB 做多 thesis
>
> 你：用 bear-pre-mortem 打一下这个做多 thesis
>
> 你：用 research-journal 总结这轮 RKLB 研究

---

### 场景 D：财报季，你跟踪的股票要发财报了

> 你：帮我新建一个 GE Q1 2026 财报的研究 session
>
> 你：用 earnings-setup 准备 GE 下周的财报
>
> 你：（财报出了后）用 model-update 把最新数据更新进 GE 的模型
>
> 你：用 research-journal 记录 post-earnings 的判断更新

---

### 场景 E：你看到一个不熟悉的行业，想系统搞懂

> 你：帮我新建一个燃气轮机行业的研究 session
>
> 你：用 industry-quickread 看燃气轮机行业
>
> 你：（看完觉得需要搞懂技术）用 mechanism-map 解释燃气轮机
>
> 你：（搞清机制后）用 candidate-screener 在燃气轮机价值链上找上市公司
>
> 你：用 peer-deep-dive 比较 GE Vernova、西门子能源、三菱重工
>
> 你：用 research-journal 总结这轮燃气轮机行业研究

---

### 场景 F：突发新闻来了，想快速判断对哪些股票有影响

> 你：我刚刚看到一条消息——"美国商务部提议限制用于数据中心的 AI 芯片出口，征求意见期 30 天"。用 information-impact 分析这条消息
>
> Claude 输出分析后，如果你觉得有标的值得看：
>
> 你：用 candidate-screener 按这个消息的逻辑找受益股
>
> 你：用 stock-quickread 快速看这几家候选公司

---

### 场景 G：朋友圈/群里传了一篇小作文，你想验证真假

1. 把这篇小作文的内容复制粘贴给 Claude
2. 对 Claude 说：

> 这是一篇在投资群里流传的文章，用 information-impact 核实里面的 claim

Claude 会逐条标注哪些有 source 支撑、哪些和已知事实矛盾、逻辑链有没有漏洞。

根据 Claude 的反馈，选择下一步：

> （如果关键 claim 无法验证）用 primary-research-plan 设计验证方案

> （如果担心市场会信这篇小作文）用 consensus-map 看相关股票的市场预期

---

### 场景 H：收到一份卖方报告，想独立判断靠不靠谱

1. 如果报告是 PDF，放进对应 topic 的 `_inbox/`，说：*"帮我用 ingest 处理这份卖方报告"*
2. 然后说：

> 用 information-impact 分析这份摩根士丹利关于 GE Vernova 的报告

Claude 会拆解报告的核心假设、和 consensus 的差异、以及关键假设的合理性。

> （如果某个核心假设值得深挖）用 primary-research-plan 设计验证方案

---

### 场景 I：你想找一个做空标的

> 你：帮我新建一个做空筛选的研究 session
>
> 你：用 candidate-screener 在 AI 数据中心电力主题里找做空候选
>
> 你：（锁定某家后）用 consensus-map 看市场对这家公司的预期
>
> 你：用 driver-map 拆这家公司的 revenue driver
>
> 你：用 alpha-thesis 写做空 thesis
>
> 你：用 bear-pre-mortem 反打这份做空 thesis
>
> 你：用 research-journal 总结做空逻辑和 kill criteria

---

### 场景 J：两家公司你都看了，想决定做哪一边

> 你：用 pair-trade 分析做多 VRT 做空 SMCI
>
> 你：（看完觉得需要补数据）用 financial-data 拉 VRT 和 SMCI 最近三年的数据
>
> 你：用 research-journal 总结这个 pair trade 的核心逻辑

---

## 7. 文件放在哪里？Workspace 结构详解

研究 workspace 是你电脑上的一个普通文件夹。下面是目标结构；`_raw/`、`_cache/`、`_models/` 都是按需出现，不是 `new-session` 默认创建。

```
我的研究/                                 ← 你的 workspace 根目录
│
├── CLAUDE.md                             ← workspace 配置（不要手动改）
├── AGENTS.md                             ← AI agent 指针（不要手动改）
├── edge-radar.md                         ← 跨主题研究雷达（记录你关注的问题）
│
├── _inbox/                               ← 还没分类的临时文件丢这里
│   └── 某篇想读的行业报告.pdf
│
├── _scripts/                             ← 辅助脚本（自动生成，不要手动改）
│
└── topics/                               ← 所有研究都在这里
    │
    ├── company/                          ← 公司研究
    │   └── rocket-lab/                   ← Rocket Lab 这个 topic
    │       ├── index.md                  ← topic 地图（自动维护）
    │       ├── _inbox/                   ← RKLB 专属待处理文件
    │       ├── _raw/                     ← ingest 后才出现；原始文件存档
    │       │   ├── filings/              ←   SEC filings / 年报
    │       │   ├── transcripts/          ←   earnings call 记录
    │       │   ├── sellside/             ←   卖方报告
    │       │   ├── industry/             ←   行业报告
    │       │   ├── irdecks/              ←   公司 IR 演示文稿
    │       │   └── datasets/             ←   数据集
    │       ├── _cache/                   ← ingest / financial-data / driver-map 后才出现
    │       │   ├── filings/              ←   filing 转的 markdown
    │       │   ├── financial-data/       ←   结构化财务数据
    │       │   │   ├── financial-data-summary.md   ← 你读这个
    │       │   │   └── internal/                   ← 机器读的 JSON（你不用管）
    │       │   └── driver-map/           ←   driver 拆解缓存
    │       ├── _models/                  ← 建模后才出现；通常只在 company topic
    │       │   ├── rklb-3statement-model.xlsx
    │       │   └── rklb-dcf-model.xlsx
    │       ├── 2026-05-13-stock-quickread.md    ← 研究产物（日期+技能名）
    │       ├── 2026-05-14-driver-map.md
    │       ├── 2026-05-15-dcf-model.md
    │       └── 2026-05-16-alpha-thesis.md
    │
    ├── industry/                         ← 行业研究
    │   └── nuclear-power/
    │       ├── index.md
    │       ├── _inbox/
    │       ├── 2026-05-18-industry-quickread.md
    │       ├── 2026-05-18-peer-deep-dive.md
    │       └── 2026-05-18-rklb-stock-quickread.md
    │       # 行业 topic 默认不建 _models/
    │
    ├── theme/                            ← 主题研究
    │   └── ai-data-center-power/
    │       ├── index.md
    │       ├── _inbox/
    │       └── 2026-05-18-industry-quickread.md
    │
    └── pair/                             ← Pair trade 研究
        └── vrt-long-smci-short/
            ├── index.md
            ├── _inbox/
            └── 2026-05-18-pair-trade.md
```

### 几个重要的规则

1. **日期文件名**：研究产物直接放在 topic 根目录下，文件名格式为 `YYYY-MM-DD-<skill名>.md`。如果同一天同一 skill 产生了多个版本，后面的自动加 `-2`、`-3`。
   - 示例：`2026-05-14-driver-map.md`、`2026-05-14-driver-map-2.md`
   - 行业 / 主题 topic 里的单公司研究用 `YYYY-MM-DD-<company-slug>-<skill名>.md`，例如 `2026-05-18-rklb-stock-quickread.md`。

2. **公司沉淀**：行业 / 主题里跑出来的公司研究，确认有长期价值后用 `promote-company` 沉淀到 `topics/company/<company-slug>/`；文件名会去掉公司前缀，例如 `2026-05-18-rklb-stock-quickread.md` 变成 `2026-05-18-stock-quickread.md`。

3. **缓存 vs 产物**：`_cache/` 下面的文件是"中间材料"（原始文件转的 markdown、拉取的财务数据），不是研究结论。研究结论是以日期文件名放在 topic 根目录的 markdown 文件。

4. **internal vs 外显**：`internal/` 下的 JSON 是给建模 skill 和 `driver-map` 读的机器文件，你不需要手动打开。人类阅读入口是 `financial-data-summary.md` 和 `driver-map.md`。`actuals-resolved.json` 放三表和可选 `revenue_split`；如果没有结构化收入拆分，`driver-map` 会从 `full-filing.md` 用 LLM 抽 disclosed split。

5. **一个 topic 是长期容器**：你不会因为"这轮研究做完了"就删除 topic 文件夹。下次有新发现、新财报，继续往里加日期文件即可。

---

## 8. 常见问题与排错

### Q1：我不知道该用哪个 skill

**答**：直接用自然语言跟 Claude 说你想干什么，比如 *"我想快速看一下 Vertiv 这家公司"*，Claude 会自动判断该触发哪个 skill。你不需要死记硬背上表。

如果你明确知道要用什么 skill，可以加上 skill 名字提高精准度：*"用 stock-quickread 看 VRT"*。

---

### Q2：Claude 说 "skill 找不到" 或插件没生效

**答**：对 Claude 说：*"帮我检查 buy-side-research-skills 插件是否正确安装了"*，让 Claude 帮你排查。如果没有安装，按上面第二步的步骤从 GitHub Release 下载并安装。

---

### Q3：ingest 处理 PDF 时报错

**答**：把报错信息直接发给 Claude，说：*"ingest 这个 PDF 时报了错，帮我看看是什么问题"*。常见原因和解决方法：

1. **Python 没装或没配好**：让 Claude 帮你检查——*"帮我检查 Python 是否装好并加了 PATH"*。
2. **Python 依赖没装**：让 Claude 帮你装——*"帮我检查并安装 ingest 的 Python 依赖"*。
3. **PDF 是扫描件（图片 PDF）**：扫描件需要 OCR，质量取决于图片清晰度。Claude 会自动标注"需要 Vision review"，你也可以直接把 PDF 截图贴给 Claude 看。
4. **PDF 有密码保护**：需要你先用 Adobe Reader 等工具手动解除密码。

---

### Q4：financial-data 拉美股数据时报错

**答**：把报错信息直接发给 Claude，说：*"financial-data 拉美股数据时报了错，帮我排查"*。常见原因：

1. EDGAR 身份没配置——对 Claude 说：*"我的 EDGAR 身份是 姓名 邮箱，帮我配置美股数据访问"*。
2. Python 依赖没装——对 Claude 说：*"帮我检查并安装 financial-data 的 Python 依赖"*。
3. 股票代码写错了——确认是美股代码（如 AAPL、GE、RKLB），不是 A 股代码（600519）。

---

### Q5：我搞混了，在插件文件夹里做了研究

**答**：没关系。你产出的 markdown 文件和 Excel 模型可以手动复制到你的 workspace 对应位置。但以后记得：**在本插件文件夹外面建 workspace**。

---

### Q6：我的 workspace 太乱了

**答**：对 Claude 说：*"帮我用 init-workspace 修复 workspace 骨架"*。它会修复缺失的文件夹，不会删除你已有的研究文件。

---

### Q7：研究产物应该写多长？

**答**：看 skill 类型。`stock-quickread` 一两页就够了；`alpha-thesis` 可能需要 3-5 页；`research-journal` 的 Boss Brief 应该控制在投资人 5 分钟能读完的长度。Claude 会根据 skill 类型自动控制篇幅。

---

### Q8：两个 skill 的输出好像重复了？

**答**：有些 skill 之间有自然的衔接关系。比如 `stock-quickread` → `driver-map` → `alpha-thesis` 是一个递进链条，后面的 skill 会引用前面 skill 的结论但不重复输出。如果 Claude 重复输出了，直接提醒它：*"这部分跟上次某某 skill 的输出重复了，跳过重复内容"*。

---

### Q9：结果文件里的 source link 打不开

**答**：
- 如果链接标注了 `[link 待补]`，说明 Claude 不确定 URL 是否存在，这部分事实需要你手动查证。
- 如果链接标注了 `[agent-provided, 未验证]`，说明是 AI agent 提供的 URL，需要你亲自抽查是否匹配对应的 claim。
- 插件遵循严格的反幻觉规则，宁可标注"不确定"也不编造链接。

---

### Q10：sub-agent 是不是会直接替我写结论？

**答**：不会。v3.10.0 开始，现在只有极少数高 fan-out research skill 默认会用 sub-agent / delegate worker 并行查 source，但 sub-agent 只能交 evidence card。最终结论、peer ranking、driver 判断、估值解释和 URL 抽查都必须由主 agent 完成。Runtime cap: no per-skill sub-agent count limit; max 6-8 active sub-agents globally; parallel within one skill but serial across skills; close sub-agents immediately after evidence cards or QA notes return.

默认执行 Parallel Evidence Pass 的 skill 现在只保留：`peer-deep-dive`、`candidate-screener`、`cross-market-compare`、`pair-trade`、`driver-map`。其它 research skill 默认单线执行；只有用户明确说 `sub-agent`、`delegate` 或 `并行` 时才会并行。如果当前 host / runner 真的没有 sub-agent 能力，只有默认并行 shortlist 或用户显式要求并行的场景才需要明示 `sub-agent unavailable`、原因和 coverage caveat，不能悄悄降级。

Modeling skills use a separate Model Sub-Agent Protocol. `3-statement-model`、`dcf-model`、`comps-analysis` 和 `model-update` 可以让 sub-agent 做 actuals mapping audit、formula check、peer multiple check 或 update-map QA，但 sub-agent 只能返回 model QA notes / work-packet findings。最终 workbook、valuation verdict、price target、model treatment 和 delivery decision 必须由主 agent 负责。建模前必须检查 `actuals-resolved.json`、`evidence-pack.json`、source-map 和 completeness；missing or unmapped actuals 不得写成 0。

---

### Q11：我需要 GitHub 账号吗？

**答**：不需要。你只需要从 GitHub Release 页面下载 zip 文件即可（甚至这一步也可以让 Claude 帮你——*"帮我找到 buy-side-research-skills 最新版本的下载地址"*）。你不需要注册 GitHub 账号，也不需要会用 git。

---

### Q12：我连 Python 都不会装

**答**：去 python.org，点那个黄色的大按钮下载，安装时**一定要勾选 "Add Python to PATH"**（这一步最重要），然后一路下一步。装好之后，剩下的依赖安装全部交给 Claude——对它说：*"帮我检查并安装 ingest 和 financial-data 的 Python 依赖"*。

---

## 9. 进阶：自定义与维护

> 以下内容面向有一定技术基础、想做自定义的用户。完全没有编程经验的用户可以跳过。

### 更新插件

当有新版本发布时，在**你当前正在用的宿主**里说：

> "用 update-agent-runtime 更新当前宿主插件并同步这个 workspace"

它会：

- 自动判断当前是在 Claude Code 还是 Codex 里运行
- 只更新当前宿主，不碰另一个宿主
- 从 GitHub latest release 拉最新 zip
- 同步修复当前 workspace 的 hooks、`_scripts/`、`CLAUDE.md` / `AGENTS.md` managed runtime sections

### 报告问题

在 [GitHub Issues](https://github.com/iRyantik/buy-side-research-skills/issues) 提 issue。

---

## 附录：快速参考卡片

### 我想…… 对照表

| 我想做什么 | 用这个 skill | 需要 Python 吗 | 大概耗时 |
|---|---|---|---|
| 快速看一家公司 | `stock-quickread` | 否 | 15-30 分钟 |
| 快速看一个行业 | `industry-quickread` | 否 | 20-40 分钟 |
| 从主题找受益股 | `candidate-screener` | 否 | 30-60 分钟 |
| 判断一条新闻 | `information-impact` | 否 | 10-15 分钟 |
| 看 Reddit 情绪 | `reddit-sentiment` | **是** | 15-45 分钟 |
| 研究卡住了 | `next-step` | 否 | 10 分钟 |
| 深度拆公司业务 | `company-primer` | 否 | 1-2 小时 |
| 拆市场预期 | `consensus-map` | 否 | 1-2 小时 |
| 搞懂行业技术 | `mechanism-map` | 否 | 1-2 小时 |
| 把研究文做成图 | `research-viz` | 否 | 20-60 分钟 |
| 拆收入/利润 driver | `driver-map` | 否（产出 markdown）/ 是（产出 JSON cache） | 1-3 小时 |
| 跨市场估值比较 | `cross-market-compare` | 否 | 1-2 小时 |
| 横向比较同行业公司 | `peer-deep-dive` | 否 | 2-4 小时 |
| 写做多/做空 thesis | `alpha-thesis` | 否 | 2-4 小时 |
| 找 thesis 漏洞 | `bear-pre-mortem` | 否 | 1-2 小时 |
| 准备财报 | `earnings-setup` | 否 | 1-2 小时 |
| 分析 pair trade | `pair-trade` | 否 | 2-3 小时 |
| 设计调研计划 | `primary-research-plan` | 否 | 1-2 小时 |
| 搭三表模型 | `3-statement-model` | 否 | 2-4 小时 |
| 做 DCF 估值 | `dcf-model` | 否 | 2-4 小时 |
| 做可比估值 | `comps-analysis` | 否 | 1-3 小时 |
| 更新已有模型 | `model-update` | 否 | 1-2 小时 |
| 沉淀研究结论 | `research-journal` | 否 | 30 分钟 |
| 处理 PDF/Excel 文件 | `ingest` | **是** | 按文件数量 |
| 拉美股财务数据 | `financial-data` | **是** | 5-15 分钟 |
| 拉 A 股/港股财务数据 | `financial-data` | **是** | 5-15 分钟 |
| 拉日/韩/欧股财务数据 | `financial-data` | **是** | 5-15 分钟 |

---

**版本**：v4.0.0
**最后更新**：2026-05-22
