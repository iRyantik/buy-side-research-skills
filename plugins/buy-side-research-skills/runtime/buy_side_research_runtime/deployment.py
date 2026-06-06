"""Manifest-driven, transactional workspace deployment."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
import zipfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


FORBIDDEN_PARTS = {"__pycache__", "_tmp", "tests", "fixtures", ".pytest_cache"}
FORBIDDEN_SUFFIXES = {".pyc", ".pdf", ".db"}
RELEASE_ALLOWED_TOP_LEVEL = {
    ".claude-plugin",
    ".codex-plugin",
    "skills",
    "runtime",
    "README.md",
    "release-manifest.json",
    "payload-pollution-report.json",
    "hashes.sha256",
}


class ManifestError(ValueError):
    """Raised when a managed-assets manifest is unsafe or invalid."""


@dataclass(frozen=True)
class PlanItem:
    target: str
    source: str | None = None
    reason: str = ""


@dataclass
class DeploymentPlan:
    add: list[PlanItem] = field(default_factory=list)
    update: list[PlanItem] = field(default_factory=list)
    keep: list[PlanItem] = field(default_factory=list)
    remove: list[PlanItem] = field(default_factory=list)
    conflict: list[PlanItem] = field(default_factory=list)

    def as_dict(self) -> dict[str, list[dict[str, str | None]]]:
        return {
            name: [item.__dict__ for item in getattr(self, name)]
            for name in ("add", "update", "keep", "remove", "conflict")
        }


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_relative(value: str, field_name: str) -> Path:
    path = Path(value.replace("\\", "/"))
    if path.is_absolute() or ".." in path.parts:
        raise ManifestError(f"{field_name} must be a safe relative path: {value}")
    return path


def discover_runtime_source(
    start: Path | None = None, runtime_root: Path | None = None
) -> tuple[Path, Path]:
    """Find the explicit runtime payload and manifest without scanning payload contents."""
    candidates: list[Path] = []
    if runtime_root:
        candidates.append(Path(runtime_root))
    configured = os.environ.get("BUY_SIDE_RESEARCH_RUNTIME_ROOT")
    if configured:
        candidates.append(Path(configured))
    origin = Path(start or __file__).resolve()
    candidates.extend([origin, *origin.parents])
    home = Path.home()
    for host in (home / ".codex" / "plugins" / "cache", home / ".claude" / "plugins" / "cache"):
        if host.exists():
            candidates.extend(sorted(host.glob("buy-side-research-skills/**/runtime"), reverse=True))
    seen: set[Path] = set()
    for candidate in candidates:
        candidate = candidate.resolve()
        if candidate in seen:
            continue
        seen.add(candidate)
        manifest = candidate / "managed-assets.json"
        if manifest.is_file():
            return candidate, manifest.resolve()
        nested = candidate / "runtime" / "managed-assets.json"
        if nested.is_file():
            return nested.parent.resolve(), nested.resolve()
        installed = candidate / ".research-runtime" / "installed-manifest.json"
        if installed.is_file():
            try:
                source = json.loads(installed.read_text(encoding="utf-8")).get("source", {})
                payload = Path(source.get("payload_root", ""))
                source_manifest = Path(source.get("manifest", ""))
                if payload.is_dir() and source_manifest.is_file():
                    return payload.resolve(), source_manifest.resolve()
            except (OSError, json.JSONDecodeError):
                pass
    raise ManifestError(
        "cannot discover runtime payload; pass --runtime-root or set BUY_SIDE_RESEARCH_RUNTIME_ROOT"
    )


def verify_workspace(workspace: Path) -> dict[str, Any]:
    """Verify installed managed assets without changing the workspace."""
    workspace = Path(workspace).resolve()
    installed_path = workspace / ".research-runtime" / "installed-manifest.json"
    if not installed_path.is_file():
        return {"status": "missing", "manifest": str(installed_path), "missing": [], "modified": []}
    try:
        installed = json.loads(installed_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "status": "failed",
            "manifest": str(installed_path),
            "missing": [],
            "modified": [],
            "error": str(exc),
        }
    missing: list[str] = []
    modified: list[str] = []
    for asset in installed.get("assets", []):
        if not isinstance(asset, dict) or not asset.get("target"):
            continue
        target_name = str(asset["target"])
        target = workspace / target_name
        if not target.is_file():
            missing.append(target_name)
        elif asset.get("sha256") != sha256_file(target):
            modified.append(target_name)
    return {
        "status": "ok" if not missing and not modified else "failed",
        "manifest": str(installed_path),
        "runtime_version": installed.get("runtime_version", "unknown"),
        "missing": sorted(missing),
        "modified": sorted(modified),
    }


class DeploymentManager:
    """Plan and apply explicit managed asset changes."""

    def __init__(self, payload_root: Path, workspace: Path, manifest_path: Path):
        self.payload_root = Path(payload_root).resolve()
        self.workspace = Path(workspace).resolve()
        self.manifest_path = Path(manifest_path).resolve()
        self.state_dir = self.workspace / ".research-runtime"
        self.installed_path = self.state_dir / "installed-manifest.json"
        self.manifest = self._load_manifest()
        self.assets = self._validate_assets(self.manifest.get("assets"))

    def _load_manifest(self) -> dict[str, Any]:
        try:
            return json.loads(self.manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ManifestError(f"cannot read manifest: {exc}") from exc

    def _validate_assets(self, assets: Any) -> list[dict[str, str]]:
        if not isinstance(assets, list):
            raise ManifestError("manifest assets must be a list")
        validated: list[dict[str, str]] = []
        seen_targets: set[str] = set()
        for raw in assets:
            if not isinstance(raw, dict) or "source" not in raw or "target" not in raw:
                raise ManifestError("each asset requires source and target")
            source = _safe_relative(str(raw["source"]), "source")
            target = _safe_relative(str(raw["target"]), "target")
            normalized_source = source.as_posix()
            normalized_target = target.as_posix()
            if any(part in FORBIDDEN_PARTS for part in source.parts):
                raise ManifestError(f"forbidden payload directory: {normalized_source}")
            if source.suffix.lower() in FORBIDDEN_SUFFIXES:
                raise ManifestError(f"forbidden payload file: {normalized_source}")
            if normalized_target in seen_targets:
                raise ManifestError(f"duplicate target: {normalized_target}")
            source_path = (self.payload_root / source).resolve()
            if self.payload_root not in source_path.parents or not source_path.is_file():
                raise ManifestError(f"missing or unsafe source: {normalized_source}")
            seen_targets.add(normalized_target)
            validated.append(
                {
                    "source": normalized_source,
                    "target": normalized_target,
                    "strategy": str(raw.get("strategy", "overwrite")),
                    "owner": str(raw.get("owner", "runtime")),
                }
            )
        return validated

    def _installed(self) -> dict[str, Any]:
        if not self.installed_path.exists():
            return {"assets": []}
        try:
            return json.loads(self.installed_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ManifestError(f"cannot read installed manifest: {exc}") from exc

    def _write_installed(self, assets: list[dict[str, Any]]) -> None:
        self.state_dir.mkdir(parents=True, exist_ok=True)
        payload = {
            "runtime_version": self.manifest.get("runtime_version", "unknown"),
            "installed_at_utc": _utc_now(),
            "source": {
                "payload_root": str(self.payload_root),
                "manifest": str(self.manifest_path),
            },
            "assets": assets,
        }
        temporary = self.installed_path.with_suffix(".json.tmp")
        temporary.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        temporary.replace(self.installed_path)

    def plan(self) -> DeploymentPlan:
        result = DeploymentPlan()
        installed = {
            item["target"]: item
            for item in self._installed().get("assets", [])
            if isinstance(item, dict) and item.get("target")
        }
        current_targets: set[str] = set()

        for asset in self.assets:
            target_name = asset["target"]
            current_targets.add(target_name)
            source_path = self.payload_root / asset["source"]
            target_path = self.workspace / target_name
            item = PlanItem(target=target_name, source=asset["source"])
            if not target_path.exists():
                result.add.append(item)
                continue
            if sha256_file(source_path) == sha256_file(target_path):
                result.keep.append(item)
                continue
            prior = installed.get(target_name)
            if prior and prior.get("sha256") == sha256_file(target_path):
                result.update.append(item)
            elif asset["strategy"] == "overwrite" and not prior:
                result.conflict.append(
                    PlanItem(target=target_name, source=asset["source"], reason="unmanaged target exists")
                )
            else:
                result.conflict.append(
                    PlanItem(target=target_name, source=asset["source"], reason="managed target modified")
                )

        for target_name, prior in installed.items():
            if target_name in current_targets:
                continue
            target_path = self.workspace / target_name
            if not target_path.exists():
                continue
            if prior.get("sha256") == sha256_file(target_path):
                result.remove.append(PlanItem(target=target_name, reason="stale managed asset"))
            else:
                result.conflict.append(PlanItem(target=target_name, reason="stale asset modified by user"))
        return result

    def verify_installed(self) -> dict[str, Any]:
        return verify_workspace(self.workspace)

    def adopt_conflicts(self, targets: list[str], dry_run: bool = False) -> dict[str, Any]:
        """Explicitly mark conflict targets as plugin-managed without overwriting them."""
        if not targets:
            raise ManifestError("adopt requires one or more explicit --target values")
        asset_by_target = {asset["target"]: asset for asset in self.assets}
        plan = self.plan()
        conflict_targets = {item.target for item in plan.conflict}
        normalized: list[str] = []
        for raw_target in targets:
            target = _safe_relative(raw_target, "target").as_posix()
            if target not in asset_by_target:
                raise ManifestError(f"cannot adopt unmanaged target: {target}")
            if target not in conflict_targets:
                raise ManifestError(f"target is not an active conflict: {target}")
            if not (self.workspace / target).is_file():
                raise ManifestError(f"cannot adopt missing target: {target}")
            normalized.append(target)

        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        backup_root = self.state_dir / "backups" / f"adopt-{stamp}"
        adopted: list[dict[str, Any]] = []
        if not dry_run:
            backup_root.mkdir(parents=True, exist_ok=True)

        installed = {
            item["target"]: item
            for item in self._installed().get("assets", [])
            if isinstance(item, dict) and item.get("target")
        }
        for target_name in normalized:
            target = self.workspace / target_name
            backup = backup_root / target_name
            file_hash = sha256_file(target)
            if not dry_run:
                backup.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(target, backup)
                installed[target_name] = {
                    **asset_by_target[target_name],
                    "sha256": file_hash,
                    "adopted_at_utc": _utc_now(),
                    "adopted_from": "workspace-conflict",
                }
            adopted.append(
                {
                    "target": target_name,
                    "sha256": file_hash,
                    "backup": str(backup),
                }
            )
        if not dry_run:
            self._write_installed(list(installed.values()))
        return {
            "status": "dry-run" if dry_run else "ok",
            "adopted": adopted,
            "backup_root": str(backup_root),
        }

    def apply(self, plan: DeploymentPlan) -> None:
        """Apply a plan atomically enough to restore all touched files on failure."""
        self.state_dir.mkdir(parents=True, exist_ok=True)
        stage = Path(tempfile.mkdtemp(prefix="deploy-stage-", dir=self.state_dir))
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        backup = self.state_dir / "backups" / stamp
        touched = plan.add + plan.update + plan.remove
        try:
            for item in plan.add + plan.update:
                staged = stage / item.target
                staged.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(self.payload_root / str(item.source), staged)

            for item in touched:
                target = self.workspace / item.target
                if target.exists():
                    destination = backup / item.target
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(target, destination)

            for item in plan.add + plan.update:
                target = self.workspace / item.target
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(stage / item.target, target)
            for item in plan.remove:
                target = self.workspace / item.target
                if target.exists():
                    target.unlink()

            installed_assets = []
            accepted_targets = {
                item.target for item in plan.add + plan.update + plan.keep
            }
            previous = {
                item["target"]: item
                for item in self._installed().get("assets", [])
                if isinstance(item, dict) and item.get("target")
            }
            for asset in self.assets:
                target = self.workspace / asset["target"]
                if asset["target"] not in accepted_targets or not target.exists():
                    prior = previous.get(asset["target"])
                    if prior and any(item.target == asset["target"] for item in plan.conflict):
                        installed_assets.append(prior)
                    continue
                installed_assets.append(
                    {
                        **asset,
                        "sha256": sha256_file(target),
                    }
                )
            self._write_installed(installed_assets)
        except Exception:
            for item in touched:
                target = self.workspace / item.target
                backed_up = backup / item.target
                if backed_up.exists():
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(backed_up, target)
                elif target.exists():
                    target.unlink()
            raise
        finally:
            shutil.rmtree(stage, ignore_errors=True)


def _copy_release_tree(source: Path, destination: Path) -> None:
    def ignore(directory: str, names: list[str]) -> set[str]:
        ignored: set[str] = set()
        for name in names:
            path = Path(directory) / name
            parts = set(path.parts)
            suffix = path.suffix.lower()
            if name in FORBIDDEN_PARTS or parts & FORBIDDEN_PARTS or suffix in FORBIDDEN_SUFFIXES:
                ignored.add(name)
        return ignored

    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(source, destination, ignore=ignore)


def _patch_release_version(release_root: Path, version: str) -> None:
    manifest = release_root / "runtime" / "managed-assets.json"
    if manifest.is_file():
        data = json.loads(manifest.read_text(encoding="utf-8"))
        data["runtime_version"] = version
        manifest.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    init_file = release_root / "runtime" / "buy_side_research_runtime" / "__init__.py"
    if init_file.is_file():
        init_file.write_text(
            '"""Managed runtime for buy-side-research-skills workspaces."""\n\n'
            f'__version__ = "{version}"\n',
            encoding="utf-8",
        )


def verify_release_payload(release_root: Path) -> dict[str, Any]:
    """Verify a packaged release payload without changing it."""
    release_root = Path(release_root).resolve()
    violations: list[str] = []
    required = {".claude-plugin", ".codex-plugin", "skills", "runtime", "README.md"}
    if not release_root.is_dir():
        return {"status": "failed", "release_root": str(release_root), "violations": ["missing release root"]}
    for name in required:
        if not (release_root / name).exists():
            violations.append(f"missing required payload entry: {name}")
    for child in release_root.iterdir():
        if child.name not in RELEASE_ALLOWED_TOP_LEVEL:
            violations.append(f"unexpected top-level payload entry: {child.name}")
    for path in release_root.rglob("*"):
        relative_path = path.relative_to(release_root)
        relative = relative_path.as_posix()
        if any(part in FORBIDDEN_PARTS for part in relative_path.parts):
            violations.append(f"forbidden payload directory: {relative}")
        if path.is_file() and path.suffix.lower() in FORBIDDEN_SUFFIXES:
            violations.append(f"forbidden payload file: {relative}")
    manifest = release_root / "runtime" / "managed-assets.json"
    if not manifest.is_file():
        violations.append("missing runtime/managed-assets.json")
    else:
        try:
            DeploymentManager(release_root / "runtime", release_root, manifest)
        except ManifestError as exc:
            violations.append(f"managed-assets invalid: {exc}")
    return {
        "status": "ok" if not violations else "failed",
        "release_root": str(release_root),
        "violations": sorted(set(violations)),
    }


def build_release_payload(plugin_root: Path, version: str = "6.0.0-rc.2", dist_root: Path | None = None) -> dict[str, Any]:
    """Build a packaged release payload from the plugin dev repo."""
    plugin_root = Path(plugin_root).resolve()
    dist_root = Path(dist_root or plugin_root / "_dist" / "buy-side-research-skills").resolve()
    release_root = dist_root / version
    release_root.parent.mkdir(parents=True, exist_ok=True)
    if release_root.exists():
        shutil.rmtree(release_root)
    release_root.mkdir(parents=True)

    for name in (".claude-plugin", ".codex-plugin", "skills", "runtime"):
        source = plugin_root / name
        if not source.exists():
            raise ManifestError(f"missing release source: {name}")
        _copy_release_tree(source, release_root / name)
    readme_candidates = [plugin_root / "README.md"]
    if len(plugin_root.parents) > 1:
        readme_candidates.append(plugin_root.parents[1] / "README.md")
    readme = next((candidate for candidate in readme_candidates if candidate.is_file()), None)
    if readme is not None:
        shutil.copy2(readme, release_root / "README.md")
    else:
        (release_root / "README.md").write_text(
            f"# buy-side-research-skills {version}\n", encoding="utf-8"
        )
    _patch_release_version(release_root, version)
    pollution = verify_release_payload(release_root)
    (release_root / "payload-pollution-report.json").write_text(
        json.dumps(pollution, indent=2) + "\n", encoding="utf-8"
    )

    hashes: list[str] = []
    files: list[dict[str, str]] = []
    for path in sorted(p for p in release_root.rglob("*") if p.is_file()):
        relative = path.relative_to(release_root).as_posix()
        digest = sha256_file(path)
        hashes.append(f"{digest}  {relative}")
        files.append({"path": relative, "sha256": digest})
    (release_root / "hashes.sha256").write_text("\n".join(hashes) + "\n", encoding="utf-8")
    release_manifest = {
        "name": "buy-side-research-skills",
        "version": version,
        "built_at_utc": _utc_now(),
        "files": files,
        "pollution_status": pollution["status"],
    }
    (release_root / "release-manifest.json").write_text(
        json.dumps(release_manifest, indent=2) + "\n", encoding="utf-8"
    )

    zip_path = dist_root / f"{version}.zip"
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(p for p in release_root.rglob("*") if p.is_file()):
            archive.write(path, path.relative_to(release_root).as_posix())
    final_report = verify_release_payload(release_root)
    return {
        "status": final_report["status"],
        "version": version,
        "release_root": str(release_root),
        "zip": str(zip_path),
        "violations": final_report["violations"],
    }


def _release_version(release_root: Path) -> str:
    manifest = release_root / "runtime" / "managed-assets.json"
    if manifest.is_file():
        try:
            return str(json.loads(manifest.read_text(encoding="utf-8")).get("runtime_version", "unknown"))
        except json.JSONDecodeError:
            pass
    return "unknown"


def _copy_release_payload(release_root: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        shutil.rmtree(target)
    _copy_release_tree(release_root, target)


def _update_claude_installed(path: Path, target_dir: Path, version: str) -> None:
    now = _utc_now()
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
    else:
        data = {"version": 2, "plugins": {}}
    plugins = data.setdefault("plugins", {})
    entries = plugins.setdefault("buy-side-research-skills@buy-side-research-skills", [{}])
    if not entries:
        entries.append({})
    entry = entries[0]
    entry.setdefault("scope", "user")
    entry.setdefault("installedAt", now)
    entry["installPath"] = str(target_dir)
    entry["version"] = version
    entry["lastUpdated"] = now
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _update_agents_marketplace(path: Path, codex_version_dir: Path, version: str) -> None:
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
    else:
        data = {"name": "local", "plugins": []}
    plugins = data.setdefault("plugins", [])
    target = None
    for plugin in plugins:
        if plugin.get("name") == "buy-side-research-skills":
            target = plugin
            break
    if target is None:
        target = {
            "name": "buy-side-research-skills",
            "source": {"source": "local"},
            "policy": {"installation": "INSTALLED_BY_DEFAULT", "authentication": "ON_INSTALL"},
            "category": "Finance",
        }
        plugins.append(target)
    target.setdefault("source", {})["source"] = "local"
    target["source"]["path"] = f"./.codex/plugins/cache/buy-side-research-skills/buy-side-research-skills/{version}"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def sync_hosts(release_root: Path, home: Path | None = None, dry_run: bool = False) -> dict[str, Any]:
    """Sync a packaged release payload into installed Claude/Codex host caches."""
    release_root = Path(release_root).resolve()
    release_report = verify_release_payload(release_root)
    if release_report["status"] != "ok":
        return {"status": "failed", "source": str(release_root), "violations": release_report["violations"]}
    home = Path(home or Path.home()).resolve()
    version = _release_version(release_root)
    claude_cache = home / ".claude" / "plugins" / "cache" / "buy-side-research-skills"
    codex_cache = home / ".codex" / "plugins" / "cache" / "buy-side-research-skills"
    claude_version_dir = claude_cache / "buy-side-research-skills" / version
    codex_version_dir = codex_cache / "buy-side-research-skills" / version
    report: dict[str, Any] = {
        "status": "dry-run" if dry_run else "ok",
        "version": version,
        "source": str(release_root),
        "hosts": {},
        "restart_required": not dry_run,
    }

    if claude_cache.exists():
        report["hosts"]["claude"] = {"status": "would-update" if dry_run else "updated", "path": str(claude_version_dir)}
        if not dry_run:
            _copy_release_payload(release_root, claude_version_dir)
            _update_claude_installed(home / ".claude" / "plugins" / "installed_plugins.json", claude_version_dir, version)
    else:
        report["hosts"]["claude"] = {"status": "not-installed"}

    if codex_cache.exists():
        report["hosts"]["codex"] = {"status": "would-update" if dry_run else "updated", "path": str(codex_version_dir)}
        if not dry_run:
            _copy_release_payload(release_root, codex_version_dir)
            flat_skills = codex_cache / "skills"
            if flat_skills.exists():
                shutil.rmtree(flat_skills)
            shutil.copytree(release_root / "skills", flat_skills)
            for hidden in (".codex-plugin", ".claude-plugin"):
                destination = codex_cache / hidden
                if destination.exists():
                    shutil.rmtree(destination)
                shutil.copytree(release_root / hidden, destination)
    else:
        report["hosts"]["codex"] = {"status": "not-installed"}

    agents_marketplace = home / ".agents" / "plugins" / "marketplace.json"
    if codex_cache.exists() or agents_marketplace.exists():
        report["hosts"]["agents_marketplace"] = {
            "status": "would-update" if dry_run else "updated",
            "path": str(agents_marketplace),
        }
        if not dry_run:
            _update_agents_marketplace(agents_marketplace, codex_version_dir, version)
    else:
        report["hosts"]["agents_marketplace"] = {"status": "skipped"}
    return report
