---
name: meta-skill
description: Create review or update buy-side research skills metadata docs manifests and governance.
---

# Meta Skill

> This is the English translation of [SKILL.md](./SKILL.md). The Chinese version is the source of truth.

Agent and plugin runtime upgrades belong to `update-agent-runtime`; `init-workspace` remains responsible for workspace scaffold and repair only.

`meta-skill` is the sole active skill-authoring guide for this plugin. It maintains the `research / operations` dual track: research skills retain strict buy-side research structure, operations skills use a lighter execution structure.

When writing or modifying any active skill, treat the root `CLAUDE.md` as the project constitution and this skill as the authoring guide.

## Philosophy

The core of this skill is not "fill out the template" but preventing gradual system drift: research skills degenerating into sell-side boilerplate, operations skills being forced into research-report structures, and metadata, body text, docs, and manifests falling out of sync.

Before designing any skill, ask: what decision moment does it actually serve? If it changes a research judgment, it is `research`; if it handles workspace, files, cache, sessions, paths, toolchains, or skill authoring, it is `operations`. Getting the category wrong cascades errors into structure, source discipline, save policy, and docs / manifests downstream.

A good skill reduces the researcher's cognitive burden rather than adding an AI self-gratifying ritual. The user is an Asia-timezone buy-side LS researcher whose pain points are information overload, fragmented per-company time, and susceptibility to noise. Every new skill must articulate how it makes research faster, more accurate, and more retainable.

## Scope of Responsibility

This skill is responsible for:

- Designing, rewriting, and reviewing active skill `SKILL.md` and `skill.yaml`.
- Determining `category: research|operations`.
- Assigning `research_layer` for research skills: `triage`, `foundation`, `deep-work`, `memory`, `supporting`.
- Maintaining consistency across artifact policy, version policy, public docs, and manifests.
- Maintaining research skill writing discipline within active runtime skills.
- Maintaining the authority hierarchy, hard gate, and UTF-8 text discipline.

This skill is NOT responsible for:

- Writing company research, theses, driver-maps, mechanism-insights, Boss Briefs, or topic artifacts.
- Creating dated topic research artifacts.
- Restoring the `meta.json` dual track.
- Restoring v2 state files, portfolio tracker, decision-journal, thesis-tracker, or v2 pair state logs.
- Physically moving active skills into nested category directories; plugin runtime skills remain flat under `plugins/buy-side-research-skills/skills/[skill-name]/SKILL.md` at the payload root.

## Triggers and Inputs

Trigger phrases include:

- "write a new skill"
- "modify this skill"
- "rewrite meta-skill"
- "how should skill categories work"
- "adjust governance"
- "add artifact policy"
- "distribute this rule across skills"
- "review current skill governance"

Confirm inputs before executing:

- The name of the skill to create or modify.
- Whether the skill is `research` or `operations`.
- If research, which layer: `triage`, `foundation`, `deep-work`, or `memory`.
- Whether new scripts, assets, or references are needed; do not create empty directories if there is no actual runtime need.
- Whether public docs, manifest keywords, or release package shape will be affected.
- Whether README, docs, payload manifests, or root marketplace metadata need syncing.

If the user's requirements are unclear, clarify before writing. Do not invent a skill from imagination.

## Execution Modes

### Mode A: New Skill Design

For adding a new active skill. Must first articulate:

- What "decision moment" or operational job this skill serves.
- `category` and `research_layer`.
- `artifact_policy`.
- Runtime boundary: what it does and does not do.
- Upstream / downstream skills.
- Which docs / manifests need to be added or updated.

### Mode B: Existing Skill Rewrite

For rewriting or substantially modifying an existing skill. Must preserve the user's existing changes and avoid unrelated refactoring; only modify body text, metadata, docs, and manifests relevant to the current objective. If the old skill already has a clear philosophy, source policy, anti-patterns, and save policy, inherit rather than rewriting in a different style.

### Mode C: Governance Update

For adjusting categories, version policy, artifact policy, global rules, docs, or manifests. Must sync public docs, payload manifests, and root marketplace metadata to avoid "rules written but install entry points not updated."

Modeling skills (`3-statement-model`, `dcf-model`, `comps-analysis`, `model-update`) use `Model Sub-Agent Protocol`. Do not add them to `Parallel Evidence Pass`, and do not give them `evidence_cards_only`.

### Mode D: Review / Gap Audit

For checking whether existing skills have drifted. Output should focus on issues and gaps; do not rewrite directly unless the user explicitly requests implementation.

## Authority Hierarchy

When rules conflict, resolve in the following order:

1. Plugin dev repo root `CLAUDE.md`
   - Plugin development constitution
2. `init-workspace/assets/CLAUDE.md.template`
   - Workspace high-level constitution template
3. Invoked `SKILL.md`
   - Runtime executable contract
