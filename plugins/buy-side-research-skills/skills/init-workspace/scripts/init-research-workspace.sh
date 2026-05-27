#!/usr/bin/env bash
# Initialize a buy-side research workspace (macOS / Linux).
# Mirrors init-research-workspace.ps1 for platforms without PowerShell.
#
# Usage:
#   chmod +x init-research-workspace.sh
#   bash init-research-workspace.sh --workspace-path /path/to/workspace

set -euo pipefail

WORKSPACE_PATH=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --workspace-path|-WorkspacePath)
            WORKSPACE_PATH="$2"
            shift 2
            ;;
        *)
            echo "Unknown flag: $1"
            exit 1
            ;;
    esac
done

if [ -z "$WORKSPACE_PATH" ]; then
    echo '{"status":"failed","error":"--workspace-path is required"}'
    exit 1
fi

# ---------- resolve paths ----------
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SKILLS_ROOT="$(cd "$SKILL_ROOT/.." && pwd)"
PLUGIN_ASSETS_ROOT="$SKILL_ROOT/assets"
LOCAL_ASSETS_ROOT="$SCRIPT_DIR/init-assets"

if [ -d "$PLUGIN_ASSETS_ROOT" ]; then
    ASSETS_ROOT="$PLUGIN_ASSETS_ROOT"
else
    ASSETS_ROOT="$LOCAL_ASSETS_ROOT"
fi

INGEST_SCRIPTS_ROOT="$SKILLS_ROOT/ingest/scripts"
INGEST_ASSETS_ROOT="$SKILLS_ROOT/ingest/assets"
FINANCIAL_SCRIPTS_ROOT="$SKILLS_ROOT/financial-data/scripts"
FINANCIAL_ASSETS_ROOT="$SKILLS_ROOT/financial-data/assets"

if [ ! -d "$INGEST_SCRIPTS_ROOT" ]; then INGEST_SCRIPTS_ROOT="$SCRIPT_DIR"; fi
if [ ! -d "$INGEST_ASSETS_ROOT" ]; then INGEST_ASSETS_ROOT="$SCRIPT_DIR"; fi
if [ ! -d "$FINANCIAL_SCRIPTS_ROOT" ]; then FINANCIAL_SCRIPTS_ROOT="$SCRIPT_DIR/financial-data"; fi
if [ ! -d "$FINANCIAL_ASSETS_ROOT" ]; then FINANCIAL_ASSETS_ROOT="$SCRIPT_DIR/financial-data"; fi

WORKSPACE="$(cd "$WORKSPACE_PATH" 2>/dev/null && pwd || echo '')"
if [ -z "$WORKSPACE" ]; then
    WORKSPACE="$(mkdir -p "$WORKSPACE_PATH" && cd "$WORKSPACE_PATH" && pwd)"
fi

# ---------- helpers ----------
CREATED=()
UPDATED=()
SKIPPED=()

add_result() {
    local list="$1"
    local value="$2"
    case "$list" in
        created) CREATED+=("$value") ;;
        updated) UPDATED+=("$value") ;;
        skipped) SKIPPED+=("$value") ;;
    esac
}

write_template_if_missing() {
    local template="$1"
    local target="$2"
    local name="$3"

    if [ -f "$target" ]; then
        add_result skipped "$name"
        return
    fi

    local date_str
    date_str=$(date +%Y-%m-%d)
    sed -e "s|{{WORKSPACE_PATH}}|$WORKSPACE|g" \
        -e "s|{{DATE}}|$date_str|g" \
        "$template" > "$target"
    add_result created "$name"
}

copy_script_if_missing() {
    local source="$1"
    local relative_target="$2"
    local target="$WORKSPACE/$relative_target"

    if [ -f "$target" ]; then
        add_result skipped "$relative_target"
        return
    fi

    mkdir -p "$(dirname "$target")"
    cp "$source" "$target"
    add_result created "$relative_target"
}

sync_managed_file() {
    local source="$1"
    local relative_target="$2"
    local target="$WORKSPACE/$relative_target"
    local name="$relative_target"

    mkdir -p "$(dirname "$target")"

    if [ ! -f "$target" ]; then
        cp "$source" "$target"
        add_result created "$name"
        return
    fi

    local source_hash target_hash
    source_hash=$(shasum -a 256 "$source" | awk '{print $1}')
    target_hash=$(shasum -a 256 "$target" | awk '{print $1}')

    if [ "$source_hash" = "$target_hash" ]; then
        add_result skipped "$name"
        return
    fi

    cp -f "$source" "$target"
    add_result updated "$name"
}

sync_managed_text() {
    local content="$1"
    local relative_target="$2"
    local target="$WORKSPACE/$relative_target"
    local name="$relative_target"

    mkdir -p "$(dirname "$target")"

    if [ ! -f "$target" ]; then
        printf '%s' "$content" > "$target"
        add_result created "$name"
        return
    fi

    local target_content
    target_content=$(cat "$target")
    if [ "$content" = "$target_content" ]; then
        add_result skipped "$name"
        return
    fi

    printf '%s' "$content" > "$target"
    add_result updated "$name"
}

# ---------- refuse init inside plugin repo ----------
PLUGIN_MARKERS=(".claude-plugin/plugin.json" ".codex-plugin/plugin.json" "skills")
PLUGIN_HITS=0
for marker in "${PLUGIN_MARKERS[@]}"; do
    if [ -f "$WORKSPACE/$marker" ]; then
        PLUGIN_HITS=$((PLUGIN_HITS + 1))
    fi
