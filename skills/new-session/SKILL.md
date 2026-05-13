---
name: new-session
description: Use when creating or locating a topic research session, resolving where a skill artifact should be saved, or lightly updating a topic index with session links and open questions.
---

# New Session

本 skill 的目标是把 topic 和 session 分清楚：topic 是长期容器，session 是某一天 / 某次研究问题。它解决的是“这次研究应该落到哪个 dated session”，不是“应该研究什么”。

## 心法

研究文件夹最容易乱，不是因为研究员不知道怎么研究，而是因为每次保存时临时造路径。`new-session` 的核心价值是把保存位置变成可复用的确定动作：先定位长期 topic，再定位本次 dated session，最后只解析用户明确需要的 artifact path。

`index.md` 是演进式地图，不是 journal、不是 checklist、不是状态数据库。它只记录当前 topic 的研究问题、session links、当前结论占位和 open questions；真正的 earned insight 仍然必须交给 `research-journal`。

## 职责边界

负责：

- 创建或定位 `topics/[topic-namespace]/[topic-slug]/[YYYY-MM-DD]-[session-slug]/`。
- 支持并记录 topic namespace：`company`、`industry`、`theme`、`pair`。
- 创建 topic 完整 scaffold：`_inbox/`、`_raw/{filings,transcripts,sellside,industry,irdecks,datasets}/`、`_cache/`、`_models/`。
- 确保 topic-level `index.md` 存在。
- 只为用户明确请求的 artifact 输出 save path。
- 轻量更新 `index.md` 的 session link、current question、open questions。

不负责：

- 不做公司研究、行业研究、driver-map、mechanism-map、thesis 或 financial model。
- 不写 `research-journal.md`、`boss-brief.md` 或 earned insight。
- 不推荐下一步 research skill。
- 不 ingest raw material（只创建空 `_inbox/` 和 `_raw/` 目录，不往里写文件）。
- 不预创建 research output markdown；session 内只保存实际产出的文件。
- 不按 research skill 名创建 session；`session_slug` 必须来自本次研究问题。
- 可扫描 `topics/<topic-namespace>/<topic-slug>/_cache/` 列出已有材料，供后续研究 skill 使用。
- 不创建 v2 state folders，例如 `coverage/`、`pairs/`、`portfolio/`。

## 触发与输入

触发短语：

- “新建一个 NVDA supply chain 的 topic session”
- “帮我开一个 company/GE 的 session”
- “这个 driver-map 应该存到哪里”
- “更新一下这个 topic index”
- “resolve save path”
- “create topic session”
- “new session”

输入要求：

| 输入 | 用途 | 默认 / 缺失处理 |
|---|---|---|
| `topic_slug` | topic 目录名 | 从公司 / 主题名生成 kebab-case slug |
| `topic_namespace` | `company` / `industry` / `theme` / `pair` | 公司默认 `company`；行业默认 `industry`；主题默认 `theme`；pair 默认 `pair` |
| `session_slug` | session 目录名 | 从本次研究问题生成 kebab-case slug，不使用 skill 名 |
| `date` | session 日期 | 默认使用当前日期 `YYYY-MM-DD` |
| `workspace_path` | research workspace 根目录 | 不明确时只输出相对路径，不写文件 |
| `artifact_name` | 需要 resolve 的 artifact | 缺失时只输出 session path，不列全套 artifact paths |

## 执行模式

### New Topic Session

创建或定位：

```text
topics/[topic-namespace]/[topic-slug]/[YYYY-MM-DD]-[session-slug]/
```

同时确保：

```text
topics/[topic-namespace]/[topic-slug]/index.md
```

如果 topic 已存在，只追加或定位 dated session，不重建 topic scaffold。若同一天同 topic 有不同问题，使用不同 `session_slug`，例如：

```text
topics/company/rklb/2026-05-13-launch-economics/
topics/company/rklb/2026-05-13-backlog-quality/
```

如果用户说“继续上次”，优先定位最近 session，并报告 located，不新建。若用户明确说“新开一轮研究”，即使 topic 相同，也创建新的 dated session。Session 目录只保存实际产出的 research Markdown，不预创建全套文件。

创建 session 后，扫描 `topics/<topic-namespace>/<topic-slug>/_cache/` 列出该 topic 下已 ingest 的 markdown 材料。对 company topic，同时列出 `financial-data` evidence pack 路径（如存在）。

### Resolve Save Path

当其他 skill 要保存 artifact 但当前 session 不明确时，只输出用户明确请求的 canonical path，不要一次性列出所有可能 artifact。

示例：

```text
topics/company/rklb/2026-05-13-launch-economics/driver-map.md
topics/company/rklb/2026-05-13-launch-economics/alpha-thesis.md
```

