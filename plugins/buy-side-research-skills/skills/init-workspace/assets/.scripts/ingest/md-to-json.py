#!/usr/bin/env python3
"""md-to-json.py — Extract structured JSON from markdown using LLM.

Usage:
    # With a JSON schema file
    python md-to-json.py <input.md> --schema <schema.json> [--output <path>]

    # With inline field definitions
    python md-to-json.py <input.md> --fields "revenue,gross_profit,net_income" [--output <path>]

Design:
    This script scaffolds the extraction. The agent (Claude) reads the markdown,
    extracts structured data according to the schema, and writes JSON.
    The --verify flag checks that every extracted value exists in source.

Anti-hallucination: every string/numeric value in the output MUST be findable
in the source markdown. Use --verify to enforce this.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def load_schema(schema_path: Path) -> dict | None:
    if schema_path.exists():
        return json.loads(schema_path.read_text(encoding="utf-8"))
    return None


def verify_output(md_path: Path, json_path: Path) -> bool:
    """Verify that every string/numeric value in JSON exists in source MD."""
    md = md_path.read_text(encoding="utf-8")
    md_clean = re.sub(r"[\s,]", "", md)

    data = json.loads(json_path.read_text(encoding="utf-8"))

    def _check(obj, path="") -> list[str]:
        errors = []
        if isinstance(obj, dict):
            for k, v in obj.items():
                errors.extend(_check(v, f"{path}.{k}"))
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                errors.extend(_check(v, f"{path}[{i}]"))
        elif isinstance(obj, (int, float)):
            val_str = str(int(abs(obj))) if isinstance(obj, float) and obj == int(obj) else str(abs(obj))
            val_str = val_str.replace(".0", "")
            if val_str not in md_clean:
                errors.append(f"  NOT FOUND: {path}={obj}")
        elif isinstance(obj, str) and obj and len(obj) > 3:
            if obj not in md:
                errors.append(f"  NOT FOUND: {path}=\"{obj[:80]}\"")
        return errors

    errors = _check(data)
    if errors:
        print(f"Verification FAILED — {len(errors)} values not in source:")
        for e in errors:
            print(e)
        return False

    print(f"Verification PASSED — all values in source")
    return True


def main():
    parser = argparse.ArgumentParser(description="Extract structured JSON from markdown")
    parser.add_argument("input", nargs="?", help="Markdown file to extract from")
    parser.add_argument("--schema", help="JSON schema file defining extraction fields")
    parser.add_argument("--fields", help="Comma-separated field names to extract")
    parser.add_argument("--output", "-o", help="Output JSON path")
    parser.add_argument("--verify", action="store_true", help="Verify existing JSON against source MD")
    parser.add_argument("--verify-json", help="JSON file to verify (used with --verify)")
    args = parser.parse_args()

    if args.verify:
        if not args.input or not args.verify_json:
            print("ERROR: --verify requires <input.md> and --verify-json <file.json>", file=sys.stderr)
            sys.exit(1)
        ok = verify_output(Path(args.input), Path(args.verify_json))
        sys.exit(0 if ok else 1)

    if not args.input:
        parser.print_help()
        return

    src = Path(args.input)
    if not src.exists():
        print(f"ERROR: file not found: {src}", file=sys.stderr)
        sys.exit(1)

    md_text = src.read_text(encoding="utf-8")
    schema = load_schema(Path(args.schema)) if args.schema else None
    fields = [f.strip() for f in args.fields.split(",")] if args.fields else []

    print(f"=== md-to-json: {src.name} ===")
    print(f"  Source: {len(md_text):,} chars")
    if schema:
        print(f"  Schema: {json.dumps(schema, indent=2)}")
    elif fields:
        print(f"  Fields: {fields}")

    print(f"\n  Agent: read the markdown above and extract the specified fields as JSON.")
    print(f"  Each extracted value MUST be findable verbatim in the source.")
    if args.output:
        print(f"  Write result to: {args.output}")
    print(f"  Then verify: python md-to-json.py {args.input} --verify --verify-json <output>.json")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
