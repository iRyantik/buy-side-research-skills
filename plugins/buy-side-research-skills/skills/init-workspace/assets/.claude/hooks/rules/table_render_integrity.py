"""Rule 3: Table render integrity — pipe table structural checks."""
import re, sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import get_markdown_tables, block, count_pipe_columns


def check(ctx: dict):
    for target in ctx.get("targets", []):
        text = target.get("text", "")
        if not text:
            continue
        display = target.get("display", "unknown")
        tables = get_markdown_tables(text)

        for table in tables:
            start = table["start_line"]
            lines = table["lines"]

            if len(lines) < 2:
                block(f"Blocked by table_render_integrity: {display} has a pipe-table block near line {start} without a valid separator row.")

            header, sep = lines[0], lines[1]

            # Rule 3: header/separator column counts must match
            header_cols = count_pipe_columns(header)
            sep_cols = count_pipe_columns(sep)
            if header_cols != sep_cols:
                block(f"Blocked by table_render_integrity: {display} has mismatched header ({header_cols}) and separator ({sep_cols}) column counts near line {start}.")

            # Rule 4: data row column counts must match header
            for row_line in lines[2:]:
                row_cols = count_pipe_columns(row_line)
                if row_cols != header_cols:
                    block(f"Blocked by table_render_integrity: {display} has a table row with {row_cols} columns but expected {header_cols} near line {start}.")
