# Buy-Side Research Skills — AI 研究员工具箱

> v5.3.0 | Claude Code + Codex 双宿主 | [iRyantik/buy-side-research-skills](https://github.com/iRyantik/buy-side-research-skills)

---

## 0. 安装

对 Claude / Codex 说：

```
按照 https://github.com/iRyantik/buy-side-research-skills/blob/main/docs/install.md 安装 buy-side-research-skills
```

---

## 0a. 升级

对 Claude / Codex 说：

```
/update-agent-runtime
```

自动从 GitHub Release 拉最新版，更新插件版本 + 同步 workspace hooks。每次发版后跑一次即可。

---

---

## 1. 需要额外配置

| 需要什么 | 怎么拿到 |
|---|---|
| **SEC EDGAR 身份** | 对 Claude 说"设置 EDGAR 身份为 姓名,邮箱" |
| **DART API Key** | [dart.fss.or.kr](https://dart.fss.or.kr) 免费申请，对 Claude 说"设 DART_API_KEY 为 xxx" |
| **EDINET Tools** | 对 Claude 说"安装 EDINET 依赖"。数据来自 [disclosure.edinet-fsa.go.jp](https://disclosure.edinet-fsa.go.jp)，免费 |
| **欧股 ESEF 包** | 从公司 IR 页下载 annual report（iXBRL，.zip 内含 .xhtml），拉数据时把文件路径给 financial-data |
| **ingest 文档转换** | 对 Claude 说"检查 ingest 依赖"，自动检测并提示安装 |
| **Longbridge 账户** | [longbridge.com](https://longbridge.com) 注册，对 Claude 说"连接 Longbridge" |

> 未列出的 skill 无需配置，装完直接用。

---

## 2. 快速开始：两个最常用 Workflow

### 从行业出发（找机会）

```
Step 1: teach-in              → 建立物理直觉（光模块是什么、怎么造的、设备链在哪）~20min
Step 2: industry-landscape    → 行业全景：价值池 51.8B、竞争格局、17 家公司注册表 ~20min
Step 3: mechanism-insight     → 深挖关键段竞争格局（固晶/耦合/Burn-in/CPO 路线分歧） ~30min
Step 4: market-sizing         → TAM 拆解（CPO burn-in $1.2B, coupling $2.8B） ~15min
Step 5: candidate-screener    → 3 regime 分场景 L/S 排序 + 7 策略原型 + 场景推票 ~40min
  ├→ scenario-model           → CPO>15% 场景 AEHR 理论市值 +148%（量化验证小赌注）
  └→ peer-deep-dive           → Top 5 横向比较、跨 5 市场统一 USD、growth-adjusted PEG
```

### 从公司出发（深挖一只票）

```
Step 1: stock-quickread       → 5 分钟 first pass：业务总览、焦点产品、财务表（标准+弹性列）、
                                  Growth Drivers & KPIs、周期位置、5 个深层问题 ~30min
  ├→ 设备公司 → 强制查 backlog/orders/ASP/B2B；流程工业 → 查产量/成本/利用率
  └→ 自动路由下一步：moat-analysis / catalyst-map / capital-allocation
Step 2: financial-data --lite → 三表 + 市场快照（增量 fill：yfinance→Bridge→WebSearch→Google） ~15s
Step 3: driver-map            → 拆 driver（organic vs M&A / price vs volume / backlog visibility）
                                  + Growth Quality（leading indicator / margin trajectory） ~30min
Step 4: moat-analysis         → 五维度评分 + peer 对标 + Hard/Medium/Soft 证据 + Killer Question
  ├→ catalyst-map             → 概率加权 catalyst chain + payoff ratio + timeline
  └→ capital-allocation       → 10Y buyback/M&A/dividend/capex ROI + moat bridge
Step 5: consensus-map         → consensus 隐含增速 vs 当前 PE 反推增速——Gap 在哪？
Step 6: scenario-model        → bull/base/bear odds memo + Growth/Margin/Multiple 三维 driver mix + sensitivity
Step 7: alpha-thesis          → thesis + kill criteria + next catalyst
```

---

> 📖 **不想读文档？** 跟着真实案例走一遍：[/examples/optical-module-equipment/](examples/optical-module-equipment/) — 从零基础到分场景 L/S 排序，5 步对话实录。

---

## 3. 完整 Skill 清单（32 个）

### Triage 层（快速判断）

| Skill | 一句话 | 触发 |
|---|---|---|
| `stock-quickread` | 陌生公司 first pass | "用 stock-quickread 看 xxx" |
| `information-impact` | 一条信息的真假和影响 | "这条新闻靠谱吗" |
| `next-step` | 下一步最该研究什么 | "接下来该看什么" |
| `post-earnings-quick` | 财报后 5 分钟判断 | "xxx 出财报了 快速看看" |
| `reddit-sentiment` | 社交媒体情绪 | "Reddit 上怎么说" |

### Foundation 层（打地基）

| Skill | 一句话 | 触发 |
|---|---|---|
| `teach-in` | 零基础建立物理直觉 | "光模块是什么" |
| `industry-landscape` | 行业全景+投资判断 | "用 industry-landscape 看 xxx 行业" |
| `financial-data` | 三表+市场快照 | "拉 xxx 的财务数据" |
| `market-sizing` | TAM/SAM/SOM 拆解 | "这个市场有多大" |
| `mechanism-insight` | 技术/工程机制深挖 | "固晶机怎么工作的" |
| `driver-map` | 收入/利润驱动拆解 | "xxx 靠什么赚钱" |
| `company-history` | 业务演变+披露口径 | "xxx 怎么变成今天这样的" |
| `consensus-map` | 市场预期+ priced-in | "市场对 xxx 的预期是什么" |

### Deep-Work 层（深度研究）

| Skill | 一句话 | 触发 |
|---|---|---|
| `candidate-screener` | 分场景 L/S 排序（7 种策略原型） | "行业里这些票怎么排" |
| `scenario-model` | Bull/base/bear odds memo + 假设溯源 | "如果 CPO 渗透 15% AEHR 值多少" |
| `peer-deep-dive` | 横向比较（同市场/跨市场） | "这几家一起比" |
| `moat-analysis` | 竞争壁垒量化 scorecard | "xxx 的护城河强不强" |
| `catalyst-map` | 催化剂时间线+概率加权 | "xxx 有什么催化剂" |
| `capital-allocation` | 管理层资本配置 10 年 ROI | "xxx 管理层钱花得怎么样" |
| `earnings-setup` | 财报前 prepare | "xxx 要发财报了 怎么 setup" |
| `alpha-thesis` | 投资 thesis | "帮我写 xxx 的 thesis" |
| `bear-pre-mortem` | 空头 pre-mortem | "xxx 怎么死" |
| `pair-trade` | LS 对 | "long A short B 怎么样" |
| `primary-research-plan` | 一手研究计划 | "怎么验证 xxx 假设" |
| `3-statement-model` | 完整三表模型 | "给 xxx 搭个模型" |
| `dcf-model` | DCF 估值 | "用 DCF 给 xxx 估值" |
| `comps-analysis` | 可比估值 | "用 comps 给 xxx 估值" |

### Supporting 层（辅助）

| Skill | 一句话 | 触发 |
|---|---|---|
| `research-viz` | 可视化 | "把这个做成图" |

### Memory 层（沉淀）

| Skill | 一句话 | 触发 |
|---|---|---|
| `research-journal` | 沉淀研究认知 | "记录今天的发现" |
| `coverage-tracker` | 跟踪覆盖公司状态 | "更新 coverage 优先级" |

---

## 4. 常见问题

**Q: 财务数据拉不下来？**
对 Claude 说 `检查 financial-data 依赖`。

**Q: 美股财报报错？**
需要配 EDGAR 身份。对 Claude 说 `设置 EDGAR 身份为 姓名,邮箱`。

**Q: 长桥怎么连？**
对 Claude 说 `连接 Longbridge`。仅 US/HK/SH/SZ 需要。

**Q: 日股/韩股/欧股数据怎么拿？**
见 §1 配置表。日股免费、韩股需 API key、欧股需下载 ESEF 包。

**Q: 如何更新插件？**
对 Claude 说 `/update-agent-runtime`。自动从 GitHub Release 拉最新版，更新插件+同步 workspace hooks。每次发新版本后跑一次。

---

## 5. 版本历史

| 版本 | 日期 | 主要变化 |
|---|---|---|
| v5.0.0 | 2026-06 | 7 个新 skill、candidate-screener 分场景 L/S、全链路 hook 治理、跨市场合并、事实治理层、Codex 双宿主 |
| v4.6.2 | 2026-05 | Runtime Capsule 标准化、market data trust-based fill、C-level modeling hooks |
| v4.5.6 | 2026-05 | mechanism-insight/industry-landscape/teach-in 改名、peer-deep-dive 重构 |
