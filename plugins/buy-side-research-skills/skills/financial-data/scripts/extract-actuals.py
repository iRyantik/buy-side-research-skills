#!/usr/bin/env python3
"""extract-actuals.py — Extract financial data from IR filing markdown files.

Usage:
    # Scan: show which registry concepts are found in filings
    python extract-actuals.py --filings-dir <path> --scan

    # Template extraction: locate fields using filing-templates.json
    python extract-actuals.py --filings-dir <path> --filing-type jp_kessan_tanshin

    # Guided extraction: per-field context windows (best for MarkItDown output)
    python extract-actuals.py --filings-dir <path> --filing-type jp_kessan_tanshin --guided

    # Table-dump extraction: dump entire IS/BS/CF table regions (best for pymupdf4llm)
    python extract-actuals.py --filings-dir <path> --filing-type tw_financial_report --table-dump

    # Validate: check all values in actuals exist in source filings
    python extract-actuals.py --validate <actuals.json> --filings-dir <path>

    # Template: output blank actuals skeleton from field registry
    python extract-actuals.py --ticker 5334.T --template

Field schema: .references/policy/statement-line-items.md — the single source of truth.
Principle: extract everything the filing has. No field caps. Concept normalization via registry.
"""
from __future__ import annotations

import argparse, json, re, sys
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


# ── Registry loader ──────────────────────────────────────────

def load_registry(workspace: Path | None = None) -> dict:
    """Parse statement-line-items.md → {concept: {labels, section, ...}}."""
    if workspace is None:
        workspace = Path(__file__).resolve().parent.parent.parent
    reg_path = workspace / ".references" / "policy" / "statement-line-items.md"
    if not reg_path.exists():
        reg_path = workspace / "references" / "policy" / "statement-line-items.md"
    if not reg_path.exists():
        return {}

    text = reg_path.read_text(encoding="utf-8")
    registry = {}
    current_section = None

    for line in text.split("\n"):
        # Detect section
        if "利润表" in line or "Income Statement" in line:
            current_section = "income_statement"
            continue
        if "资产负债表" in line or "Balance Sheet" in line:
            current_section = "balance_sheet"
            continue
        if "现金流量表" in line or "Cash Flow" in line:
            current_section = "cash_flow"
            continue
        if "分部" in line or "Segment" in line:
            current_section = "supplementary"
            continue

        # Parse table rows with concept codes like IS-01, BS-01, etc.
        m = re.match(r'\| (IS-\d+|BS-\d+|CF-\d+|SG-\d+|MK-\d+) \| (\w+) \|', line)
        if m:
            code = m.group(1)
            concept = m.group(2)
            cols = [c.strip() for c in line.split("|")]
            # Build search terms from all market-specific labels
            labels = set()
            for c in cols[3:]:
                if c and c not in ("—", "-", "FS", "MKT", "DER", "CON", ""):
                    for label in re.split(r'\s*/\s*', c):
                        label = label.strip()
                        if label and len(label) >= 2:
                            labels.add(label)
            registry[concept] = {
                "code": code,
                "section": current_section or "unknown",
                "labels": sorted(labels, key=len, reverse=True),
            }

    return registry


def load_markdown_files(filings_dir: Path) -> dict:
    result = {}
    if not filings_dir.is_dir(): return result
    for f in sorted(filings_dir.glob("*.md")):
        result[f.name] = f.read_text(encoding="utf-8")
    return result


# ── Scan ─────────────────────────────────────────────────────

