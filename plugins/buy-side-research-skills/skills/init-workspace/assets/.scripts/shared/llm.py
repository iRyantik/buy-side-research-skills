"""统一 LLM 客户端（DeepSeek Anthropic 兼容端点 · [1M] 模型 · 32k 输出）。

所有 skill 共享同一入口：标题翻译 / mover 归因 / email 情报 review / 图表描述——
调用方只构造 prompt，本模块统一端点/认证/模型/重试/错误语义。

配置（workspace .env，与 Claude Code 同款模型）：
    DEEPSEEK_API_KEY=sk-...
    DEEPSEEK_MODEL=deepseek-v4-flash-vision-exp[1M]   # 可选，默认同款
    DEEPSEEK_ANTHROPIC_BASE=https://api.deepseek.com/anthropic/v1  # 可选

零第三方依赖（stdlib urllib）。无 key / 连续失败 → chat() 返回 None，
调用方走自己的降级链（honest degrade）；chat_json() 失败抛 LLMError。
"""

from __future__ import annotations

import json
import os
import re
import urllib.request
import urllib.error
from pathlib import Path

DEFAULT_BASE = "https://api.deepseek.com/anthropic/v1"
DEFAULT_MODEL = "deepseek-v4-flash-vision-exp[1M]"
MAX_TOKENS = 32_000
RETRIES = 2


class LLMError(RuntimeError):
    """LLM 调用或解析失败（带 cause 信息）。"""


def _workspace_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


def load_env(workspace: Path | None = None) -> dict:
    """进程环境变量优先，workspace .env 补缺（零依赖解析）。"""
    ws = workspace or _workspace_root()
    env: dict = {}
    try:
        for line in (ws / ".env").read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            env[k.strip()] = v.strip().strip('"').strip("'")
    except OSError:
        pass
    merged = dict(os.environ)
    for k, v in env.items():
        merged.setdefault(k, v)
    return merged


def config(workspace: Path | None = None) -> dict:
    env = load_env(workspace)
    return {
        "api_key": env.get("DEEPSEEK_API_KEY", ""),
        "api_base": (env.get("DEEPSEEK_ANTHROPIC_BASE") or DEFAULT_BASE).rstrip("/"),
        "model": env.get("DEEPSEEK_MODEL") or DEFAULT_MODEL,
    }


def chat(prompt: str, workspace: Path | None = None, system: str | None = None,
         max_tokens: int = MAX_TOKENS, temperature: float = 0.1,
         timeout: int = 180, images: list[dict] | None = None) -> str | None:
    """单次对话。无 key → None；重试 RETRIES 次；仍失败 → None（调用方降级）。

    images: Anthropic 多模态 block 列表：[{"media_type": "image/png", "data": "<base64>"}, ...]
    ——传入时 content 为文本+图片混合数组（vision-exp 多模态读取邀请函/日程/截图）。
    """
    cfg = config(workspace)
    if not cfg["api_key"]:
        return None
    content: list = [{"type": "text", "text": prompt}]
    for img in images or []:
        content.append({"type": "image", "source": {
            "type": "base64", "media_type": img.get("media_type", "image/png"),
            "data": img.get("data", "")}})
    payload: dict = {
        "model": cfg["model"],
        "messages": [{"role": "user", "content": content}],
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    if system:
        payload["system"] = system
    request = urllib.request.Request(
        f"{cfg['api_base']}/messages",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {cfg['api_key']}",
                 "anthropic-version": "2023-06-01"},
        method="POST",
    )
    last_err = ""
    for attempt in range(RETRIES + 1):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                data = json.loads(response.read(6_000_000).decode("utf-8"))
            return "".join(b.get("text", "") for b in data.get("content", [])) or ""
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            last_err = f"{type(exc).__name__}: {str(exc)[:120]}"
    return None


def chat_json(prompt: str, workspace: Path | None = None, **kwargs):
    """要求 JSON 输出并解析（[...] 或 {...}）。失败抛 LLMError。"""
    raw = chat(prompt, workspace, **kwargs)
    if raw is None:
        raise LLMError("llm chat failed")
    match = re.search(r"\[.*\]|\{.*\}", raw, re.S)
    if not match:
        raise LLMError(f"no JSON in output: {raw[:120]}")
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError as exc:
        raise LLMError(f"JSON decode failed: {exc} | tail: {raw[-160:]}")
