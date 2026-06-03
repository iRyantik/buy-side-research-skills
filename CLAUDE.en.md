# CLAUDE.md — Buy-Side Research Skills Plugin Development Constitution

> This file serves the `buy-side-research-skills` plugin dev repo only.
> It is the source of truth for plugin development and release governance — not the runtime constitution for user research workspaces.

---

## 1. Scope

- **This file**: plugin development constitution — authoring governance, metadata / manifest / packaging / release sync, authority hierarchy, hard gate.
- **Workspace constitution**: maintained in `plugins/buy-side-research-skills/skills/init-workspace/assets/CLAUDE.md.template` — delivered to user workspaces via `init-workspace`.
- **Hooks**: delivered via `init-workspace` to user workspace project-level config (`.claude/settings.json`, `.codex/hooks.json`). Plugin dev repo docs are NOT an automatic hook discovery surface.
- **Runtime behavior**: governed by each active skill's `plugins/buy-side-research-skills/skills/*/SKILL.md`.
- **`references/policy/research-policy-baseline.md`**: authoring baseline / review baseline only — not assumed to auto-load as runtime authority.

> Agent/plugin runtime upgrade flow → `update-agent-runtime`; workspace scaffold and repair → `init-workspace`.

---

## 2. Authority Hierarchy

When rules conflict, resolve in this order:

1. root `CLAUDE.md`
   - Plugin development constitution
2. `init-workspace/assets/CLAUDE.md.template`
   - Workspace high-level constitution template
3. Invoked research `SKILL.md`
   - Runtime executable contract
4. `references/policy/research-policy-baseline.md`
   - Authoring baseline only — not runtime authority

If the workspace template's high-level summary appears inconsistent with a specific research skill's execution rules:

- **Research `SKILL.md` wins**
- Templates provide only high-level constraints, not procedural overrides

---

## 3. Layer Responsibilities

### 3.1 Root `CLAUDE.md`

Responsible for:
- Plugin repo purpose, boundaries, authoring governance
- Metadata / manifest / release / packaging sync rules
- Which files are runtime truth vs. maintenance baseline only
- Hard gate maintenance discipline

Not responsible for:
- Detailed research runtime procedures
- Full source / fallback / sub-agent playbooks
- Research artifact writing templates

### 3.2 `CLAUDE.md.template`

Responsible for:
- Workspace context and high-level principles
- Language defaults (Chinese), conclusion-first, data-first, anti-sell-side discipline
- Workspace file rules / topic structure / routing stance
- High-level source stance

Not responsible for:
- Full claim-level source contract text
- Full fallback taxonomy
- Full status code dictionary
- Skill-specific section-level rules

### 3.3 Research `SKILL.md`

Responsible for:
- The actual runtime contract used during execution
- Canonical medium capsule
- Skill-specific delta
- Output structure, fallback boundaries, default single-threaded / parallel strategy, routing handoff

### 3.4 `research-policy-baseline.md`

Responsible for:
- Complete research rules baseline
- Reviewer / batch-sync reference master copy
- Centralized preservation of key original rules: multi-language disclosure rules, local-language / home-market source priority, claim-level source contract, clickable short anchors + `## Resources`

Not responsible for:
- Independently determining runtime behavior

---

## 4. Skill Families

### 4.1 Research Skills

Research skills must embed the **canonical medium capsule + skill-specific delta**.

The public capsule covers at minimum:
- Language defaults (Chinese), conclusion-first, data-first
- Every truth-like claim must carry a clickable short anchor
- Single `## Resources` section at end of artifact
- Honest degradation when no source is available: [需查证] or [来源待补]
- Source quality first
- Same-tier priority: local-language / home-market source
- `internet source` only fills market / consensus / valuation / liquidity / price-action gaps
- `internet source` must not impersonate company-disclosed fact
- Default single-threaded or parallel strategy per skill (one-line rule)
- Main agent owns final synthesis

### 4.2 Modeling Skills

`3-statement-model`, `dcf-model`, `comps-analysis`, `model-update` use a **separate modeling capsule** — they do not consume the research capsule.

The public modeling capsule covers at minimum:
- Actuals completeness check
- Source-map verification
- No silent zeros
- Bounded QA-type sub-agents
- Main agent owns the final workbook, valuation treatment, and delivery

### 4.3 Operations Skills

Operations skills do NOT embed a research capsule. They only retain their operational boundaries, file safety rules, input/output contracts, and necessary source discipline.

---

## 5. Hard Gate

Any public research rule change must be completed **in the same change** across:

1. Update `references/policy/research-policy-baseline.md`
2. Sync all affected active research `SKILL.md` capsules
3. If workspace high-level principles are affected, update `CLAUDE.md.template`
4. If public behavior / package language is affected, sync `README.md`, `docs/release.md`, plugin manifests / marketplace manifests

Merging or releasing a change that only updates the baseline or template without syncing the skills is forbidden.

Hooks-first supplement:

5. New deterministic runtime rules should prefer workspace hooks over stacking into `SKILL.md` prose, where scriptable.
6. Once a rule is hook-enforced, the corresponding binary rule prose in affected `SKILL.md` files must be removed in the same change.
7. Hook shared scripts and host adapters must be maintained in sync; Claude-only or Codex-only changes are not permitted.
8. The official delivery surface for hooks is the `init-workspace` scaffold; plugin dev repo local files must not be mistaken for host auto-load surfaces.
9. After adding a skill-specific hook, any remaining old prose enforcing the same rule counts as a governance failure.
10. New runtime hooks, repair scripts, or install commands must use cross-platform launchers — no hardcoded `powershell ... .ps1` without macOS `pwsh` equivalents.

---

## 6. Language Policy (Dual-Language)

- **SKILL.md**: Chinese is the single source of truth. `SKILL.en.md` is an English translation kept in sync by AI.
- **skill.yaml**: English fields only.
- **Agent output language**: controlled by workspace `CLAUDE.md` `LANG-default`, independent of skill language.
- **Hooks, scripts, references**: English or language-agnostic code.
- **English versions** must match Chinese originals in content density — no summaries, no shortcuts. Every section present in Chinese must be present in English.

---

## 7. UTF-8 Text Discipline

All Chinese or multilingual text assets must use **UTF-8 without BOM**.

This applies at minimum to:
- `.md`
- `.yaml`
- `.json`

Hard rules:
- When modifying files containing Chinese or multilingual text, write back explicitly as UTF-8.
- When batch scripts rewrite text, explicitly specify UTF-8 to avoid mojibake.
- Do not rely on terminal default encoding to "hope" files are written correctly.
- If Chinese displays incorrectly, first determine whether it is a console rendering problem or file content corruption; do not dismiss mojibake as "just a terminal issue" and commit it.

---

## 8. Authoring Rules

- Active runtime skills remain flat under `plugins/buy-side-research-skills/skills/[skill-name]/`.
- Do not restore retired `meta.json`, v2 state workflows, or ticker-centric tracker structures.
- Any new skill or major skill rewrite that affects public positioning, skill map, keywords, or release payload must sync docs / manifests.
- "Reuse existing original text where possible" takes priority over "rewrite for structural consistency." Especially for multi-language disclosure rules, source contracts, local-language source priority, and other proven rules — default to preserving the original text with minimal edits.

---

## 9. Release Shape

The runtime release zip maintains a flat payload:

- `.claude-plugin/`
- `.codex-plugin/`
- `skills/`
- `README.md`

Whether repo docs, authoring baselines, and release notes are included in the zip is governed by the current release policy; do not default to bundling all repo documentation into the runtime package.
