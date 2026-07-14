import argparse
import importlib
import json
import math
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
HOOKS_DIR = ROOT / ".claude" / "hooks"
if str(HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(HOOKS_DIR))

import fill_gaps  # noqa: E402


CONFIG_PATH = Path(__file__).with_name("financial_data_lite_samples.json")
def _find_plugin_root():
    """Walk up from test file dir to find plugin dev repo root."""
    p = ROOT
    while p != p.parent:
        if (p / "plugins" / "buy-side-research-skills" / "skills").is_dir():
            return p
        p = p.parent
    return None

_PLUGIN_ROOT = _find_plugin_root()
_PROVIDER_REL = "plugins/buy-side-research-skills/skills/financial-data/scripts/providers"

PROVIDER_ROOTS = []
if _PLUGIN_ROOT:
    PROVIDER_ROOTS.append(_PLUGIN_ROOT / _PROVIDER_REL)

SKILL_DOC_VARIANTS = {}
if _PLUGIN_ROOT:
    SKILL_DOC_VARIANTS["repo"] = _PLUGIN_ROOT / "plugins" / "buy-side-research-skills" / "skills"
DOC_CONTRACT_TARGETS = {
    "financial-data": "Growth-first consumer profile:",
    "stock-quickread": "Consumer data contract: consume `segments.status`, `segments.segments`, plus growth-first `supplementary` fields",
    "peer-deep-dive": "Consumer data contract: consume `segments.status`, `segments.segments`, plus growth-first `supplementary` fields",
    "comps-analysis": "Consumer data contract: consume `segments.status`, `segments.segments`, plus growth-first `supplementary` fields",
    "cross-market-compare": "Consumer data contract: consume `segments.status`, `segments.segments`, plus growth-first `supplementary` fields",
    "earnings-setup": "Consumer data contract: consume `segments.status`, `segments.segments`, plus growth-first `supplementary` fields",
    "consensus-map": "Consumer data contract: consume `segments.status`, `segments.segments`, plus growth-first `supplementary` fields",
    "bear-pre-mortem": "Consumer data contract: consume `segments.status`, `segments.segments`, plus growth-first `supplementary` fields",
}
PLUGIN_ROOT_CANDIDATES = []
if _PLUGIN_ROOT:
    PLUGIN_ROOT_CANDIDATES.append(_PLUGIN_ROOT)


def _load_config():
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def _provider_root():
    for root in PROVIDER_ROOTS:
        if root.is_dir():
            return root
    return None


def _plugin_root():
    for root in PLUGIN_ROOT_CANDIDATES:
        script = root / "plugins" / "buy-side-research-skills" / "skills" / "financial-data" / "scripts" / "financial_data.py"
        if root.is_dir() and script.is_file():
            return root
    return None


def _load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _print_sample_result(name, market, coverage, latest_period, latest_basis):
    print(f"[sample] {name} ({market})")
    print(f"  latest_quarter_period={latest_period!s}")
    print(f"  latest_quarter_period_basis={latest_basis!s}")
    print(f"  total_fill_rate={coverage['fill_rate']}%")
    print(f"  consumer_required_fill_rate={coverage['consumer_required_fill_rate']}%")
    print(f"  layer2_fill_share={coverage['layer2_fill_share']}%")
    print(f"  layer2_plus_official_fill_share={coverage['layer2_plus_official_fill_share']}%")
    print(f"  core_fields_fill_rate={coverage['core_fields_fill_rate']}%")
    print(f"  segments_status={coverage.get('segments_status')!s}")
    print(f"  segments_count={coverage.get('segments_count')!s}")
    print(f"  supplementary_high_value_fill_rate={coverage.get('supplementary_high_value_fill_rate')}%")
    print(f"  supplementary_sector_conditional_fill_rate={coverage.get('supplementary_sector_conditional_fill_rate')}%")
    if coverage["provider_gap_list"]:
        print("  provider_gap_list=" + ", ".join(coverage["provider_gap_list"][:8]))
    if coverage.get("provider_gap_reason_counts"):
        rendered = ", ".join(f"{k}={v}" for k, v in sorted(coverage["provider_gap_reason_counts"].items()) if v)
        if rendered:
            print("  provider_gap_reason_counts=" + rendered)
    if coverage.get("supplementary_high_value_missing"):
        print("  supplementary_high_value_missing=" + ", ".join(coverage["supplementary_high_value_missing"][:8]))
    if coverage.get("supplementary_sector_conditional_missing"):
        print("  supplementary_sector_conditional_missing=" + ", ".join(coverage["supplementary_sector_conditional_missing"][:8]))
    if coverage.get("skippable_missing_fields"):
        print("  skippable_missing_fields=" + ", ".join(coverage["skippable_missing_fields"][:8]))
    if coverage["missing_fields"]:
        print("  missing_fields=" + ", ".join(coverage["missing_fields"][:8]))


