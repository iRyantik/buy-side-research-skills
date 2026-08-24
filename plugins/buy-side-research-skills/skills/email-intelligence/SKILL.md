---
name: email-intelligence
description: Review preserved sell-side emails and generate a lightweight buy-side brief of updates, ideas, signals, and meetings.
---

# Email Intelligence

## 心法

这个 skill 不是逐封邮件摘要器。它把已保存的 sell-side 邮件压缩成一个轻量的注意力分配面板：哪些覆盖公司变了、哪些非核心公司值得调整研究优先级、哪些未覆盖公司可能成为 New Idea、行业发生了什么、哪些会议值得参加。

系统保持两层分离：Power Automate 只负责可靠保存邮件；本 skill 只读取保存结果并 review。New Idea 也不等于 sell-side initiation——必须是未进入 coverage 的公司出现了实质变化，并且符合当前 `## Focus` 区，才进入候选。

## 职责边界

负责：

- 读取 `/Email-AI/<邮件目录>/` 下的 `meta.txt`、`body.txt`、`outlook.link.txt` 和附件文件名。
- 结合 workspace `COVERAGE.md` 判断 Core / Other Coverage / 未覆盖公司。
- 结合 `## Focus` 区 判断当前研究 lens、主题假设和 New Idea fit。
- 一封 roundup 邮件拆出多个公司信息；一封会议合集拆出多场会议。
- 去重同一事件的多 broker 邮件，生成 5-section HTML brief。
- 增量记录已处理邮件，并复用 coverage-monitor 的 SMTP delivery。

不负责：

- 不配置或修改 Power Automate flow。
- 不下载 broker 登录墙后的报告。
- 不把附件全文自动写成 research artifact；长报告精炼属于后续 knowledge/extract layer。
- 不自动修改 `COVERAGE.md` 或 `## Focus` 区。
- 不把普通 initiation、目标价微调或 recap 包装成 New Idea。

## 触发与输入

触发短语：

- “review 卖方邮件”
- “生成 email brief”
- “email intelligence”
- “帮我筛今天的会议邮件”
- “看看卖方邮件有什么值得读的”

输入：

| 输入 | 默认 | 用途 |
|---|---|---|
| `base` | `EMAIL_INTELLIGENCE_BASE`，否则默认 OneDrive `/Email-AI/` | 邮件保存目录 |
| `workspace` | 当前 research workspace | 读取 `COVERAGE.md` / `## Focus` 区，保存 report/state |
| `all` | false | 忽略增量状态，重看全部邮件 |
| `dry_run` | false | 生成 HTML，不发送 |

前置条件：保存层至少提供 `body.txt`；`meta.txt` 和 Outlook link 缺失时可继续，但必须 honest degrade。AI review 需要 `DEEPSEEK_API_KEY`。

## 执行模式

### Mode A: Incremental Review

```bash
python .scripts/email-intelligence/run_email_intel.py review
```

流程：`scan → unseen filter → structured review → deterministic routing → merge → HTML → delivery → state`。

只有成功返回结构化 review 的邮件才标记 seen。AI review 全部失败时退出非零，不推进 state。

### Mode B: Dry Run / Full Replay

```bash
python .scripts/email-intelligence/run_email_intel.py review --dry-run
python .scripts/email-intelligence/run_email_intel.py review --all --no-send
```

## Report Contract

报告固定保持轻量，共 5 个正文 section：

1. **Core Watch**：Core 公司 earnings、guidance、order、estimate 或其他实质 update。
2. **Other Coverage**：非 Core coverage 的边际变化，并给 `read / watch / research / note / skip` 建议。
3. **New Ideas**：未进入 coverage、出现实质变化、且符合 `## Focus` 区 的公司。initiation 本身不构成入选理由。
4. **Industry & Sell-side Signals**：相关行业事实、peer read-through、宏观主题变化和真正 differentiated 的卖方观点。
5. **Meetings**：逐场列出会议名称、时间、主办方、讲者、形式、主题、推荐级别和一句理由。

顶部 `Worth Your Time` 只摘取最多 3 个优先事项，不另做重型 Top Changes section。重复、recap 和失败数量只放页尾一行。

## 工具资源

- 入口：`python .scripts/email-intelligence/run_email_intel.py review`
- AI：DeepSeek OpenAI-compatible API
- Delivery：复用 `.scripts/coverage-monitor/coverage_monitor/delivery.py`
- 状态：`.cache/email-intelligence/state.json`
- 产物：`daily/email/YYYYMMDD-email-brief-HHMM.html`

## 文件安全

- 保存层目录只读，不移动、不重命名、不删除原邮件或附件。
- `COVERAGE.md`、`## Focus` 区 只读。
- 只写 `daily/email/` 和 `.cache/email-intelligence/`。
- 不把 API key、邮件正文或附件内容写入日志。
- dry-run 不发送邮件；`--no-send` 不调用 SMTP。

## 运行输出契约

默认终端输出保持短：

```markdown
## Email Intelligence Result

**结论先行**
[处理邮件数、有效 signals、会议数、是否发送]

## Output
- [HTML 路径]

## Gaps
- [review / parse / delivery gap]
```

HTML 卡片只保留：发生了什么、为什么重要、建议动作、原邮件链接。会议卡只保留信息、主题和推荐。

## 失败处理

- 保存目录不存在或没有邮件：报告 `no emails found`，不写 state。
- `DEEPSEEK_API_KEY` 缺失或全部 chunk 失败：退出非零，不标记 seen。
- 部分 chunk 失败：成功邮件进入 brief；失败邮件保持 unseen，下次重试。
- Outlook link 缺失：展示 sender 文本，不伪造链接。
- SMTP 失败：保留已生成 HTML，返回 delivery gap；review state 仍记录成功解析的邮件，避免重复消耗 AI。

## Workflow 联动

| 上游 | 作用 |
|---|---|
| Power Automate `/Email-AI/` | 保存原始邮件、正文、link 和附件 |
| `COVERAGE.md` | 判断 Core / Other / 未覆盖 |
| `## Focus` 区 | 判断主题关联和 New Idea fit |

| 下游 | 作用 |
|---|---|
| `stock-quickread` | 对 New Idea 做 first pass |
| `candidate-screener` | 把邮件线索放进更完整的候选漏斗 |
| `meeting-minutes` | 会后把录音/转录变成研究输出 |
| future knowledge/extract layer | 精炼长附件和高价值邮件 |

## 安全自查

- ❌ 一封邮件只允许一个公司或一场会议。
- ❌ 把 initiation 自动放进 New Ideas。
- ❌ 因公司不在 coverage 就过滤同行业 update。
- ❌ 把普通目标价微调当 differentiated view。
- ❌ Meeting card 写成长篇投资分析。
- ❌ review 失败仍把全部邮件标记 seen。
- ❌ 修改或删除保存层原始文件。
- ❌ 没有 `## Focus` 区 时假装知道用户当前 preference。
