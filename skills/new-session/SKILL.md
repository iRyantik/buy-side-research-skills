---
name: new-session
description: Use when creating or locating a topic root, resolving a dated research result filename, or lightly updating a topic index.
---

# New Session

本 skill 的目标是把 research 保存位置变简单：topic 是长期容器，research Markdown 直接在 topic root 用日期命名。它解决的是“这个结果应该落到哪个 topic、用什么日期文件名”，不是“应该研究什么”。

## 心法

研究文件夹最容易乱，不是因为研究员不知道怎么研究，而是因为每次保存时临时造路径。`new-session` 的核心价值是把保存位置变成可复用的确定动作：先定位长期 topic，再解析一个日期化 result filename。

`index.md` 是演进式地图，不是 journal、不是 checklist、不是状态数据库。它只记录当前 topic 的研究问题、dated result links、当前结论占位和 open questions；真正的 earned insight 仍然必须交给 `research-journal`。

## 职责边界

负责：

- 创建或定位 `topics/[topic-namespace]/[topic-slug]/`。
- 支持并记录 topic namespace：`company`、`industry`、`theme`、`pair`。
- 创建 topic 完整 scaffold：`_inbox/`、`_raw/{filings,transcripts,sellside,industry,irdecks,datasets}/`、`_cache/`、`_models/`。
- 确保 topic-level `index.md` 存在。
- 只为用户明确请求的 artifact 输出 dated result path。
- 轻量更新 `index.md` 的 dated result links、current question、open questions。
- 可扫描 `topics/<topic-namespace>/<topic-slug>/_cache/` 列出已有材料，供后续研究 skill 使用。

不负责：

- 不做公司研究、行业研究、driver-map、mechanism-map、thesis 或 financial model。
- 不写 `research-journal.md`、`boss-brief.md` 或 earned insight。
- 不推荐下一步 research skill。
- 不 ingest raw material（只创建空 `_inbox/` 和 `_raw/` 目录，不往里写文件）。
- 不预创建 research output markdown；只解析用户明确要保存的那个文件名。
- 不为每一次研究创建子目录；research 结果只用 topic root + 日期文件名区分。
- 不创建 v2 state folders，例如 `coverage/`、`pairs/`、`portfolio/`。

## 触发与输入

触发短语：

- “新建一个 NVDA supply chain 的 topic”
- “帮我开一个 company/GE”
- “这个 driver-map 应该存到哪里”
- “更新一下这个 topic index”
- “resolve save path”
- “create topic”
- “new session”

输入要求：

| 输入 | 用途 | 默认 / 缺失处理 |
|---|---|---|
| `topic_slug` | topic 目录名 | 从公司 / 主题名生成 kebab-case slug |
| `topic_namespace` | `company` / `industry` / `theme` / `pair` | 公司默认 `company`；行业默认 `industry`；主题默认 `theme`；pair 默认 `pair` |
| `date` | result 日期 | 默认使用当前日期 `YYYY-MM-DD` |
| `workspace_path` | research workspace 根目录 | 不明确时只输出相对路径，不写文件 |
| `artifact_name` | 需要 resolve 的 artifact | 缺失时只输出 topic root 和“artifact name needed” |

## 执行模式

### New Topic Root

创建或定位：

```text
topics/[topic-namespace]/[topic-slug]/
```

同时确保：

```text
topics/[topic-namespace]/[topic-slug]/index.md
```

如果 topic 已存在，只复用 topic scaffold，不重建已有目录。创建 / 定位 topic 后，扫描 `topics/<topic-namespace>/<topic-slug>/_cache/` 列出该 topic 下已 ingest 的 markdown 材料。对 company topic，同时列出 `financial-data` evidence pack 路径（如存在）。

### Resolve Dated Result Path

当其他 skill 要保存 artifact 但保存位置不明确时，只输出用户明确请求的 canonical path，不要一次性列出所有可能 artifact。

默认格式：

```text
topics/[topic-namespace]/[topic-slug]/[YYYY-MM-DD]-[artifact].md
```

示例：

```text
topics/company/rklb/2026-05-14-driver-map.md
topics/company/rklb/2026-05-14-alpha-thesis.md
```