def _find_nonfinite_field_paths(data):
    bad = []

    def walk(node, path=""):
        if isinstance(node, dict):
            if set(node.keys()) >= {"value", "source_layer", "source_detail"}:
                value = node.get("value")
                if isinstance(value, float) and not math.isfinite(value):
                    bad.append(path)
            for key, value in node.items():
                next_path = f"{path}.{key}" if path else key
                walk(value, next_path)
        elif isinstance(node, list):
            for idx, value in enumerate(node):
                walk(value, f"{path}[{idx}]")

    walk(data)
    return bad


def _safe_text(text):
    value = str(text)
    try:
        value.encode(sys.stdout.encoding or "utf-8")
        return value
    except Exception:
        return value.encode("ascii", errors="backslashreplace").decode("ascii")


def run_segment_derivation_fixture(verbose=True):
    fixture_data = {
        "latest_fy_period": "FY2025",
        "latest_quarter_period": "FY2026Q1",
        "latest_quarter_period_label": "Q1 FY2026",
        "latest_quarter_period_basis": "quarter",
        "currency": "USD",
        "income_statement": {
            "latest_fy": {
                "revenue": {"value": 1000.0, "source_layer": "provider_api", "source_detail": "fixture"},
                "operating_income": {"value": 200.0, "source_layer": "provider_api", "source_detail": "fixture"},
            },
            "latest_quarter": {
                "revenue": {"value": 330.0, "source_layer": "provider_api", "source_detail": "fixture"},
                "operating_income": {"value": 66.0, "source_layer": "provider_api", "source_detail": "fixture"},
            },
        },
    }
    entries = [
        {"name": "Compute", "type": "business_line", "period": "FY2024", "metric": "revenue", "value": 500.0, "unit": "USD"},
        {"name": "Compute", "type": "business_line", "period": "FY2025", "metric": "revenue", "pct_of_total": 60.0, "unit": "USD"},
        {"name": "Compute", "type": "business_line", "period": "FY2025", "metric": "operating_income", "margin_pct": 20.0, "unit": "USD"},
        {"name": "Compute", "type": "business_line", "period": "FY2025Q4", "metric": "revenue", "value": 300.0, "unit": "USD"},
        {"name": "Compute", "type": "business_line", "period": "FY2026Q1", "metric": "revenue", "sequential_pct": 10.0, "unit": "USD"},
        {"name": "Services", "type": "business_line", "period": "FY2025", "metric": "revenue", "value": 100.0, "unit": "USD"},
    ]
    normalized = fill_gaps._normalize_segment_entries(entries, fixture_data, "official_web", "fixture")
    by_key = {
        (entry["name"], entry["metric"], entry["period"]): entry
        for entry in normalized
    }
    mismatches = []
    compute_fy = by_key.get(("Compute", "revenue", "FY2025"), {})
    compute_margin = by_key.get(("Compute", "operating_income", "FY2025"), {})
    compute_q1 = by_key.get(("Compute", "revenue", "FY2026Q1"), {})
    services_fy = by_key.get(("Services", "revenue", "FY2025"), {})

    if round(float(compute_fy.get("value") or 0.0), 2) != 600.0:
        mismatches.append(f"expected Compute FY2025 value=600, got {compute_fy.get('value')}")
    if round(float(compute_fy.get("ratio") or 0.0), 4) != 0.6:
        mismatches.append(f"expected Compute FY2025 ratio=0.6, got {compute_fy.get('ratio')}")
    if round(float(compute_fy.get("yoy_pct") or 0.0), 4) != 20.0:
        mismatches.append(f"expected Compute FY2025 yoy_pct=20, got {compute_fy.get('yoy_pct')}")
    if round(float(compute_margin.get("value") or 0.0), 2) != 120.0:
        mismatches.append(f"expected Compute FY2025 operating_income value=120, got {compute_margin.get('value')}")
    if round(float(compute_margin.get("ratio") or 0.0), 4) != 0.2:
        mismatches.append(f"expected Compute FY2025 operating_income ratio=0.2, got {compute_margin.get('ratio')}")
    if round(float(compute_q1.get("value") or 0.0), 2) != 330.0:
        mismatches.append(f"expected Compute FY2026Q1 value=330, got {compute_q1.get('value')}")
    if round(float(services_fy.get("pct_of_total") or 0.0), 4) != 10.0:
        mismatches.append(f"expected Services FY2025 pct_of_total=10, got {services_fy.get('pct_of_total')}")
    if round(float(services_fy.get("ratio") or 0.0), 4) != 0.1:
        mismatches.append(f"expected Services FY2025 ratio=0.1, got {services_fy.get('ratio')}")

    result = {
        "segment_count": len(normalized),
        "mismatches": mismatches,
    }
    if verbose:
        print("[segment-derivation-fixture]")
        print(f"  segment_count={result['segment_count']}")
        print("  status=" + ("ok" if not mismatches else "mismatch"))
        if mismatches:
            print("  mismatches=" + "; ".join(mismatches))
    return result


