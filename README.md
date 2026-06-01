# Buy-Side Research Skills — AI 研究员工具箱

> v5.0.0 | [iRyantik/buy-side-research-skills](https://github.com/iRyantik/buy-side-research-skills)

---

## 0. 一键安装

```bash
# Claude Code
claude plugin install buy-side-research-skills@buy-side-research-skills

# 第一次使用前，安装依赖
claude  # 进入 Claude Code
> /init-workspace  # 创建或修复 workspace
```

安装完成后问 Claude：`有哪些研究 skill？`——它应该列出 30+ 个技能。

> 如果看到 "command not found"，先确保 Claude Code 版本 >= 1.0.200。macOS 用户不需要额外配置。Windows 用户如果拉美股财务数据，需要配置 EDGAR_IDENTITY（详见 [docs/install.md](docs/install.md)）。

---

## 1. 快速开始：两个最常用 Workflow

### 从行业出发（找机会）

```
"用 industry-landscape 看光模块设备行业"
    → 行业全景：价值池、竞争格局、17 家公司表
"用 candidate-screener 做分场景 L/S 排序"
    → 3 个 regime 场景下哪家该多、哪家该空
"用 peer-deep-dive 比较 Top 5"
    → 横向矩阵：跨 5 个市场，统一 USD 估值
"用 scenario-model CPO>15% Long AEHR"
    → TAM x 份额 x PE = 隐含市值 + upside
```

### 从公司出发（深挖一只票）

```
"用 stock-quickread 看 MYCR SS"
    → 5 分钟快扫：业务、财务、催化剂、风险
    → 自动推荐下一步：driver-map / moat-analysis / capital-allocation
"用 moat-analysis 分析 MYCR 护城河"
    → Scorecard：技术壁垒 9/10、客户锁入 7/10
"用 catalyst-map 画催化剂时间线"
    → 2026 Q3 GT 订单 → 2027 H1 猎奇专利 → ...
"用 scenario-model bull/base/bear"
    → Base +22% / Bull +56% / Bear -22%
"用 alpha-thesis 写完整 thesis"
    → Long MYCR SS, target SEK 420, kill criteria
```

---

## 2. 完整 Skill 清单（32 个）

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
| `candidate-screener` | 分场景 L/S 排序 | "行业里这些票怎么排" |
| `peer-deep-dive` | 横向比较（同/跨市场） | "这几家一起比" |
| `moat-analysis` | 竞争壁垒量化 | "xxx 的护城河强不强" |
| `catalyst-map` | 催化剂时间线 | "xxx 有什么催化剂" |
| `capital-allocation` | 管理层资本配置评分 | "xxx 管理层钱花得怎么样" |
| `earnings-setup` | 财报前 prepare | "xxx 要发财报了 怎么 setup" |
| `alpha-thesis` | 投资 thesis | "帮我写 xxx 的 thesis" |
| `bear-pre-mortem` | 空头 pre-mortem | "xxx 怎么死" |
| `pair-trade` | LS 对 | "long A short B 怎么样" |
| `primary-research-plan` | 一手研究计划 | "怎么验证 xxx 假设" |
| `3-statement-model` | 三表模型 | "给 xxx 搭个模型" |
| `dcf-model` | DCF 估值 | "用 DCF 给 xxx 估值" |
| `comps-analysis` | 可比估值 | "用 comps 给 xxx 估值" |

### Supporting 层（辅助）

| Skill | 一句话 | 触发 |
|---|---|---|
| `scenario-model` | 场景量化测算 | "如果 CPO 渗透 15% AEHR 值多少" |
| `research-viz` | 可视化 | "把这个做成图" |

### Memory 层（沉淀）

| Skill | 一句话 | 触发 |
|---|---|---|
| `research-journal` | 沉淀研究认知 | "记录今天的发现" |
| `coverage-tracker` | 跟踪覆盖状态 | "更新 coverage 优先级" |

---

## 3. 系统特色

### 数据管线（防幻觉）

所有研究 skill 的财务数据走 `financial-data --lite` 统一入口。市场数据更经过四层 trust-based fill 链验证：

```
Bridge (Longbridge API) → yfinance → WebSearch → Google Finance
```

每一层的值如果被更高层覆盖，自动取高信任度结果。每个估值字段标注来源和 as-of 日期。详见 [docs/architecture.md](docs/architecture.md)。

### 38 条自动化 Hook 规则

保存每个研究产物前，系统自动检查：
- **Source contract**：每个数字/引语必须有 source link
- **Model checks**：三表模型公式自动用 Excel 打开重算，check ≠ 0 则拦截
- **Fact provenance**：每个定量声明必须有 Tier 标注
- **Claim proximity**：强声明（"独家供应商"）必须有 source 在同段

研究员不需要记这些规则——写错了系统会拦。

### 分场景 L/S 框架

`candidate-screener` v1.4 支持：
- 3 个宏观 regime（当前主导/过渡期/新范式）
- 每个 regime 下的多空方向
- 7 种策略原型：全场景多仓、小赌注、Flip 对冲、事件驱动、估值收敛、代际升级、叙事套利
- 每种策略绑定估值锚和目标估值

---

## 4. 依赖和环境

### 最小配置（所有平台）

| 市场 | 财务数据 | 市场数据 |
|---|---|---|
| US | 自动（SEC EDGAR） | Longbridge API 或 yfinance |
| A 股 | AKShare | 同上 |
| 港股 | Eastmoney HKF10 | 同上 |
| 日股 | EDINET | yfinance + WebSearch |
| 韩股 | DART（需 API key） | yfinance + WebSearch |
| 欧股 | openesef | yfinance + WebSearch |

### 一键环境检查

```bash
# 检查所有依赖
python _scripts/financial-data/financial_data.py --check-deps

# 安装缺失依赖
_scripts/financial-data/bootstrap-financial-data-deps.ps1 -Yes  # Windows
pwsh _scripts/financial-data/bootstrap-financial-data-deps.ps1 -Yes  # macOS
```

---

## 5. 版本历史

| 版本 | 日期 | 主要变化 |
|---|---|---|
| v5.0.0 | 2026-06 | 新增 7 个 skill、candidate-screener 分场景 L/S、全链路 hook 治理、跨市场合并至 peer-deep-dive、事实治理层 |
| v4.6.2 | 2026-05 | Runtime Capsule 标准化、market data trust-based fill、C-level modeling hooks |
| v4.5.6 | 2026-05 | mechanism-insight/industry-landscape/teach-in 改名、peer-deep-dive 重构 |

---

## 6. 常见问题

**Q: 财务数据拉不下来？**  
运行 `python _scripts/financial-data/financial_data.py --check-deps` 检查缺什么依赖。

**Q: 美股财报报错？**  
需要配置 `EDGAR_IDENTITY`（你的名字+邮箱），告诉 SEC 你是谁。详见 `docs/install.md`。

**Q: 市场数据拿不到？**  
非美股/港股/A 股的市场，yfinance 有时不稳定。系统会自动降级到 WebSearch 或 Google Finance 兜底。

**Q: 某个 skill 触发了错误的 skill？**  
检查 ChatGPT/Claude 的 slash command 设置——`.claude/settings.json`。

**Q: 如何更新插件？**  
运行 `/update-agent-runtime` 自动更新到最新版。