def scan_filings(filings_dir: Path, workspace: Path | None = None):
    """Scan filings against the field registry — report coverage."""
    mds = load_markdown_files(filings_dir)
    if not mds:
        print("No markdown filings found.")
        return

    registry = load_registry(workspace)
    combined = "\n".join(mds.values())

    print(f"Source: {filings_dir} ({len(mds)} files, {len(combined):,} chars)")
    print(f"Registry: {len(registry)} concepts loaded\n")

    combined_lower = combined.lower()
    by_section = {}
    for concept, info in registry.items():
        section = info["section"]
        by_section.setdefault(section, [])
        found = any(label.lower() in combined_lower for label in info["labels"])
        by_section[section].append((concept, found))

    for section in ["income_statement", "balance_sheet", "cash_flow", "supplementary"]:
        items = by_section.get(section, [])
        if not items:
            continue
        found = sum(1 for _, f in items if f)
        total = len(items)
        print(f"## {section}: {found}/{total}")
        missing = [c for c, f in items if not f]
        if missing and len(missing) < 10:
            print(f"   Missing: {', '.join(missing)}")
        elif missing:
            print(f"   Missing: {len(missing)} concepts")

    # Also scan for segment/commentary/outlook headers
    print()
    for kw in ["セグメント情報", "사업부문", "Segment Information", "部門別", "経営成績等の概況",
               "사업의 개요", "Business review", "今後の見通し", "Outlook", "Guidance"]:
        if kw in combined:
            print(f"  ✓ {kw}")


# ── Template ─────────────────────────────────────────────────

def get_template(ticker: str, workspace: Path | None = None) -> dict:
    """Build blank actuals-resolved.json skeleton from field registry."""
    registry = load_registry(workspace)

    statements = {}
    section_map = {
        "income_statement": "income_statement",
        "balance_sheet": "balance_sheet",
        "cash_flow": "cash_flow",
    }

    for concept, info in sorted(registry.items()):
        section = info["section"]
        stmt_key = section_map.get(section)
        if not stmt_key:
            continue
        statements.setdefault(stmt_key, []).append({
            "label": "[FILL]",
            "concept": concept,
            "values": {"FY____": "[FILL]"},
            "unit": "[FILL]",
            "source": "[FILL]",
        })

    statements["revenue_split"] = [{
        "segment": "[FILL]",
        "type": "business",
        "revenue": {"FY____": "[FILL]"},
        "operating_profit": {"FY____": "[FILL]"},
        "unit": "[FILL]",
        "source": "[FILL]",
    }]

    return {
        "ticker": ticker,
        "market": "[FILL]",
        "source": "[FILL]",
        "identity": {
            "ticker": ticker,
            "name_en": "[FILL]",
            "name_native": "[FILL]",
            "fiscal_year_end": "[FILL]",
        },
        "statements": statements,
        "commentary": "[FILL]",
        "outlook": {},
        "market_data": {},
        "source_map": {
            "S1": {"source_layer": "[FILL]", "url": "[FILL]", "detail": "[FILL]"}
        },
    }


# ── Validate ─────────────────────────────────────────────────

def validate_actuals(actuals_path: Path, filings_dir: Path) -> bool:
    """Check every value in actuals exists somewhere in the source filings.

    Returns True if all values verified, False otherwise.
    """
    mds = load_markdown_files(filings_dir)
    if not mds:
        print("ERROR: no markdown filings", file=sys.stderr)
        return False

    combined = " ".join(mds.values())
    # Remove separators that don't affect number matching
    combined_clean = re.sub(r"[\s,]", "", combined)

    actuals = json.loads(actuals_path.read_text(encoding="utf-8"))
    statements = actuals.get("statements", {})

    total, errors = 0, []
    for stmt_name in ["income_statement", "balance_sheet", "cash_flow"]:
        for item in statements.get(stmt_name, []):
            concept = item.get("concept", "?")
            for period, val in item.get("values", {}).items():
                if val is None or isinstance(val, str):
                    continue
                total += 1
                # Normalize: abs value, strip decimals for integer-like numbers
                abs_val = abs(val)
                if isinstance(abs_val, float) and abs_val == int(abs_val):
                    vs = str(int(abs_val))
                else:
                    vs = str(abs_val).replace(".0", "")
                if vs and vs not in combined_clean:
                    errors.append(f"  MISS: {concept} {period}={val}")

    # Also check revenue_split
    for seg in statements.get("revenue_split", []):
        sname = seg.get("segment", "?")
        for key in ["revenue", "operating_profit"]:
            vals = seg.get(key, {})
            if not isinstance(vals, dict):
                continue
            for period, val in vals.items():
                if val is None or isinstance(val, str):
                    continue
                total += 1
                abs_val = abs(val)
                if isinstance(abs_val, float) and abs_val == int(abs_val):
                    vs = str(int(abs_val))
                else:
                    vs = str(abs_val).replace(".0", "")
                if vs and vs not in combined_clean:
                    errors.append(f"  MISS: {sname}/{key} {period}={val}")

    if errors:
        print(f"\n{len(errors)} of {total} values NOT FOUND in source:")
        for e in errors[:20]:
            print(e)
        if len(errors) > 20:
            print(f"  ... and {len(errors)-20} more")
        return False

    print(f"✓ All {total} values verified in source filings")
    return True


