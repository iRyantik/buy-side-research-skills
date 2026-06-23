#!/usr/bin/env python3
"""update_agent_runtime.py — fetch latest buy-side-research-skills from GitHub,
refresh host plugin caches + marketplace pointers, and sync workspace assets.

Single command, zero dependencies beyond Python stdlib.

Usage:
  python update_agent_runtime.py                    # auto-detect workspace
  python update_agent_runtime.py --workspace <path> # explicit workspace
  python update_agent_runtime.py --dry-run           # fetch only, no writes
"""

from __future__ import annotations

import sys
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

import argparse
import json
import os
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError

GITHUB_API = "https://api.github.com/repos/iRyantik/buy-side-research-skills/releases/latest"
PLUGIN_NAME = "buy-side-research-skills"
CLAUDE_CACHE = Path.home() / ".claude" / "plugins" / "cache" / PLUGIN_NAME / PLUGIN_NAME
CODEX_CACHE = Path.home() / ".codex" / "plugins" / "cache" / PLUGIN_NAME / PLUGIN_NAME
CODEX_SKILLS = Path.home() / ".codex" / "plugins" / "cache" / PLUGIN_NAME / "skills"
INSTALLED_PLUGINS = Path.home() / ".claude" / "plugins" / "installed_plugins.json"
AGENTS_MARKETPLACE = Path.home() / ".agents" / "plugins" / "marketplace.json"

WORKSPACE_MARKERS = ["industry", "CLAUDE.md", ".scripts"]


# ── helpers ──────────────────────────────────────────────────

def _log(msg: str):
    print(f"  {msg}")


def _fail(msg: str):
    print(f"  ❌ {msg}", file=sys.stderr)
    sys.exit(1)


def _fetch_json(url: str) -> dict:
    req = Request(url, headers={"User-Agent": "buy-side-research-skills/update-agent-runtime",
                                 "Accept": "application/vnd.github+json"})
    try:
        with urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except URLError as e:
        _fail(f"Failed to fetch {url}: {e}")


def _download(url: str, dest: Path):
    _log(f"Downloading {url}")
    req = Request(url, headers={"User-Agent": "buy-side-research-skills/update-agent-runtime"})
    try:
        with urlopen(req, timeout=120) as resp:
            dest.write_bytes(resp.read())
    except URLError as e:
        _fail(f"Download failed: {e}")


def _discover_workspace() -> Path:
    cwd = Path.cwd()
    for parent in [cwd, *cwd.parents]:
        if sum(1 for m in WORKSPACE_MARKERS if (parent / m).exists()) >= 2:
            return parent
    _fail("Workspace not found. Pass --workspace or run from inside a workspace.")


def _host_installed(cache_dir: Path) -> bool:
    return cache_dir.parent.parent.exists()


# ── fetch ─────────────────────────────────────────────────────

def fetch_latest() -> tuple[str, Path]:
    """Fetch latest release from GitHub, return (version, payload_dir)."""
    _log("Fetching latest release info...")
    release = _fetch_json(GITHUB_API)
    version = release["tag_name"].lstrip("v")
    zip_url = release.get("zipball_url")
    if not zip_url:
        _fail("No zipball_url in release")

    tmp = Path(tempfile.mkdtemp(prefix="bsrs-update-"))
    zip_path = tmp / "release.zip"
    _download(zip_url, zip_path)

    _log(f"Extracting {version}...")
    extract_dir = tmp / "extracted"
    extract_dir.mkdir()
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(extract_dir)

    # GitHub zipball wraps everything in <owner>-<repo>-<commit>/
    root_dirs = [d for d in extract_dir.iterdir() if d.is_dir()]
    if not root_dirs:
        _fail("Empty zipball")
    payload = root_dirs[0] / "plugins" / PLUGIN_NAME
    if not payload.is_dir():
        _fail(f"Payload not found at expected path in zipball: {payload}")

    return version, payload


# ── cache update ──────────────────────────────────────────────

def update_host_cache(payload: Path, version: str, cache_dir: Path, host_name: str):
    """Copy plugin payload into host cache directory."""
    ver_dir = cache_dir / version
    if ver_dir.exists():
        shutil.rmtree(ver_dir)
    ver_dir.mkdir(parents=True)
    _log(f"Copying to {host_name} cache: {ver_dir}")
    shutil.copytree(payload, ver_dir, dirs_exist_ok=True)


