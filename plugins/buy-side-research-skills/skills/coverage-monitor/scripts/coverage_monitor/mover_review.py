"""Movers Agent review：对每只异动股，让 Agent（claude）读当天 news，
筛掉噪音，总结涨跌原因，挑真正解释涨跌的高相关链接。

输出结构（每家）：
    {"TICKER": {"summary": "涨跌原因1-2句", "confidence": "high|medium|low",
                "links": [{"title": "...", "url": "..."}], "reason": "原因未明 or None"}}
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

# agent_session（固定会话）是 coverage_monitor 的上层模块，注入路径后绝对导入
_PKG_ROOT = Path(__file__).resolve().parent.parent
if str(_PKG_ROOT) not in sys.path:
    sys.path.insert(0, str(_PKG_ROOT))
from typing import Any

# 发布者参考权重（仅作 Agent 初始排序提示，Agent 最终判断）
SOURCE_HINTS = {
    "high": ["reuters", "bloomberg", "wsj", "ft.com", "financial times", "defensenews",
             "globenewswire", "businesswire", "prnewswire", "company", "exchange"],
    "low": ["investing.com", "yahoo", "benzinga", "seekingalpha", "fool.com", "zacks",
            "defenseworld", "insidermonkey", "marketwatch"],
}


def _claude_available() -> bool:
    """claude CLI 可用性：PATH 优先，再查常见安装路径。

    launchd 触发时进程 PATH 是最小环境（/usr/bin:/bin:...），不含 ~/.local/bin，
    shutil.which 会漏判 → 定时日报退化为规则 fallback（机械复刻标题）。
    已知路径兜底保证 launchd 定时跑也能走 claude 真实审查。
    """
    import shutil
    from pathlib import Path

    if shutil.which("claude"):
        return True
    for cand in (
        Path.home() / ".local" / "bin" / "claude",
        Path("/opt/homebrew/bin/claude"),
        Path("/usr/local/bin/claude"),
    ):
        if cand.exists():
            return True
    return False


def _source_rank(item) -> int:
    """发布者权重：high 来源 0，low 来源 2，其他 1。"""
    s = (getattr(item, "source", "") or "").lower()
    host = s
    for hint in SOURCE_HINTS["high"]:
        if hint in host:
            return 0
    for hint in SOURCE_HINTS["low"]:
        if hint in host:
            return 2
    return 1


def _rule_review(movers: list[tuple[str, str, dict]], news_map: dict[str, list], protect: tuple = ()) -> dict[str, dict]:
    """无 claude CLI 时的规则 fallback：来源权重排序 + 关键词标签 + 候选链接。

    summary 质量粗（low confidence），但保证每天有输出，不再"原因未明"。
    """
    from .news import protect_names, tag_news_title, translate_zh
    out: dict[str, dict] = {}
    for ticker, company, snap in movers:
        items = news_map.get(ticker, [])
        if not items:
            out[ticker] = {"summary": "板块联动/无明确 news 驱动（当日无合格新闻）",
                           "confidence": "low", "links": [], "reason": "no news"}
            continue
        ranked = sorted(items, key=_source_rank)
        top = ranked[:3]
        tag = tag_news_title(top[0].title)
        label = f"（{tag}）" if tag else ""
        from .news import event_direction
        summary = f"候选：{translate_zh(top[0].title, protect=protect)[:52]}{label}"
        # 2C 方向一致性：标题事件方向 vs 价格涨跌；相反 → 标注「逆向」
        direction = event_direction(top[0].title, tag)
        move = float(snap.get("price_move_pct") or 0)
        if direction == "positive" and move < 0:
            summary += "（⚠ 逆向：标题利好但股价下跌）"
        elif direction == "negative" and move > 0:
            summary += "（⚠ 逆向：标题利空但股价上涨）"
        out[ticker] = {
            "summary": summary, "confidence": "low",
            "links": [{"title": it.title, "url": it.url} for it in top[:2]],
        }
    return out


def _claude_review_chunk(chunk: list[tuple[str, str, dict]], news_map: dict[str, list], today: str, sid: str) -> dict | None:
    """claude CLI 审查一个分块（≤8 家）；成功返回 dict，失败/超时返回 None。

    sid: 固定 session-id，让所有分块落入同一个会话（不新建文件）。
    """
    payload = {}
    for ticker, company, snap in chunk:
        items = news_map.get(ticker, [])
        if not items:
            payload[ticker] = {"company": company, "price_move_pct": snap.get("price_move_pct"),
                               "news": []}
            continue
        payload[ticker] = {
            "company": company,
            "price_move_pct": snap.get("price_move_pct"),
            "news": [{"title": it.title, "url": it.url, "source": getattr(it, "source", ""),
                      "snippet": (getattr(it, "summary", "") or "")[:160]} for it in items[:12]],
        }
    prompt = f"""你是买方研究员。今天是 {today}。下面是今天异动股（Movers）的新闻候选。
对每只股票：
1. 筛掉噪音（持仓变动/机构买入卖出/推广/聚合站重复标题/SEO 标题）
2. 总结这次涨跌的原因（1-2 句，中文；若判断为板块联动或无明确 news 驱动，明确说"板块联动/无明确 news 驱动"）
3. 只挑 2-4 条【真正解释涨跌】的链接（宁缺毋滥；没有就空数组）
4. confidence: high/medium/low
5. 归因分类：summary 开头写明「公司特定」或「板块联动」或「宏观」（例：板块联动：SpaceX 解禁冲击波...）
6. 方向一致性：若标题事件方向（利好/利空）与价格涨跌相反，在 summary 里明确标注「逆向」

