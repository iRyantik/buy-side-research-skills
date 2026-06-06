"""Source Intake Router and lifecycle owner."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from .converters import ConversionError, convert_source


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_route(value: str | None, name: str) -> str | None:
    if value is None:
        return None
    normalized = value.replace("\\", "/").strip("/")
    path = Path(normalized)
    if not normalized or path.is_absolute() or ".." in path.parts:
        raise ValueError(f"{name} must be a safe relative route")
    return path.as_posix()


def _atomic_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", delete=False, dir=path.parent, suffix=".tmp"
    ) as handle:
        handle.write(text)
        temporary = Path(handle.name)
    os.replace(temporary, path)


@dataclass(frozen=True)
class IntakeRequest:
    source: Path
    topic: str | None = None
    category: str | None = None
    source_url: str | None = None
    reproducible: bool = False


@dataclass(frozen=True)
class IntakeResult:
    status: str
    job_id: str
    source_id: str
    original_path: str
    raw_path: str
    cache_path: str
    manifest_path: str


class SourceIntake:
    """Register, convert, validate, and publish local research sources."""

    def __init__(self, workspace: Path):
        self.workspace = Path(workspace).resolve()
        self.jobs_dir = self.workspace / ".research-runtime" / "state" / "source-intake" / "jobs"

    def _source_id(self, path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def _result_from_manifest(self, manifest_path: Path, status: str) -> IntakeResult:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        return IntakeResult(
            status=status,
            job_id=manifest["job_id"],
            source_id=manifest["source_id"],
            original_path=manifest["original_path"],
            raw_path=manifest["raw_path"],
            cache_path=manifest["cache_path"],
            manifest_path=str(manifest_path),
        )

    def _save_job(self, payload: dict) -> None:
        _atomic_text(
            self.jobs_dir / f"{payload['job_id']}.json",
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        )

    def enqueue(
        self, source: Path, source_url: str | None = None, topic: str | None = None, category: str | None = None
    ) -> dict:
        source = Path(source).expanduser().resolve()
        if not source.is_file():
            raise FileNotFoundError(source)
        queue_dir = self.workspace / ".research-runtime" / "state" / "source-intake" / "queue"
        queue_id = hashlib.sha256(
            f"{source}:{source.stat().st_mtime_ns}:{source.stat().st_size}".encode("utf-8")
        ).hexdigest()[:16]
        payload = {
            "queue_id": queue_id,
            "status": "queued",
            "source": str(source),
            "source_url": source_url,
            "topic": topic,
            "category": category,
            "queued_at_utc": _utc_now(),
        }
        _atomic_text(queue_dir / f"{queue_id}.json", json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
        return payload

    def queued(self) -> list[dict]:
        queue_dir = self.workspace / ".research-runtime" / "state" / "source-intake" / "queue"
        if not queue_dir.exists():
            return []
        return [
            json.loads(path.read_text(encoding="utf-8"))
            for path in sorted(queue_dir.glob("*.json"))
        ]

    def add(self, request: IntakeRequest) -> IntakeResult:
        source = Path(request.source).expanduser().resolve()
        if not source.is_file():
            raise FileNotFoundError(source)
        topic = _safe_route(request.topic, "topic")
        category = _safe_route(request.category, "category")
        source_id = self._source_id(source)
        job_id = source_id[:16]

        try:
            converted = convert_source(source)
            if not converted.markdown.strip():
                raise ConversionError("conversion produced empty Markdown")
        except Exception as exc:
            return self._quarantine(request, source, source_id, job_id, "", str(exc))

        if not topic or not category:
            return self._quarantine(
                request, source, source_id, job_id, converted.markdown, "route_requires_confirmation"
            )

        topic_root = self.workspace / topic
        raw_path = topic_root / "_raw" / category / source_id / f"original{source.suffix.lower()}"
        cache_path = topic_root / "_cache" / category / source_id / "document.md"
        manifest_path = topic_root / "_cache" / category / source_id / "source-manifest.json"
        if manifest_path.exists():
            return self._result_from_manifest(manifest_path, "duplicate")

        raw_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, raw_path)
        _atomic_text(cache_path, converted.markdown)
        payload = {
            "schema_version": 1,
            "status": "published",
            "job_id": job_id,
            "source_id": source_id,
            "content_sha256": source_id,
            "original_path": str(source),
            "raw_path": str(raw_path),
            "cache_path": str(cache_path),
            "topic": topic,
            "category": category,
            "source_url": request.source_url,
            "reproducible": request.reproducible,
            "converter": converted.converter,
            "warnings": list(converted.warnings),
            "route": {"topic": topic, "category": category, "confidence": "explicit"},
            "published_at_utc": _utc_now(),
        }
        _atomic_text(manifest_path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
        self._save_job(payload)
        if request.reproducible and request.source_url:
            source.unlink()
        return self._result_from_manifest(manifest_path, "published")

    def _quarantine(
        self,
        request: IntakeRequest,
        source: Path,
        source_id: str,
        job_id: str,
        markdown: str,
        reason: str,
    ) -> IntakeResult:
        root = self.workspace / "_inbox" / "_quarantine" / job_id
        raw_path = root / f"original{source.suffix.lower()}"
        cache_path = root / "candidate.md"
        manifest_path = root / "job.json"
        root.mkdir(parents=True, exist_ok=True)
        if not raw_path.exists():
            shutil.copy2(source, raw_path)
        if markdown:
            _atomic_text(cache_path, markdown)
        payload = {
            "schema_version": 1,
            "status": "quarantined",
            "reason": reason,
            "job_id": job_id,
            "source_id": source_id,
            "content_sha256": source_id,
            "original_path": str(source),
            "raw_path": str(raw_path),
            "cache_path": str(cache_path),
            "source_url": request.source_url,
            "reproducible": request.reproducible,
            "route_candidates": {"topic": request.topic, "category": request.category},
            "created_at_utc": _utc_now(),
        }
        _atomic_text(manifest_path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
        self._save_job(payload)
        return self._result_from_manifest(manifest_path, "quarantined")

    def scan(self, path: Path, recursive: bool = False) -> list[IntakeResult]:
        root = Path(path).expanduser().resolve()
        iterator = root.rglob("*") if recursive else root.glob("*")
        return [
            self.add(IntakeRequest(source=source))
            for source in iterator
            if source.is_file() and "_quarantine" not in source.parts
        ]

    def publish(self, job_id: str, topic: str, category: str) -> IntakeResult:
        job_path = self.jobs_dir / f"{job_id}.json"
        job = json.loads(job_path.read_text(encoding="utf-8"))
        return self.add(
            IntakeRequest(
                source=Path(job["raw_path"]),
                topic=topic,
                category=category,
                source_url=job.get("source_url"),
                reproducible=False,
            )
        )

    def status(self, job_id: str | None = None) -> list[dict] | dict:
        if job_id:
            return json.loads((self.jobs_dir / f"{job_id}.json").read_text(encoding="utf-8"))
        if not self.jobs_dir.exists():
            return []
        return [
            json.loads(path.read_text(encoding="utf-8"))
            for path in sorted(self.jobs_dir.glob("*.json"))
        ]