def update_marketplace_pointers(version: str):
    """Update installed_plugins.json and .agents marketplace to point to latest."""
    # Claude Code
    if INSTALLED_PLUGINS.exists():
        with open(INSTALLED_PLUGINS, encoding="utf-8") as f:
            data = json.load(f)
        key = f"{PLUGIN_NAME}@{PLUGIN_NAME}"
        if key in data.get("plugins", {}):
            for entry in data["plugins"][key]:
                entry["version"] = version
                entry["installPath"] = str(CLAUDE_CACHE / version)
                from datetime import datetime, timezone
                entry["lastUpdated"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
            with open(INSTALLED_PLUGINS, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            _log("installed_plugins.json updated")

    # .agents marketplace
    if AGENTS_MARKETPLACE.exists():
        with open(AGENTS_MARKETPLACE, encoding="utf-8") as f:
            mp = json.load(f)
        for p in mp.get("plugins", []):
            if p.get("name") == PLUGIN_NAME:
                p["version"] = version
                p["path"] = str(CODEX_CACHE / version)
        with open(AGENTS_MARKETPLACE, "w", encoding="utf-8") as f:
            json.dump(mp, f, indent=2, ensure_ascii=False)
        _log(".agents marketplace updated")


def refresh_codex_skills(payload: Path):
    """Sync latest skills to Codex skills cache."""
    skills_src = payload / "skills"
    if skills_src.is_dir():
        CODEX_SKILLS.mkdir(parents=True, exist_ok=True)
        shutil.copytree(skills_src, CODEX_SKILLS, dirs_exist_ok=True)
        _log(f"Codex skills refreshed ({len(list(CODEX_SKILLS.iterdir()))} dirs)")


# ── workspace sync ────────────────────────────────────────────

def sync_workspace(payload: Path, workspace: Path):
    """Sync workspace runtime assets from init-workspace."""
    assets = payload / "skills" / "init-workspace" / "assets"
    if not assets.is_dir():
        _log("init-workspace assets not found, skipping workspace sync")
        return

    # A. Hooks
    hooks_src = assets / ".claude" / "hooks"
    if hooks_src.is_dir():
        hooks_dst = workspace / ".claude" / "hooks"
        hooks_dst.mkdir(parents=True, exist_ok=True)
        shutil.copytree(hooks_src, hooks_dst, dirs_exist_ok=True)
        _log("hooks synced")

    # B. Host configs
    for fname in ["settings.json"]:
        src = assets / ".claude" / fname
        if src.is_file():
            shutil.copy2(src, workspace / ".claude" / fname)
    for fname in ["hooks.json", "mcp.example.json"]:
        src = assets / ".codex" / fname
        if src.is_file():
            dst = workspace / ".codex" / fname
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
    _log("host configs synced")

    # C. .scripts/
    # C1 — platform-owned scripts from assets/.scripts/
    scripts_src = assets / ".scripts"
    if scripts_src.is_dir():
        for f in scripts_src.glob("*.py"):
            shutil.copy2(f, workspace / ".scripts" / f.name)
    # C2 — skill workspace scripts (auto-discover)
    skills_dir = payload / "skills"
    if skills_dir.is_dir():
        for skill_dir in skills_dir.iterdir():
            if not skill_dir.is_dir():
                continue
            if (skill_dir / ".platform").exists():
                continue
            src_scripts = skill_dir / "scripts"
            if src_scripts.is_dir():
                dst_dir = workspace / ".scripts" / skill_dir.name
                dst_dir.mkdir(parents=True, exist_ok=True)
                shutil.copytree(src_scripts, dst_dir, dirs_exist_ok=True)
    _log(".scripts/ synced")

    # D. .references/
    refs = {
        ".references/policy": assets / ".references" / "policy",
        ".references/kpi-drivers": assets / ".references" / "kpi-drivers",
        ".references/runtime": assets / ".references" / "runtime",
        ".references/templates": assets / ".references" / "templates",
    }
    for rel, src in refs.items():
        if src.is_dir():
            dst = workspace / rel
            dst.mkdir(parents=True, exist_ok=True)
            shutil.copytree(src, dst, dirs_exist_ok=True)
    _log(".references/ synced")

    # E. Root docs — edge-radar moved to .references/, everything else via templates


def run_verify(workspace: Path) -> bool:
    verify_script = workspace / ".scripts" / "verify-runtime.py"
    if not verify_script.is_file():
        _log("verify-runtime.py not found, skipping")
        return True
    _log("Running verify-runtime.py...")
    result = subprocess.run(
        [sys.executable, str(verify_script)],
        cwd=str(workspace), capture_output=True, text=True, timeout=120
    )
    print(result.stdout)
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
    return result.returncode == 0


# ── main ──────────────────────────────────────────────────────

def main():
    p = argparse.ArgumentParser(description="Update buy-side-research-skills plugin and workspace")
    p.add_argument("--workspace", help="Workspace path (auto-detect if omitted)")
    p.add_argument("--dry-run", action="store_true", help="Fetch and report version only")
    args = p.parse_args()

    print("Buy-Side Research Skills — Update Agent Runtime")
    print(f"{'='*50}")

    # 1. Fetch latest from GitHub
    version, payload = fetch_latest()
    print(f"Latest: v{version}")

    if args.dry_run:
        _log(f"Dry run — would install v{version} to:")
        if _host_installed(CLAUDE_CACHE):
            _log(f"  Claude Code: {CLAUDE_CACHE / version}")
        if _host_installed(CODEX_CACHE):
            _log(f"  Codex:       {CODEX_CACHE / version}")
        shutil.rmtree(payload.parent.parent)
        return 0

    # 2. Update host caches
    hosts_updated = []
    if _host_installed(CLAUDE_CACHE):
        update_host_cache(payload, version, CLAUDE_CACHE, "Claude Code")
        hosts_updated.append("Claude Code")
    else:
        _log("Claude Code not installed, skipping")

    if _host_installed(CODEX_CACHE):
        update_host_cache(payload, version, CODEX_CACHE, "Codex")
        hosts_updated.append("Codex")
    else:
        _log("Codex not installed, skipping")

    # 3. Marketplace pointers
    update_marketplace_pointers(version)

    # 4. Codex skills
    refresh_codex_skills(payload)

    # 5. Workspace sync
    workspace = Path(args.workspace).resolve() if args.workspace else _discover_workspace()
    _log(f"Workspace: {workspace}")
    sync_workspace(payload, workspace)

    # 6. Verify
    ok = run_verify(workspace)

    # 7. Cleanup
    shutil.rmtree(payload.parent.parent)

    # Summary
    print()
    print(f"{'='*50}")
    print(f"Updated: {', '.join(hosts_updated) if hosts_updated else 'none'}")
    print(f"Version: v{version}")
    print(f"Workspace: {workspace}")
    print(f"Verify: {'PASS' if ok else 'FAIL — check output above'}")
    print(f"{'='*50}")

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
