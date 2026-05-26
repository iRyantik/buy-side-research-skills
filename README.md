# Buy-Side Research Skills —— 零基础完全上手指南

> 当前版本：`4.3.1`
>
> 仓库地址：[iRyantik/buy-side-research-skills](https://github.com/iRyantik/buy-side-research-skills)

---

## 0. 这是什么？

**这个插件把专业股票研究员（buy-side analyst）的工作流程，变成了一套你在 Claude Code 或 Codex 里可以直接用中文对话触发的「技能」。**

想象你雇了一个非常聪明的研究助理。你跟他说：

- "帮我看一下 Vertiv 这家公司值不值得深入研究"
- "市场现在对 GE Vernova 的预期是什么？有没有哪里可能错了？"
- "帮我把 Rocket Lab 的财务数据拉出来，我要搭模型"
- "我想做多 Vertiv、做空西门子能源，帮我分析这个 pair trade 合不合理"

这个插件就是让 Claude / Codex 听得懂这些指令，并且按照专业研究员的标准来执行和输出。

### 你能做什么（不写一行代码）

| 你想做的事 | 跟 Claude 说什么 |
|---|---|
| 快速看一家不熟的公司 | "用 stock-quickread 看 Vertiv" |
| 快速了解一个陌生行业 | "用 industry-quickread 看核电行业" |
| 搞清楚一家公司到底靠什么赚钱 | "用 driver-map 拆 Rocket Lab 的收入 driver" |
| 搞懂一个行业的技术原理 | "用 mechanism-map 解释燃气轮机产业链" |
| 拉美股/A股/港股/日股/韩股/欧股的财务数据 | "用 financial-data 拉 AAPL 美股数据" |
| 搭三表财务预测模型 | "用 3-statement-model 给 GE 搭模型" |
| 做 DCF 估值 | "用 dcf-model 给 Rocket Lab 做 DCF" |
| 看市场对一只股票的预期 | "用 consensus-map 看市场对 IONQ 的预期" |
| 写一份完整的做多/做空 thesis | "用 alpha-thesis 写 GE Vernova 做多逻辑" |
| 找 thesis 的漏洞 | "用 bear-pre-mortem 打我 GEV 做多 thesis" |
| 准备财报季 | "用 earnings-setup 准备下周 GE 的财报" |
| 设计一对 pair trade | "用 pair-trade 分析做多 VRT 做空 SMCI" |
| 比较几家同行业公司 | "用 peer-deep-dive 比较 VRT、GEV、SMCI" |
| 看 Reddit 上的情绪和高信号帖子 | "用 reddit-sentiment 查 IONQ 在 Reddit 上怎么看" |
| 把研究文做成 memo-ready HTML 图 | "用 research-viz 把这篇做成 capability map" |
| 把研究结论沉淀下来 | "用 research-journal 总结这轮研究" |
| 拉取实时行情/估值/共识数据 | "用 trusted-market-bridge 拉 NVDA 的市场数据" |

### 你不能做什么（重要边界）

- 插件不会替你买卖股票，不会替你下单。
- 插件给的是分析框架和判断依据，不是投资建议。
- 所有财务数据来自公开源（SEC、交易所公告等），插件不做数据造假，也不会替你核实每一条第三方数据。
- Longbridge 提供的是市场快照数据（行情/估值/共识），不替代公司披露原文。

---

## 1. 我不会编程，能用吗？

**能。** 你需要会的是：

1. **打字** —— 用自然语言跟 Claude Code 或 Codex 对话。
2. **知道你要研究什么** —— 知道公司名或股票代码，知道你想回答什么问题。
3. **有基本的文件操作能力** —— 新建文件夹、把 PDF/Excel 拖进文件夹。

### 你需要先装好的东西

| 你需要什么 | 怎么装 | 要不要钱 |
|---|---|---|
| **Claude Code** 或 **Codex** | 去官网下载安装即可 | Claude Code 需要 Anthropic 账号和 API 额度；Codex 取决于你的授权 |
| **Python**（仅处理文件或拉财务数据时需要） | 去 python.org 下载，安装时勾选 "Add Python to PATH" | 免费 |
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

## 2. 安装

### 第一步：确认 Claude Code 或 Codex 已装好

打开你的 Claude Code，随便跟它说句话（比如"你好"）。如果能正常回复，说明已装好。

### 第二步：安装本插件

**方法一：通过 Marketplace 安装（推荐）**

直接在 Claude Code 或 Codex 里说：

> **Claude Code**：`/plugin marketplace add iRyantik/buy-side-research-skills`，然后 `/plugin install buy-side-research-skills`

> **Codex**：`codex plugin marketplace add iRyantik/buy-side-research-skills`

**方法二：从 Release 下载本地安装**

1. 打开 [GitHub Release 页面](https://github.com/iRyantik/buy-side-research-skills/releases)
2. 下载最新版本的 `buy-side-research-skills-X.X.X.zip`
3. 解压到你电脑上的一个文件夹（记下路径）
4. 在 Claude Code 里说：**"帮我安装本地插件，路径是 xxx"**（把 xxx 换成你解压的文件夹路径）

### 第三步：验证安装成功

在 Claude Code 里说：

> "帮我检查 buy-side-research-skills 插件是否正确安装了"

如果 Claude 回复说能看到一列 skill 名字（如 `stock-quickread`、`financial-data`、`driver-map` 等），说明安装成功。

> **macOS 用户**：workspace 需要 PowerShell 7（`pwsh`）环境。



## 3. 配置

以下所有步骤都**不需要你手动敲任何命令**。你只需要在 Claude Code 里用中文说一句话，Claude 会帮你完成。

### 3.1 创建你的研究 Workspace

**关键原则：不要在本插件文件夹里做研究。** 你需要另外建一个空文件夹作为你的"研究笔记本"。

在你的电脑桌面或文档文件夹里，新建一个空文件夹。名字随意，比如 `我的研究`。然后打开 Claude Code，把工作目录切到这个新文件夹。接着对 Claude 说：

> "帮我初始化研究 workspace"

Claude 会自动帮你创建如下骨架：

```
我的研究/
├── CLAUDE.md              # workspace 配置
├── _inbox/                # 临时存放待处理的文件
├── _scripts/              # 辅助脚本
├── edge-radar.md          # 跨主题研究雷达
└── topics/                # 所有研究主题都放在这里（目前是空的）
```

`init-workspace` 只建骨架，不安装 Python 依赖。

### 3.2 配置数据源

#### 美股（SEC EDGAR）

美国 SEC 要求访问 EDGAR 数据库的人自报身份。**不需要注册，不需要密码。**

> "我的 EDGAR 身份是 张三 zhangsan@email.com，帮我配置好美股数据访问"

#### Longbridge 市场数据（可选，但推荐）

Longbridge（长桥证券）提供 **A股 / 港股 / 美股** 的实时行情、估值、分析师共识、财务快照等市场数据。本插件的 research skills 会通过 `trusted-market-bridge` 自动补市场数据缺口，如果 Longbridge 不可用，会自动降级到公开互联网数据。

对 Claude 说以下 prompt 即可一键完成 Longbridge 安装和登录：

> 请按照以下指南安装 Longbridge AI toolkit：
>
> **Claude Code 用户（插件方式）：**
> `/plugin marketplace add longbridge/skills`，然后 `/plugin install longbridge@longbridge-skills`
>
> **Codex 用户（插件方式）：**
> `codex plugin marketplace add longbridge/skills`
>
> 安装指南：https://open.longbridge.com/skill/install.md
>
> 安装完成后，完成登录授权，查询一支股票行情确认可用。

#### A股 / 港股

**零配置**，不需要任何 key，直接用。

#### 日股（EDINET）/ 韩股（DART）/ 欧股（ESEF）

| 市场 | 需要什么 | 获取方式 |
|---|---|---|
| 日股（JP） | `EDINET_API_KEY` | 去 https://disclosure2.edinet-fsa.go.jp/ 注册申请 |
| 韩股（KR） | `DART_API_KEY` | 去 https://opendart.fss.or.kr/ 注册即可 |
| 欧股（EU） | 通常无 | 提供 filing URL 或本地 ESEF 文件即可 |

拿到 key 后告诉 Claude：*"帮我配置日股 EDINET key：xxx"*。

### 3.3 安装 Python 依赖（可选）

**如果你只做对话类研究（分析、写 thesis、做 peer comparison），跳过这一步。**

需要用文件处理、数据拉取、Reddit 情绪分析或 DCF 建模功能时，对 Claude 说你想做什么，它会自动安装对应的依赖：

> "我要用 ingest 处理 PDF 文件，帮我检查并安装需要的依赖"
>
> "我要用 financial-data 拉美股数据，帮我检查并安装需要的依赖"
>
> "我要用 reddit-sentiment 查 Reddit 情绪，帮我检查并安装需要的依赖"
>
> "我要用 dcf-model 搭模型，帮我检查并安装需要的依赖"

各功能对应的 Python 包：

| 功能 | 会装哪些 Python 包 |
|---|---|
| **处理 PDF/Excel/PPT/Word 文件**（ingest） | docling, edgartools, pymupdf4llm, openpyxl, python-pptx, python-docx, pdfplumber, pypdf, Pillow |
| **拉取美股/A股/港股/日股/韩股财务数据**（financial-data） | edgartools, akshare, edinet-tools, dart-fss, openesef |
| **看 Reddit 情绪**（reddit-sentiment） | scrapi-reddit |
| **生成 DCF Excel 模型**（dcf-model） | openpyxl, requests |

> **可选环境变量**：`env-setup.ps1.template` 还包含 `EDGAR_LOCAL_DATA_DIR`（EDGAR 缓存路径）、`HF_ENDPOINT`（中国用户 HuggingFace 镜像）和 `VLM_API_URL`（图片描述视觉模型），这些通常不需要手动设置，Claude 会按需配置。

---

## 4. 快速入门

以下所有场景，你都是在用中文跟 Claude 对话。不需要写代码，不需要敲命令。

### 场景 A：快速看一家不熟的公司

**你**：帮我新建一个 Vertiv 的研究 session

**你**：用 stock-quickread 快速看一下 VRT

**你**：（看完觉得有意思）用 consensus-map 看市场对 VRT 的预期

**你**：用 driver-map 拆 VRT 的 revenue driver

**你**：（研究完了）用 research-journal 总结这轮 VRT 的发现

---

### 场景 B：有主题想法，找受益股

**你**：帮我新建一个 AI 数据中心电力的研究 session

**你**：用 industry-quickread 看 AI 数据中心电力行业

**你**：用 candidate-screener 找 AI 数据中心电力的受益股

**你**：（筛选出几家后）用 peer-deep-dive 比较 VRT、GEV、SMCI

---

### 场景 C：认真研究一家公司，搭模型

**你**：帮我新建一个 Rocket Lab 的研究 session

**你**：用 financial-data 拉 RKLB 美股数据

**你**：用 company-primer 深度看 RKLB

**你**：用 driver-map 拆 RKLB 的 revenue driver

**你**：用 3-statement-model 给 RKLB 搭历史+预测三表模型

**你**：用 dcf-model 给 RKLB 做估值

**你**：用 alpha-thesis 写 RKLB 做多 thesis

**你**：用 bear-pre-mortem 打一下这个做多 thesis

---

### 场景 D：财报季来了

**你**：帮我新建一个 GE Q1 2026 财报的研究 session

**你**：用 earnings-setup 准备下周 GE 的财报

**你**：（财报出了后）用 model-update 把最新数据更新进 GE 的模型

**你**：用 research-journal 记录 post-earnings 的判断更新

---

### 场景 E：搞懂一个陌生行业

**你**：帮我新建一个燃气轮机行业的研究 session

**你**：用 industry-quickread 看燃气轮机行业

**你**：用 mechanism-map 解释燃气轮机

**你**：（搞清机制后）用 candidate-screener 在燃气轮机价值链上找上市公司

**你**：用 peer-deep-dive 比较 GE Vernova、西门子能源、三菱重工

---

### 场景 F：突发新闻来了

**你**：我刚刚看到——"美国商务部提议限制 AI 芯片出口"。用 information-impact 分析这条消息

**你**：（根据分析结果）用 candidate-screener 按这个消息的逻辑找受益股

---

### 场景 G：想做空一只股票

**你**：帮我新建一个 IONQ 做空的研究 session

**你**：用 consensus-map 看市场对 IONQ 的预期

**你**：用 driver-map 拆 IONQ 的 revenue driver

**你**：用 alpha-thesis 写 IONQ 做空 thesis

**你**：用 bear-pre-mortem 反打这份做空 thesis（检验你的做空逻辑）

---

**整个过程你没有写一行代码，也没有敲任何命令。你只是在用中文跟 Claude 对话。**

## 5. Skill 速查表

### 运维类

| 我想做什么 | 跟 Claude 说 | Skill 名字 |
|---|---|---|
| 创建/修复研究 workspace | "帮我初始化研究 workspace" | `init-workspace` |
| 新建一个研究主题 | "帮我新建一个 XXX 的研究 session" | `new-session` |
| 把 PDF/Excel/PPT 转成可搜索文本 | "帮我用 ingest 处理 \_inbox 里的文件" | `ingest` |
| 拉取美股/A股/港股/日股/韩股财务数据 | "用 financial-data 拉 AAPL 美股数据" | `financial-data` |
| 获取实时行情/估值/共识（A股/港股/美股） | "用 trusted-market-bridge 拉 NVDA 市场数据" | `trusted-market-bridge` |
| 更新插件到最新版 | "用 update-agent-runtime 更新插件" | `update-agent-runtime` |
| 合并子 topic | "帮我把子 topic 合并到父 topic" | `integrate` |
| 把行业里的公司研究沉淀到 company 目录 | "把 XXX 的 RKLB 研究 promote 到 company" | `promote-company` |

### 研究类

| 我想做什么 | 跟 Claude 说 | Skill 名字 |
|---|---|---|
| 快速看一家公司 | "用 stock-quickread 看 VRT" | `stock-quickread` |
| 快速了解一个行业 | "用 industry-quickread 看核电行业" | `industry-quickread` |
| 从主题出发找受益股 | "用 candidate-screener 找 AI 电力的受益股" | `candidate-screener` |
| 判断一条新闻靠不靠谱 | "用 information-impact 分析这条消息" | `information-impact` |
| 看 Reddit 上的股票情绪 | "用 reddit-sentiment 查 IONQ 在 Reddit 上怎么看" | `reddit-sentiment` |
| 研究卡住了问下一步 | "用 next-step 帮我判断下一步研究什么" | `next-step` |
| 深度拆解一家公司业务 | "用 company-primer 深度看 GE Vernova" | `company-primer` |
| 拆市场预期/priced-in | "用 consensus-map 看市场对 IONQ 的预期" | `consensus-map` |
| 搞懂行业技术/工程原理 | "用 mechanism-map 解释燃气轮机" | `mechanism-map` |
| 拆收入/利润 driver | "用 driver-map 拆 Rocket Lab 的 revenue driver" | `driver-map` |
| 跨市场估值比较（A/H/ADR） | "用 cross-market-compare 比较比亚迪 A 股和 H 股" | `cross-market-compare` |
| 横向比较同行业公司 | "用 peer-deep-dive 比较 VRT、GEV、SMCI" | `peer-deep-dive` |
| 写做多/做空 thesis | "用 alpha-thesis 写 IONQ 做空 thesis" | `alpha-thesis` |
| 找 thesis 漏洞/压测 | "用 bear-pre-mortem 压测我对 RKLB 的多头 thesis" | `bear-pre-mortem` |
| 准备财报季 | "用 earnings-setup 准备下周 GE 的财报" | `earnings-setup` |
| 分析 pair trade | "用 pair-trade 分析做多 VRT 做空 SMCI" | `pair-trade` |
| 设计专家访谈/调研计划 | "用 primary-research-plan 设计验证方案" | `primary-research-plan` |
| 搭三表财务预测模型 | "用 3-statement-model 给 Rocket Lab 搭模型" | `3-statement-model` |
| 做 DCF 估值 | "用 dcf-model 给 GE Vernova 做估值" | `dcf-model` |
| 做可比公司估值 | "用 comps-analysis 做核电行业的可比分析" | `comps-analysis` |
| 更新已有模型（财报后） | "用 model-update 更新 GE 的模型" | `model-update` |
| 把研究结论沉淀下来 | "用 research-journal 总结这轮研究" | `research-journal` |
| 把研究文做成 HTML 图表 | "用 research-viz 把这篇做成 capability map" | `research-viz` |

---

## 6. 文件放在哪里？

研究产物都放在 `topics/` 下。你不需要手动管理，Claude 会自动处理。

```
我的研究/
├── _inbox/                    ← 还没分类的临时文件丢这里
├── _scripts/                  ← 辅助脚本（自动生成）
├── edge-radar.md              ← 跨主题研究雷达
└── topics/
    ├── company/rocket-lab/    ← Rocket Lab 的所有研究
    │   ├── index.md
    │   ├── 2026-05-13-stock-quickread.md
    │   └── 2026-05-15-dcf-model.md
    ├── industry/nuclear-power/ ← 核电行业研究
    └── pair/vrt-long-smci/    ← pair trade 研究
```

**两条核心规则**：

1. **文件名带日期**，格式为 `YYYY-MM-DD-<skill名>.md`。例如 `2026-05-14-driver-map.md`。
2. **一个 topic 是长期容器**，不会因为"这轮研究做完了"就删除。下次有新发现、新财报，继续往里加日期文件即可。

---

## 7. 常见问题

### Q1：我不知道该用哪个 skill

直接用自然语言跟 Claude 说你想干什么，比如 *"我想快速看一下 Vertiv 这家公司"*，Claude 会自动判断该触发哪个 skill。不需要死记硬背上表。

### Q2：Claude 说 "skill 找不到" 或插件没生效

对 Claude 说：*"帮我检查 buy-side-research-skills 插件是否正确安装了"*。

### Q3：ingest 处理 PDF 时报错

把报错信息直接发给 Claude：*"ingest 这个 PDF 时报了错，帮我看看是什么问题"*。常见原因：Python 没装好、依赖没装、PDF 是扫描件（需要 OCR）、PDF 有密码保护。

### Q4：financial-data 拉美股数据时报错

对 Claude 说：*"financial-data 拉美股数据时报了错，帮我排查"*。常见原因：EDGAR 身份没配置、Python 依赖没装、股票代码写错了。

### Q5：结果文件里的 source link 打不开

- 链接标注了 `[link 待补]` → Claude 不确定 URL 是否存在，需手动查证。
- 链接标注了 `[agent-provided, 未验证]` → AI 提供的 URL，需抽查。
- 插件遵循严格的反幻觉规则，宁可标注"不确定"也不编造链接。

---

**版本**：v4.3.0
**最后更新**：2026-05-26
