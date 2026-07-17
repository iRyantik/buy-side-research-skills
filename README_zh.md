# Buy-Side Research Skills — AI 研究员工具箱

> v8.2.1 | Claude Code + Codex 双宿主 | [iRyantik/buy-side-research-skills](https://github.com/iRyantik/buy-side-research-skills)

journal-first 买方股权研究 skill 套件：35 个 skill 覆盖 triage、foundation、deep-work、operations 四层。source-tracked、evidence-gated、跨市场。

English → [README.md](README.md)

---

## 0. 安装

对 Claude Code 说：

```
按照 https://github.com/iRyantik/buy-side-research-skills/blob/main/docs/install.md 安装 buy-side-research-skills
```

如果提示"unable to verify domain"，先在 `~/.claude/settings.json` 加 `"skipWebFetchPreflight": true` 并重启 CC。

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

详见 [README.md §3](README.md#3-full-skill-list-35-skills)

---

## 4. 常见问题

详见 [README.md §4](README.md#4-faq)