如果用户没有指定 artifact，只输出 session path 和“artifact name needed”，不要猜文件名。

### Index Touch

只更新 topic `index.md` 的轻量地图字段：

- current question
- session links
- open questions
- related artifacts

不要写 earned insight。已经研究清楚、能改变判断的内容必须交给 `research-journal`。

## 工具资源

本 skill 没有独立脚本。可以直接使用文件系统操作创建目录和轻量编辑 `index.md`。

参考：

- workspace `CLAUDE.md`
- `skills/init-workspace/assets/CLAUDE.md.template`
- `research-journal` 的 Topic Index Update 行为
- `skill.yaml.artifact_policy` 中的 canonical paths

## 文件安全

- 不覆盖已有 `index.md`；只追加 / 轻量更新明确字段。
- 不删除、移动或重命名已有 session。
- 不写入 `topics/<topic>/_raw/`、`_cache/`、`_models/`。
- 不创建 root `screens/`、`peers/`、`quickreads/`、`cross-market/`。
- 不在 plugin dev repo 里创建 research workspace topic，除非用户明确说明这是 example workspace。
- 路径不明确时只输出建议路径，不执行写入。

## 运行输出契约

默认输出：

```markdown
## New Session Result

**结论先行**
已创建 / 已定位 topic session: [path]

## Topic / Session
- topic root: [...]
- topic index: [...]
- session path: [...]
- session mode: created / located / reused recent session

## Requested Save Path
- requested artifact: [... or "not provided"]
- path: [... or "artifact name needed"]

## Cached Materials
- topic: [...]
- path: `topics/<topic-namespace>/<topic-slug>/_cache/`
- files found: [... or "none"]

## Index Touch
- index path: [...]
- added session link: yes / no
- updated current question: yes / no
- updated open questions: yes / no
```

阻塞时输出：

```markdown
## New Session Blocked

**结论先行**
还不能创建 / 更新 topic session，因为路径或 topic 信息不明确。
- missing: [...]
- suggested_path: [...]
- needed_input: [...]
```

不要输出 `Next Step` 或“建议继续用哪个 research skill”。

## 失败处理

- `topic_slug` 不清：只给候选 slug，不写文件。
- workspace path 不清：输出相对路径，不创建目录。
- session 已存在：报告 located，不覆盖文件。
- 用户说“继续上次”：定位最近 session 并报告 located，不新建。
- 用户明确说“新开一轮研究”：即使 topic 相同，也创建新的 dated session。
- `index.md` 已存在但结构不同：只追加 session link，不重写整个 index。
- 用户要求写研究结论：拒绝在本 skill 内写，说明应交给 `research-journal`。

## Workflow 联动

| 场景 | 处理 |
|---|---|
| `init-workspace` 完成后用户要开始研究某个 topic | 用 `new-session` 创建 topic session |
| 研究 skill 要保存 artifact 但 session 不明确 | 用 `new-session` resolve save path |
| `research-journal` 要写 journal / Boss Brief 但路径不明确 | 先用 `new-session` 确认 session |
| 用户只想把本次 session 加进 topic map | 用 `Index Touch`，不写 earned insight |
| 用户说“继续上次” | 定位最近 dated session，不新建 |
| 用户说“新开一轮研究” | 在同一 topic 下创建新的 dated session |
| 用户问下一步研究什么 | 不是本 skill，交给 `next-step` |

Artifact policy：

- `save_policy`: `topic_session_scaffold`
- `default_artifact`: `dated topic session folder + index.md`
- `canonical_location`: `topics/[topic-namespace]/[topic-slug]/[YYYY-MM-DD]-[session-slug]/`

Topic namespace convention：

- company: `topics/company/<company-slug>/`
- industry: `topics/industry/<industry-slug>/`
- theme: `topics/theme/<theme-slug>/`
- pair: `topics/pair/<pair-slug>/`

## 安全自查

- ❌ 写研究结论、thesis、driver 判断或 source-backed insight。
- ❌ 推荐下一步 research skill。
- ❌ 把 `index.md` 写成 checklist、transcript 或 v2 state file。
- ❌ 覆盖已有 `index.md` 或 session 文件。
- ❌ session 不明确时擅自发明复杂目录树并写入。
- ❌ 预创建全套 research output markdown。
- ❌ 按 research skill 名创建 session，而不是按本次研究问题命名。
- ❌ 把 `_cache/` markdown 文件当作 topic artifact（cache 是研究辅助，不是 earned memory）。
- ❌ 创建 `coverage/`、`pairs/`、`portfolio/` 等 v2 state folders。
