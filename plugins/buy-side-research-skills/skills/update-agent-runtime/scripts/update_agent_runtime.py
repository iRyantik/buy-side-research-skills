#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


REPO_URL = "https://github.com/iRyantik/buy-side-research-skills.git"
LATEST_RELEASE_API = "https://api.github.com/repos/iRyantik/buy-side-research-skills/releases/latest"
PLUGIN_NAME = "buy-side-research-skills"
MARKETPLACE_NAME = "buy-side-research"
LOCAL_CLAUDE_PLUGIN_ID = f"{PLUGIN_NAME}@local-desktop-app-uploads"
GITHUB_CLAUDE_PLUGIN_ID = f"{PLUGIN_NAME}@{MARKETPLACE_NAME}"
PLUGIN_MARKERS = (".claude-plugin", ".codex-plugin", "skills")
CLAUDE_SECTION_HEADINGS = [
    "## 3. Output Style",
    "## 4. Source Stance",
    "## 5. Workspace Structure",
    "## 6. Routing Stance",
    "## 7. UTF-8 文本纪律",
    "## 8. Boundary",
]


class UpdateRuntimeError(RuntimeError):
    pass


@dataclass
class ReleaseInfo:
    tag: str
    version: str
    asset_name: str
    asset_url: str


@dataclass
class WorkspacePatchResult:
    status: str
    details: list[str] = field(default_factory=list)


@dataclass
class Report:
    host: str
    latest_version: str
    workspace: str
    host_actions: list[str] = field(default_factory=list)
    workspace_actions: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    claude_md: WorkspacePatchResult | None = None
    agents_md: WorkspacePatchResult | None = None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Update current host plugin runtime and sync current workspace.")
    parser.add_argument("--host", choices=["auto", "claude", "codex"], default="auto")
    parser.add_argument("--workspace", help="Workspace root to repair. Defaults to the current workspace root.")
    return parser.parse_args()