4. workspace `.references/policy/research-policy-baseline.md`
   - Authoring baseline only, not runtime authority

At runtime, if the template's high-level summary appears inconsistent with a specific research skill's detailed execution rules:

- **Research `SKILL.md` wins**

## Capsule Policy

### Research skills

Active research skills now allow only an extremely short capsule; long-form shared runtime / source prose is no longer duplicated locally.

Research capsule retains only:
- One hooks-first reminder line
- One shared runtime/source baseline pointer line
- 2-4 skill-specific judgment / workflow / routing delta lines that are not machine-checkable

Already-hookified source legality, anchor / `## Resources` contract, subagent binary boundary, section floor, and table render integrity must not be written back into individual research `SKILL.md`.

### Modeling skills

`3-statement-model`, `dcf-model`, `comps-analysis`, `model-update` use a separate modeling capsule and do not consume the research capsule.

### Supporting visualization skills

Supporting visualization skills like `research-viz` remain on the research track but do not enter the main research ladder. They can generate a topic-side HTML artifact, must bind to a baseline markdown research artifact, and default to reusing the baseline stem with only the extension changed to `.html`; if multiple visuals are needed, a minimal qualifier may be appended after the stem.

### Operations skills

Operations skills do not embed the research capsule.

## Hooks-First Runtime Law

Cross-host deterministic runtime law should be placed into workspace hooks first, rather than piled into skill prose. The formal loading surface is:

- workspace `.claude/settings.json`
- workspace `.claude/hooks/`
- workspace `.codex/hooks.json`

Hook configurations and scripts in the plugin dev repo are delivered to workspaces via `init-workspace`; plugin-local docs are not the host's automatic hook discovery surface.

Hooks are responsible only for binary / machine-checkable guardrails, such as source legality, subagent boundary, workspace path safety, and obvious narrative drift. Rules that are judgment-dense, depend on research taste, or require subjective adjudication remain in `SKILL.md`, `skill.yaml`, and authoring governance.

`information-impact` claim qualification and `primary-research-plan` compliance floor also belong to hook-first binary rules.
`reddit-sentiment` social clue-only boundary also belongs to hook-first binary rules.
`peer-deep-dive` cross-market parity (listing status / currency / as-of) is enforced by the skill's own §4.1 column definition (5 cross-market columns mandatory when ≥2 markets), no separate hook.
When modeling workbook artifacts are in scope, statement presence, balance integrity, formula discipline, missing-actuals floor, valuation-basis floor, actuals_cross_check, driver_cross_check, internal_consistency, dcf_linked_to_3sm, dcf_input_sourcing, comps_sourced, and meta_sheet for `3-statement-model`, `dcf-model`, `comps-analysis`, and `model-update` also belong to xlsx-aware hook-first binary rules.
`research-journal` earned-insight gate and topic index map-only boundary also belong to hook-first binary rules.
`research-viz` stem-binding, self-contained delivery, and source-line contract also belong to hook-first binary rules.
The quantitative fact governance layer (`fact_provenance`: Tier 0-3 verification, `claim_source_proximity`: strong claims must have source anchors) also belongs to hook-first binary rules.

If a hook conflicts with prose on binary legality, hook enforcement prevails. `research-policy-baseline.md` remains an authoring baseline only, not runtime authority.

## Hard Gate

Any public research rule change must synchronize within the same change:

1. workspace `.references/policy/research-policy-baseline.md`
2. All affected active research `SKILL.md`
3. If workspace high-level summary is affected, also update `CLAUDE.md.template`
4. If public behavior / package language is affected, also update `README.md`, `docs/release.md`, payload manifests / marketplace manifests

Merging or releasing with only baseline / template changes and no skill changes is not allowed.

Hooks-first supplementary hard gate:

5. New deterministic runtime rules, if scriptable, go into workspace hooks first, not piled into `SKILL.md` prose.
6. Once a rule is hookified, the corresponding binary rule prose in `SKILL.md` must be deleted in the same change.
7. Hook shared scripts and host adapters must be maintained in sync; changing only Claude-side or only Codex-side configuration is not allowed.
8. The formal delivery surface for hooks is the `init-workspace` scaffold; treating plugin dev repo local files as the host auto-load surface is not allowed.
9. After adding skill-specific hooks, retaining old prose in review is treated as governance failure.
10. When adding new runtime hooks / repair scripts / install commands, hardcoding `powershell ... .ps1` is prohibited; must use the cross-platform launcher, or explicitly provide both Windows `powershell` and macOS `pwsh` commands.

Naming rule supplementary hard gate:

9. If research topic artifact naming rules change, must sync workspace `.references/policy/research-policy-baseline.md` §11.
10. Every research skill that produces a topic markdown must declare `naming_mode` under `artifact_policy` in `skill.yaml`.
11. Changing only a skill's prose / examples without changing `skill.yaml` is not allowed.
12. Supporting visualization skills that generate topic-side HTML artifacts must write the stem-binding save contract into both `skill.yaml` and `SKILL.md`; do not create a parallel dated naming system.