def run_actuals_samples(run_fill=False, verbose=True):
    config = _load_config()
    summaries = []
    for sample in config.get("actuals_samples", []):
        actuals_path = ROOT / sample["actuals_path"]
        if run_fill:
            subprocess.run(
                [sys.executable, str(HOOKS_DIR / "fill_gaps.py"), sample["industry"], sample["ticker_slug"]],
                cwd=str(ROOT),
                check=False,
            )
        data = _load_json(actuals_path)
        coverage = fill_gaps.build_coverage_report(data)
        nonfinite_fields = _find_nonfinite_field_paths(data)
        latest_period = data.get("latest_quarter_period")
        latest_basis = data.get("latest_quarter_period_basis")
        layer3_sources = fill_gaps.get_layer3_sources(data, sample["market"])
        first_official_query = next((item["query"] for item in layer3_sources if item["layer_name"] == "official_web"), None)
        if verbose:
            _print_sample_result(sample["name"], sample["market"], coverage, latest_period, latest_basis)
            if first_official_query:
                print("  first_official_query=" + _safe_text(first_official_query))
        expected = sample.get("expected", {})
        mismatches = []
        if expected.get("latest_quarter_period_basis") and latest_basis != expected["latest_quarter_period_basis"]:
            mismatches.append(f"expected basis={expected['latest_quarter_period_basis']}, got {latest_basis}")
        if expected.get("quarter_dominant") and latest_period and latest_basis == "half_year":
            mismatches.append("quarter-dominant sample landed on half_year")
        expected_official_contains = expected.get("official_query_contains", [])
        for token in expected_official_contains:
            if not first_official_query or token.lower() not in first_official_query.lower():
                mismatches.append(f"expected official query to contain {token!r}, got {first_official_query!r}")
        expected_segments_status = expected.get("segments_status")
        if expected_segments_status and coverage.get("segments_status") != expected_segments_status:
            mismatches.append(
                f"expected segments_status={expected_segments_status}, got {coverage.get('segments_status')}"
            )
        if nonfinite_fields:
            mismatches.append("non-finite values present: " + ", ".join(nonfinite_fields[:8]))
        if not coverage.get("segments_status"):
            mismatches.append("segments_status missing")
        if "supplementary_high_value_fill_rate" not in coverage:
            mismatches.append("supplementary_high_value_fill_rate missing")
        if "supplementary_sector_conditional_fill_rate" not in coverage:
            mismatches.append("supplementary_sector_conditional_fill_rate missing")
        if "skippable_missing_fields" not in coverage:
            mismatches.append("skippable_missing_fields missing")
        if "provider_gap_reason_counts" not in coverage:
            mismatches.append("provider_gap_reason_counts missing")
        summaries.append({
            "name": sample["name"],
            "market": sample["market"],
            "coverage": coverage,
            "nonfinite_fields": nonfinite_fields,
            "latest_quarter_period": latest_period,
            "latest_quarter_period_basis": latest_basis,
            "first_official_query": first_official_query,
            "segments_status": coverage.get("segments_status"),
            "segments_count": coverage.get("segments_count"),
            "mismatches": mismatches,
        })
    return summaries


