# CONTEXT.md — Buy-Side Research Skills

Domain glossary and architecture decisions for the `buy-side-research-skills` plugin.

## Glossary

### Skill Layers

- **Research Skill** — produces a dated, source-tracked artifact. Read by human, routed by agent.
- **Operations Skill** — mutates workspace state. No artifact output. Examples: init-workspace, update-agent-runtime, ingest, financial-data.
- **Platform Skill** — `.platform` marker. Deployed as-is by init-workspace Class A. Not copied per-skill.

### Data Architecture

- **actuals-resolved.json** — lite mode output. Flat `{income_statement: {latest_fy: {...}, latest_quarter: {...}}, balance_sheet: {...}, cash_flow: {...}, market_data: {...}, segments: {...}, consensus: {...}}`. Each line item is `{value, source_layer, source_detail}`.
- **actuals_schema.json** — field template defining period keys, line item labels, required fields, and supplementary taxonomy. Read by fill_gaps.py at runtime.
- **evidence ledger** — ticker-scoped `_cache/evidence/<TICKER>.evidence.json`. Cross-artifact claim reuse. Schema v3.

### Period System

- **latest mode** — `latest_fy` + `latest_quarter`. Fast. Default.
- **3Y mode** — `fy_y2`, `fy_y1`, `fy_y0` + `sub_0` … `sub_3`. Enabled by `--periods 3Y` on financial-data lite. For appendix display.
- **Period basis** — `Q` (quarterly) or `H` (half-year). Stored in `latest_quarter_period_basis`.

### Source Verification

- **Fallback chain** — Tier 0 (actuals) → Tier 1 (WebFetch) → Tier 2 (Playwright) → Tier 3 (curl) → Tier 4 ([UNVERIFIED]).
- **Source anchor** — `[S#](url)` = company disclosure, `[I#](url)` = third-party. Verified sources carry no badge. Only `[UNVERIFIED]` is marked.
- **Two-track source hierarchy** — disclosure-fact (`topic-local evidence cache > primary public > trusted third-party > web`) and market-snapshot (`financial-data > trusted third-party > web`).

### Subagent Architecture

- **Default-parallel skills** — peer-deep-dive, candidate-screener, pair-trade, comps-analysis. Must produce evidence cards from subagents.
- **Evidence card** — structured JSON output from subagent. Schema at `references/policy/evidence-card-schema.json`. Contains: financial highlights, business profile, competitive position, growth outlook, valuation context, sentiment, scoring, claims needing verification.
- **Evidence card triplet** — `claim:`, `evidence:`, `source:` lines in artifact body. Required by subagent_protocol hook for DEFAULT_PARALLEL skills.

### Bilingual Architecture

- **Source of truth** — Chinese `SKILL.md`. English `SKILL.en.md` is translation.
- **Sync rule** — Chinese change → English must follow in same commit. Enforced by CLAUDE.md §9.
- **Non-translatable** — code, paths, YAML keys, tickers, financial abbreviations, CLI commands, `[需查证]`, `[UNVERIFIED]`, `[ND]`.
- **README** — English primary (`README.md`), Chinese secondary (`docs/README.cn.md`). Cross-linked.

### Workspace Structure

- **industry/** — top-level organization. `industry/<slug>/companies/<ticker>/` for company artifacts.
- **Single-industry primary residence** — earliest artifact date determines home industry. Cross-industry = reference in other index.md.
- **_cache/** — source-tracked materials. Never original source.

### Appendix System

- **actuals-to-appendix.py** — render actuals-resolved.json as sell-side appendix tables. Single: `python actuals-to-appendix.py <TICKER>`. Multi: `--tickers T1,T2,...`.
- **Output** — IS → BS → CF → Market Data → Segments → Consensus → Fill Rate. Empty rows skipped. Period columns dynamic.

---

## Architecture Decision Records

### ADR-001: Flat actuals structure

**Decision**: actuals-resolved.json uses flat `{income_statement: {latest_fy: {...}, latest_quarter: {...}}}` at top level, not nested under `statements:`.

**Why**: Evolved from fill_gaps.py post-processing. Legacy format had `statements:` wrapper; current format is direct. Backward compat via `_is_legacy_actuals()` detection.

**Trade-off**: Flatter structure is easier for appendix rendering and direct field access. But diverges from original financial_data.py full-mode output.

### ADR-002: --lite as skill instruction, not CLI flag

**Decision**: `/financial-data --lite <ticker>` is a skill-level abstraction. The Python script (`financial_data.py`) has no `--lite` argument. The skill instructs the agent to fetch data and write actuals-resolved.json.

**Why**: Lite mode involves agent judgment (provider selection, fallback, manual web verification). Not automatable as a pure script. The agent is the orchestrator.

### ADR-003: evidence-card-schema as shared reference

**Decision**: Evidence card JSON schema lives in `references/policy/evidence-card-schema.json`, shared by all default-parallel skills. Not duplicated per skill.

**Why**: Single source of truth for subagent output contract. Changes propagate automatically. Hook validation references the same schema.

### ADR-004: Bilingual .en.md alongside source

**Decision**: English translations live as `SKILL.en.md` in the same directory as Chinese `SKILL.md`. Not in a separate `-en/` plugin tree.

**Why**: Same `skill.yaml`, same `scripts/`, same hooks. Only markdown content diverges. Avoids directory duplication and sync drift.

### ADR-005: topics/ → industry/ migration (zero backward compat)

**Decision**: All `topics/` paths were migrated to `industry/`. No backward-compatible fallback code retained. ingest.py, hooks, and documentation all use `industry/` exclusively.

**Why**: Clean architecture. `topics/` was ambiguous (company/industry/theme/pair). `industry/` is precise. The migration was mechanical and complete as of v5.7.0.