def run_command(cmd: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def ensure_ok(result: subprocess.CompletedProcess[str], context: str) -> str:
    if result.returncode != 0:
        stderr = result.stderr.strip()
        stdout = result.stdout.strip()
        detail = stderr or stdout or f"exit code {result.returncode}"
        raise UpdateRuntimeError(f"{context} failed: {detail}")
    return result.stdout


def detect_host(explicit: str) -> str:
    if explicit != "auto":
        return explicit

    script_str = str(Path(__file__).resolve()).lower()
    if "\\.codex\\plugins\\cache\\" in script_str or "/.codex/plugins/cache/" in script_str:
        return "codex"
    if "\\.claude\\plugins\\" in script_str or "/.claude/plugins/" in script_str:
        return "claude"

    env = os.environ
    if env.get("CODEX_HOME") or env.get("CODEX_THREAD_ID"):
        return "codex"
    if env.get("CLAUDE_PROJECT_DIR") or env.get("CLAUDE_CODE_ENTRYPOINT") or env.get("CLAUDE_PLUGIN_ROOT"):
        return "claude"

    raise UpdateRuntimeError("unable to detect current host; rerun with --host claude or --host codex")


def find_workspace_root(start: Path) -> Path:
    current = start.resolve()
    for candidate in [current, *current.parents]:
        if (candidate / "CLAUDE.md").exists() and (candidate / "AGENTS.md").exists():
            return candidate
        if (candidate / "topics").exists() and (candidate / "_scripts").exists():
            return candidate
    return current


def ensure_safe_workspace(workspace: Path) -> None:
    marker_hits = [marker for marker in PLUGIN_MARKERS if (workspace / marker).exists()]
    if len(marker_hits) >= 2:
        raise UpdateRuntimeError(f"refusing to repair plugin repo or plugin install directory: {workspace}")


def github_json(url: str) -> Any:
    req = urllib.request.Request(url, headers={"User-Agent": "buy-side-research-skills-update-agent-runtime"})
    try:
        with urllib.request.urlopen(req) as response:
            return json.load(response)
    except urllib.error.URLError as exc:
        raise UpdateRuntimeError(f"failed to fetch {url}: {exc}") from exc


def resolve_latest_release() -> ReleaseInfo:
    payload = github_json(LATEST_RELEASE_API)
    tag = payload["tag_name"]
    version = tag[1:] if tag.startswith("v") else tag
    expected_asset = f"{PLUGIN_NAME}-{version}.zip"
    for asset in payload.get("assets", []):
        if asset.get("name") == expected_asset:
            return ReleaseInfo(tag=tag, version=version, asset_name=expected_asset, asset_url=asset["browser_download_url"])
    raise UpdateRuntimeError(f"latest release is missing expected asset {expected_asset}")


def download_and_extract_release(release: ReleaseInfo, temp_root: Path) -> Path:
    zip_path = temp_root / release.asset_name
    req = urllib.request.Request(release.asset_url, headers={"User-Agent": "buy-side-research-skills-update-agent-runtime"})
    try:
        with urllib.request.urlopen(req) as response, zip_path.open("wb") as handle:
            shutil.copyfileobj(response, handle)
    except urllib.error.URLError as exc:
        raise UpdateRuntimeError(f"failed to download release asset {release.asset_url}: {exc}") from exc

    extract_root = temp_root / "release"
    extract_root.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(extract_root)
    return extract_root


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def write_text(path: Path, text: str, newline: str) -> None:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    path.write_text(normalized.replace("\n", newline), encoding="utf-8", newline="")


def detect_newline(text: str) -> str:
    return "\r\n" if "\r\n" in text else "\n"


def section_from_heading(text: str, heading: str) -> str | None:
    pattern = re.compile(rf"(?ms)^({re.escape(heading)}\n.*?)(?=^## |\Z)")
    match = pattern.search(text)
    return match.group(1) if match else None


def replace_section(text: str, heading: str, replacement: str) -> tuple[str, bool]:
    pattern = re.compile(rf"(?ms)^{re.escape(heading)}\n.*?(?=^## |\Z)")
    match = pattern.search(text)
    if not match:
        return text, False
    return text[: match.start()] + replacement.rstrip() + "\n\n" + text[match.end() :], True


def patch_claude_md(target: Path, template_path: Path) -> WorkspacePatchResult:
    if not target.exists():
        return WorkspacePatchResult(status="skipped", details=["CLAUDE.md missing after scaffold repair"])

    current = read_text(target)
    template = read_text(template_path)
    newline = detect_newline(current)
    details: list[str] = []
    patched = current

    generation_match = re.search(r"^(- Current system generation: `)([^`]+)(`)$", template, flags=re.MULTILINE)
    if generation_match:
        new_line = "".join(generation_match.groups())
        patched, count = re.subn(
            r"^(- Current system generation: `)([^`]+)(`)$",
            new_line,
            patched,
            flags=re.MULTILINE,
            count=1,
        )
        if count:
            details.append("updated Current system generation")
        else:
            details.append("missing Current system generation anchor")

    missing = []
    for heading in CLAUDE_SECTION_HEADINGS:
        replacement = section_from_heading(template, heading)
        if not replacement:
            missing.append(f"template missing {heading}")
            continue
        patched, replaced = replace_section(patched, heading, replacement)
        if replaced:
            details.append(f"updated {heading}")
        else:
            missing.append(f"missing {heading}")

    if patched != current:
        write_text(target, patched, newline)

    if missing:
        details.extend(missing)
        return WorkspacePatchResult(status="manual_merge_required", details=details)
    return WorkspacePatchResult(status="updated", details=details)


def patch_agents_md(target: Path, template_path: Path) -> WorkspacePatchResult:
    if not target.exists():
        return WorkspacePatchResult(status="skipped", details=["AGENTS.md missing after scaffold repair"])

    current = read_text(target)
    template = read_text(template_path)
    newline = detect_newline(current)

    current_match = re.search(r"(?m)^# .*$", current)
    template_match = re.search(r"(?m)^# .*$", template)
    if not current_match or not template_match:
        return WorkspacePatchResult(
            status="manual_merge_required",
            details=["missing top-level H1 anchor in AGENTS.md"],
        )

    preamble = current[: current_match.start()]
    managed_body = template[template_match.start() :]
    patched = preamble + managed_body
    if patched != current:
        write_text(target, patched, newline)
    return WorkspacePatchResult(status="updated", details=["updated managed AGENTS.md body"])


def resolve_powershell() -> list[str]:
    pwsh = shutil.which("pwsh")
    if pwsh:
        return [pwsh, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File"]
    powershell = shutil.which("powershell")
    if powershell:
        return [powershell, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File"]
    raise UpdateRuntimeError("unable to locate pwsh or powershell for init-workspace repair")


def repair_workspace(release_root: Path, workspace: Path, report: Report) -> None:
    init_script = release_root / "skills" / "init-workspace" / "scripts" / "init-research-workspace.ps1"
    if not init_script.exists():
        raise UpdateRuntimeError(f"packaged init-workspace helper missing: {init_script}")

    cmd = [*resolve_powershell(), str(init_script), "-WorkspacePath", str(workspace)]
    ensure_ok(run_command(cmd), "workspace scaffold repair")
    report.workspace_actions.append("repaired workspace scaffold from latest release package")

    claude_template = release_root / "skills" / "init-workspace" / "assets" / "CLAUDE.md.template"
    agents_template = release_root / "skills" / "init-workspace" / "assets" / "AGENTS.md.template"
    report.claude_md = patch_claude_md(workspace / "CLAUDE.md", claude_template)
    report.agents_md = patch_agents_md(workspace / "AGENTS.md", agents_template)


def resolve_claude_cli() -> str:
    cli = shutil.which("claude")
    if cli:
        return cli
    raise UpdateRuntimeError("claude CLI not found on PATH")


def resolve_codex_cli() -> str:
    env_cli = os.environ.get("CODEX_CLI_PATH")
    if env_cli and Path(env_cli).exists() and run_command([env_cli, "--help"]).returncode == 0:
        return env_cli

    path_cli = shutil.which("codex")
    if path_cli and run_command([path_cli, "--help"]).returncode == 0:
        return path_cli

    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        bin_root = Path(local_app_data) / "OpenAI" / "Codex" / "bin"
        candidates = sorted(bin_root.glob("*/codex.exe"), key=lambda p: p.stat().st_mtime, reverse=True)
        for candidate in candidates:
            if run_command([str(candidate), "--help"]).returncode == 0:
                return str(candidate)

    raise UpdateRuntimeError("unable to locate a working Codex CLI")


def ensure_claude_marketplace(cli: str, report: Report) -> None:
    raw = ensure_ok(run_command([cli, "plugins", "marketplace", "list", "--json"]), "claude plugin marketplace list")
    marketplaces = json.loads(raw)
    if any(item.get("name") == MARKETPLACE_NAME for item in marketplaces):
        return
    ensure_ok(
        run_command([cli, "plugins", "marketplace", "add", REPO_URL, "--scope", "user"]),
        "claude plugin marketplace add",
    )
    report.host_actions.append("added Claude marketplace buy-side-research")


def claude_plugins_list(cli: str) -> list[dict[str, Any]]:
    raw = ensure_ok(run_command([cli, "plugins", "list", "--json"]), "claude plugin list")
    return json.loads(raw)


def update_claude_host(cli: str, release: ReleaseInfo, report: Report) -> None:
    ensure_claude_marketplace(cli, report)
    installed = {item["id"]: item for item in claude_plugins_list(cli)}

    if GITHUB_CLAUDE_PLUGIN_ID in installed:
        ensure_ok(
            run_command([cli, "plugins", "update", GITHUB_CLAUDE_PLUGIN_ID, "-s", "user"]),
            "claude plugin update",
        )
        report.host_actions.append(f"updated {GITHUB_CLAUDE_PLUGIN_ID}")
    else:
        ensure_ok(
            run_command([cli, "plugins", "install", GITHUB_CLAUDE_PLUGIN_ID, "-s", "user"]),
            "claude plugin install",
        )
        report.host_actions.append(f"installed {GITHUB_CLAUDE_PLUGIN_ID}")

    installed = {item["id"]: item for item in claude_plugins_list(cli)}
    github_plugin = installed.get(GITHUB_CLAUDE_PLUGIN_ID)
    if github_plugin and not github_plugin.get("enabled", False):
        ensure_ok(run_command([cli, "plugins", "enable", GITHUB_CLAUDE_PLUGIN_ID, "-s", "user"]), "claude plugin enable")
        report.host_actions.append(f"enabled {GITHUB_CLAUDE_PLUGIN_ID}")

    local_plugin = installed.get(LOCAL_CLAUDE_PLUGIN_ID)
    if local_plugin:
        if local_plugin.get("enabled", False):
            ensure_ok(run_command([cli, "plugins", "disable", LOCAL_CLAUDE_PLUGIN_ID, "-s", "user"]), "claude plugin disable")
            report.host_actions.append(f"disabled {LOCAL_CLAUDE_PLUGIN_ID}")
        ensure_ok(run_command([cli, "plugins", "uninstall", LOCAL_CLAUDE_PLUGIN_ID, "-s", "user", "-y"]), "claude plugin uninstall")
        report.host_actions.append(f"uninstalled {LOCAL_CLAUDE_PLUGIN_ID}")

    final_plugins = {item["id"]: item for item in claude_plugins_list(cli)}
    github_plugin = final_plugins.get(GITHUB_CLAUDE_PLUGIN_ID)
    if not github_plugin:
        raise UpdateRuntimeError(f"{GITHUB_CLAUDE_PLUGIN_ID} is not installed after Claude update")
    if str(github_plugin.get("version")) != release.version:
        raise UpdateRuntimeError(
            f"Claude plugin version mismatch: expected {release.version}, got {github_plugin.get('version')}"
        )
    if LOCAL_CLAUDE_PLUGIN_ID in final_plugins:
        raise UpdateRuntimeError(f"{LOCAL_CLAUDE_PLUGIN_ID} is still installed after channel normalization")

    report.host_actions.append(f"verified Claude host at {release.version}")


def codex_home() -> Path:
    return Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))).expanduser()