## UTF-8 Text Discipline

Chinese or multilingual text assets uniformly use **UTF-8 without BOM**.

- `.md` / `.yaml` / `.json` are maintained as UTF-8 without BOM by default.
- When modifying Chinese files, must explicitly write back as UTF-8.
- Batch scripts rewriting text must specify UTF-8 to avoid mojibake.
- Do not perform whole-file reformatting or bulk formatting on `SKILL.md`; make only the minimum edits required for the current fields, preserving frontmatter, top-level `# H1`, blank-line structure, and parser-sensitive ordering.
- JSON: key-value-level minimal edits only, do not reorder the entire object; YAML: preserve existing indentation and quoting style, do not perform full rewrites for cosmetic purposes.

## Tool Resources

This skill has no standalone script dependencies. When modifying this repo, prioritize reading:

- `CLAUDE.md`
- `README.md`
- `docs/`
- root `.claude-plugin/marketplace.json`
- 2-3 adjacent reference skill `SKILL.md` and `skill.yaml`

Required reference skills:

| Skill | What to learn |
|---|---|
| `information-impact` | Strong discipline, 500-character hard cap, dual mode, source judgment |
| `candidate-screener` | AI limitation acknowledgment, anti-fabrication, tier grouping, funnel closure |
| `industry-landscape` | Industry first-pass, value pool, KPI/source map, routing boundary |
| `consensus-map` | Sell-side consensus, buy-side bar, priced-in assumptions, variant-view gap |
| `primary-research-plan` | Compliant primary research, expert call, channel check, survey, decision gates |
| `stock-quickread` | Data-first, reverse engineering, forced structure |
| `peer-deep-dive` | Industry lens, cross-cut insight, ranking and resource allocation |
| `pair-trade` | LS / hedge / spread methodology, hard standards, risk / sizing |

If only writing or reviewing skills, no external network is needed. Only consult official Claude / Codex plugin documentation when the user explicitly requests verification against official structures.

## File Safety

- Do not create `meta.json`.
- Do not move active skill directories; keep `plugins/buy-side-research-skills/skills/[skill-name]/SKILL.md`.
- Do not modify `AGENTS.md`, `.claude/`, `RTK.md`, or local planning files unless the user explicitly names them.
- Do not create empty `scripts/`, `assets/`, `references/` directories.
- Do not treat examples as runtime dependencies.
- Do not restore root `screens/`, `peers/`, `quickreads/`, `cross-market/` as default active artifact paths.

## Skill Directory Spec

The following subdirectories are permitted under each skill directory. This is the closed list — new skills may only create directories listed here, and `init-workspace` and `update-agent-runtime` auto-discovery only processes these.

### Directory Definitions

| Directory | Responsibility | Deployment Behavior | Policy |
|---|---|---|---|
| `scripts/` | Executable code (.py, .js) | `.scripts/<skill>/` | Overwrite |
| `assets/` | Data files, config, requirements, templates | `.scripts/<skill>/` | Overwrite |
| `assets/templates/` | User-modifiable template files | `.scripts/<skill>/` | Fill-if-missing |
| `references/` | The skill's own reference docs | **Not deployed** — agent reads directly from plugin cache | — |
| `examples/` | Example artifacts, example HTML | **Not deployed** — agent reads directly from plugin cache | — |
| `.platform` | Empty marker file. Presence → skill is platform-level (init-workspace, update-agent-runtime), assets go via Class-A deployment to workspace root, excluded from Class-B auto-discovery | — | — |

### Rules

1. **Not deployed ≠ not important** — `references/` and `examples/` are the skill's canonical references and examples; the agent can read them directly from plugin cache when executing the skill. Do not delete them just because they do not land in the workspace.
2. **No runtime need, no empty directories** — if the skill does not need scripts or assets, do not create `scripts/` / `assets/`.
3. **Do not create directories outside this list** — if a new need arises, amend this spec first, then create the directory.
4. **Class-B auto-discovery** — `init-workspace` and `update-agent-runtime` Class-B rules simply traverse `skills/*/scripts/` + `skills/*/assets/`. Adding files to these directories → auto-deployed, zero changes needed.

### Deployment Matrix Overview

```
skills/<skill>/scripts/          →  _scripts/<skill>/          Overwrite
skills/<skill>/assets/           →  _scripts/<skill>/          Overwrite
skills/<skill>/assets/templates/ →  _scripts/<skill>/          Fill-if-missing
skills/<skill>/references/       →  (not deployed, agent reads cache)
skills/<skill>/examples/         →  (not deployed, agent reads cache)
skills/<skill>/.platform         →  Class-A, deployed to workspace root
```

