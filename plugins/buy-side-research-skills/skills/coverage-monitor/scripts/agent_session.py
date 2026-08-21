"""定时 claude 批处理的固定 session-id 管理。

背景：movers 审查 / 标题翻译用 `claude -p` 非交互批处理，默认每次调用新建
一个 session 文件，堆进 .sessions/，污染会话列表（2026-08-21 一次 21 个）。

本模块让所有定时调用落在【同一个】固定 session：
    claude -p --output-format text --session-id <sid> "prompt"   # 首次：创建
    claude -p --output-format text --resume <sid> "prompt"       # 之后：复用追加
首次运行生成 sid 并写入 .cache/coverage-monitor/session-id；
之后所有调用复用（没有则新建，有则用这一个）。列表里只有一个固定会话。

删除 .cache/coverage-monitor/session-id 即重置为新会话（旧的 jsonl 保留在
.sessions/，可按需清理）。
"""
import os
import subprocess
import sys
import uuid
from pathlib import Path

WS = Path(__file__).resolve().parents[2]
_cache = WS / ".cache" / "coverage-monitor"
_SID_FILE = _cache / "session-id"


def _claude_env() -> dict:
    env = dict(os.environ)
    env["PATH"] = f"{Path.home()}/.local/bin:/opt/homebrew/bin:" + env.get("PATH", "")
    return env


def _ensure_claude() -> bool:
    import shutil
    return shutil.which("claude") is not None


def get_session_id(*, init_title: bool = True) -> str:
    """返回固定 session-id；不存在则生成并写入。init_title=True 时首次用
    claude 初始化一条引导消息，让会话在列表里显示清晰标题。"""
    if _SID_FILE.is_file():
        sid = _SID_FILE.read_text(encoding="utf-8").strip()
        if sid:
            return sid
    if not _ensure_claude():
        return ""
    sid = str(uuid.uuid4())
    try:
        _cache.mkdir(parents=True, exist_ok=True)
        _SID_FILE.write_text(sid, encoding="utf-8")
    except OSError:
        return ""
    if init_title:
        _init_title(sid)
    print(f"[agent_session] 新建定时会话 {sid}", file=sys.stderr)
    return sid


def _init_title(sid: str) -> None:
    """让固定会话在列表里显示为「coverage-monitor 定时任务」。

    提示词必须给明确指令：陈述句会让 claude 当任务去探索、触发工具调用，
    而 workspace 的 hook 在非交互下会卡住进程不退出（2026-08-21 实测）。
    """
    try:
        subprocess.run(
            ["claude", "-p", "--output-format", "text", "--session-id", sid,
             "coverage-monitor 定时任务专用会话。只回复：OK"],
            capture_output=True, text=True, timeout=60, env=_claude_env(),
        )
    except Exception:
        pass  # 标题初始化失败不致命，会话照常用


def claude_args(sid: str) -> list[str]:
    """claude 批处理公共参数：首次创建用 --session-id，之后复用用 --resume。

    实测（2026-08-21）：--session-id 指定新会话但不可复用（第二次报
    "already in use"）；--resume 追加已有会话但不存在时报错。组合起来恰好
    实现"没有则新建，有则用这一个"。"""
    first = not (WS / ".sessions" / f"{sid}.jsonl").is_file()
    flag = "--session-id" if first else "--resume"
    return ["claude", "-p", "--output-format", "text", flag, sid]
