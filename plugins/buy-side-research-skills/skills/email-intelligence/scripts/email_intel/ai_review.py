"""Two-stage email review: gate (relevance) → deep (structured extraction).

coverage 恒定为 system 前缀（DeepSeek 前缀缓存 ≈ 0.1×），gate 与 deep 共用同一份。
gate：确定性(覆盖公司名/ticker) + LLM 兜底(行业/focus)；related → 进 deep，not_related → filter_reason。
deep：仅 related 邮件逐封提取 items/meetings（含 broker/company_en/evidence/confidence/related_tickers）。
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

from .parse import Email


def _shared_dir() -> str:
    return str(Path(__file__).resolve().parent.parent.parent / "shared")


def _llm(prompt: str, workspace: Path, system: str | None = None, max_tokens: int = 32_000,
         images: list | None = None, timeout: int = 180) -> str:
    """统一 LLM 入口（shared/llm：Anthropic 端点 + [1M]，重试/降级在模块内）。失败抛异常。"""
    sys.path.insert(0, _shared_dir())
    from llm import chat as _chat
    result = _chat(prompt, workspace, system=system, max_tokens=max_tokens,
                   images=images, timeout=timeout)
    if result is None:
        raise RuntimeError("LLM call failed")
    return result


def _coverage_system(context: dict) -> str:
    """coverage 精简骨架 → 恒定 system 前缀（gate/deep 共用，前缀缓存命中）。

    只保留判相关所需的字段（公司名+ticker / 覆盖行业 / focus / 事件基线），
    去掉 coverage 详情（notes/status 等）——gate 只是粗筛，不需要 48KB 全量。
    """
    companies = []
    for c in context.get("coverage", []):
        row = {}
        for k in ("ticker", "company_en", "company_native"):
            if c.get(k):
                row[k] = c.get(k)
        if row:
            companies.append(row)
    compact = {
        "companies": companies[:200],
        "covered_industries": context.get("covered_industries", []),
        "focus": str(context.get("focus", ""))[:600],
        "last_events": context.get("last_events", {}),
    }
    return json.dumps(compact, ensure_ascii=False)


# ----------------------------- Gate（粗筛） -----------------------------
_GATE_PROMPT = """判断这封sell-side邮件是否与当前研究覆盖有关。

判断标准（只要命中任一即 related）：
- 提到覆盖公司（名称或 ticker）
- 涉及覆盖行业（半导体设备 / 国防 / AI 算力 / 先进制造 / 核电 / 海底电缆 等）
- 触及 ## Focus 假设（订单能见度、产能、国产替代、先进封装、AI 算力 等）
related = 有交集且可能是实质新信息（业绩/订单/指引/评级/会议邀请等）
not_related = 行业完全无关，或纯营销/转发/无实质/只重复旧闻
borderline = 拿不准（放行让深层再判）

邮件：
{email}

只输出 JSON：{"relevant": "related|not_related|borderline"}"""


def _gate_terms(context: dict) -> tuple[set, set]:
    """coverage 公司名（中文/英文）+ ticker，供 0-token 确定性命中。"""
    names: set = set()
    tickers: set = set()
    for c in context.get("coverage", []):
        for k in ("company_en", "company_native", "company", "name"):
            if c.get(k):
                names.add(str(c[k]).strip())
        if c.get("ticker"):
            tickers.add(str(c["ticker"]).strip())
    return names, tickers


def _deterministic_gate(email: Email, names: set, tickers: set) -> bool:
    """覆盖公司名/ticker 字面命中 → 直接相关（0 token）。"""
    hay = ((email.subject or "") + " " + (email.body_text or "")[:600]).lower()
    for ticker in tickers:
        t = ticker.lower()
        if t and t in hay:
            return True
    for name in names:
        n = name.lower()
        if len(n) >= 2 and n in hay:
            return True
    return False


def _llm_gate(email: Email, system_coverage: str, workspace: Path) -> bool:
    """LLM 兜底：判行业/focus。返回 True=进 deep（related/borderline）。"""
    blurb = (email.body_text or "")[:300]
    prompt = _GATE_PROMPT.replace("{email}", json.dumps({
        "subject": email.subject, "from": email.sender, "body": blurb}, ensure_ascii=False))
    raw = _llm(prompt, workspace, system=system_coverage, max_tokens=60, timeout=60)
    m = re.search(r'"(related|not_related|borderline)"', raw)
    verdict = m.group(1) if m else "related"  # 解析失败 → 放行（recall）
    return verdict != "not_related"


# ----------------------------- Deep（精筛提取） -----------------------------
_PROMPT = """你是 buy-side researcher 的 sell-side 邮件筛选器。目标不是逐封摘要，而是提取值得研究员花时间的信息。

