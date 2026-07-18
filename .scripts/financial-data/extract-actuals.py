#!/usr/bin/env python3
"""extract-actuals.py — Extract financial data from IR filing markdown files.

Usage:
    # Scan: show what data is available in filings
    python extract-actuals.py --filings-dir .cache/financial-data/filings/ --ticker 5334.T --scan

    # Validate: check that all values in actuals-resolved.json exist in source MDs
    python extract-actuals.py --filings-dir .cache/financial-data/filings/ --validate actuals-resolved.json

    # Template: output a blank actuals template for the agent to fill
    python extract-actuals.py --ticker 5334.T --template

Design:
    - This script scaffolds and validates. The agent (Claude) does the LLM extraction
      from markdown to structured JSON.
    - Anti-hallucination: every numeric value in actuals MUST be findable in source MD.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


EXPECTED_FIELDS = {
    "income_statement": [
        "revenue", "cost_of_sales", "gross_profit",
        "operating_income", "pretax_income", "net_income",
        "eps_basic", "dps",
    ],
    "balance_sheet": [
        "cash", "receivables", "inventories",
        "current_assets", "ppe", "goodwill_intangibles",
        "total_assets", "payables", "total_debt", "total_liabilities",
        "total_equity",
    ],
    "cash_flow": [
        "operating_cf", "investing_cf", "financing_cf",
        "depreciation", "capex",
    ],
}


def load_markdown_files(filings_dir: Path) -> dict[str, str]:
    """Load all markdown files from filings directory. Returns {filename: content}."""
    result = {}
    if not filings_dir.is_dir():
        print(f"ERROR: filings dir not found: {filings_dir}", file=sys.stderr)
        return result
    for f in sorted(filings_dir.glob("*.md")):
        result[f.name] = f.read_text(encoding="utf-8")
    return result


def scan_filings(filings_dir: Path):
    """Scan filings and report what financial data is available."""
    mds = load_markdown_files(filings_dir)
    if not mds:
        print("No markdown filings found.")
        return

    print(f"=== Filings: {len(mds)} files ===")
    for name, content in mds.items():
        chars = len(content)
        # Count potential numeric values (currency amounts)
        numbers = len(re.findall(r"[\d,]+\.?\d*", content))
        print(f"  {name}: {chars:,} chars, ~{numbers} numeric values")

    # Check for key financial terms across all MDs
    combined = " ".join(mds.values()).lower()
    print(f"\n=== Field coverage (combined {len(combined):,} chars) ===")
    for section, fields in EXPECTED_FIELDS.items():
        found = {f: f.lower().replace("_", " ") in combined for f in fields}
        count = sum(found.values())
        missing = [f for f, ok in found.items() if not ok]
        pct = f"{count}/{len(fields)}"
        if missing:
            pct += f"  (missing: {', '.join(missing)})"
        print(f"  {section}: {pct}")


def get_template(ticker: str) -> dict:
    """Return a blank actuals template."""
    statements = {}
    for section, fields in EXPECTED_FIELDS.items():
        items = []
        for concept in fields:
            items.append({
                "label": f"[FILL - {concept}]",
                "concept": concept,
                "values": {"FY____": "[FILL]", "FY____": "[FILL]"},
                "unit": "[FILL]",
                "source": "[FILL - S# from source_map]",
            })
        statements[section] = items

    return {
        "schema_version": 2,
        "ticker": ticker,
        "market": "[FILL]",
        "source": "ir_playwright",
        "statements": {
            **statements,
            "revenue_split": [{
                "segment": "[FILL]",
                "type": "business",
                "revenue": {"FY____": "[FILL]"},
                "source": "[FILL]",
            }],
        },
        "market_data": {
            "price": "[FILL - yfinance]",
            "market_cap": "[FILL - yfinance]",
            "pe_ttm": "[FILL]",
            "pb": "[FILL]",
            "source_layer": "yfinance",
        },
        "source_map": {
            "S1": {"source_layer": "ir_playwright", "url": "[FILL]", "detail": "[FILL]", "label": "S1"},
        },
    }


def validate_actuals(actuals_path: Path, filings_dir: Path) -> bool:
    """Validate that every numeric value in actuals exists in source MDs."""
    mds = load_markdown_files(filings_dir)
    if not mds:
        print("ERROR: no markdown filings to validate against", file=sys.stderr)
        return False

    combined = " ".join(mds.values())
    # Remove all whitespace and commas for numeric matching
    combined_clean = re.sub(r"[\s,]", "", combined)

    actuals = json.loads(actuals_path.read_text(encoding="utf-8"))

    total = 0
    errors = []
    statements = actuals.get("statements", {})

    for section in ["income_statement", "balance_sheet", "cash_flow"]:
        for item in statements.get(section, []):
            values = item.get("values", {})
            for period, val in values.items():
                if val is None or isinstance(val, str):
                    continue
                total += 1
                val_str = str(abs(int(val)) if isinstance(val, float) and val == int(val) else abs(val)).replace(".0", "")
                if val_str not in combined_clean:
                    label = item.get("label", item.get("concept", "?"))
                    errors.append(f"  MISS: {label} {period}={val} (raw='{val_str}' not in source)")

    # Revenue split
    for seg in statements.get("revenue_split", []):
        for key in ("revenue", "op_profit"):
            for period, val in seg.get(key, {}).items():
                if val is None:
                    continue
                total += 1
                val_str = str(abs(int(val))).replace(".0", "")
                if val_str not in combined_clean:
                    errors.append(f"  MISS: {seg['segment']} {key} {period}={val}")

    print(f"=== Validation: {actuals_path} ===")
    print(f"  Total numeric fields: {total}")
    print(f"  Errors (value not in source): {len(errors)}")
    for e in errors:
        print(e)

    if total == 0:
        print("  WARN: no numeric fields to validate — template not filled?")
        return False

    ok = len(errors) == 0
    print(f"  Result: {'ALL VALUES IN SOURCE' if ok else f'{total - len(errors)}/{total} verified'}")
    return ok


def main():
    parser = argparse.ArgumentParser(description="Extract financial data from IR filings")
    parser.add_argument("--filings-dir", help="Directory containing markdown filings")
    parser.add_argument("--ticker", help="Ticker symbol")
    parser.add_argument("--scan", action="store_true", help="Scan filings for available financial data")
    parser.add_argument("--template", action="store_true", help="Output a blank actuals template")
    parser.add_argument("--validate", help="Validate an existing actuals-resolved.json against source MDs")
    args = parser.parse_args()

    if args.template:
        if not args.ticker:
            print("ERROR: --ticker required with --template", file=sys.stderr)
            sys.exit(1)
        template = get_template(args.ticker)
        print(json.dumps(template, indent=2, ensure_ascii=False))
        return

    if args.validate:
        actuals_path = Path(args.validate)
        if not args.filings_dir:
            print("ERROR: --filings-dir required with --validate", file=sys.stderr)
            sys.exit(1)
        ok = validate_actuals(actuals_path, Path(args.filings_dir))
        sys.exit(0 if ok else 1)

    if args.scan:
        if not args.filings_dir:
            print("ERROR: --filings-dir required with --scan", file=sys.stderr)
            sys.exit(1)
        scan_filings(Path(args.filings_dir))
        return

    # No mode specified — show help
    parser.print_help()


if __name__ == "__main__":
    main()