## Runtime Output Contract

Default output is short and executable:

```markdown
## Meta Skill Result

**Conclusion first**
[What should be added / modified this time, and why]

## Required Edits
- [...]

## Validation
- [...]

## Open Risks
- [...]
```

If the user requests implementation, edit files directly. The root `scripts/` dev validation layer has been removed; do not reference or restore old validator / build-release entry points unless the user separately requests a toolchain redesign. Do not output lengthy design prose in place of execution.

If only brainstorming / reviewing, output should prioritize issues, tradeoffs, and recommended paths; do not write a full `SKILL.md` prematurely.

## Failure Handling

- If category is unclear, first explain the two possible consequences; do not guess it as research.
- If the skill will increase the active count, must sync skill list and path descriptions in README / CLAUDE / docs / manifests.
- If an operations skill is asked to adopt a research template, should use the operations structure instead.
- If the user requests restoring v2 state workflow, must pause and explain that this is an architectural regression.
- If old docs conflict with the current payload structure, the root `CLAUDE.md` and `plugins/buy-side-research-skills/` current structure prevails; do not restore deleted root `scripts/` or root `skills/` to maintain compatibility with old workflows.

## Workflow Integration

### 1. User Context (Must Internalize)

- **Identity**: Buy-side equity researcher, hedge fund / LS long-short strategy research context.
- **Location**: Asia timezone, affecting US equity post-print workflow.
- **Coverage markets**: Greater China (A-shares + HK + China ADR) + Global (US / Japan / Korea / Europe).
- **Coverage sectors**: Industrials, aerospace and defense, advanced manufacturing, oil and gas, renewable energy, nuclear, emerging tech themes (AI software, AI hardware, humanoid robots, commercial aerospace, quantum, etc.).

LS work characteristics:

| Characteristic | Design Implication |
|---|---|
| Two-way perspective | Thesis-related research skills default to two-way consideration, not assuming long-only |
| Pair trade is a core tool | When a long X idea is triggered, naturally bring short Y candidate / hedge option; handoff to `pair-trade` when necessary |
| Mechanism decomposition is a reusable primitive | When industry mechanisms, engineering principles, equipment chains, process flows, key terminology, or know-how gaps are involved, prefer reusing `mechanism-insight` |
| Driver decomposition is a reusable primitive | When company / segment / product line / disclosure bucket revenue / margin / backlog / price-volume-mix drivers are involved, prefer reusing `driver-map`; do not reinvent a decomposition in each skill; use `industry-landscape` for broad industry first-pass, `mechanism-insight` when mechanism is unclear |
| Market sizing | TAM/SAM/SOM estimation and scenario sizing prefer reusing `market-sizing` → `scenario-model`; do not improvise numbers in a thesis |
| Competitive moat / management / catalysts | Before deep-diving, reuse `moat-analysis`, `capital-allocation`, `catalyst-map`; do not patch together from stock-quickread |
| Post-earnings rapid judgment | Post-print verdict uses `post-earnings-quick`, reading the most recent `earnings-setup` bar as baseline comparison |
| Coverage tracking | Covered-company status updates and priority re-ranking use `coverage-tracker`, division of labor with `research-journal`: the former manages status, the latter manages cognition |
| Consensus framing is a foundation primitive | When sell-side consensus, buy-side bar, priced-in assumptions, market-implied expectations, or variant-view gaps are involved, prefer reusing `consensus-map`; do not reinvent in thesis or quickread |
| Primary evidence needs a compliance plan | When expert calls, customer / supplier channel checks, surveys, fieldwork, or ex-employee interviews are needed to verify key hypotheses, prefer reusing `primary-research-plan`; do not fabricate interview results |
| Cross-market inertia | Multiple listings of the same company and cross-market peer comparison are the norm |
| Timezone disadvantage | Work begins after US equity earnings prints; post-print tools must be efficient |
| Information drowning | Core pain point is fragmented per-company time; skills prioritize noise reduction |

Every skill design must answer: does this skill reduce cognitive burden or increase it? If it increases, explain what irreplaceable value it delivers in return.

### 2. Current System Design Philosophy (v3 Journal-First)

Do not redesign what v2 already abandoned:

- Do not restore state files for portfolio tracking, e.g., `coverage/[ticker]/thesis.md`, `pairs/[X-Y]/`, `portfolio/catalyst-pipeline.md`.
- Do not restore thesis-tracker, decision-journal, v2 pair state logs.
- Do not restore ticker-centric organization; research revolves around industries.

v3 core positioning:

```text
Senior Analyst Radar -> Better AI Question -> Research -> Journal -> Boss Brief
```

AI is not a status tracker but a senior analyst coach: helping the researcher ask better questions, retain earned cognitive increments, and discover high-value doubts.

Topic-centric organization:

