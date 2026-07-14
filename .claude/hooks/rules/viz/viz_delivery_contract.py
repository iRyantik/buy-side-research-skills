"""Check: research-viz HTML must have dated stem name, be self-contained, have title/subtitle/source."""
import re, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from common import block, warn

GENERIC_NAME = re.compile(r'(?i)^(?:\d{4}-\d{2}-\d{2}-)?research-viz(?:-[^.]+)?\.html$')
DATED_HTML = re.compile(r'^\d{4}-\d{2}-\d{2}-.+\.html$')
TITLE = re.compile(r'(?is)(<title>.+?</title>|<h1\b[^>]*>.+?</h1>)')
SUBTITLE = re.compile(r'(?is)(subtitle|sub-title|class=["\'][^"\']*subtitle|as-of|updated|ticker|currency)')
SOURCE = re.compile(r'(?is)(source line|sources?:|data source|class=["\'][^"\']*source|来源)')
EXTERNAL = re.compile(r'(?is)(script|link|img)\b[^>]+(?:src|href)=["\'](?:https?:)?//')

def check(ctx):
    for t in ctx.get("targets", []):
        text = t.get("text", "")
        path = t.get("path", "") or ""
        leaf = os.path.basename(path) if path else ""
        is_target = (t.get("kind") == "file" and (leaf.endswith('.html') or 'research-viz' in leaf)) or bool(re.search(r'(?im)^#\s*Research Viz\b|<html', text or ""))
        if not is_target:
            continue
        d = t.get('display', '?')
        if path and leaf:
            if GENERIC_NAME.search(leaf):
                block(f"viz_delivery_contract: {d} must bind topic-side HTML to the base research stem, not a generic research-viz file name.")
            if not DATED_HTML.search(leaf):
                block(f"viz_delivery_contract: {d} must use a dated base-research stem HTML name (YYYY-MM-DD-*.html).")
        if text:
            if EXTERNAL.search(text):
                block(f"viz_delivery_contract: {d} must be self-contained and cannot depend on external http(s) assets.")
            if not TITLE.search(text):
                block(f"viz_delivery_contract: {d} must include a visible title.")
            if not SUBTITLE.search(text):
                block(f"viz_delivery_contract: {d} must include subtitle-style context such as ticker, as-of, updated time, or currency basis.")
            if not SOURCE.search(text):
                block(f"viz_delivery_contract: {d} must include a source line.")
