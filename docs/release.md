# Release

This file is for maintainers of the plugin source repo. Normal plugin users do not need to read it.

Current release version: `7.6.30`.

## Source And Runtime Shape

The source repo is a wrapper. The canonical plugin payload is:

```text
.agents/plugins/marketplace.json
.claude-plugin/marketplace.json
plugins/buy-side-research-skills/
  .claude-plugin/
    plugin.json
  .codex-plugin/
    plugin.json
  skills/
```

Release zip files stay flat for installation:

```text
.claude-plugin/
.codex-plugin/
skills/
README.md
```

## Release Package Contents

Release zip includes only runtime/install materials copied from the payload plus root README:

- `plugins/buy-side-research-skills/.claude-plugin/` -> `.claude-plugin/`
- `plugins/buy-side-research-skills/.codex-plugin/` -> `.codex-plugin/`
- `plugins/buy-side-research-skills/skills/` -> `skills/`
- `README.md`

Each release also ships `longbridge-skills.zip` as a companion asset (Longbridge market-data plugin, 80+ skills). Download the zip from the same GitHub Release page and install as a local plugin.

Release zip must not include source-repo maintenance files:

- `plugins/`
- root `CLAUDE.md`
- root `AGENTS.md`
- `docs/`
- `examples/`
- `.git/`
- `.claude/`
- `RTK.md`
- `dist/`
- local editor or agent state
- root marketplace wrapper files

`skills/_shared/research-policy-baseline.md` is a repository-side authoring baseline. It helps preserve canonical research rules and sync capsules, but it is not a runtime authority layer.

Chinese or multilingual text assets in this repo should be maintained as UTF-8 without BOM, especially governance docs, templates, and skill markdown.

Release zip must include skill-owned runtime resources, especially:

```text
# init-workspace (platform-owned assets)
skills/init-workspace/assets/CLAUDE.md.template
skills/init-workspace/assets/CLAUDE.en.md.template
skills/init-workspace/assets/AGENTS.md.template
skills/init-workspace/assets/AGENTS.en.md.template
skills/init-workspace/assets/COVERAGE.md.template
skills/init-workspace/assets/.claude/hooks/hook_entry.py
skills/init-workspace/assets/.claude/hooks/py
skills/init-workspace/assets/.claude/hooks/py.cmd
skills/init-workspace/assets/.claude/mcp.json
skills/init-workspace/assets/.claude/settings.json
skills/init-workspace/assets/.scripts/shared/browser-cdp.py
skills/init-workspace/assets/.scripts/shared/verify-claim.py
skills/init-workspace/assets/.scripts/shared/web-extract.py
skills/init-workspace/assets/.scripts/shared/pdf-extract.py
skills/init-workspace/assets/.scripts/shared/search.py
skills/init-workspace/assets/.scripts/shared/download-image.py
skills/init-workspace/assets/.scripts/shared/route.py
skills/init-workspace/assets/.scripts/shared/transcribe.py
skills/init-workspace/assets/.scripts/shared/to-markdown.py
skills/init-workspace/assets/.scripts/shared/extract-*.py
skills/init-workspace/assets/.scripts/shared/fix-bare-anchors.py
skills/init-workspace/assets/.scripts/shared/generate-memory-cards.py
skills/init-workspace/assets/.scripts/browser-cdp/page-extract.py
skills/init-workspace/assets/.scripts/browser-cdp/twitter-search.py
skills/init-workspace/assets/.scripts/browser-cdp/twitter-profiles.py
skills/init-workspace/assets/.scripts/browser-cdp/xiaohongshu-search.py
skills/init-workspace/assets/.scripts/verify-runtime.py
skills/init-workspace/assets/.scripts/evidence_ledger.py
skills/init-workspace/assets/.scripts/ingest.py
skills/init-workspace/assets/.references/
skills/init-workspace/assets/.vscode/settings.json

# ingest
skills/ingest/assets/requirements-ingest.txt
skills/ingest/scripts/bootstrap-ingest-deps.ps1
skills/ingest/scripts/bootstrap-ingest-deps.sh
skills/ingest/scripts/ingest.py
skills/ingest/scripts/ingest_xlsx.py
skills/ingest/scripts/ingest_table_crosscheck.py

# financial-data
skills/financial-data/assets/requirements-financial-data.txt
skills/financial-data/scripts/financial_data.py
skills/financial-data/scripts/bootstrap-financial-data-deps.ps1
skills/financial-data/scripts/providers/*.py

# reddit-sentiment
skills/reddit-sentiment/assets/requirements-reddit-sentiment.txt
skills/reddit-sentiment/assets/default-clusters.json
skills/reddit-sentiment/scripts/reddit_label.py
skills/reddit-sentiment/scripts/bootstrap-reddit-sentiment-deps.ps1
skills/reddit-sentiment/scripts/bootstrap-reddit-sentiment-deps.sh

# research-viz
skills/research-viz/SKILL.md
skills/research-viz/skill.yaml
skills/research-viz/assets/template.html
skills/research-viz/assets/template-interactive.html
skills/research-viz/references/*.md
skills/research-viz/examples/*.html

# update-agent-runtime
skills/update-agent-runtime/SKILL.md
skills/update-agent-runtime/skill.yaml
skills/update-agent-runtime/scripts/update_agent_runtime.py
```

