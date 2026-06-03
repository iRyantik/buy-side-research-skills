---
name: ingest
description: Convert raw research files into source-tracked topic cache markdown before analysis.
---

# Ingest

> This is the English translation of [SKILL.md](./SKILL.md). The Chinese version is the source of truth.

`ingest` converts local raw materials into LLM-friendly, source-tracked Markdown under a topic `_cache/`. It records source path, hash, modified time, converter, converted time, document type, route, and precision caveats. It is an operations skill, not a research skill.

## Mental Model

The invariant is traceability. `_cache/` is easier for an LLM to read, but the original file remains the source of truth.

Agent (per policy baseline §11) auto-creates the topic root. `ingest` creates `_raw/` and `_cache/` only when material is actually converted, so empty research topics stay light.

## Responsibilities

Responsible for:
- Convert TXT, Markdown, CSV, PDF, DOCX, PPTX, XLSX, XLSM, and supported workbook-style files.
- Write source-tracked Markdown to `industry/<industry>/companies/<ticker>/_cache/[source-filename].md`.
- Create `_raw/<category>/` and `_cache/` on first conversion.
- Move successfully converted source files from topic `_inbox/` to `_raw/<category>/`.
- Report converted / skipped / failed summary.
- Fail honestly on dependency or conversion gaps.

Not responsible for:
- Do not create topic roots or `index.md`; agent auto-creates per policy baseline §11.
- Do not move files already under `_raw/`.
- Do not write investment conclusions or earned insight.
- Do not treat `_cache/` as original source.
- Do not fetch structured financial data by ticker; use `financial-data`.
- Do not silently install dependencies.

## Trigger And Input

Trigger phrases:
- "ingest this"
- "convert this PDF to markdown"
- "process this _inbox file"

Pre-condition:
- `industry/<industry>/companies/<ticker>/index.md` must already exist.
- Topic `_inbox/` normally auto-created by agent per policy baseline §11.

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
- source under `industry/space-launch/_inbox/` resolves to `industry/space-launch`.
- source under `industry/optical-module-equipment/companies/robo-technik/_raw/filings/` resolves to `company/rklb`.
- root `_inbox/<topic>/` remains supported for unclassified staging.
- if no topic can be inferred, fail or require explicit `--topic`; do not silently create a new topic.

## Execution Modes

### Dependency Check

```bash
python _scripts/ingest.py --check-deps
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

## Tool Resources

Runtime scripts:
- `skills/ingest/scripts/ingest.py`
- `skills/ingest/scripts/ingest_xlsx.py`
- `skills/ingest/scripts/ingest_table_crosscheck.py`
- `skills/ingest/scripts/describe-figures.py`
- `skills/ingest/scripts/bootstrap-ingest-deps.sh`
- `skills/ingest/assets/requirements-ingest.txt`

Core routes include Docling, PyMuPDF4LLM, EdgarTools readiness checks, openpyxl, python-pptx, python-docx, PDFPlumber, pypdf, and Pillow.

Skill-local environment notes:

- SEC filing ingest still requires `EDGAR_IDENTITY`; keep using the ingest bootstrap or the shared env template before converting SEC filings.
- `describe-figures` may optionally use `VLM_API_URL`, `VLM_API_KEY`, and `VLM_MODEL`.
- `HF_ENDPOINT` remains optional and mainly helps mirror access, not core ingest correctness.

## File Safety

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

## Output Contract

```markdown
## Ingest Result

**Conclusion-First**
[converted / skipped / failed summary]

| Source | Cache | Status | Converter | Precision |
|---|---|---|---|---|
| [...] | [...] | [...] | [...] | [...] |

## Topic
- topic: [...]
- cache: `industry/<industry>/companies/<ticker>/_cache/`
- raw: `industry/<industry>/companies/<ticker>/_raw/<category>/`

## Route / Dependency
- document_type: [...]
- route: [...]
- precision_level: [...]
- dependency_status: [...]

## Caveats
- [...]
```

## Failure Handling

- Missing topic root: agent auto-creates per policy baseline §11.
- Source path missing: failed, no cache written.
- Workspace cannot be discovered: ask for `--workspace`.
- Dependency missing: report exact package and bootstrap command.
- Converter failure: failed, no fake Markdown.
- Topic cannot be inferred: require explicit `--topic`.

## Workflow Links

| Scenario | Handling |
|---|---|
| Workspace has no `industry/` | Use `init-workspace` |
| Topic root is missing | Agent auto-creates per policy baseline §11 |
| User has files in topic `_inbox/` | Use `ingest` |
| Cache is annual report / 10-K / 20-F | Feed `company-history` or `driver-map` |
| Cache is industry report / technical paper | Feed `industry-landscape` or `mechanism-insight` |
| Need structured financial statements by ticker | Use `financial-data` |
| Need company promotion from industry workbench | Use `promote-company` after research files exist |

Artifact policy:
- `save_policy`: `cache_artifact`
- `default_artifact`: `[source-filename].md`
- `canonical_location`: `industry/<industry>/companies/<ticker>/_cache/[source-filename].md`

## Safety Self-Check

- ❌ Created a topic root or `index.md`.
- ❌ Moved a source file before conversion succeeded.
- ❌ Moved files already under `_raw/`.
- ❌ Treated `_cache/` as original source.
- ❌ Wrote investment conclusions.
- ❌ Silently installed dependencies.
- ❌ Ran recursive ingest without explicit request.