def run_provider_smoke(verbose=True):
    root = _provider_root()
    if not root:
        print("[provider-smoke] provider root unavailable")
        return []
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

    config = _load_config()
    results = []
    for sample in config.get("provider_smoke_samples", []):
        provider_name = sample["provider"]
        module = importlib.import_module(provider_name)
        info = {
            "name": sample["name"],
            "provider": provider_name,
            "dependency_available": bool(module.dependency_available()),
            "status": "skipped",
        }
        if info["dependency_available"]:
            request = dict(sample.get("request", {}))
            request["identifier"] = sample["identifier"]
            try:
                if provider_name == "sec_provider":
                    sec_cache_dir = ROOT / ".claude" / "hooks" / "tests" / "_tmp" / "edgar"
                    sec_cache_dir.mkdir(parents=True, exist_ok=True)
                    os.environ["EDGAR_LOCAL_DATA_DIR"] = str(sec_cache_dir)
                result = module.fetch(request)
                periods, basis = fill_gaps._collect_periods_and_basis(result)
                _, latest_qh = fill_gaps._select_latest_periods(periods, basis)
                info["status"] = result.get("status", "unknown")
                info["items_extracted"] = result.get("items_extracted", [])
                info["latest_qh_period"] = latest_qh
                info["latest_qh_basis"] = basis.get(latest_qh) if latest_qh else None
            except Exception as exc:
                info["status"] = f"error: {exc}"
        if verbose:
            print(f"[provider-smoke] {info['name']} provider={provider_name} dependency={info['dependency_available']} status={info['status']}")
            if info.get("latest_qh_period"):
                print(f"  latest_qh_period={info['latest_qh_period']} basis={info.get('latest_qh_basis')}")
        results.append(info)
    return results


def run_doc_contract_consistency(verbose=True):
    results = []
    for skill_name, snippet in DOC_CONTRACT_TARGETS.items():
        variants = {}
        mismatches = []
        for variant_name, root in SKILL_DOC_VARIANTS.items():
            path = root / skill_name / "SKILL.md"
            info = {
                "path": str(path),
                "exists": path.is_file(),
                "snippet_present": False,
                "matched_line": None,
            }
            if path.is_file():
                text = path.read_text(encoding="utf-8")
                for line in text.splitlines():
                    if snippet in line:
                        info["snippet_present"] = True
                        info["matched_line"] = line.strip()
                        break
            variants[variant_name] = info
        present_lines = [info["matched_line"] for info in variants.values() if info["matched_line"]]
        if len(present_lines) != len(SKILL_DOC_VARIANTS):
            missing = [name for name, info in variants.items() if not info["snippet_present"]]
            mismatches.append("missing snippet in: " + ", ".join(missing))
        elif len(set(present_lines)) != 1:
            mismatches.append("contract line drift across variants")
        result = {
            "skill": skill_name,
            "required_snippet": snippet,
            "variants": variants,
            "mismatches": mismatches,
        }
        if verbose:
            print(f"[doc-consistency] {skill_name} status=" + ("ok" if not mismatches else "mismatch"))
            if mismatches:
                print("  mismatches=" + "; ".join(mismatches))
        results.append(result)
    return results


