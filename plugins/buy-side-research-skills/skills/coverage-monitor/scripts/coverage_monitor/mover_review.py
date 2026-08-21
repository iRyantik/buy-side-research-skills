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
from typing import Any

# 发布者参考权重（仅作 Agent 初始排序提示，Agent 最终判断）
SOURCE_HINTS = {
    "high": ["reuters", "bloomberg", "wsj", "ft.com", "financial times", "defensenews",
             "globenewswire", "businesswire", "prnewswire", "company", "exchange"],
    "low": ["investing.com", "yahoo", "benzinga", "seekingalpha", "fool.com", "zacks",
            "defenseworld", "insidermonkey", "marketwatch"],
}


def _claude_available() -> bool:
    import shutil
    return shutil.which("claude") is not None


def review_movers(movers: list[tuple[str, str, dict]], news_map: dict[str, list],
                  today: str) -> dict[str, dict]:
    """Agent review 所有 Movers。movers = [(ticker, company, snapshot)]。

    Agent 不可用 → 返回 {}（渲染 fallback：只列脚本 news，原因标待人工）。
    """
    if not movers:
        return {}
    if not _claude_available():
        print("[mover_review] claude CLI 不可用 → 跳过 Agent review", file=sys.stderr)
        return {}

    # 组装输入：每家的 news 候选（title + url + source + snippet）
    payload = {}
    for ticker, company, snap in movers:
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

只输出 JSON，格式：
{{"TICKER": {{"summary": "...", "confidence": "high", "links": [{{"title":"...","url":"..."}}]}}}}

输入：
{json.dumps(payload, ensure_ascii=False, indent=1)}"""

    try:
        env = dict(os.environ)
        env["PATH"] = f"{Path.home()}/.local/bin:/opt/homebrew/bin:" + env.get("PATH", "")
        proc = subprocess.run(
            ["claude", "-p", "--output-format", "text", prompt],
            capture_output=True, text=True, timeout=180, env=env,
        )
        out = (proc.stdout or "").strip()
        # 提取 JSON（可能被 claude 包在代码块里）
        j = _extract_json(out)
        if not isinstance(j, dict):
            print(f"[mover_review] Agent 输出非 JSON: {out[:200]}", file=sys.stderr)
            return {}
        return j
    except subprocess.TimeoutExpired:
        print("[mover_review] Agent 超时", file=sys.stderr)
        return {}
    except Exception as e:
        print(f"[mover_review] Agent 调用失败: {e}", file=sys.stderr)
        return {}


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