done
if [ "$PLUGIN_HITS" -ge 2 ]; then
    echo "{\"status\":\"failed\",\"error\":\"Refusing to initialize research workspace inside a plugin repo or plugin install directory: $WORKSPACE\"}"
    exit 1
fi

# ---------- create directories ----------
for dir in "_inbox" "_scripts" "topics"; do
    target="$WORKSPACE/$dir"
    if [ -d "$target" ]; then
        add_result skipped "$dir"
    else
        mkdir -p "$target"
        add_result created "$dir"
    fi
done

# ---------- write templates ----------
write_template_if_missing "$ASSETS_ROOT/CLAUDE.md.template" "$WORKSPACE/CLAUDE.md" "CLAUDE.md"
write_template_if_missing "$ASSETS_ROOT/AGENTS.md.template" "$WORKSPACE/AGENTS.md" "AGENTS.md"
write_template_if_missing "$ASSETS_ROOT/gitignore.template" "$WORKSPACE/.gitignore" ".gitignore"
write_template_if_missing "$ASSETS_ROOT/edge-radar.md" "$WORKSPACE/edge-radar.md" "edge-radar.md"

# ---------- copy this script ----------
copy_script_if_missing "$0" "_scripts/init-research-workspace.sh"

# ---------- copy asset templates ----------
for asset in "CLAUDE.md.template" "AGENTS.md.template" "gitignore.template" "edge-radar.md" "env-setup.ps1.template"; do
    src="$ASSETS_ROOT/$asset"
    if [ -f "$src" ]; then
        copy_script_if_missing "$src" "_scripts/init-assets/$asset"
    fi
done

# ---------- sync config files ----------
render_hook_config() {
    local source="$1"
    # Replace {{HOOK_RUNNER}} xxx.ps1 with sh run-hook.sh xxx.ps1 (macOS-style)
    sed -E 's/\{\{HOOK_RUNNER\}\}\s+([^\s"\\]+\.ps1)/sh ".claude\/hooks\/run-hook.sh" "\1"/g' "$source"
}

for config in ".claude/settings.json" ".codex/hooks.json"; do
    src="$ASSETS_ROOT/$config"
    if [ -f "$src" ]; then
        rendered=$(render_hook_config "$src")
        sync_managed_text "$rendered" "$config"
        sync_managed_text "$rendered" "_scripts/init-assets/$config"
    fi
done

# ---------- sync hooks ----------
HOOKS_ROOT="$ASSETS_ROOT/.claude/hooks"
if [ -d "$HOOKS_ROOT" ]; then
    while IFS= read -r -d '' hook_file; do
        rel_hook="${hook_file#$HOOKS_ROOT/}"
        workspace_hook=".claude/hooks/$rel_hook"
        sync_managed_file "$hook_file" "$workspace_hook"
        sync_managed_file "$hook_file" "_scripts/init-assets/.claude/hooks/$rel_hook"
    done < <(find "$HOOKS_ROOT" -type f -print0)
fi

# ---------- copy ingest scripts ----------
for script in "ingest.py" "ingest_xlsx.py" "ingest_table_crosscheck.py" "bootstrap-ingest-deps.ps1" "bootstrap-ingest-deps.sh"; do
    src="$INGEST_SCRIPTS_ROOT/$script"
    if [ -f "$src" ]; then
        copy_script_if_missing "$src" "_scripts/$script"
    fi
done

req="$INGEST_ASSETS_ROOT/requirements-ingest.txt"
if [ -f "$req" ]; then
    copy_script_if_missing "$req" "_scripts/requirements-ingest.txt"
fi

# ---------- copy financial-data scripts ----------
FD_ROOT="_scripts/financial-data"
for script in "financial_data.py" "bootstrap-financial-data-deps.ps1" "bootstrap-financial-data-deps.sh"; do
    src="$FINANCIAL_SCRIPTS_ROOT/$script"
    if [ -f "$src" ]; then
        copy_script_if_missing "$src" "$FD_ROOT/$script"
    fi
done

for provider in "sec_provider.py" "akshare_provider.py" "edinet_provider.py" "dart_provider.py" "openesef_provider.py"; do
    src="$FINANCIAL_SCRIPTS_ROOT/providers/$provider"
    if [ -f "$src" ]; then
        copy_script_if_missing "$src" "$FD_ROOT/providers/$provider"
    fi
done

fd_req="$FINANCIAL_ASSETS_ROOT/requirements-financial-data.txt"
if [ -f "$fd_req" ]; then
    copy_script_if_missing "$fd_req" "$FD_ROOT/requirements-financial-data.txt"
fi

# ---------- output JSON result ----------
json_array() {
    local -n arr=$1
    local out="["
    local first=true
    for item in "${arr[@]}"; do
        if $first; then first=false; else out+=","; fi
        out+="\"$item\""
    done
    out+="]"
    echo "$out"
}

CREATED_JSON=$(json_array CREATED)
UPDATED_JSON=$(json_array UPDATED)
SKIPPED_JSON=$(json_array SKIPPED)

cat <<JSONEOF
{
  "workspace_path": "$WORKSPACE",
  "created": $CREATED_JSON,
  "updated": $UPDATED_JSON,
  "skipped": $SKIPPED_JSON,
  "note": "No git init, no dependency install, and no ingest execution were performed. No financial-data execution was performed. To enable toolchains, run the platform-appropriate bootstrap helpers: macOS may use _scripts/bootstrap-ingest-deps.sh and _scripts/financial-data/bootstrap-financial-data-deps.sh where provided."
}
JSONEOF
