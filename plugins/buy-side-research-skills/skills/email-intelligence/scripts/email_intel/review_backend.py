"""Selectable agent-backed review providers.

Codex is the default and is deliberately restricted to ChatGPT authentication so a
scheduled email review cannot silently fall back to API billing.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path


class ReviewBackendError(RuntimeError):
    pass


def backend_name() -> str:
    return os.environ.get("EMAIL_INTELLIGENCE_REVIEW_BACKEND", "codex").strip().lower()


class CodexBackend:
    def __init__(self, model: str | None = None):
        self.model = model or os.environ.get("EMAIL_INTELLIGENCE_CODEX_MODEL", "gpt-5.6-terra")
        self._auth_checked = False

    def check_auth(self) -> None:
        if not shutil.which("codex"):
            raise ReviewBackendError("Codex CLI 未安装")
        result = subprocess.run(["codex", "login", "status"], capture_output=True, text=True, timeout=30)
        status = (result.stdout or "") + (result.stderr or "")
        if result.returncode != 0 or "using ChatGPT" not in status:
            raise ReviewBackendError("Codex 必须使用 ChatGPT 登录；已拒绝 API key 计费模式")
        self._auth_checked = True

    def complete(self, prompt: str, workspace: Path, *, schema: dict | None = None,
                 timeout: int = 600, images: list[str] | None = None) -> str:
        if not self._auth_checked:
            self.check_auth()
        with tempfile.TemporaryDirectory(prefix="email-intel-codex-") as temp_dir:
            temp = Path(temp_dir)
            output = temp / "result.json"
            command = ["codex", "exec", "-", "--ephemeral", "--sandbox", "read-only",
                       "--skip-git-repo-check", "--ignore-user-config", "--ignore-rules",
                       "--model", self.model, "--cd", str(workspace), "-o", str(output)]
            if schema:
                schema_path = temp / "schema.json"
                schema_path.write_text(json.dumps(schema, ensure_ascii=False), encoding="utf-8")
                command.extend(["--output-schema", str(schema_path)])
            for image in images or []:
                command.extend(["-i", str(image)])
            result = subprocess.run(command, input=prompt, capture_output=True, text=True,
                                    encoding="utf-8", errors="replace", timeout=timeout)
            if result.returncode != 0:
                tail = ((result.stderr or result.stdout or "")[-1200:]).strip()
                raise ReviewBackendError(f"Codex review failed: {tail}")
            text = output.read_text(encoding="utf-8") if output.exists() else result.stdout
            if not text.strip():
                raise ReviewBackendError("Codex returned an empty review")
            return text.strip()


class ClaudeBackend:
    def complete(self, prompt: str, workspace: Path, *, schema: dict | None = None,
                 timeout: int = 600, images: list[str] | None = None) -> str:
        if not shutil.which("claude"):
            raise ReviewBackendError("Claude Code 未安装；安装并完成订阅登录后才能启用")
        result = subprocess.run(["claude", "-p", "--output-format", "text", prompt], cwd=workspace,
                                capture_output=True, text=True, encoding="utf-8", errors="replace",
                                timeout=timeout)
        if result.returncode != 0:
            raise ReviewBackendError(f"Claude Code review failed: {(result.stderr or '')[-1200:]}")
        return result.stdout.strip()


class ExternalBackend:
    def complete(self, prompt: str, workspace: Path, *, schema: dict | None = None,
                 timeout: int = 600, images: list[str] | None = None) -> str:
        from .ai_review import _shared_dir
        import sys
        sys.path.insert(0, _shared_dir())
        from llm import chat
        result = chat(prompt, workspace, max_tokens=32_000, timeout=timeout)
        if not result:
            raise ReviewBackendError("External LLM returned an empty review")
        return result


def get_backend():
    name = backend_name()
    if name == "codex":
        return CodexBackend()
    if name == "claude":
        return ClaudeBackend()
    if name == "external":
        return ExternalBackend()
    raise ReviewBackendError(f"Unsupported review backend: {name}")


class ReviewSession:
    """Small provider-neutral conversation wrapper used by grouped extraction."""
    def __init__(self, backend, workspace: Path, system: str | None = None):
        self.backend = backend
        self.workspace = workspace
        self.system = system or ""
        self.calls = 0
        self.elapsed = 0.0

    def turn(self, prompt: str, max_tokens: int = 8192, timeout: int = 600,
             schema: dict | None = None, images: list[str] | None = None) -> str:
        # 不把上一封全文重新塞回 prompt（此前会把最近 4 轮完整正文重复传给模型）。
        # 每封邮件独立提取；系统前缀保留 coverage/focus 骨架。
        full = f"系统约束：\n{self.system}\n\n当前任务：\n{prompt}" if self.system else prompt
        started = time.monotonic()
        try:
            answer = self.backend.complete(full, self.workspace, schema=schema,
                                           timeout=timeout, images=images)
        finally:
            self.calls += 1
            self.elapsed += time.monotonic() - started
        return answer