def run_cli_smoke(verbose=True):
    plugin_root = _plugin_root()
    if not plugin_root:
        result = {
            "status": "skipped",
            "reason": "plugin_root_unavailable",
            "check_deps_ok": False,
            "missing_args_failure_ok": False,
            "mismatches": ["plugin_root unavailable"],
        }
        if verbose:
            print("[cli-smoke] status=skipped reason=plugin_root_unavailable")
        return result

    script_path = plugin_root / "plugins" / "buy-side-research-skills" / "skills" / "financial-data" / "scripts" / "financial_data.py"
    mismatches = []

    deps = subprocess.run(
        [sys.executable, str(script_path), "--check-deps"],
        cwd=str(plugin_root),
        capture_output=True,
        text=True,
        check=False,
    )
    deps_json = {}
    if deps.returncode != 0:
        mismatches.append(f"--check-deps exit={deps.returncode}")
    else:
        try:
            deps_json = json.loads(deps.stdout)
        except Exception as exc:
            mismatches.append(f"--check-deps invalid json: {exc}")
        else:
            packages = deps_json.get("packages", {})
            env = deps_json.get("env", {})
            if not packages:
                mismatches.append("--check-deps missing packages payload")
            if not env:
                mismatches.append("--check-deps missing env payload")

    missing_args = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=str(plugin_root),
        capture_output=True,
        text=True,
        check=False,
    )
    missing_args_json = {}
    if missing_args.returncode == 0:
        mismatches.append("missing-args invocation unexpectedly succeeded")
    else:
        try:
            missing_args_json = json.loads(missing_args.stdout)
        except Exception as exc:
            mismatches.append(f"missing-args invalid json: {exc}")
        else:
            if missing_args_json.get("error") != "--market and --identifier required":
                mismatches.append(
                    "missing-args error drift: " + repr(missing_args_json.get("error"))
                )

    result = {
        "status": "ok" if not mismatches else "mismatch",
        "script_path": str(script_path),
        "check_deps_ok": deps.returncode == 0 and not [m for m in mismatches if m.startswith("--check-deps")],
        "missing_args_failure_ok": missing_args.returncode != 0 and not [m for m in mismatches if m.startswith("missing-args")],
        "package_count": len((deps_json or {}).get("packages", {})),
        "configured_env_count": sum(
            1
            for item in (deps_json or {}).get("env", {}).values()
            if isinstance(item, dict) and item.get("configured")
        ),
        "mismatches": mismatches,
    }
    if verbose:
        print("[cli-smoke] status=" + result["status"])
        print(f"  check_deps_ok={result['check_deps_ok']}")
        print(f"  missing_args_failure_ok={result['missing_args_failure_ok']}")
        if mismatches:
            print("  mismatches=" + "; ".join(mismatches))
    return result


def main():
    parser = argparse.ArgumentParser(
        description="Financial-Data Lite regression runner (defaults to release-critical checks only)"
    )
    parser.add_argument("--run-fill", action="store_true", help="Re-run fill_gaps.py for actuals-backed samples before reporting")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON summary")
    parser.add_argument("--output", help="Optional path to write the JSON payload directly")
    parser.add_argument(
        "--with-provider-smoke",
        action="store_true",
        help="Include slower provider fetch smoke tests in addition to release-critical checks",
    )
    parser.add_argument(
        "--with-doc-consistency",
        action="store_true",
        help="Include cross-variant doc contract checks; off by default because they are not release-critical",
    )
    args = parser.parse_args()

    verbose = not args.json
    actuals = run_actuals_samples(run_fill=args.run_fill, verbose=verbose)
    derivation = run_segment_derivation_fixture(verbose=verbose)
    cli_smoke = run_cli_smoke(verbose=verbose)
    smoke = run_provider_smoke(verbose=verbose) if args.with_provider_smoke else []
    docs = run_doc_contract_consistency(verbose=verbose) if args.with_doc_consistency else []
    payload = {
        "actuals_samples": actuals,
        "provider_smoke": smoke,
        "segment_derivation_fixture": derivation,
        "cli_smoke": cli_smoke,
        "doc_contract_consistency": docs,
        "run_profile": {
            "provider_smoke_enabled": args.with_provider_smoke,
            "doc_contract_consistency_enabled": args.with_doc_consistency,
        },
    }
    if args.json:
        rendered = json.dumps(payload, ensure_ascii=True, indent=2)
        if args.output:
            Path(args.output).write_text(rendered, encoding="utf-8")
        else:
            print(rendered)


if __name__ == "__main__":
    main()