只允许基于邮件正文内容输出——邮件中没有的公司/数字/日期/事件一律不得出现，发现不了信息就输出空数组。

本批邮件（JSON 数组；subject/from/body 为真实内容）：
{input_json}

严格输出 JSON 数组，每封一个对象：
{{
  "email_index": 0,
  "broker": "发件机构名（如 长江证券/广发证券/UBS/Jefferies/久谦；识别不出则发件人域主名；纯个人可 null）",
  "items": [{{
    "kind": "company_update|industry_signal|sell_side_view",
    "company": "公司名；公司/个股类信号必填（正文无法确定时取主题中最具体实体），行业/宏观类可为 null", "ticker": "ticker 或 null", "industry": "行业或 null",
    "company_en": "公司英文名（如 NAURA Technology）或 null",
    "event_type": "earnings|estimate_revision|order|guidance|initiation|product|management_change|capital_allocation|rating_change|macro|other",
    "summary": "卡片正文——中文自然段 2-4 句（60-120 字）：先事实（公司/数字/时间/范围），再研判（投资含义+建议动作），'——'衔接",
    "what_changed": "增量摘要 1-2 句（跨天 baseline 用）",
    "evidence": "一句话依据（正文里最支撑该条的原文片段/数字）或 null",
    "confidence": "high|medium|low（该信息确定性）",
    "related_tickers": "关联标的 ticker/公司 数组（read-through 用）；无则 []",
    "focus_fit": "strong|moderate|weak|none",
    "focus_reason": "与 ## Focus 区哪条假设/当前 lens 相关；没有则 null",
    "action": "read|watch|research|note|skip",
    "merge_key": "同一事件跨 broker 共用的稳定键（不含日期——如 HWM-guidance-legacy-aftermarket）",
    "delta_vs_last": "若 merge_key 已在 last_events，列相对基线的实质新增；首次或无明显新增则 null",
    "priority": "high|medium|low"
  }}],
  "meetings": [{{
    "broker": "发件机构名或 null",
    "title": "会议名称", "industry": "会议所属行业（关键：归行业卡与筛选；无法判定用最接近覆盖行业或 null）",
    "company": "公司/机构或 null", "ticker": "ticker 或 null",
    "date": "原邮件日期（统一 MM-DD）", "time": "原邮件时间（**必须带时区**，如 2pm-3pm HKT / 11:00 HKT）",
    "host": "机构名", "host_person": "主持分析师或 null",
    "participants": "讲者/管理层或 null", "speaker_bio": "讲者履历一句话或 null",
    "agenda_items": "看点关键词短语 1-2 条（每条≤14字，不要完整问句）；无则 []",
    "related_tickers": "相关标的 ticker/公司 数组；无则 []",
    "language": "语言或 null", "seats_limit": "限席/'10 位' 等或 null",
    "format": "线上/线下/电话会/Webinar", "location": "地点或 null",
    "registration": "报名链接 URL 或入场说明",
    "recommendation": "recommend|consider|skip", "reason": "为什么值得/不值得，最多1句"
  }}],
  "filter_reason": "整封无有效信息时说明；否则 null"
}}

