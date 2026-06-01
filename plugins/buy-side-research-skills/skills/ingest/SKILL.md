---
name: ingest
description: Convert raw research files into source-tracked topic cache markdown before analysis.
---

# Ingest

`ingest` converts local raw materials into LLM-friendly, source-tracked Markdown under a topic `_cache/`. It records source path, hash, modified time, converter, converted time, document type, route, and precision caveats. It is an operations skill, not a research skill.

## 心法

The invariant is traceability. `_cache/` is easier for an LLM to read, but the original file remains the source of truth.

`new-session` prepares the topic root and `_inbox/`. `ingest` creates `_raw/` and `_cache/` only when material is actually converted, so empty research topics stay light.

## 职责边界

负责：
- Convert TXT, Markdown, CSV, PDF, DOCX, PPTX, XLSX, XLSM, and supported workbook-style files.
- Write source-tracked Markdown to `topics/<namespace>/<topic-slug>/_cache/[source-filename].md`.
- Create `_raw/<category>/` and `_cache/` on first conversion.
- Move successfully converted source files from topic `_inbox/` to `_raw/<category>/`.
- Report converted / skipped / failed summary.
- Fail honestly on dependency or conversion gaps.

不负责：
- Do not create topic roots or `index.md`; use `new-session`.
- Do not move files already under `_raw/`.
- Do not write investment conclusions or earned insight.
- Do not treat `_cache/` as original source.
- Do not fetch structured financial data by ticker; use `financial-data`.
- Do not silently install dependencies.

## 触发与输入

Trigger phrases:
- "ingest this"
- "convert this PDF to markdown"
- "process this _inbox file"
- "把 PDF / Excel / PPT 转成 cache"

Pre-condition:
- `topics/<namespace>/<topic-slug>/index.md` must already exist.
- Topic `_inbox/` normally comes from `new-session`.

Inputs:

| Input | Purpose |
|---|---|
| `source_path` | file or directory to ingest |
| `workspace` | research workspace root |
| `topic` | namespaced topic such as `industry/space-launch` or `company/rklb` |
| `category` | `filings`, `transcripts`, `sellside`, `industry`, `irdecks`, `datasets`, or `unclassified` |
| `force` | overwrite stale cache when explicitly requested |
| `recursive` | recurse through a directory only when explicitly requested |

Topic inference:
- explicit `--topic industry/space-launch` wins.
- source under `topics/industry/space-launch/_inbox/` resolves to `industry/space-launch`.
- source under `topics/company/rklb/_raw/filings/` resolves to `company/rklb`.
- root `_inbox/<topic>/` remains supported for unclassified staging.
- if no topic can be inferred, fail or require explicit `--topic`; do not silently create a new topic.

## 执行模式

### Dependency Check

```powershell
python _scripts/ingest.py --check-deps
_scripts/bootstrap-ingest-deps.ps1 -CheckOnly
```

Only install dependencies after explicit user confirmation.

### Single File Ingest

1. Verify workspace and topic root exist.
2. Detect document format and category.
3. Convert to Markdown using the best available route.
4. Create `_cache/` and `_raw/<category>/` as needed.
5. Write cache Markdown.
6. If the source was inside topic `_inbox/`, move it to `_raw/<category>/`.

### Directory Ingest

Process supported files in the directory. A single file failure should not block other files, but the final result must list failures.

### Cache Reuse

If cache exists and source hash matches, skip unless `--force` is set. If cache exists but source differs, use a collision-safe filename rather than overwriting by default.

## 工具资源

Runtime scripts:
- 如果你只是在找“整体有哪些环境要先知道”，先看 `init-workspace` 的统一环境入口与 `_scripts/init-assets/env-setup.ps1.template`。本节只保留 `ingest` 自己的 converter、bootstrap 和 SEC filing / optional VLM 边界。
- `skills/ingest/scripts/ingest.py`
- `skills/ingest/scripts/ingest_xlsx.py`
- `skills/ingest/scripts/ingest_table_crosscheck.py`
- `skills/ingest/scripts/describe-figures.py`
- `skills/ingest/scripts/bootstrap-ingest-deps.ps1`
- `skills/ingest/scripts/bootstrap-ingest-deps.sh`
- `skills/ingest/assets/requirements-ingest.txt`

Core routes include Docling, PyMuPDF4LLM, EdgarTools readiness checks, openpyxl, python-pptx, python-docx, PDFPlumber, pypdf, and Pillow.

Skill-local environment notes:

- SEC filing ingest still requires `EDGAR_IDENTITY`; keep using the ingest bootstrap or the shared env template before converting SEC filings.
- `describe-figures` may optionally use `VLM_API_URL`, `VLM_API_KEY`, and `VLM_MODEL`.
- `HF_ENDPOINT` remains optional and mainly helps mirror access, not core ingest correctness.

## 文件安全

- Never delete source files.
- Never move files already under `_raw/`.
- Move only files from `_inbox/` after successful conversion.
- Never write empty or fake cache.
- Never write research Markdown artifacts into topic root.
- Default is non-recursive.
- Missing parser dependencies must be reported, not hidden.

Cache header must include:
- `source_path`
- `source_sha256`
- `source_modified_utc`
- `converter`
- `converted_at_utc`
- `precision`
- `precision_level`
- `document_type`
- `route`

## 运行输出契约

```markdown
## Ingest Result

**结论先行**
[converted / skipped / failed summary]

| Source | Cache | Status | Converter | Precision |
|---|---|---|---|---|
| [...] | [...] | [...] | [...] | [...] |

## Topic
- topic: [...]
- cache: `topics/<namespace>/<topic-slug>/_cache/`
- raw: `topics/<namespace>/<topic-slug>/_raw/<category>/`

## Route / Dependency
- document_type: [...]
- route: [...]
- precision_level: [...]
- dependency_status: [...]

## Caveats
- [...]
```

## 失败处理

- Missing topic root: block and ask user to run `new-session`.
- Source path missing: failed, no cache written.
- Workspace cannot be discovered: ask for `--workspace`.
- Dependency missing: report exact package and bootstrap command.
- Converter failure: failed, no fake Markdown.
- Topic cannot be inferred: require explicit `--topic`.

## Workflow 联动

| Scenario | Handling |
|---|---|
| Workspace has no `topics/` | Use `init-workspace` |
| Topic root is missing | Use `new-session` |
| User has files in topic `_inbox/` | Use `ingest` |
| Cache is annual report / 10-K / 20-F | Feed `company-history` or `driver-map` |
| Cache is industry report / technical paper | Feed `industry-quickread` or `mechanism-map` |
| Need structured financial statements by ticker | Use `financial-data` |
| Need company promotion from industry workbench | Use `promote-company` after research files exist |

Artifact policy:
- `save_policy`: `cache_artifact`
- `default_artifact`: `[source-filename].md`
- `canonical_location`: `industry/<industry>/companies/<ticker>/_cache/[source-filename].md`

## 安全自查

- ❌ Created a topic root or `index.md`.
- ❌ Moved a source file before conversion succeeded.
- ❌ Moved files already under `_raw/`.
- ❌ Treated `_cache/` as original source.
- ❌ Wrote investment conclusions.
- ❌ Silently installed dependencies.
- ❌ Ran recursive ingest without explicit request.