def codex_config_text() -> str:
    config_path = codex_home() / "config.toml"
    if not config_path.exists():
        raise UpdateRuntimeError(f"Codex config.toml not found: {config_path}")
    return read_text(config_path)


def codex_has_marketplace(config_text: str) -> bool:
    return f"[marketplaces.{MARKETPLACE_NAME}]" in config_text


def codex_plugin_enabled(config_text: str) -> bool:
    header = f'[plugins."{PLUGIN_NAME}@{MARKETPLACE_NAME}"]'
    if header not in config_text:
        return False
    section = config_text.split(header, 1)[1]
    section = section.split("\n[", 1)[0]
    return "enabled = true" in section


def update_codex_host(cli: str, release: ReleaseInfo, report: Report) -> None:
    config_text = codex_config_text()
    if not codex_has_marketplace(config_text):
        ensure_ok(run_command([cli, "plugin", "marketplace", "add", REPO_URL]), "codex plugin marketplace add")
        report.host_actions.append("added Codex marketplace buy-side-research")

    ensure_ok(run_command([cli, "plugin", "marketplace", "upgrade", MARKETPLACE_NAME]), "codex plugin marketplace upgrade")
    report.host_actions.append("upgraded Codex marketplace snapshot")

    ensure_ok(run_command([cli, "plugin", "add", f"{PLUGIN_NAME}@{MARKETPLACE_NAME}"]), "codex plugin add")
    report.host_actions.append(f"added/refreshed {PLUGIN_NAME}@{MARKETPLACE_NAME}")

    final_config = codex_config_text()
    if not codex_has_marketplace(final_config):
        raise UpdateRuntimeError("Codex marketplace buy-side-research missing after update")
    if not codex_plugin_enabled(final_config):
        raise UpdateRuntimeError(f"{PLUGIN_NAME}@{MARKETPLACE_NAME} is not enabled in Codex config after update")

    cache_dir = codex_home() / "plugins" / "cache" / MARKETPLACE_NAME / PLUGIN_NAME / release.version
    if not cache_dir.exists():
        raise UpdateRuntimeError(f"Codex cache directory missing after update: {cache_dir}")

    required = [cache_dir / ".claude-plugin" / "plugin.json", cache_dir / ".codex-plugin" / "plugin.json", cache_dir / "skills"]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise UpdateRuntimeError(f"Codex cache is incomplete after update: {missing}")

    report.host_actions.append(f"verified Codex host at {release.version}")