判断规则：
1. 一封邮件可拆多个 company items，也可列多个 meetings；不得只留第一个。
2. Core/coverage 按 context 公司名单判断。同行业公司即使不在 coverage，也要保留为行业信号或 new-idea 候选，不能因"不在 coverage"过滤。
3. New Idea 语义非 initiation：不在 coverage + 实质变化 + 符合 Focus 且值得 read/watch/research 才具备。initiation 只是 event，不构成推荐理由。
4. 不符合 Focus 但能说明行业发生了什么 → 行业信号。
5. differentiated view/idea 可作 sell_side_view；普通目标价微调/营销转发/recap 不算新信息。
6. 会议轻量：列清信息、看点、讲者、一句理由；会议合集必须逐场提取。
7. 只使用正文/附件名能确认的信息；不补写正文没有的数字/日期/ticker/结论。
8. what_changed 为空的普通邮件放 filter_reason，不制造"变化"。
9. last_events 提供事件基线；若 merge_key 已在，delta_vs_last 列相对基线的实质新增；只重复旧信息则 null。
10. 研究/推荐汇总：能具名拆公司级 items；不能具名的差异化观点作行业信号；纯行情/无差异 → filter_reason。
11. 会议 recommendation：行业在 covered_industries 内且与研究相关 → recommend；相关但边际 → consider；不在覆盖或纯营销 → skip。
12. 每封优先输出信息量/相关性最大的 items 与 meetings；内容过多保留最重要的一至四条（其余在 summary/filter_reason 合并）。
13. 字段无值时省略该 key（不写 null），仅保留有值的字段——减少冗余输出。"""




def _extract_email_json(e) -> str:
    import json as _j
    return _j.dumps({"subject": e.subject, "body": (e.body_text or "")}, ensure_ascii=False)


def _extract_json(raw: str):
    text = raw.strip()
    m = re.match(r"```(?:json)?\s*(.*?)\s*```", text, re.S)
    if m:
        text = m.group(1)
    try:
        return json.JSONDecoder().raw_decode(text.lstrip())[0]
    except (json.JSONDecodeError, ValueError):
        match = re.search(r"\[.*\]|\{.*\}", text, re.S)
        if not match:
            raise ValueError("no JSON in LLM output")
        return json.loads(match.group(0))


_IMAGE_HINT = ("这张图片来自卖方邮件。如果它是会议/日程/邀请函/关键图表，用中文概述内容"
               "（会议名、日期时间、主题、讲者、链接等关键信息，≤100 字）；与内容无关则一句话说明。")


def _preview_images(emails: list[Email], workspace: Path) -> dict:
    """有图邮件 → vision 提取摘要 → {email.key: 摘要}。失败 → 空（降级）。"""
    import base64
    out: dict = {}
    for e in emails:
        if not e.images:
            continue
        blocks = []
        for _name, img_path in e.images[:2]:
            try:
                data = base64.b64encode(Path(img_path).read_bytes()).decode("ascii")
                mt = "image/png" if img_path.lower().endswith("png") else "image/jpeg"
                blocks.append({"media_type": mt, "data": data})
            except OSError:
                continue
        if not blocks:
            continue
        try:
            desc = _llm(_IMAGE_HINT, workspace, max_tokens=800, images=blocks)
            if desc:
                out[e.key] = desc[:300]
        except Exception:
            continue
    return out


def _preview_pdfs(emails: list[Email], workspace: Path) -> dict:
    import subprocess
    script = workspace / ".scripts" / "pdf-to-md.py"
    out: dict = {}
    if not script.exists():
        return out
    for e in emails:
        if not e.pdfs:
            continue
        parts = []
        for _name, pdf_path in e.pdfs[:2]:
            try:
                r = subprocess.run([sys.executable, str(script), pdf_path],
                                   capture_output=True, text=True, timeout=180)
                if r.returncode != 0 or not (r.stdout or "").strip():
                    continue
                parts.append(r.stdout[:1_200])
            except Exception:
                continue
        if parts:
            out[e.key] = chr(10) * 2 + chr(10).join([x[:1000] for x in parts])
    return out


def _crop(body: str, head: int = 400, tail: int = 600) -> str:
    """正文首尾关键段：研究邮件信息集中在前段摘要+尾段结论，中段前情/表格可省。"""
    b = body or ""
    if len(b) <= head + tail:
        return b
    return b[:head] + "\n…[中段省略]…\n" + b[-tail:]


def _weak_signal(email: Email) -> bool:
    return len((email.body_text or "").strip()) < 120


from concurrent.futures import ThreadPoolExecutor



_EXTRACT = """提取这封卖方邮件为 buy-side 结构化信息。只基于该邮件内容，不可编造。

