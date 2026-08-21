#!/usr/bin/env python3
"""estimates-resolved.json 全局存储层（integration plan §6）。

位置：workspace/.cache/estimates/estimates-resolved.json
每公司一条：
    {TICKER: {
        "consensus": {...} | null,   # FMP analyst-estimates（未来财年一致预期）
        "forward":   null,           # skill 产出（driver-map/model-update → forward）
        "valuation": null,
        "next_earnings": null,
        "history":   []              # append-only：旧 consensus 快照
    }}
写必须带 source + updated_at；拿不到 = null 不硬凑。

用法：
    python3 estimates_store.py fill            # 全 COVERAGE 拉 FMP consensus
    python3 estimates_store.py fill --tickers 079550.KS,BESI.AS
    python3 estimates_store.py show            # 概览（有/无 consensus 家数）
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

_DIR = Path(__file__).resolve().parent
WS = _DIR.parent.parent

_CONSENSUS_FIELDS = (
    ("eps_avg", "epsAvg"), ("eps_high", "epsHigh"), ("eps_low", "epsLow"),
    ("revenue_avg", "revenueAvg"), ("revenue_high", "revenueHigh"), ("revenue_low", "revenueLow"),
    ("ebitda_avg", "ebitdaAvg"), ("net_income_avg", "netIncomeAvg"),
    ("num_analysts_eps", "numAnalystsEps"), ("num_analysts_revenue", "numAnalystsRevenue"),
)


def _key():
    for line in (WS / ".env").read_text(encoding="utf-8", errors="replace").splitlines():
        if line.strip().startswith("FMP_API_KEY="):
            return line.strip().split("=", 1)[1].strip().strip('"').strip("'")
    return ""


def estimates_path(workspace: Path) -> Path:
    return workspace / ".cache" / "estimates" / "estimates-resolved.json"


def load(workspace: Path = WS) -> dict:
    p = estimates_path(workspace)
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def save(workspace: Path, data: dict) -> None:
    p = estimates_path(workspace)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def fmp_consensus(ticker: str, key: str, limit: int = 4) -> list | None:
    """FMP analyst-estimates → 映射后的 periods 列表；失败/空返回 None。"""
    url = ("https://financialmodelingprep.com/stable/analyst-estimates"
           f"?symbol={urllib.parse.quote(ticker)}&period=annual&limit={limit}&apikey={key}")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "estimates-store/1.0"})
        with urllib.request.urlopen(req, timeout=25) as r:
            rows = json.loads(r.read(1_000_000).decode("utf-8", "replace"))
    except Exception:
        return None
    if not isinstance(rows, list) or not rows:
        return None
    return map_periods(rows)


def map_periods(rows: list) -> list:
    """FMP analyst-estimates 原始行 → periods 列表（date + 白名单字段）。"""
    periods = []
    for row in rows:
        if not isinstance(row, dict) or not row.get("date"):
            continue
        p = {"date": row["date"]}
        for ours, api in _CONSENSUS_FIELDS:
            v = row.get(api)
            if v is not None:
                p[ours] = v
        periods.append(p)
    return periods


def upsert_consensus(workspace: Path, ticker: str, periods: list, source: str) -> dict:
    """写入/刷新某公司 consensus 槽；旧值推入 history（append-only）。返回该公司条目。"""
    data = load(workspace)
    entry = data.setdefault(ticker, {
        "consensus": None, "forward": None, "valuation": None,
        "next_earnings": None, "history": [],
    })
    hist = entry.setdefault("history", [])
    if entry.get("consensus"):
        hist.append({"section": "consensus", "prev": entry["consensus"],
                     "archived_at": _now()})
    entry["consensus"] = {
        "source": source, "updated_at": _now(), "periods": periods,
    }
    save(workspace, data)
    return entry


_SKIP_COL = {"Field", "Status", "Monitor", "Ticker", "Company", "Values", "Contract", "#"}
_TICKER_RE = re.compile(r"^[A-Za-z0-9]+(\.[A-Z]{2,4})?$")


def coverage_tickers(workspace: Path) -> list[str]:
    """COVERAGE.md Coverage 表第一列 ticker（跳过列名/合同说明行，要求含市场后缀）。"""
    cov = workspace / "COVERAGE.md"
    out = []
    if cov.exists():
        for line in cov.read_text(encoding="utf-8", errors="replace").splitlines():
            m = re.match(r"^\|\s*([A-Za-z0-9.]+)\s*\|", line.strip())
            if m:
                t = m.group(1)
                if t in _SKIP_COL:
                    continue
                if _TICKER_RE.match(t) and "." in t:
                    out.append(t)
    return out


def fill(workspace: Path, tickers: list[str], key: str) -> dict:
    ok, missing = [], []
    for t in tickers:
        periods = fmp_consensus(t, key)
        if periods:
            upsert_consensus(workspace, t, periods, "fmp:analyst-estimates")
            ok.append(t)
        else:
            missing.append(t)
    return {"ok": ok, "missing": missing}


def _show(workspace: Path) -> int:
    data = load(workspace)
    h = health(workspace, list(data.keys()))
    print(f"estimates-resolved.json: {len(data)} 家")
    print(f"  L1 forward + consensus: {len(h['both'])}")
    print(f"  仅 forward:             {len(h['forward_only'])}")
    print(f"  仅 consensus (L2):      {len(h['consensus_only'])}")
    print(f"  缺 estimate:            {len(h['missing'])}  {h['missing'][:15]}")
    return 0


# ── forward 槽（L1 自有假设，skill 回写）──

_FORWARD_METRICS = (
    "eps", "revenue", "revenue_growth", "ebitda", "ebitda_margin",
    "net_income", "net_debt", "bvps", "fcf", "dps",
)


def upsert_forward(workspace: Path, ticker: str, metrics: dict, basis: str,
                   source: str, currency: str | None = None) -> dict:
    """写入/刷新某公司 forward 槽（basis: model/estimate/consensus/user-session）。

    metrics 只收 _FORWARD_METRICS 白名单字段，其他忽略；旧值推入 history。
    """
    assert basis in ("model", "estimate", "consensus", "user-session"), f"bad basis: {basis}"
    clean = {k: v for k, v in (metrics or {}).items() if k in _FORWARD_METRICS and v is not None}
    data = load(workspace)
    entry = data.setdefault(ticker, {
        "consensus": None, "forward": None, "valuation": None,
        "next_earnings": None, "history": [],
    })
    hist = entry.setdefault("history", [])
    if entry.get("forward"):
        hist.append({"section": "forward", "prev": entry["forward"],
                     "archived_at": _now()})
    entry["forward"] = {
        "basis": basis, "source": source, "updated_at": _now(),
        "currency": currency, "metrics": clean,
    }
    save(workspace, data)
    return entry


# ── 取数：L1 forward 优先，L2 consensus 兜底 ──

def effective(workspace: Path, ticker: str) -> dict:
    """返回 {level: "L1"|"L2"|"none", data: forward|consensus|None}。

    有 forward（L1 自有假设）→ 用它；无 → consensus（L2 外部一致预期）；
    都无 → none。与 consensus 差异即潜在 alpha，由调用方自行对比。
    """
    entry = load(workspace).get(ticker) or {}
    fwd = entry.get("forward")
    if fwd and fwd.get("metrics"):
        return {"level": "L1", "data": fwd}
    con = entry.get("consensus")
    if con and con.get("periods"):
        return {"level": "L2", "data": con}
    return {"level": "none", "data": None}


def health(workspace: Path, tickers: list[str] | None = None) -> dict:
    """估算覆盖统计：{both, forward_only, consensus_only, missing}（ticker 列表）。"""
    data = load(workspace)
    tks = tickers if tickers is not None else list(data.keys())
    both, f_only, c_only, missing = [], [], [], []
    for t in tks:
        fwd = bool((data.get(t) or {}).get("forward"))
        con = bool((data.get(t) or {}).get("consensus"))
        if fwd and con:
            both.append(t)
        elif fwd:
            f_only.append(t)
        elif con:
            c_only.append(t)
        else:
            missing.append(t)
    return {"both": both, "forward_only": f_only, "consensus_only": c_only, "missing": missing}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="estimates-resolved.json 存储层")
    sub = ap.add_subparsers(dest="cmd")
    f = sub.add_parser("fill", help="拉 FMP analyst-estimates 写 consensus 槽")
    f.add_argument("--tickers", default="", help="逗号分隔；空 = 全 COVERAGE")
    f.add_argument("--workspace", default="", help="workspace 根（默认自动发现）")
    sf = sub.add_parser("set-forward", help="写入/刷新 forward 槽（L1 自有假设，skill 回写用）")
    sf.add_argument("ticker")
    sf.add_argument("--basis", required=True, choices=("model", "estimate", "consensus", "user-session"))
    sf.add_argument("--source", required=True, help="产出来源（driver-map/model-update/...）")
    sf.add_argument("--currency")
    for _m in _FORWARD_METRICS:
        sf.add_argument(f"--{_m.replace('_','-')}", type=float)
    sf.add_argument("--workspace", default="", help="workspace 根（默认自动发现）")
    sub.add_parser("show", help="概览")
    args = ap.parse_args(argv)

    ws = Path(args.workspace) if getattr(args, "workspace", "") else WS
    key = _key()
    if not key:
        print("error: FMP_API_KEY 缺失（.env）")
        return 2
    if args.cmd == "set-forward":
        metrics = {k: getattr(args, k, None) for k in _FORWARD_METRICS}
        metrics = {k: v for k, v in metrics.items() if v is not None}
        upsert_forward(ws, args.ticker, metrics, args.basis, args.source, args.currency)
        print(f"forward 已写入 {args.ticker}（basis={args.basis}, source={args.source}, metrics={list(metrics)}）")
        return 0
    if args.cmd == "fill":
        tickers = [t.strip() for t in args.tickers.split(",") if t.strip()] if args.tickers else coverage_tickers(ws)
        res = fill(ws, tickers, key)
        print(f"consensus 写入 {len(res['ok'])} 家，缺失 {len(res['missing'])} 家: {res['missing'][:15]}")
        return 0
    if args.cmd == "show":
        return _show(ws)
    ap.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
