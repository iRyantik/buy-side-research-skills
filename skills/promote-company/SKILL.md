---
name: promote-company
description: Use when promoting company-specific research from an industry or theme workbench topic into the canonical company topic.
---

# Promote Company

`promote-company` moves clearly company-scoped research from a workbench topic, usually `industry` or `theme`, into the canonical `topics/company/<company-slug>/` topic. It preserves provenance in both indexes and leaves mixed industry / peer work in the source topic with backlinks.

## 心法

Industry and theme topics are good workbenches: they let you screen many companies without creating empty company folders. Once a company matters, it should have a canonical company topic so future `financial-data`, `driver-map`, and modeling work have one stable home.

Promotion is not research synthesis. It is a filesystem and provenance operation: move deterministic company-scoped files, preserve history, and make later discovery easy.

## 职责边界

负责：
- Create or locate `topics/company/<company-slug>/index.md` and `_inbox/`.
- Move company-prefixed research Markdown from source topic root into the company topic.
- Move clearly attributable `_inbox`, `_raw`, and `_cache` files when filename, alias, or cache provenance identifies the company.
- Rename promoted Markdown by removing the company prefix.
- Preserve collisions with `-2`, `-3`, etc.
- Update source and company `index.md` with provenance, moved files, and backlinks.

不负责：
- Do not summarize or rewrite investment conclusions.
- Do not move industry-level or peer-level artifacts by default.
- Do not promote ambiguous files without explicit user direction.
- Do not build models or pull financial data.
- Do not replace `integrate`; whole-topic directory merge remains `integrate`.

## 触发与输入

Trigger phrases:
- "promote RKLB to company"
- "沉淀 RKLB 到 company 目录"
- "把行业 topic 里的 RKLB 研究转到 company"
- "company promotion"
- "promote-company"

Inputs:

| Input | Purpose |
|---|---|
| `source_topic` | namespaced workbench topic, e.g. `industry/space-launch` |
| `company_slug` | canonical company slug, e.g. `rklb` |
| `company_display_name` | optional readable name |
| `aliases` | optional aliases used to detect inbox/raw/cache files |
| `workspace_path` | research workspace root |
| `apply` | apply move plan; otherwise run dry-run first when using helper script |

## 执行模式

### Promote Company

Create or locate:

```text
topics/company/<company-slug>/
  index.md
  _inbox/
```

Move root Markdown matching:

```text
topics/industry/space-launch/2026-05-18-rklb-stock-quickread.md
-> topics/company/rklb/2026-05-18-stock-quickread.md
```

Also move:
- `2026-05-18-rklb-driver-map.md`
- `2026-05-18-rklb-company-primer.md`
- `2026-05-18-rklb-alpha-thesis.md`
- other `YYYY-MM-DD-<company-slug>-*.md`

Move `_inbox`, `_raw`, and `_cache` files only when attribution is clear:
- filename contains `company_slug` or an alias
- cache header `source_path` points to a source file moved during the promotion
- user explicitly named the file

Do not move by vague semantic guess.

### Backlink Only

Leave mixed files in source topic, but add backlinks from the company index:

```text
2026-05-18-peer-deep-dive.md
2026-05-18-industry-quickread.md
2026-05-18-candidate-screener.md
```

### Dry Run

When using the helper script, first inspect the move plan. Apply only when the plan matches the user request.

## 工具资源

Optional helper:

```powershell
python skills/promote-company/scripts/promote_company.py --workspace <workspace> --source-topic industry/space-launch --company-slug rklb --alias RKLB --alias "Rocket Lab"
python skills/promote-company/scripts/promote_company.py --workspace <workspace> --source-topic industry/space-launch --company-slug rklb --apply
```

The skill can also be executed with careful filesystem operations if the helper is unavailable.

## 文件安全

- Never overwrite existing files.
- Never move industry-level or peer-level Markdown by default.
- Never delete source topic.
- Never rewrite research conclusions.
- Preserve original file history through moved paths and index provenance.
- If attribution is ambiguous, leave the file in source topic and add a backlink.

## 运行输出契约

```markdown
## Promote Company Result

**结论先行**
已将 [company] 从 [source topic] 沉淀到 `topics/company/[company-slug]/`。

## Moved
| From | To | Reason |
|---|---|---|
| [...] | [...] | company-prefixed markdown |

## Left In Source With Backlinks
| File | Reason |
|---|---|
| [...] | mixed peer / industry artifact |

## Index Updated
- source topic index: [...]
- company topic index: [...]

## Caveats
- [...]
```

## 失败处理

- Source topic missing: block and ask user to confirm `source_topic`.
- Company slug missing: block; do not infer silently.
- Destination conflict: use suffix `-2`, `-3`, etc.
- No matched files: create/locate company topic only if user explicitly requested; otherwise report no promotion candidates.
- Ambiguous raw/cache attribution: leave in source and backlink.

## Workflow 联动

| Scenario | Handling |
|---|---|
| Industry research produced company-prefixed Markdown | `promote-company` |
| Company needs `financial-data` or model work | promote first, then use company canonical topic |
| Two topics should be related but contents stay separate | use index backlink or `promote-company` backlink-only behavior |
| Whole child topic should move under parent topic | use `integrate` |
| New company topic needs only root and inbox | `promote-company` creates `index.md` and `_inbox/` |

Artifact policy:
- `save_policy`: `none`
- `default_artifact`: `conversation-only`
- `canonical_location`: `conversation-only`

## 安全自查

- ❌ Moved `peer-deep-dive.md` or `industry-quickread.md` automatically.
- ❌ Copied instead of moved deterministic company-prefixed files.
- ❌ Overwrote company topic files.
- ❌ Removed source topic provenance.
- ❌ Rewrote research conclusions.
- ❌ Used `promote-company` for whole-topic directory merge; use `integrate`.