```text
industry/
  [topic-namespace]/[topic-slug]/
    index.md
    [YYYY-MM-DD]-research-journal.md
    [YYYY-MM-DD]-boss-brief.md
```

### 3. Research / Operations Dual-Track Structure

Only two top-level categories are permitted:

- `research`
- `operations`

Research layers:

| Layer | Skills | Purpose |
|---|---|---|
| `triage` | `information-impact`, `stock-quickread`, `post-earnings-quick`, `reddit-sentiment`, `next-step` | Filter information, rapid judgment, post-earnings rapid reaction, social sentiment, identify the next highest-leverage question |
| `foundation` | `teach-in`, `industry-landscape`, `financial-data`, `market-sizing`, `company-history`, `consensus-map`, `mechanism-insight`, `driver-map` | Lay the foundation: zero-to-one physical intuition, industry landscape, structured financial + market data, TAM estimation, company business/disclosure history, market expectations, industry mechanisms, model drivers |
| `deep-work` | `candidate-screener`, `peer-deep-dive`, `moat-analysis`, `catalyst-map`, `capital-allocation`, `alpha-thesis`, `bear-pre-mortem`, `earnings-setup`, `pair-trade`, `primary-research-plan`, `scenario-model`, `3-statement-model`, `dcf-model`, `comps-analysis`, `model-update` | Deep research: scenario-based L/S ranking, horizontal comparison (same market / cross-market), competitive moat, catalyst chain, management capital allocation, thesis, odds memo, modeling |
| `supporting` | `research-viz` | Visualization post-processing |
| `memory` | `research-journal`, `coverage-tracker` | Retain earned insight, track covered-company status and priority |

Operations skills:

| Skill | Purpose |
|---|---|
| `coverage-monitor` | Turn `COVERAGE.md` into daily briefs and intraday alerts |
| `init-workspace` | Create / repair research workspace scaffold |
| `integrate` | Merge a child topic into a parent topic and update indexes |
| `ingest` | Convert raw material into source-tracked `_cache/` markdown |
| `meta-skill` | Create / modify / review this plugin's skills, metadata, docs, manifests, and governance |
| `update-agent-runtime` | Upgrade the installed runtime and sync workspace assets |

Active skills must remain flat at the payload root: `plugins/buy-side-research-skills/skills/[skill-name]/SKILL.md`. Do not physically move into `skills/research/` or `skills/operations/`.

### 4. 9 Core Principles for Writing Research Skills

Each principle is a hard rule; violating it requires a rewrite.

1. **Serve a "decision moment," not "output a document"**: Skills should be divided by which decision moment the researcher invokes them at, not by memo / report format.
2. **Anti-boilerplate discipline**: Prohibit company history, management biographies, generic SWOT, industry primers, unqualified qualitative statements, table regurgitation.
3. **Data-first / forced structure**: Judgments must have concrete numbers, tables, or source-backed evidence; tables must have structural takeaways.
4. **Source policy hard enforcement**: Facts, numbers, and quotes must have sources; absolutely no fabricating URLs, page numbers, quotes, numbers, names, or dates.
5. **Anti-pattern self-check mandatory**: Each anti-pattern must be specific enough for mechanical self-inspection.
6. **Clear length benchmarks**: State the lower / upper bound for user-visible output length, and what exceeding it implies.
7. **Hard Standards / Hard Cutoffs**: Any rating must have observable indicators; gut-feel is not allowed.
8. **Clear workflow integration**: Upstream, downstream, and artifact save policy must be clearly stated.
9. **Philosophy section conveys design intent**: 1-3 paragraphs explaining what the skill truly solves and where it fails most easily.

### 5. Research SKILL.md Required Structure

All research skills use the following section order. Items marked mandatory cannot be omitted; optional items are added only when needed.

```
1. Frontmatter (short trigger-only description, <=140 chars) [mandatory]
2. # Title [mandatory]
3. Research Runtime Capsule [mandatory] - forced read of references/runtime/ format (see §5.1)
4. Philosophy [mandatory] - 1-3 paragraphs on what it solves and where it fails most easily
5. Trigger Scenarios [mandatory]
6. Input Clarification Requirements [optional] - add when input is complex
7. Execution Modes (Mode A/B/C) [optional] - only for genuinely multi-mode skills
8. Output Structure [mandatory] - includes fenced ```markdown artifact skeleton + source contract
9. Artifact / Save Policy [mandatory]
10. Boundaries with Adjacent Skills [mandatory]
11. Anti-Pattern Self-Check [mandatory] - >=10 items, mechanically inspectable
12. Length Benchmarks [mandatory] - lower/upper bound and what exceeding it implies
```

Deleted sections:
- `Global Rules Capsule` - no longer needed. Global discipline lives in workspace `.references/runtime/research-runtime.md` §2.2 and hooks.
- standalone `Source Policy` / `Source Contract` section - merged into a one-line contract inside Output Structure.
- standalone `Material Collection and Source Verification` section - merged into workspace `.references/runtime/research-runtime.md` §2. Skills keep only their unique execution logic.

Research frontmatter:

```yaml
---
name: skill-name
description: Use when [specific trigger scenario and user symptoms].
---
```

Frontmatter must contain only a short single-line UI summary, not a workflow summary; `description` must be plain-text single-line, recommended under 140 characters, and must not use `|` / `>` block scalars, Markdown, lists, or long trigger rules.

To prevent skill card descriptions from appearing blank again, active `SKILL.md` must, in addition to correct frontmatter, retain a top-level `# ...` heading; do not let the frontmatter be directly followed by `## Research Runtime Capsule` or `## Modeling Runtime Capsule`.