def main() -> int:
    args = parse_args()
    host = detect_host(args.host)
    workspace = find_workspace_root(Path(args.workspace).expanduser() if args.workspace else Path.cwd())
    ensure_safe_workspace(workspace)
    release = resolve_latest_release()
    report = Report(host=host, latest_version=release.version, workspace=str(workspace))

    if host == "claude":
        update_claude_host(resolve_claude_cli(), release, report)
    elif host == "codex":
        update_codex_host(resolve_codex_cli(), release, report)
    else:
        raise UpdateRuntimeError(f"unsupported host: {host}")

    with tempfile.TemporaryDirectory(prefix="buy-side-research-skills-") as temp_dir:
        release_root = download_and_extract_release(release, Path(temp_dir))
        repair_workspace(release_root, workspace, report)

    print(
        json.dumps(
            {
                "host": report.host,
                "latest_version": report.latest_version,
                "workspace": report.workspace,
                "host_actions": report.host_actions,
                "workspace_actions": report.workspace_actions,
                "warnings": report.warnings,
                "claude_md": None if report.claude_md is None else {"status": report.claude_md.status, "details": report.claude_md.details},
                "agents_md": None if report.agents_md is None else {"status": report.agents_md.status, "details": report.agents_md.details},
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except UpdateRuntimeError as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False, indent=2), file=sys.stderr)
        sys.exit(1)