如果同名文件已存在，保留历史，使用最低可用序号：

```text
topics/company/rklb/2026-05-14-driver-map.md
topics/company/rklb/2026-05-14-driver-map-2.md
topics/company/rklb/2026-05-14-driver-map-3.md
```

如果用户没有指定 artifact，只输出 topic root 和“artifact name needed”，不要猜文件名。

### Index Touch

只更新 topic `index.md` 的轻量地图字段：

- current question
- dated result links
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
- 不删除、移动或重命名已有 research result 文件。
- 不写入 `topics/<topic>/_raw/`、`_cache/`、`_models/`。
- 不创建 root `screens/`、`peers/`、`quickreads/`、`cross-market/`。
- 不在 plugin dev repo 里创建 research workspace topic，除非用户明确说明这是 example workspace。
- 路径不明确时只输出建议路径，不执行写入。

## 运行输出契约

默认输出：

```markdown
## New Session Result

**结论先行**
已创建 / 已定位 topic root: [path]

## Topic
- topic root: [...]
- topic index: [...]
- topic mode: created / located

## Result Path
- requested artifact: [... or "not provided"]
- path: [... or "artifact name needed"]
- conflict handling: no conflict / suffixed to `-2`

## Cached Materials
- topic: [...]
- path: `topics/<topic-namespace>/<topic-slug>/_cache/`
- files found: [... or "none"]

## Index Touch
- index path: [...]
- added result link: yes / no
- updated current question: yes / no
- updated open questions: yes / no
```

阻塞时输出：

```markdown
## New Session Blocked

**结论先行**
还不能创建 / 更新 topic root，因为路径或 topic 信息不明确。
- missing: [...]
- suggested_path: [...]
- needed_input: [...]
```

不要输出 `Next Step` 或“建议继续用哪个 research skill”。

## 失败处理

- `topic_slug` 不清：只给候选 slug，不写文件。
- workspace path 不清：输出相对路径，不创建目录。
- topic 已存在：报告 located，不覆盖文件。
- result path 已存在：自动加 `-2`、`-3` 等最低可用序号，不覆盖文件。
- `index.md` 已存在但结构不同：只追加 dated result link，不重写整个 index。
- 用户要求写研究结论：拒绝在本 skill 内写，说明应交给 `research-journal`。

## Workflow 联动

| 场景 | 处理 |
|---|---|
| `init-workspace` 完成后用户要开始研究某个 topic | 用 `new-session` 创建 topic root |
| 研究 skill 要保存 artifact 但路径不明确 | 用 `new-session` resolve dated result path |
| `research-journal` 要写 journal / Boss Brief 但路径不明确 | 先用 `new-session` 确认 topic root 和 dated filename |
| 用户只想把本次结果加进 topic map | 用 `Index Touch`，不写 earned insight |
| 用户问下一步研究什么 | 不是本 skill，交给 `next-step` |

Artifact policy：

- `save_policy`: `topic_scaffold`
- `default_artifact`: `topic root + dated result file`
- `canonical_location`: `topics/[topic-namespace]/[topic-slug]/[YYYY-MM-DD]-[artifact].md`

Topic namespace convention：

- company: `topics/company/<company-slug>/`
- industry: `topics/industry/<industry-slug>/`
- theme: `topics/theme/<theme-slug>/`
- pair: `topics/pair/<pair-slug>/`

## 安全自查

- ❌ 写研究结论、thesis、driver 判断或 source-backed insight。
- ❌ 推荐下一步 research skill。
- ❌ 把 `index.md` 写成 checklist、transcript 或 v2 state file。
- ❌ 覆盖已有 `index.md` 或 dated result 文件。
- ❌ 路径不明确时擅自发明复杂目录树并写入。
- ❌ 预创建全套 research output markdown。
- ❌ 为每次研究创建子目录，导致 topic root 下面层级膨胀。
- ❌ 把 `_cache/` markdown 文件当作 topic artifact（cache 是研究辅助，不是 earned memory）。
- ❌ 创建 `coverage/`、`pairs/`、`portfolio/` 等 v2 state folders。
