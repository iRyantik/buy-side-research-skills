---
name: promote-company
description: Use when promoting company-specific research from an industry or theme workbench topic into the canonical company topic.
---

# Promote Company

`promote-company` 用来把 industry / theme workbench topic 里已经能明确归属到单一公司的研究文件，沉淀到 canonical company topic：`topics/company/<company-slug>/`。它负责移动文件、保留 provenance、更新双向索引；混合行业 / peer 研究默认留在来源 topic，并从 company index 加 backlink。

## 心法

Industry 和 theme topic 很适合作为 workbench：你可以先横向筛很多公司，而不用为每个候选都创建空 company topic。等某家公司变成值得长期跟踪的对象，就应该进入 canonical company topic，让后续 `financial-data`、`driver-map`、建模和 journal 都有稳定归属。

Promotion 不是研究综合，也不是重新写结论。它是文件系统和 provenance 操作：只移动确定属于单公司的文件，保留来源路径和历史线索，让以后能快速找到“这份公司研究从哪里来、为什么被沉淀”。

## 职责边界

负责：

- 创建或定位 `topics/company/<company-slug>/index.md` 和 `_inbox/`。
- 将来源 topic 根目录下带公司前缀的 research Markdown 移动到 company topic。
- 对移动后的 Markdown 去掉公司前缀。
- 在文件名、alias 或 cache provenance 能明确识别公司时，移动 `_inbox`、`_raw`、`_cache` 中的相关文件。
- 遇到目标文件名冲突时保留历史，用 `-2`、`-3` 等后缀避让。
- 更新来源 topic 和 company topic 的 `index.md`，记录 provenance、已移动文件和 backlink。

不负责：

- 不总结、改写或重判投资结论。
- 不默认移动行业级、主题级或 peer-level artifact。
- 不在 attribution 模糊时擅自移动文件。
- 不拉取财务数据、不建模、不生成 research artifact。
- 不替代 `integrate`；whole-topic directory merge 仍由 `integrate` 处理。

## 触发与输入

触发短语包括：

- "promote RKLB to company"
- "把 RKLB 沉淀到 company topic"
- "把行业 topic 里的 RKLB 研究转到 company"
- "company promotion"
- "promote-company"

输入：

| Input | 作用 |
|---|---|
| `source_topic` | namespaced workbench topic，例如 `industry/space-launch` |
| `company_slug` | canonical company slug，例如 `rklb` |
| `company_display_name` | 可选的人类可读公司名 |
| `aliases` | 可选 alias，用于识别 inbox / raw / cache 文件 |
| `workspace_path` | research workspace root |
| `apply` | 使用 helper script 时执行移动；不带 `apply` 时先 dry run |

## 执行模式

### Promote Company

创建或定位：

```text
topics/company/<company-slug>/
  index.md
  _inbox/
```

移动来源 topic 根目录中匹配以下模式的 Markdown：

```text
topics/industry/space-launch/2026-05-18-rklb-stock-quickread.md
-> topics/company/rklb/2026-05-18-stock-quickread.md
```

同类文件也应移动，例如：

- `2026-05-18-rklb-driver-map.md`
- `2026-05-18-rklb-company-primer.md`
- `2026-05-18-rklb-alpha-thesis.md`
- 其他 `YYYY-MM-DD-<company-slug>-*.md`

只在 attribution 清楚时移动 `_inbox`、`_raw`、`_cache` 文件：

- 文件名包含 `company_slug` 或 alias。
- cache header 的 `source_path` 指向本次已移动的 source file。
- 用户明确点名该文件属于这家公司。

不要凭语义猜测移动文件。

### Backlink Only

混合行业 / peer 文件保留在来源 topic，但在 company index 加 backlink：

```text
2026-05-18-peer-deep-dive.md
2026-05-18-industry-quickread.md
2026-05-18-candidate-screener.md
```

### Dry Run

使用 helper script 时，先检查 move plan。只有 move plan 和用户意图一致时才执行 `--apply`。

## 工具资源

可选 helper：

```powershell
python skills/promote-company/scripts/promote_company.py --workspace <workspace> --source-topic industry/space-launch --company-slug rklb --alias RKLB --alias "Rocket Lab"
python skills/promote-company/scripts/promote_company.py --workspace <workspace> --source-topic industry/space-launch --company-slug rklb --apply
```

如果 helper 不可用，也可以用谨慎的文件系统操作执行，但必须先列出 move plan，并确保不会覆盖文件。

## 文件安全

- 不覆盖已有文件。
- 不默认移动 industry-level 或 peer-level Markdown。
- 不删除 source topic。
- 不改写 research conclusions。
- 通过移动路径和 index provenance 保留原始历史。
- attribution 模糊时，文件留在 source topic，只在 company index 加 backlink。

## 运行输出契约

默认输出短而可执行：

```markdown
## Promote Company 结果

**结论先行**
已将 [company] 从 [source topic] 沉淀到 `topics/company/[company-slug]/`。

## 已移动
| From | To | Reason |
|---|---|---|
| [...] | [...] | company-prefixed markdown |

## 保留在来源 Topic 并加 Backlink
| File | Reason |
|---|---|
| [...] | mixed peer / industry artifact |

## Index 更新
- source topic index: [...]
- company topic index: [...]

## Caveats
- [...]
```

## 失败处理

- Source topic missing：停止，要求用户确认 `source_topic`。
- Company slug missing：停止，不要 silent infer。
- Destination conflict：使用 `-2`、`-3` 等后缀避让。
- No matched files：只有用户明确要求创建 company topic 时，才创建 / 定位 company topic；否则报告没有 promotion candidates。
- Ambiguous raw/cache attribution：留在 source topic，并从 company index backlink。

## Workflow 联动

| 场景 | 处理 |
|---|---|
| Industry research 产出了 company-prefixed Markdown | 使用 `promote-company` |
| 公司需要 `financial-data` 或 model work | 先 promote，再使用 canonical company topic |
| 两个 topic 需要关联但内容不应合并 | 使用 index backlink 或 `promote-company` 的 backlink-only 行为 |
| 整个 child topic 应移动到 parent topic 下 | 使用 `integrate` |
| 新 company topic 只需要 root 和 inbox | `promote-company` 创建 `index.md` 和 `_inbox/` |

Artifact policy:

- `save_policy`: `none`
- `default_artifact`: `conversation-only`
- `canonical_location`: `conversation-only`

## 安全自查

- 不要自动移动 `peer-deep-dive.md` 或 `industry-quickread.md`。
- 不要 copy 确定属于公司的前缀文件；应 move，并在 index 记录 provenance。
- 不要覆盖 company topic 里的已有文件。
- 不要移除 source topic provenance。
- 不要重写研究结论。
- 不要用 `promote-company` 做 whole-topic directory merge；那是 `integrate` 的职责。
