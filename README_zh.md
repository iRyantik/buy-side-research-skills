# Buy-Side Research Skills — AI 研究员工具箱

English → [README.md](README.md)

35 个 skill 覆盖 triage、foundation、deep-work、operations 四层。source-tracked、evidence-gated、跨市场。

---

## 0. 安装

### VS Code 扩展

复制到 Claude Code：

```
1. 写 "skipWebFetchPreflight": true 到 ~/.claude/settings.json，然后重启 CC
2. 按照 https://github.com/iRyantik/buy-side-research-skills/blob/main/docs/install-vscode.md 安装 buy-side-research-skills
```

### CC Terminal

```
/plugin marketplace add iRyantik/buy-side-research-skills
/plugin install buy-side-research-skills
```

## 0a. 升级

```
/update-agent-runtime
```

---

## 1. 可选配置

| 需要什么 | 怎么拿到 |
|---|---|
| **SEC EDGAR 身份** | 对 Claude 说"设置 EDGAR 身份为 姓名,邮箱" |
| **DART API Key** | [dart.fss.or.kr](https://dart.fss.or.kr) 免费申请 |
| **EDINET Tools** | 对 Claude 说"安装 EDINET 依赖" |
| **欧股 ESEF 包** | 公司 IR 页下载 annual report（iXBRL）、提供文件路径 |
| **Longbridge 账户** | [longbridge.com](https://longbridge.com) 注册 |

---

## 2. 快速开始

**从行业出发**：`teach-in` → `industry-landscape` → `mechanism-insight` → `market-sizing` → `candidate-screener`

**从公司出发**：`stock-quickread` → `financial-data --lite` → `driver-map` → `moat-analysis` → `consensus-map` → `scenario-model` → `alpha-thesis`

📖 真实案例：[/examples/optical-module-equipment/](examples/optical-module-equipment/)

---

## 3. 完整 Skill 清单（35 个）

### Triage 层

| Skill | 一句话 |
|---|---|
| `stock-quickread` | 陌生公司 first pass |
| `information-impact` | 信息真伪和影响评估 |
| `post-earnings-quick` | 财报后 5 分钟判断 |
| `reddit-sentiment` | 社交媒体情绪分析 |

### Foundation 层

| Skill | 一句话 |
|---|---|
| `teach-in` | 零基础建立物理直觉 |
| `industry-landscape` | 行业全景 + 投资判断 |
| `financial-data` | 三表 + 市场快照 |
| `market-sizing` | TAM/SAM/SOM 拆解 |
| `mechanism-insight` | 技术/工程机制深挖 |
| `driver-map` | 收入/利润驱动拆解 |
| `company-history` | 业务演变 + 披露口径 |
| `consensus-map` | 市场预期 + priced-in |

### Deep-Work 层

| Skill | 一句话 |
|---|---|
| `candidate-screener` | 分场景 L/S 排序（7 种策略原型） |
| `scenario-model` | bull/base/bear odds memo + 假设溯源 |
| `peer-deep-dive` | 跨市场横向比较 |
| `moat-analysis` | 竞争壁垒量化 scorecard |
| `catalyst-map` | 催化剂时间线 + 概率加权 |
| `capital-allocation` | 管理层资本配置 10 年 ROI |
| `earnings-setup` | 财报前 setup |
| `alpha-thesis` | 投资 thesis |
| `bear-pre-mortem` | 空头 pre-mortem |
| `pair-trade` | LS 对 |
| `primary-research-plan` | 一手研究计划 |

### Supporting

| Skill | 一句话 |
|---|---|
| `research-viz` | 研究可视化 |

### Memory

| Skill | 一句话 |
|---|---|
| `research-journal` | 沉淀研究认知 |
| `coverage-tracker` | 跟踪覆盖公司状态 |

---

## 4. 常见问题

**Q: 财务数据拉不到？**
对 Claude 说：`check financial-data dependencies`

**Q: 美股 SEC 报错？**
配置 EDGAR 身份：`set EDGAR identity to 姓名,邮箱`

**Q: 怎么连 Longbridge？**
对 Claude 说：`connect Longbridge`。覆盖 US/HK/SH/SZ。

**Q: 日/韩/欧股数据？**
见上方 §1 配置表。日本免费，韩国需 API Key，欧盟需下载 ESEF 包。

**Q: 怎么更新插件？**
`/update-agent-runtime`，自动从 GitHub Release 拉最新版。

## 5. 版本历史

完整历史：[CHANGELOG.md](CHANGELOG.md)

| Version | Date | Changes |
|---|---|---|
| v8.3.0 | 2026-07 | 文档重构：CLAUDE 197 行，3 个新 reference 文件，35 skills |
| v8.0.0 | 2026-07 | 同事版：Python 自动安装，PreToolUse hooks，全部硬编码路径移除 |
| v7.6.35 | 2026-07 | P0-P2 修复：hook 激活、pip --user、路径清理 |