邮件：{email}

只输出 JSON：{{"broker":"发件机构名或 null","items":[{{"kind":"company_update|industry_signal|sell_side_view","company":..,"ticker":..,"industry":..,"company_en":..,"event_type":..,"summary":..,"what_changed":..,"evidence":..,"confidence":"high|medium|low","related_tickers":[..],"focus_fit":..,"action":..,"merge_key":..,"priority":..}}],"meetings":[{{"title":..,"industry":..,"company":..,"ticker":..,"date":..,"time":..(必须带时区，如"11:00 HKT"或"2pm-3pm HKT"),"host":..,"host_person":..(主持分析师，如 Lisa Liao/彭沈楠)..,"participants":..,"agenda_items":[看点关键词短语 1-2 条，每条≤14字，如"ABF膜涨价预期""国产替代测试进展"——不要完整问句],"related_tickers":[相关标的"公司名"数组——输出公司名(如 Sumitomo Electric、中际旭创)，不要 ticker(ticker可能未注册无法转] ,"language":..,"format":..,"registration":..,"recommendation":"recommend|consider|skip","reason":..}}],"filter_reason":null|"..."}}
（items/meetings 字段无值时省略该 key；同事件只列最值得的一条。）

要求：
- meetings：若邮件是会议邀请/多场活动清单，必须**逐场全部提取**每场（不合并、不丢场次）；
  每场含 title / industry / date / time(必须带时区，如 "11:00 HKT") / host / participants /
  agenda_items(看点关键词短语，每条≤14字，不要完整问句) / registration(取正文"立即报名"后的真实 URL，
  即使被 urldefense.proofpoint.com 包装也原样提取；无则 null) / recommendation / reason。
- items：公司/个股/行业信号，含 company/ticker/industry/company_en/event_type/summary/what_changed/
  evidence/confidence/related_tickers/focus_fit/action/merge_key/priority。
- broker：发件机构名（如 长江证券/广发证券/UBS/Jefferies/久谦）。
- 数量节制：每封 items 最多 3-4 条重点；同行业/同类聚合成一条（行业周报只出最重要 1-2 条行业要点，不要每个都提一点）。
- 覆盖过滤：只提取覆盖行业/覆盖公司/触及 ## Focus 的 item；非覆盖行业（美妆、消费、零售等不在 covered_industries）不要列为 item（除非与覆盖行业强 read-through）。
- 覆盖公司必拆：companies（coverage 名单）里的公司只要被实质提及（业绩/订单/评级/指引等），**必须拆成一个独立的 company item**（含 company/ticker/industry/summary/coverage 相关），不能只合并在行业面文本里。
- 跨天增量：merge_key 若在 system 的 last_events 出现过（昨天/之前提过），delta_vs_last 必须输出相对基线的**实质新增**（具体数字/新事实/新变化）；若只是重复旧信息、无实质新增，则该条不产出（放 filter_reason），不要重复报旧事。"""


_INTEGRATE_PROMPT = """下面是各邮件组提取的候选 items 与 meetings。请结合研究覆盖融合成最终结果：

- 去重：同 merge_key 的公司项合并为一条（跨 broker 归并，sources 保留所有来源邮件 key）
- 判定：按 coverage 标 bucket（core/other_coverage/new_idea/industry_signal）、coverage_status、是否 core
- 标 priority/focus_fit/confidence（取各来源最高）
- meetings 同理去重（同 title+company+date 合并），按 covered_industries 定 recommend/consider/skip
- 每条保留 sources（来源邮件 key 数组）、broker
只输出最终数组：{{"items":[{{"company":..,"ticker":..,"industry":..,"company_en":..,"event_type":..,"summary":..,"what_changed":..,"evidence":..,"confidence":..,"related_tickers":[..],"focus_fit":..,"focus_reason":..,"action":..,"bucket":..,"coverage_status":..,"priority":..,"merge_key":..,"delta_vs_last":..,"sources":[..],"broker":..}}],"meetings":[{{"title":..,"industry":..,"company":..,"ticker":..,"date":..,"time":..,"host":..,"host_person":..(主持分析师，如 Lisa Liao/彭沈楠)..,"participants":..,"agenda_items":[..],"related_tickers":[相关标的"公司名"数组——输出公司名(如 Sumitomo Electric、中际旭创)，不要 ticker(ticker可能未注册无法转] ,"language":..,"format":..,"registration":..,"recommendation":..,"reason":..,"sources":[..],"broker":..}}]}}

候选：
{summary}"""


def _group_emails(emails, names, tickers):
    """按公司/事件聚类：命中同一 coverage 公司名/ticker 的邮件同组；无命中 → misc 组。"""
    from collections import defaultdict
    groups_map = defaultdict(list)
    for e in emails:
        hay = ((e.subject or "") + " " + (e.body_text or "")[:300]).lower()
        host = None
        for ticker in sorted(tickers, key=len, reverse=True):
            t = ticker.lower()
            if t and t in hay:
                host = ticker
                break
        if host is None:
            for name in sorted(names, key=len, reverse=True)[:200]:
                n = name.lower()
                if len(n) >= 2 and n in hay:
                    host = name
                    break
        groups_map[host or "__misc__"].append(e)
    return [v for v in groups_map.values() if v]


def _extract_group(emails, workspace, system_coverage=None):
    """组 session（带精简 coverage system）：逐封 turn 提取，组内跨封记忆。coverage 供按覆盖行业过滤/控件数量。"""
    sys.path.insert(0, _shared_dir())
    from llm import Session
    sess = Session(workspace, system=system_coverage)
    items, meetings = [], []
    for e in emails:
        body = (e.body_text or "")  # 读全文——报名链接/中段议程等靠筛选(deep)完整保留，不 crop
        prompt = _EXTRACT.format(email=json.dumps({"subject": e.subject, "body": body},
                                                  ensure_ascii=False))
        # DeepSeek 对含特殊字符/长链的 body 偶发返回空 content → 重试（空或解析失败最多3次）
        parsed = None
        for _attempt in range(3):
            out = sess.turn(prompt, max_tokens=8192, timeout=240)
            if out:
                try:
                    parsed = _extract_json(out)
                    break
                except ValueError:
                    continue
            prompt = _EXTRACT.format(email=_extract_email_json(e)) + "\n（必须只输出 JSON，meetings 逐场全部提取；为空则重写）"
        if parsed is None:
            continue
        objs = parsed if isinstance(parsed, list) else [parsed]
        for obj in objs:
            if not isinstance(obj, dict):
                continue
            for it in obj.get("items") or []:
                it["_email_id"] = e.key
                it["sources"] = [e.key]
                items.append(it)
            for m in obj.get("meetings") or []:
                m["_email_id"] = e.key
                m["sources"] = [e.key]
                meetings.append(m)
    return {"items": items, "meetings": meetings, "keys": [e.key for e in emails]}


def _integrate(group_results, context, workspace):
    """整合 session（带 coverage，一次）：去重/归并/bucket/priority。"""
    sys.path.insert(0, _shared_dir())
    from llm import Session
    sess = Session(workspace, system=_coverage_system(context))   # coverage 只此一次
    summary = {"items": [it for g in group_results for it in g["items"]],
               "meetings": [m for g in group_results for m in g["meetings"]]}
    raw = sess.turn(_INTEGRATE_PROMPT.format(summary=json.dumps(summary, ensure_ascii=False)),
                    max_tokens=16384, timeout=180)
    try:
        final = _extract_json(raw or "")
    except ValueError:
        final = {"items": summary["items"], "meetings": summary["meetings"]}
    return final


def review_batch(emails: list[Email], context: dict, workspace: Path,
                 max_body: int = 2_500, chunk: int = 1) -> list[dict]:
    """gate → 分组 → 组 session 并行提取 → 整合 session（coverage 一次）→ reviews。"""
    system_coverage = _coverage_system(context)
    names, tickers = _gate_terms(context)

    # Stage 1: gate（粗筛，recall 优先）
    related, excluded = [], []
    for e in emails:
        if _weak_signal(e):
            excluded.append(e)
            continue
        if _deterministic_gate(e, names, tickers):
            related.append(e)
        else:
            excluded.append(e)
    maybes = [e for e in excluded if not _weak_signal(e)]
    with ThreadPoolExecutor(max_workers=4) as pool:
        verdicts = list(pool.map(lambda e: _llm_gate(e, system_coverage, workspace), maybes))
    related += [e for e, ok in zip(maybes, verdicts) if ok]
    excluded = [e for e in emails if e not in related]
    print(f"[email-intel] gate: scan={len(emails)} related={len(related)} excluded={len(excluded)}"
          f" (det=0token:{sum(1 for e in emails if _deterministic_gate(e, names, tickers))}, llm:{len(maybes)})")

    # Stage 2: 按公司/事件聚类分组 → 组 session 并行提取（带精简 coverage）
    groups = _group_emails(related, names, tickers)
    with ThreadPoolExecutor(max_workers=4) as pool:
        group_results = list(pool.map(lambda g: _extract_group(g, workspace, system_coverage), groups))

    print(f"[email-intel] extract: groups={len(groups)} group_items={sum(len(g['items']) for g in group_results)} group_meets={sum(len(g['meetings']) for g in group_results)}")
    # Stage 3: 整合（coverage 一次，只做去重/归并）——bucket/coverage/broker 程序化补
    from .classify import classify_item
    from .brief import _broker_label
    final = _integrate(group_results, context, workspace)   # 整合 LLM：items 去重/标 bucket
    merged = final if isinstance(final, dict) else {"items": []}
    it = merged.get("items") or []
    # meetings 透传组提取的全部（不整合，防 LLM 丢场次/报名链接）
    mt = [m for g in group_results for m in g["meetings"]]
    _sender_of = {e.key: e.sender for e in emails}
    _key_to_email = {e.key: e for e in emails}
    for x in it:
        x["bucket"] = classify_item(x, context)   # 确定性 bucket 存回（classify_item 返回 bucket）
        if not x.get("broker"):        # broker 从 sources 反查发送方
            for k in x.get("sources") or []:
                em = _key_to_email.get(k)
                if em:
                    x["broker"] = _broker_label(em.sender)
                    break
    for m in mt:
        if not m.get("broker"):
            for k in m.get("sources") or []:
                em = _key_to_email.get(k)
                if em:
                    m["broker"] = _broker_label(em.sender)
                    break

    out: list[dict] = []
    # 按来源邮件归拢（每条 item/meeting 已带 sources/_email_id）→ 组装 mail 级 review
    for _e in related:
        eits = [x for x in it if _e.key in (x.get("sources") or [])]
        emts = [x for x in mt if _e.key in (x.get("sources") or [])]
        out.append({"_email_id": _e.key, "items": eits, "meetings": emts})
    for _e in excluded:
        out.append({"_email_id": _e.key, "items": [], "meetings": [],
                    "filter_reason": "gate_excluded"})
    return out