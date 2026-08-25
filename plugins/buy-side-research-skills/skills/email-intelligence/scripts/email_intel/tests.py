"""Lightweight unit tests for gate / classify / broker (no LLM calls)."""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]   # email-intelligence/
sys.path.insert(0, str(ROOT))
from email_intel.parse import Email
from email_intel.ai_review import _gate_terms, _deterministic_gate
from email_intel.classify import classify_item
from email_intel.brief import _broker_label

ctx = {
    "coverage": [
        {"ticker": "RHM.DE", "company_en": "Rheinmetall", "company_native": "莱茵金属",
         "industry": "Defense", "coverage": "Modeled", "is_core": True},
        {"ticker": "002371.SZ", "company_en": "NAURA", "company_native": "北方华创",
         "industry": "Semiconductor-Equipment", "coverage": "Quickread", "is_core": False},
    ],
    "covered_industries": ["Defense", "Semiconductor-Equipment"],
    "focus": "国产替代、订单能见度",
}

passed = failed = 0
def check(name, cond):
    global passed, failed
    if cond: passed += 1
    else: failed += 1; print("  ✗ FAIL:", name)

def email(subj="", body="", sender=""):
    return Email(folder="f", path="/tmp", subject=subj, body_text=body, sender=sender)

# --- gate ---
names, tickers = _gate_terms(ctx)
check("gate: ticker 命中", _deterministic_gate(email(body="Rheinmetall 获订单"), names, tickers))
check("gate: 英文公司名命中", _deterministic_gate(email(body="莱茵金属 订单"), names, tickers))
check("gate: 无关不命中", not _deterministic_gate(email(body="美妆珀莱雅 618"), names, tickers))

# --- classify ---
r = classify_item(dict(company="Rheinmetall", ticker="RHM.DE", industry="Defense"), ctx)
check("classify: 覆盖公司(ticker) → core", r == "core")
r2 = classify_item(dict(company="NAURA", ticker="002371.SZ"), ctx)
check("classify: 非core覆盖 → other_coverage", r2 == "other_coverage")
r3 = classify_item(dict(company="珀莱雅", industry="Consumer"), ctx)
check("classify: 无关行业 → industry_signal", r3 == "industry_signal")

# --- broker ---
check("broker: ubs → UBS", _broker_label("a@ubs.com") == "UBS")
check("broker: cjsc 子域 → 长江", _broker_label("x@mailservice.cjsc.com.cn") == "长江证券")
check("broker: 未知域原样", _broker_label("p@unknown.xyz") == "p@unknown.xyz")

print(f"\n测试通过 {passed} / {passed+failed}")
sys.exit(1 if failed else 0)