#### §5.1 Research Runtime Capsule Standard Template

All research skills must use the following forced-read format. The core 3 lines are immutable.

```markdown
## Research Runtime Capsule

**Read these files before executing this skill:**
- workspace `.references/runtime/research-runtime.md` §1 (data acquisition chain) §2 (source verification chain) §2.1 (material collection) §2.2 (source discipline) §2.5 (image download chain) §4 (output contract) §5 (save contract)

**Automatic hook defenses:** `pre_write_gate` (source/tables/mermaid/image) `source_contract` `table_render_integrity` `mermaid_syntax` `skill_structure_contract` `evidence_ledger_floor`
```

Rules:
- The core 3 lines are immutable. Adjust § anchors only when the skill truly does not need one of them.
- Do not restate tier fallback chains, provider names, trust chains, or subagent workflow in the capsule.
- Do not write `data pipeline: call /financial-data` here; that already lives in `references/runtime/` §1.
- Do not write `Sub-agent outputs: evidence_cards_only`; that already lives in `references/runtime/` §3.
- Put skill-specific runtime nuance in `Philosophy` or `Execution Modes`, not in the capsule.

#### §5.2 Modeling Runtime Capsule Standard Template

Modeling skills use the following template. The core 4 lines are immutable; skill-specific customization is at most 2 lines.

```markdown
## Modeling Runtime Capsule

- Hook-enforced modeling rules (missing_actuals_not_zero, balance_integrity, structure_floor, etc.) live in workspace hooks.
- Shared modeling protocol: workspace `.references/policy/research-policy-baseline.md` §6.
- **DataSource**: Pull historical actuals from `actuals-resolved.json`, driver assumptions from `_cache/driver-map/`. Missing actuals are not zero-filled.
- Sub-agent QA bounded; main agent owns the final workbook.

[Skill-specific modeling rules if any, ≤2 lines]
```

**Modeling capsule self-check**:
- [ ] Is the capsule ≤ 6 lines?
- [ ] Has the Research Workspace Adapter section (cache path list) been removed?
- [ ] Has the Model Sub-Agent Protocol section (already in shared baseline §6) been removed?
- [ ] Has the consumer trust contract been removed?
- [ ] Does it duplicate hook content (missing_actuals_not_zero, etc.)?

### 6. Operations SKILL.md Required Structure

Operations skills use a lightweight execution structure:

1. Frontmatter
2. `Philosophy`
3. `Scope of Responsibility`
4. `Triggers and Inputs`
5. `Execution Modes`
6. `Tool Resources`
7. `File Safety`
8. `Runtime Output Contract`
9. `Failure Handling`
10. `Workflow Integration`
11. `Safety Self-Check`

Operations skills are not required to have:

- No mandatory `Global Rules Capsule`.
- No mandatory `Source Policy`.
- No mandatory `Anti-Pattern Self-Check`; use `Safety Self-Check` instead.
- No mandatory `Length Benchmarks`; if output length needs control, a brief note in `Runtime Output Contract` suffices.
- No `research_layer` set.

Operations skills must emphasize file safety, idempotency, failing honestly, and not overstepping to write research artifacts.

### 7. Metadata (skill.yaml, Mandatory)

Every active skill must maintain `skill.yaml`. `skill.yaml` is the metadata / index truth; `SKILL.md` is the runtime truth.

Required fields:

```yaml
metadata_schema_version: 1
name: skill-name
id: skill-name
display_name: Skill Name
version: 1.0.0
system_generation: 3.10.0
author: buy-side-research-system
namespace: research.equity
category: research
research_layer: triage
summary: ...
description: ...
trigger: ...
capabilities: ...
artifact_policy:
  save_policy: optional_topic_result
  default_artifact: skill-name.md
  canonical_location: industry/<industry>/companies/<ticker>/[YYYY-MM-DD]-skill-name.md
  naming_mode: plain
  save_trigger: save only when user asks
```

Rules:

- `category` can only be `research` or `operations`.
- Research skills must have a valid `research_layer`.
- Operations skills must not have `research_layer`.
- `meta.json` has been retired; do not create, restore, or maintain it.
- `version` is the individual skill's own semver, not the system generation.
- `system_generation` records the system generation this skill currently aligns with.
- The first non-empty body heading after `SKILL.md` frontmatter must be a top-level `# ...`, then enter capsule or other second-level headings.

Artifact policy:

- `save_policy` can only be `none`, `optional_topic_result`, `default_topic_result`, `earned_memory`, `external_workbook`, `workspace_scaffold`, `cache_artifact`, or `topic_scaffold`.
- Skills that do not write to disk use `conversation-only`.
- Topic artifacts must land in `industry/<industry>/companies/<ticker>/[YYYY-MM-DD]-[artifact].md`.
- Only research skills that produce topic markdown declare `artifact_policy.naming_mode`; allowed values are only `plain`, `optional_qualifier`, `required_qualifier`.
- `none`, `external_workbook`, `cache_artifact`, `workspace_scaffold`, `topic_scaffold` do not declare `naming_mode`.
- `research-journal` only writes earned insight / Boss Brief / topic index updates; it is not a generic save target for all skills.
- `coverage-tracker` may use `earned_memory` for the workspace-root `COVERAGE.md`; that file is workspace memory, not a topic result.
- `init-workspace` uses `workspace_scaffold`, only creating / repairing the workspace.
- `ingest` uses `cache_artifact`, only writing `_cache/` operational markdown.

Default naming tier:
- `plain`: `stock-quickread`, `company-history`, `alpha-thesis`, `bear-pre-mortem`, `earnings-setup`, `pair-trade`, `research-journal`, `moat-analysis`, `catalyst-map`, `capital-allocation`, `post-earnings-quick`
- `optional_qualifier`: `consensus-map`, `industry-landscape`, `peer-deep-dive`, `candidate-screener`, `primary-research-plan`, `scenario-model`, `market-sizing`
- `required_qualifier`: `mechanism-insight`, `teach-in`, `reddit-sentiment`

### 8. Shared Runtime / Source Baseline

General source / anti-hallucination rules for research skills are now carried by the shared baseline + workspace hooks; individual skills are no longer required to duplicate `Source Policy` locally.

Authoring hard rules:
- Research skills must default to depending on the shared source hierarchy: disclosed-fact track `topic-local evidence cache > primary public > trusted third-party > web`; market-snapshot track is uniformly obtained via `/financial-data` trust-based fill chain (Bridge → yfinance → WebSearch → Google Finance), no longer individually calling `trusted-market-bridge`.
- Examples must demonstrate inline short anchors and end-of-document `## Resources` dual-writing to the same target; writing short anchor codes like `S1` / `I1` followed by `(link)` or `(url)` placeholders is no longer allowed — such patterns will be intercepted by the source_contract hook.
- Once a binary source / structure / boundary rule enters hooks, the corresponding rule prose in `SKILL.md` must be deleted, not retained in duplicate.
- If `Source Policy` is retained, it may only contain skill-specific non-binary edge cases; shared legality must not be repeated.

### 9. Anti-Pattern Catalog

General anti-patterns:

- Appearance of "founded in / headquartered in / experienced management team."
- 5-year historical financial table listing.
- Generic SWOT.
- Industry primer / regulatory primer.
- "Benefiting from / long-term bullish / depends / remains to be seen" as a judgment.
- Data table without takeaway / takeaway that merely repeats the table.

Source-class anti-patterns:

- Specific numbers / quotes without source links.
- "Reportedly / rumored / some say" used as a source.
- Fabricated URLs.
- Sub-agent URLs treated directly as verified.
- When multiple sources conflict, picking one without flagging the conflict.
- Citing "10-K" instead of "10-K 2024 p.42."

LS perspective missing:

- Thesis defaults to long-only, not considering short / pair / hedge.
- Variant view only vs long consensus, not vs short consensus.
- Pair trade where long thesis and short thesis are not each independently sound.
- Short-only kill criteria identical to long, not accounting for squeeze risk.

Data empty talk:

- "Valuation expensive / cheap" without reverse engineering.
- "Spread deviates from history" without z-score / percentile.
- Impact = "High because this is big news."
- Catalysts are all "long-term."
- Kill criteria = "exit if wrong."
- Bear case return -2%, bear too weak.

AI fabrication class:

- Fabricating business relationships, e.g., "X is a supplier to Y" without source.
- Using known market concept stocks as a substitute for real analysis.
- Tier-2/3 connections only written as "supply chain related" without specific supplier links.
- Treating sell-side "concept stock classification" as business relationship evidence.
- AI-inferred candidates without `[需查证]` (needs verification) label.

Workflow silos:

