"""Extract structured company updates, signals, and multiple meetings from sell-side emails."""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.request
from pathlib import Path

from .parse import Email


def _read_env(workspace: Path) -> dict[str, str]:
    env = dict(os.environ)
    try:
        for line in (workspace / ".env").read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                env.setdefault(key.strip(), value.strip().strip('"').strip("'"))
    except OSError:
        pass
    return env


def _chat(prompt: str, workspace: Path, timeout: int = 180) -> str:
    env = _read_env(workspace)
    key = env.get("DEEPSEEK_API_KEY", "")
    if not key:
        raise RuntimeError("DEEPSEEK_API_KEY is not configured")
    base = env.get("DEEPSEEK_API_BASE", "https://api.deepseek.com/v1").rstrip("/")
    model = env.get("DEEPSEEK_MODEL", "deepseek-v4-flash")
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
        "max_tokens": 8_000,
        "reasoning_effort": "none",  # 关闭 reasoning：快 + content 不被 reasoning 吃空
    }
    request = urllib.request.Request(
        f"{base}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        data = json.loads(response.read(6_000_000).decode("utf-8"))
    return data["choices"][0]["message"]["content"] or ""


_PROMPT = """你是 buy-side researcher 的 sell-side 邮件筛选器。目标不是逐封摘要，而是提取值得研究员花时间的信息。

Workspace context：
{context_json}

严格输出 JSON 数组，每封邮件一个对象：
{{
  "email_index": 0,
  "items": [{{
    "kind": "company_update|industry_signal|sell_side_view",
    "company": "公司名；公司/个股类信号必填（正文无法确定时取主题中最具体实体），行业/宏观类可为 null", "ticker": "ticker 或 null", "industry": "行业或 null",
    "event_type": "earnings|estimate_revision|order|guidance|initiation|product|management_change|capital_allocation|rating_change|macro|other",
    "what_changed": "真正新增的事实或卖方判断，1-2句中文",
    "why_it_matters": "投资含义，最多1句；没有则 null",
    "focus_fit": "strong|moderate|weak|none",
    "focus_reason": "与 COVERAGE.md 的 ## Focus 区哪条假设/当前 lens 相关；没有则 null",
    "action": "read|watch|research|note|skip",
    "action_reason": "最多1句",
    "merge_key": "同一事件跨 broker 共用的稳定键（不含日期——如 HWM-guidance-legacy-aftermarket，跨天可匹配）",
    "delta_vs_last": "若 merge_key 已出现在 last_events 中（昨天/之前 broker 提过），列出相对该事件的实质新增信息；首次或无明显新增则 null",
    "priority": "high|medium|low"
  }}],
  "meetings": [{{
    "title": "会议名称", "company": "公司/机构或 null", "ticker": "ticker 或 null",
    "topic": "会议主题，简短", "date": "原邮件中的日期", "time": "原邮件中的时间",
    "host": "主办方", "participants": "讲者/管理层或 null", "format": "线上/线下/电话会等",
    "location": "地点或 null", "registration": "报名说明或链接文字",
    "recommendation": "high|medium|low", "reason": "为什么值得或不值得，最多1句"
  }}],
  "filter_reason": "整封无有效信息时说明；否则 null"
}}

判断规则：
1. 一封邮件可以拆出多个 company items，也可以列出多个 meetings；不得只保留第一个。
2. Core/coverage 必须按 context 的公司名单判断。同行业公司即使不在 coverage，也要保留为 industry signal 或 new-idea candidate，不能因“不在 coverage”过滤。
3. New Idea 的语义不是 sell-side initiation。只有不在 coverage、出现了实质变化、符合 ## Focus 区 当前 lens 且值得 read/watch/research 的公司才具备 new-idea 条件。initiation 只是 event，不是推荐理由。
4. 不符合 Focus 但能说明行业发生了什么的公司，保留为 industry_signal。
5. 卖方的 differentiated view/idea 可作为 sell_side_view；普通目标价微调、营销转发、recap 不算新信息。
6. 会议保持轻量：列清信息、主题、推荐和一句理由，不写长分析。会议合集必须逐场提取。
7. 只使用邮件正文和附件文件名能确认的信息；不补写正文没有的数字、日期、ticker 或结论。
8. what_changed 为空的普通邮件放 filter_reason，不制造“变化”。
9. last_events 提供历史事件基线（merge_key → 该事件上次 what_changed）。若本次 item 的 merge_key 已在 last_events，delta_vs_last 输出相对基线的实质新增（新数字/新角度/新结论/新推荐）；只是重复旧信息则 null。

邮件输入：
{input_json}

只输出 JSON 数组，不要 Markdown 或解释。"""


def _extract_json(raw: str):
    match = re.search(r"\[.*\]", raw, re.S)
    return json.loads(match.group(0) if match else raw)


def review_batch(emails: list[Email], context: dict, workspace: Path,
                 max_body: int = 6_000, chunk: int = 6) -> list[dict]:
    out: list[dict] = []
    compact_context = {
        "coverage": context.get("coverage", []),
        "covered_industries": context.get("covered_industries", []),
        "focus": context.get("focus", ""),
        # 跨天事件追踪：merge_key → 该事件最近一次 what_changed（AI 据此判断增量）
        "last_events": context.get("last_events", {}),
    }
    for start in range(0, len(emails), chunk):
        block = emails[start:start + chunk]
        inputs = []
        for offset, email in enumerate(block):
            inputs.append({
                "email_index": start + offset,
                "subject": email.subject,
                "from": email.sender,
                "received_at": email.received_at,
                "body": (email.body_text or "")[:max_body],
                "attachments": [name for name, _ in email.attachments],
            })
        try:
            raw = _chat(_PROMPT.format(
                context_json=json.dumps(compact_context, ensure_ascii=False),
                input_json=json.dumps(inputs, ensure_ascii=False),
            ), workspace)
            parsed = _extract_json(raw)
        except Exception as exc:
            print(f"[email-intelligence] review chunk {start // chunk} failed: {exc}", file=sys.stderr)
            continue

        for review in parsed if isinstance(parsed, list) else []:
            if not isinstance(review, dict):
                continue
            try:
                index = int(review.get("email_index"))
            except (TypeError, ValueError):
                continue
            if not 0 <= index < len(emails):
                continue
            review["_email_id"] = emails[index].key
            out.append(review)
    return out
