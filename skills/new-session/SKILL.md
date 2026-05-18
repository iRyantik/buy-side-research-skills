---
name: new-session
description: Use when creating or locating a topic root, preparing its inbox, resolving a dated research result filename, or lightly updating a topic index.
---

# New Session

`new-session` solves one narrow operations problem: where should this research live? It creates or locates a long-lived topic root, ensures the topic has an `index.md` and `_inbox/`, and resolves a dated Markdown result path. It does not run research, ingest files, build models, or create cache/raw/model folders.

## 心法

Topic is the long-lived container. Research outputs are dated files in that topic root.

Use an industry or theme topic as the early workbench when screening many companies. If a single company later deserves canonical tracking, use `promote-company` to move the company-scoped research into `topics/company/<company-slug>/`.

`index.md` is a lightweight topic map: current question, dated result links, related topics, open questions, and provenance. It is not a journal, checklist, transcript, or earned insight store.

## 职责边界

负责：
- Create or locate `topics/<topic-namespace>/<topic-slug>/`.
- Ensure `index.md` exists without overwriting existing content.
- Ensure `_inbox/` exists so users can drop raw material into the topic.
- Resolve one requested dated result path.
- Support namespaces: `company`, `industry`, `theme`, `pair`.
- Support company-scoped files inside industry/theme workbench topics.
- Lightly update topic index links when explicitly requested.

不负责：
- Do not create `_raw/`, `_cache/`, or `_models/`; `ingest`, `financial-data`, `driver-map`, and modeling skills create those on demand.
- Do not precreate research output Markdown files.
- Do not create dated session folders.
- Do not write research conclusions, thesis, driver judgments, or earned insight.
- Do not recommend next research steps; use `next-step`.
- Do not move company research out of an industry topic; use `promote-company`.

## 触发与输入

Trigger phrases:
- "new session"
- "create topic"
- "open topic"
- "resolve save path"
- "where should this artifact be saved"
- "update topic index"

Inputs:

| Input | Purpose | Default |
|---|---|---|
| `topic_namespace` | `company`, `industry`, `theme`, or `pair` | infer from user wording |
| `topic_slug` | directory slug | kebab-case from topic name |
| `date` | result date | current date as `YYYY-MM-DD` |
| `artifact_name` | artifact to save | required for path resolution |
| `company_slug` | company prefix when saving single-company research inside industry/theme | optional |
| `workspace_path` | research workspace root | if unclear, output relative path only |

## 执行模式

### New Topic Root

Create or locate:

```text
topics/<topic-namespace>/<topic-slug>/
  index.md
  _inbox/
```

Do not create:

```text
_raw/
_cache/
_models/
```

### Resolve Dated Result Path

Company canonical topic:

```text
topics/company/rklb/2026-05-18-stock-quickread.md
topics/company/rklb/2026-05-18-driver-map.md
```

Industry/theme topic research about the industry/theme itself:

```text
topics/industry/space-launch/2026-05-18-industry-quickread.md
topics/industry/space-launch/2026-05-18-peer-deep-dive.md
```

Industry/theme workbench research about one company:

```text
YYYY-MM-DD-<company-slug>-<artifact>.md
topics/industry/space-launch/2026-05-18-rklb-stock-quickread.md
topics/industry/space-launch/2026-05-18-rklb-driver-map.md
```

If a file already exists, preserve history with the lowest available suffix:

```text
2026-05-18-rklb-driver-map.md
2026-05-18-rklb-driver-map-2.md
2026-05-18-rklb-driver-map-3.md
```

### Index Touch

Only append or lightly update:
- current question
- dated result links
- open questions
- related topics
- promoted-company provenance links

Do not rewrite the whole index unless the user explicitly asks.

## 工具资源

No required script. Use filesystem operations and text edits carefully. Reference:
- workspace `CLAUDE.md`
- `skills/init-workspace/assets/CLAUDE.md.template`
- `promote-company` for moving company-scoped research into company canonical topics
- `ingest` for creating `_raw/` and `_cache/` on first material conversion

## 文件安全

- Never overwrite an existing `index.md`.
- Never overwrite an existing dated result file.
- Never create `_raw/`, `_cache/`, or `_models/` in `new-session`.
- Never move or delete research files.
- If workspace path is unclear, output a suggested relative path and do not write.
- Do not create research workspace topics inside the plugin source repo unless the user explicitly says it is an example workspace.

## 运行输出契约

```markdown
## New Session Result

**结论先行**
已创建 / 已定位 topic root: [...]

## Topic
- namespace: [...]
- slug: [...]
- root: [...]
- index: [...]
- inbox: [...]
- mode: created / located

## Result Path
- requested artifact: [...]
- company prefix: [... or none]
- path: [... or artifact name needed]
- conflict handling: no conflict / suffixed to `-2`

## Index Touch
- index path: [...]
- added result link: yes / no
- updated current question: yes / no
```

Blocked output:

```markdown
## New Session Blocked

**结论先行**
还不能创建 / 定位 topic root。

- missing: [...]
- suggested_path: [...]
- needed_input: [...]
```

## 失败处理

- Missing `topic_slug`: propose candidate slug, do not write.
- Missing workspace path: output relative path only.
- Existing topic: report located; do not recreate existing files.
- Existing result path: suffix with `-2`, `-3`, etc.
- Existing `index.md` with unusual structure: append a small section; do not rewrite.
- User asks for research conclusions: refuse within this skill and route to the appropriate research skill.

## Workflow 联动

| Scenario | Handling |
|---|---|
| Workspace is initialized and user wants a new topic | Use `new-session` |
| Research skill needs a save path | Use `new-session` to resolve dated filename |
| User drops files into a topic | `new-session` provides `_inbox/`; `ingest` creates `_raw/` and `_cache/` on conversion |
| Industry workbench produces company-specific files | Save as `YYYY-MM-DD-<company-slug>-<artifact>.md` |
| Company becomes canonical | Use `promote-company` |
| User wants to merge whole topic directories | Use `integrate` |

Artifact policy:
- `save_policy`: `topic_scaffold`
- `default_artifact`: `topic root + inbox + dated result file`
- `canonical_location`: `topics/[topic-namespace]/[topic-slug]/[YYYY-MM-DD]-[artifact].md`

## 安全自查

- ❌ Created `_raw/`, `_cache/`, or `_models/`.
- ❌ Created a dated session directory.
- ❌ Precreated a full set of research output Markdown files.
- ❌ Wrote investment conclusions or earned insight.
- ❌ Recommended next research skill.
- ❌ Overwrote `index.md` or a dated result file.
- ❌ Moved company files from industry/theme workbench; use `promote-company`.
