#!/usr/bin/env python3
"""Compare v8.3.3 init-workspace/assets vs workspace. Report gaps."""
from pathlib import Path

CACHE = Path.home() / ".claude" / "plugins" / "cache" / "buy-side-research-skills" / "buy-side-research-skills"
ASSETS = CACHE / "8.3.3" / "skills" / "init-workspace" / "assets"
SKILLS = CACHE / "8.3.3" / "skills"
WS = Path("s:/")

# Build payload file set
payload = {}
for p in ASSETS.glob("**/*"):
    if p.is_file() and "__pycache__" not in str(p):
        rel = str(p.relative_to(ASSETS)).replace("\\", "/")
        payload[rel] = p

# Build workspace file set
ws_files = set()
for d in [".scripts", ".claude", ".codex", ".references"]:
    dd = WS / d
    if dd.is_dir():
        for p in dd.glob("**/*"):
            if p.is_file() and "__pycache__" not in str(p):
                ws_files.add(str(p.relative_to(WS)).replace("\\", "/"))


def check(name, src_rel, ws_rel=None):
    """Report if a file is in payload but not in workspace."""
    if ws_rel is None:
        ws_rel = src_rel
    ok = ws_rel in ws_files
    if not ok:
        print(f"  [MISS] {ws_rel}")
    return ok


# ---- A. Hooks ----
print("=== A. Hooks (.claude/hooks/) ===")
missing_hooks = 0
for rel in sorted(payload):
    if rel.startswith(".claude/hooks/"):
        if not check("hooks", rel):
            missing_hooks += 1
if missing_hooks == 0:
    print("  all present")
print()

# ---- B. Host configs ----
print("=== B. Host configs ===")
for rel in [".claude/settings.json", ".codex/hooks.json", ".codex/mcp.example.json"]:
    check("config", rel)
print()

# ---- C1. .scripts/ from assets ----
print("=== C1. Platform scripts (.scripts/) ===")
missing_c1 = 0
for rel in sorted(payload):
    if rel.startswith(".scripts/"):
        if not check("scripts", rel):
            missing_c1 += 1
if missing_c1 == 0:
    print("  all present")
print()

# ---- C2. Skill scripts ----
print("=== C2. Skill scripts ===")
missing_c2 = 0
for skill_dir in sorted(SKILLS.iterdir()):
    if not skill_dir.is_dir():
        continue
    if (skill_dir / ".platform").exists():
        continue
    scripts_dir = skill_dir / "scripts"
    if not scripts_dir.is_dir():
        continue
    for py_file in scripts_dir.glob("**/*"):
        if py_file.is_file():
            rel = py_file.relative_to(SKILLS)
            parts = rel.parts  # skill_name/scripts/sub/...
            ws_rel = f".scripts/{parts[0]}/{'/'.join(parts[2:])}"
            if not check("C2", "", ws_rel):
                missing_c2 += 1
if missing_c2 == 0:
    print("  all present")
print()

# ---- D. .references/ ----
print("=== D. .references/ ===")
missing_refs = 0
for rel in sorted(payload):
    if rel.startswith(".references/"):
        if not check("references", rel):
            missing_refs += 1
if missing_refs == 0:
    print("  all present")
print()

# ---- E. Other (templates, etc.) ----
print("=== E. Templates (in payload but NOT synced by script) ===")
template_keys = [
    ".env.template", ".env.en.template",
    "CLAUDE.md.template", "CLAUDE.en.md.template",
    "AGENTS.md.template", "AGENTS.en.md.template",
    "coverage.md.template", "coverage.en.md.template",
    ".references/edge-radar.md", ".references/edge-radar.en.md",
    ".claude/skills/session-sync-setup.md",
    ".claude/mcp.json",
]
for rel in sorted(payload):
    if rel in template_keys or rel.startswith(".vscode/") or rel == "CLAUDE.md":
        in_ws = rel in ws_files
        print(f"  {'[OK]' if in_ws else '[N/A]'} {rel}  (not in sync scope)")

# Summary
total_missing = missing_hooks + missing_c1 + missing_c2 + missing_refs
print(f"\n=== SUMMARY: {total_missing} files missing from workspace ===")
