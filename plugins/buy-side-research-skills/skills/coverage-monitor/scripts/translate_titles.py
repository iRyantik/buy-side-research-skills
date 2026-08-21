#!/usr/bin/env python3
"""用 claude CLI（agent 能力）批量翻译 AI 审查任务包里的标题。

workflow：
  1) run_coverage_monitor.py daily --ai-review-input   → 导出任务包
  2) translate_titles.py                                → claude 批量翻译 → ai-review-output.json
  3) run_coverage_monitor.py daily --skip-fetch --ai-review <output> → 注入重渲染

默认读写 .cache/coverage-monitor/ 下的 ai-review-input.json / ai-review-output.json。
"""
import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

from agent_session import claude_args, get_session_id

WS = Path(__file__).resolve().parent.parent.parent
_cache = WS / ".cache" / "coverage-monitor"

_ap = argparse.ArgumentParser(description="claude CLI 批量翻译新闻标题")
_ap.add_argument("--input", default=str(_cache / "ai-review-input.json"), help="任务包 JSON")
_ap.add_argument("--output", default=str(_cache / "ai-review-output.json"), help="输出 JSON（translations）")
_ap.add_argument("--chunk", type=int, default=30, help="每块标题数")
_args = _ap.parse_args()

pack = json.load(open(_args.input, encoding="utf-8"))
titles = pack["titles_to_translate"]

KANA = re.compile(r"[぀-ヿ]")
HANGUL = re.compile(r"[가-힣]")
HAN = re.compile(r"[一-鿿]")

def needs_tr(t):
    # 含假名/谚文 → 翻；含汉字且无日韩特征 → 中文不翻；纯英文 → 翻
    if KANA.search(t) or HANGUL.search(t):
        return True
    if HAN.search(t):
        return False
    return True

todo = [t for t in titles if needs_tr(t)]
print(f"total={len(titles)} to_translate={len(todo)}", flush=True)

state = json.load(open(_cache / "daily-state.json", encoding="utf-8"))
names = set()
for e in state["entries"]:
    for n in (e.get("company_native") or "", e.get("company") or ""):
        n = n.strip()
        if len(n) >= 3:
            names.add(n)
name_list = ", ".join(sorted(names, key=len, reverse=True)[:80])

translations = {}
CHUNK = _args.chunk

_SID = get_session_id()  # 固定 session-id：所有 chunk 落入同一个会话

def run_claude(prompt, timeout=240):
    proc = subprocess.run(claude_args(_SID) + [prompt],
                          capture_output=True, text=True, timeout=timeout,
                          env={"PATH": "/Users/ryanxing/.local/bin:/opt/homebrew/bin:" + os.environ.get("PATH", "")})
    return proc.stdout or ""

for i in range(0, len(todo), CHUNK):
    chunk = todo[i:i + CHUNK]
    prompt = (f"逐条把下面 {len(chunk)} 条新闻标题翻译成简体中文。规则：\n"
              f"1. 每行一条，只输出译文本身，不加编号、引号、解释或空行。\n"
              f"2. 以下公司名必须原样保留，绝不音译或改写：{name_list}\n"
              f"3. 人名地名保留原文，除非有通行中文译名。\n"
              f"4. 财经术语用标准中文（contract→合同，order→订单，target price→目标价，guidance→指引）。\n"
              f"原文：\n" + "\n".join(chunk))
    out = run_claude(prompt)
    lines = [l.strip() for l in out.splitlines() if l.strip()]
    got = 0
    for j, line in enumerate(lines):
        if j >= len(chunk):
            continue
        line = re.sub(r"^\d+[.、):]\s*", "", line).strip()
        if line and line != chunk[j]:
            translations[chunk[j]] = line
            got += 1
    print(f"chunk {i // CHUNK}: {got}/{len(chunk)}", flush=True)

out_p = Path(_args.output)
json.dump({"translations": translations}, open(out_p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"WROTE {len(translations)} translations -> {out_p}", flush=True)