- Not declaring `artifact_policy`.
- Writing research material directly into `research-journal`, bypassing the Earned Insight Gate.
- New artifacts continue defaulting to root `screens/`, `peers/`, `quickreads/`, `cross-market/`.
- Not specifying which downstream skill is triggered.
- Trigger keywords conflicting with existing skills.

### 10. Length Benchmarks

Research SKILL.md file itself:

- Simple skill: 200-300 lines.
- Standard skill: 300-450 lines.
- Complex skill: 300-500 lines.
- Exceeding 600 lines is usually over-engineering; should be split or streamlined.

Research user-visible output:

- Filter / Quick judgment skills: < 500 characters hard cap.
- Single-stock research: 1,200-1,800 characters.
- Multi-stock research: N linearly scaled, 1,500-5,000 characters.
- Thesis building: 800-1,500 characters.
- Coaching: < 300 characters.

Operations output length is not subject to research length benchmarks; only needs a note in `Runtime Output Contract` stating the default output is short and executable.

### 11. Final Workflow for the Agent

Work through the following 5 steps:

1. **Understand requirements**: What skill does the user want to write? What decision moment or operational job does it solve? Which step of the v3 core cycle does it belong to?
2. **Read references**: Must read root `CLAUDE.md` and this skill; read at least 2-3 adjacent active skills.
3. **Write outline**: First write section headings + 1-2 key points per section; for complex new skills, present the outline to the user for review first.
4. **Fill in content**: Focus on polishing philosophy, anti-patterns / safety self-check, hard standards, artifact policy.
5. **Self-check + flag**: Self-check against the checklist, and proactively flag the most uncertain design decisions.

When outputting to the user:

```markdown
## [Skill Name] Result

**Conclusion first**
[What was accomplished / what is recommended]

## Key Design Decisions
- [...]

## Validation
- [...]

## Open Risks
- [...]
```

### 12. Self-Check Checklist

Research skill:

- Frontmatter name + trigger-only description.
- `skill.yaml` has `category: research` and valid `research_layer`.
- Philosophy 1-3 paragraphs.
- Includes current version `Research Runtime Capsule`.
- If `Source Policy` is retained, only skill-specific non-binary increments; shared legality must not flow back.
- Trigger scenarios are specific.
- Output structure at section level + field level.
- Artifact / save policy consistent with `skill.yaml`.
- Workflow integration table.
- Anti-pattern self-check at least 10 items, mechanically self-inspectable.
- Length benchmarks clear.
- Position in v3 core cycle clear.
- Upstream / downstream skills clear.
- Triggers do not conflict.
- Examples match LS / Asia / Industrials + AI, do not use consumer / healthcare examples.

Operations skill:

- Frontmatter name + trigger-only description.
- `skill.yaml` has `category: operations`, and no `research_layer`.
- Uses operations structure.
- File safety, idempotency, fail honestly, clear boundaries.
- Artifact policy consistent with body text.
- Does not create research artifacts, unless that operations skill's responsibility is to create scaffold / cache.
- No mandatory research capsule / skill-local Source Policy / length benchmarks.
- Validator, docs, manifest counts synced.

Supporting visualization skill:

- `category: research`, but `research_layer: supporting`, not mixed into the main research ladder.
- Has complete frontmatter, top-level `# H1`, runtime capsule, and clear output contract.
- When saving to topic, must bind to a baseline markdown research artifact and reuse the same stem to output `.html`.
- Do not move installer, drag `.skill` package instructions, or external distribution layer manifests into plugin runtime skill.
- Only do source-backed visualization; do not create new company facts or theses.

### 13. What Not to Do

- Do not let research skills only reference `CLAUDE.md`; the plugin runtime may not read `CLAUDE.md`.
- Do not forcibly add research capsule, skill-local Source Policy, or length benchmarks to operations skills.
- Do not default to long-only.
- Do not design skills as sell-side report templates.
- Do not silently make assumptions; flag uncertainty.
- Do not restore v2 state files, decision-journal, thesis-tracker, v2 pair state logs.
- Do not restore `meta.json`.
- Do not physically nest active skills into category directories.

## Safety Self-Check

- ❌ Writing an operations skill as a research report template.
- ❌ Forcing `Length Benchmarks`, Senior Analyst Radar, or primitive routing onto operations skills.
- ❌ Forgetting to update `skill.yaml`, only changing `SKILL.md`.
- ❌ Forgetting to update docs / manifests, causing rules to exist only in a single file.
- ❌ Adding a new active skill but the active count remains the old value.
- ❌ Not adding a new skill to README / CLAUDE / manifests after creation.
- ❌ Restoring `meta.json`.
- ❌ Physically nesting active skills into category directories.
- ❌ Treating `research-journal` as a generic save target for all skills.
- ❌ Treating `_cache/` as earned memory or original source.

## Document Version

- **Version**: v2.0
- **Based on**: buy-side-research-skills v5.0.0
- **Last updated**: 2026-06-01
- **Maintainer**: User