只输出 JSON，格式：
{{"TICKER": {{"summary": "...", "confidence": "high", "links": [{{"title":"...","url":"..."}}]}}}}

输入：
{json.dumps(payload, ensure_ascii=False, indent=1)}"""
    try:
        env = dict(os.environ)
        env["PATH"] = f"{Path.home()}/.local/bin:/opt/homebrew/bin:" + env.get("PATH", "")
        from agent_session import claude_args
        proc = subprocess.run(
            claude_args(sid) + [prompt],
            capture_output=True, text=True, timeout=180, env=env,
        )
        out = (proc.stdout or "").strip()
        j = _extract_json(out)
        return j if isinstance(j, dict) else None
    except Exception:
        return None


def _deepseek_review_chunk(chunk: list[tuple[str, str, dict]], news_map: dict[str, list], today: str) -> dict | None:
    """DeepSeek 批量审查一个分块（≤8 家），无痕（不走 claude CLI session）。成功 dict，失败 None。"""
    from .deepseek_translate import _chat, get_config
    cfg = get_config()
    if not cfg["api_key"]:
        return None
    payload = {}
    for ticker, company, snap in chunk:
        items = news_map.get(ticker, [])
        payload[ticker] = {
            "company": company,
            "price_move_pct": snap.get("price_move_pct"),
            "news": [{"title": it.title, "url": it.url, "source": getattr(it, "source", ""),
                      "snippet": (getattr(it, "summary", "") or "")[:160]} for it in items[:12]],
        }
    prompt = f"""你是买方研究员。今天是 {today}。下面是今天异动股（Movers）的新闻候选。
对每只股票：
1. 筛掉噪音（持仓变动/机构买入卖出/推广/聚合站重复标题/SEO 标题）
2. 总结这次涨跌的原因（1-2 句，中文；若判断为板块联动或无明确 news 驱动，明确说"板块联动/无明确 news 驱动"）
3. 只挑 2-4 条【真正解释涨跌】的链接（宁缺毋滥；没有就空数组）
4. confidence: high/medium/low
5. 归因分类：summary 开头写明「公司特定」或「板块联动」或「宏观」（例：板块联动：SpaceX 解禁冲击波...）
6. 方向一致性：若标题事件方向（利好/利空）与价格涨跌相反，在 summary 里明确标注「逆向」

只输出 JSON，格式：
{{"TICKER": {{"summary": "...", "confidence": "high", "links": [{{"title":"...","url":"..."}}]}}}}

输入：
{json.dumps(payload, ensure_ascii=False, indent=1)}"""
    try:
        raw = _chat(prompt, api_key=cfg["api_key"], api_base=cfg["api_base"],
                    model=cfg["model"], timeout=180, max_tokens=8192)
        j = _extract_json(raw)
        return j if isinstance(j, dict) else None
    except Exception:
        return None


def review_movers(movers: list[tuple[str, str, dict]], news_map: dict[str, list],
                  today: str, entries: list | None = None) -> dict[str, dict]:
    """Agent review 所有 Movers：DeepSeek 批量（无痕，Windows/Mac 通用）→ claude CLI fallback → 规则。"""
    from .news import protect_names

    if not movers:
        return {}
    _prot = protect_names(entries) if entries else tuple(c for _, c, _ in movers)
    CHUNK = 8
    combined: dict = {}

    from .deepseek_translate import deepseek_available
    if deepseek_available():
        for i in range(0, len(movers), CHUNK):
            chunk = movers[i:i + CHUNK]
            j = _deepseek_review_chunk(chunk, news_map, today)
            if j:
                combined.update(j)
                continue
            # DeepSeek 失败 → claude fallback → 规则
            print(f"[mover_review] deepseek chunk {i // CHUNK} 失败 → fallback", file=sys.stderr)
            if _claude_available():
                from agent_session import get_session_id
                j2 = _claude_review_chunk(chunk, news_map, today, get_session_id())
                if j2:
                    combined.update(j2)
                    continue
            combined.update(_rule_review(chunk, news_map, _prot))
        return combined

    # 无 DeepSeek key → claude CLI → 规则（原逻辑）
    if not _claude_available():
        print("[mover_review] claude CLI 不可用 → 规则 fallback", file=sys.stderr)
        return _rule_review(movers, news_map, _prot)

    from agent_session import get_session_id
    sid = get_session_id()  # 固定 session-id：所有分块落入同一个会话
    for i in range(0, len(movers), CHUNK):
        chunk = movers[i:i + CHUNK]
        j = _claude_review_chunk(chunk, news_map, today, sid)
        if j:
            combined.update(j)
        else:
            print(f"[mover_review] chunk {i // CHUNK} 失败 → 规则 fallback", file=sys.stderr)
            combined.update(_rule_review(chunk, news_map, _prot))
    return combined


def _extract_json(text: str) -> Any:
    """从 agent 输出提取 JSON（容忍 ```json 代码块/前后文字）。"""
    import re
    # 找 ```json ... ``` 块
    m = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.S)
    if m:
        return json.loads(m.group(1))
    # 找最外层 { ... }
    start = text.find("{")
    if start != -1:
        try:
            return json.loads(text[start:])
        except json.JSONDecodeError:
            pass
    return None