## Tooling Policy

Root `scripts/` has been removed from this source layout. Do not reference the old validator or build-release commands in maintenance instructions.

Packaging for this release is assembled manually from the payload into `dist/buy-side-research-skills-7.6.1.zip`. If future releases need automation again, design that tooling in a separate change rather than restoring stale root scripts.

Before publishing a marketplace/plugin manifest change, confirm these JSON files parse without a UTF-8 BOM and start with `{`:

```text
.agents/plugins/marketplace.json
.claude-plugin/marketplace.json
plugins/buy-side-research-skills/.codex-plugin/plugin.json
plugins/buy-side-research-skills/.claude-plugin/plugin.json
```

Before publishing skill card changes, treat `SKILL.md` frontmatter `description` as the canonical card UI description. Every active skill should keep that field as a short one-line plain text English summary. Do not use `description: |`, Markdown, bullets, or long trigger/workflow paragraphs in frontmatter; put long behavior details in the body and `skill.yaml`.

Before packaging, also confirm every active `skill.yaml` `description` matches the corresponding `SKILL.md` frontmatter description exactly, that frontmatter is followed by a top-level `# ...` heading before any `## Research Runtime Capsule` / `## Modeling Runtime Capsule`, and that both `SKILL.md` and `skill.yaml` are saved as UTF-8 without BOM using a stable newline convention.

Suggested validation checks:

```powershell
rtk rg -n '^description:' plugins/buy-side-research-skills/skills -g SKILL.md
rtk rg -n '^summary:|^description:' plugins/buy-side-research-skills/skills -g skill.yaml
rtk rg -n '^(# |## Research Runtime Capsule|## Modeling Runtime Capsule)' plugins/buy-side-research-skills/skills -g SKILL.md
```

## Release Workflow

This is the step-by-step release procedure. Execute from `~/dev/buyside`.

### Prerequisites

**gh CLI** (portable install, no admin required):

```bash
# One-time setup
mkdir -p ~/.local/gh
curl -sL "https://github.com/cli/cli/releases/latest/download/gh_VERSION_windows_amd64.zip" -o "$TEMP/gh.zip"
unzip -o "$TEMP/gh.zip" -d ~/.local/gh
```

**GitHub token**: gh CLI reads the same credential as git push (Windows Credential Manager). If `gh auth status` shows not logged in, extract the token:

```powershell
"protocol=https`nhost=github.com`n" | git credential-manager get
# Copy the password= line, then:
echo "<token>" | ~/.local/gh/bin/gh auth login --with-token
# Alternatively, set GH_TOKEN env var:
export GH_TOKEN="<token>"
```

### Procedure

All steps are mandatory. Do not skip `gh release create` — the `update-agent-runtime` script fetches from the GitHub Releases API, not git tags.

```bash
# 1. Commit all changes
cd ~/dev/buyside
git add -A
git commit -m "<type>: <description>"

# 2. Tag
git tag -a vX.Y.Z -m "vX.Y.Z: <one-line summary>"

# 3. Push
git push
git push origin vX.Y.Z

# 4. Create GitHub Release (REQUIRED — not optional)
~/.local/gh/bin/gh release create vX.Y.Z \
  --repo iRyantik/buy-side-research-skills \
  --title "vX.Y.Z" \
  --notes "<changes summary>"

# 5. Update local runtime
python s:/.scripts/update-agent-runtime/update_agent_runtime.py

# 6. Verify
python s:/.scripts/verify-runtime.py
```

### Post-Release: Cross-Machine Sync

On the **other machine**:

```bash
cd ~/dev/buyside && git pull
# Then in CC: /update-agent-runtime
```

If the other machine doesn't have `~/dev/buyside` yet:

```bash
mkdir -p ~/dev && git clone https://github.com/iRyantik/buy-side-research-skills.git ~/dev/buyside
```

---

## Dependency Policy

The package should not preinstall Docling, EdgarTools, AKShare, edinet-tools, dart-fss, openesef, Tesseract, MarkItDown, or other parsers. Users opt in from their research workspace by running the platform-appropriate bootstrap helpers: Windows may use `powershell ... .ps1`, while macOS requires `pwsh` for `.ps1` helpers and may use `_scripts/bootstrap-ingest-deps.sh` where that shell helper exists.
