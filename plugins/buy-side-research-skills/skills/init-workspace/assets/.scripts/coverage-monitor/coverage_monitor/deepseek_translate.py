"""DeepSeek（OpenAI 兼容）标题翻译——批量 + 单条。

daily 翻译链的 AI 层（2026-08-24 加入）：DeepSeek API → claude CLI（Mac）→
gtx 机械翻译 → 原文。DeepSeek 是第一条 AI 路径：Windows/Mac 通用、便宜、
launchd 定时环境（无 claude CLI）也能走真 AI 翻译。

配置（workspace .env，与 SMTP 同模式；init-workspace 引导填写）：
    DEEPSEEK_API_KEY=sk-...
    DEEPSEEK_API_BASE=https://api.deepseek.com/v1   # 可选：OpenAI 兼容中转
    DEEPSEEK_MODEL=deepseek-v4-flash                # 可选

零第三方依赖（stdlib urllib）。无 key / 调用失败 → 返回 None / 空 dict，
调用方走降级链（honest degrade，不炸）。
"""

from __future__ import annotations

import json
import os
import re
import urllib.request
from pathlib import Path

_DEFAULT_BASE = "https://api.deepseek.com/v1"
_DEFAULT_MODEL = "deepseek-v4-flash"

_BATCH_PROMPT = (
    "逐条把下面 {n} 条新闻标题翻译成简体中文。规则：\n"
    "1. 每行一条，只输出译文本身，不加编号、引号、解释或空行。\n"
    "2. 以下英文公司名保留原文；韩文/日文公司名翻译成中文（音译或通行译名）：{names}\n"
    "3. 人名地名保留原文，除非有通行中文译名。\n"
    "4. 财经术语用标准中文（contract→合同，order→订单，target price→目标价，guidance→指引）。\n"
    "原文：\n{lines}"
)


def _workspace_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent.parent


def _load_env(path: Path) -> dict:
    """简易 .env 解析（KEY=VALUE，# 注释），零依赖够用。"""
    env = {}
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            env[k.strip()] = v.strip().strip('"').strip("'")
    except OSError:
        pass
    return env


def get_config(workspace: Path | None = None) -> dict:
    """(api_key, api_base, model)——进程环境变量优先，workspace .env 补缺。"""
    ws = workspace or _workspace_root()
    env = _load_env(ws / ".env")
    key = os.environ.get("DEEPSEEK_API_KEY") or env.get("DEEPSEEK_API_KEY", "")
    base = os.environ.get("DEEPSEEK_API_BASE") or env.get("DEEPSEEK_API_BASE", _DEFAULT_BASE)
    model = os.environ.get("DEEPSEEK_MODEL") or env.get("DEEPSEEK_MODEL", _DEFAULT_MODEL)
    return {"api_key": key.strip(), "api_base": base.rstrip("/"), "model": model.strip()}


def deepseek_available(workspace: Path | None = None) -> bool:
    return bool(get_config(workspace)["api_key"])


def _chat(prompt: str, *, api_key: str, api_base: str, model: str,
          timeout: int, max_tokens: int) -> str:
    """单次 chat/completions 调用。失败抛异常（由调用方降级）。"""
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
        "max_tokens": max_tokens,
        "reasoning_effort": "none",  # 关闭 reasoning：更快 + content 不被 reasoning 吃空
    }
    req = urllib.request.Request(
        f"{api_base}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read(2_000_000).decode("utf-8"))
    return data["choices"][0]["message"]["content"] or ""


def _parse_lines(text: str) -> list:
    """响应拆行，剥可能的行号前缀（"1. "、"2、" 等）。"""
    return [re.sub(r"^\d+[.、):]\s*", "", l).strip() for l in text.splitlines() if l.strip()]


def translate_batch(titles: list, names: tuple | list = (), chunk: int = 30,
                    workspace: Path | None = None, timeout: int = 180) -> dict:
    """批量翻译标题 → {原文: 译文}。无 key / 某块失败 → 该块跳过，返回已成功的。

    行号对齐：模型可能少返/多返行，按索引对齐；译文与原文相同（模型拒绝）则丢弃。
    """
    out: dict = {}
    cfg = get_config(workspace)
    if not cfg["api_key"]:
        return out
    name_list = ", ".join(sorted({str(n) for n in names}, key=len, reverse=True)[:80])
    for i in range(0, len(titles), chunk):
        block = titles[i:i + chunk]
        prompt = _BATCH_PROMPT.format(n=len(block), names=name_list or "（无）",
                                      lines="\n".join(block))
        try:
            raw = _chat(prompt, api_key=cfg["api_key"], api_base=cfg["api_base"],
                        model=cfg["model"], timeout=timeout, max_tokens=4096)
        except Exception:
            continue  # 网络/限流 → 该块留给下一级（claude CLI / gtx）
        lines = _parse_lines(raw)
        for j, line in enumerate(lines):
            if j >= len(block):
                break
            if line and line != block[j]:
                out[block[j]] = line
    return out


def translate(text: str, workspace: Path | None = None, timeout: int = 30) -> str | None:
    """单条标题翻译。无 key / 失败 → None（调用方走 gtx 兜底）。"""
    cfg = get_config(workspace)
    if not cfg["api_key"]:
        return None
    prompt = _BATCH_PROMPT.format(n=1, names="（无）", lines=text)
    try:
        raw = _chat(prompt, api_key=cfg["api_key"], api_base=cfg["api_base"],
                    model=cfg["model"], timeout=timeout, max_tokens=1024)
    except Exception:
        return None
    lines = _parse_lines(raw)
    if not lines:
        return None
    out = lines[0]
    return out if out and out != text else None