# ── Template extraction ─────────────────────────────────────

def extract_with_template(filing_type: str, filings_dir: Path, guided: bool = False, table_dump: bool = False):
    template_path = Path(__file__).resolve().parent / "assets" / "filing-templates.json"
    if not template_path.exists():
        print(f"ERROR: filing-templates.json not found", file=sys.stderr); sys.exit(1)
    templates = json.loads(template_path.read_text(encoding="utf-8"))
    tmpl = templates.get(filing_type)
    if not tmpl:
        print(f"Unknown filing type. Available: {list(templates)}", file=sys.stderr); sys.exit(1)
    mds = load_markdown_files(filings_dir)
    if not mds: print("No markdown filings."); sys.exit(1)
    combined = "\n".join(mds.values())

    if not guided and not table_dump:
        # Quick scan: show which fields are found
        print(f"=== Template: {tmpl['filing_name']} ===")
        for section, fields in tmpl.get("fields",{}).items():
            print(f"\n## {section}")
            for f in fields:
                idx = -1
                for term in f.get("search_terms",[]):
                    idx = combined.find(term)
                    if idx >= 0: break
                status = f"pos={idx}" if idx >= 0 else "NOT FOUND"
                print(f"  {f['concept']:25s} {status}")
        print()
        for key in ["segment","commentary","outlook"]:
            cfg = tmpl.get(key,{})
            hdr = cfg.get("section_header","")
            if hdr:
                idx = combined.find(hdr)
                print(f"  {key}: {'pos='+str(idx) if idx>=0 else 'NOT FOUND'}")
        print("Use --guided or --table-dump for full extraction context.")

    elif table_dump:
        # Table-dump mode: dump entire IS/BS/CF table regions for agent to read
        print(f"=== Table-Dump Extraction: {tmpl['filing_name']} ===")
        print(f"Source: {filings_dir} ({len(mds)} files)\n")
        dump_chars = 5000

        table_headers = tmpl.get("table_headers", {})
        for section in ["income_statement", "balance_sheet", "cash_flow"]:
            headers = table_headers.get(section, [])
            if not headers:
                print(f"## {section} — no table_headers configured\n")
                continue
            found = False
            for hdr in headers:
                idx = combined.find(hdr)
                if idx >= 0:
                    print(f"## {section} — matched header: `{hdr}` at pos {idx}")
                    ctx = combined[idx:idx+dump_chars]
                    print("```")
                    print(ctx)
                    print("```\n")
                    found = True
                    break
            if not found:
                print(f"## {section} — NOT FOUND (tried: {headers})\n")

        # Segment section
        seg = tmpl.get("segment",{})
        seg_hdr = seg.get("section_header", "")
        alt_headers = seg.get("alt_headers", [])
        for hdr in [seg_hdr] + alt_headers:
            if not hdr: continue
            idx = combined.find(hdr)
            if idx >= 0:
                print(f"## Segment — matched header: `{hdr}` at pos {idx}")
                ctx = combined[idx:idx+dump_chars]
                print("```")
                print(ctx)
                print("```\n")
                break
        else:
            if seg_hdr:
                print(f"## Segment — NOT FOUND\n")

        # Commentary
        commentary = tmpl.get("commentary", {})
        comm_hdr = commentary.get("section_header", "")
        alt_comm = commentary.get("alt_headers", [])
        for hdr in [comm_hdr] + alt_comm:
            if not hdr: continue
            idx = combined.find(hdr)
            if idx >= 0:
                print(f"## Commentary — matched header: `{hdr}` at pos {idx}")
                ctx = combined[idx:idx+dump_chars]
                print("```")
                print(ctx)
                print("```\n")
                break
        else:
            if comm_hdr:
                print(f"## Commentary — NOT FOUND\n")

        # Outlook
        out = tmpl.get("outlook", {})
        out_hdr = out.get("section_header", "")
        alt_out = out.get("alt_headers", [])
        for hdr in [out_hdr] + alt_out:
            if not hdr: continue
            idx = combined.find(hdr)
            if idx >= 0:
                print(f"## Outlook — matched header: `{hdr}` at pos {idx}")
                ctx = combined[idx:idx+3000]
                print("```")
                print(ctx[:2500])
                print("```\n")
                break
        else:
            if out_hdr:
                print(f"## Outlook — NOT FOUND\n")

        print("---")
        print("Agent: all IS/BS/CF table regions dumped above.")
        print("Extract EVERY line item (concept + value + period) from each table.")
        print("Use .references/policy/statement-line-items.md for concept → standard name mapping.")
        print("Items without a registry concept: use the native label's snake_case as concept.")
        print("Write actuals-resolved.json, then run --validate.")

    else:
        # Guided mode: print per-field context for agent extraction
        print(f"=== Guided Extraction: {tmpl['filing_name']} ===")
        print(f"Source: {filings_dir} ({len(mds)} files)\n")

        for section, fields in tmpl.get("fields",{}).items():
            print(f"## {section}")
            for f in fields:
                idx = -1; term_used = ""
                for term in f.get("search_terms",[]):
                    idx = combined.find(term)
                    if idx >= 0: term_used = term; break
                if idx < 0: continue
                ctx = combined[max(0,idx-50):idx+500].replace("\n"," ")
                nums = re.findall(r'[\d,]{3,}', combined[idx:idx+800])
                label = f.get('label_ja') or f.get('label_ko') or f.get('label') or f['concept']
                print(f"### {f['concept']} ({label})")
                print(f"```\n...{ctx[:400]}...\n```")
                if nums: print(f"Numbers nearby: {', '.join(nums[:6])}")
                print()
            print()

        # Segment prose
        seg = tmpl.get("segment",{})
        prose = seg.get("prose_section",{}) if seg else {}
        hdr = prose.get("header","") if prose else ""
        if hdr:
            idx = combined.find(hdr)
            if idx >= 0:
                print("## Segment Revenue (Management Commentary)")
                ctx = combined[idx:idx+3000].replace("\n","\n")
                print("```")
                print(ctx[:2500])
                print("```\n")

        # Outlook
        out = tmpl.get("outlook",{})
        oh = out.get("section_header","")
        if oh:
            idx = combined.find(oh)
            if idx >= 0:
                print("## Management Outlook")
                ctx = combined[idx:idx+1500].replace("\n","\n")
                print("```")
                print(ctx[:1000])
                print("```\n")

        print("---")
        print("Agent: read the above, extract IS/BS/CF/segment values,")
        print("write actuals-resolved.json, then run --validate.")


# ── Main ─────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Extract financial data from IR filing markdown files")
    parser.add_argument("--filings-dir", help="Directory with markdown filings")
    parser.add_argument("--ticker")
    parser.add_argument("--scan", action="store_true")
    parser.add_argument("--template", action="store_true")
    parser.add_argument("--validate", help="Path to actuals-resolved.json")
    parser.add_argument("--filing-type", help="Filing template key from filing-templates.json")
    parser.add_argument("--guided", action="store_true")
    parser.add_argument("--table-dump", action="store_true", help="Dump entire IS/BS/CF table regions (best for pymupdf4llm)")
    args = parser.parse_args()

    if args.template:
        print(json.dumps(get_template(args.ticker or "TICKER"), indent=2, ensure_ascii=False))
        return
    if args.validate:
        ok = validate_actuals(Path(args.validate), Path(args.filings_dir))
        sys.exit(0 if ok else 1)
    if args.filing_type and args.filings_dir:
        extract_with_template(args.filing_type, Path(args.filings_dir), args.guided, args.table_dump)
        return
    if args.scan and args.filings_dir:
        scan_filings(Path(args.filings_dir))
        return
    parser.print_help()


if __name__ == "__main__":
    main()
