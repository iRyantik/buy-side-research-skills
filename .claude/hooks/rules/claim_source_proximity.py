"""Check: strong claims must have source anchor. Table rows with numbers must have source."""
import re, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import block, warn
import os as _os
_ARTIFACT_RE = __import__("re").compile(r"^\d{4}-\d{2}-\d{2}-.+\.md$")
def _is_artifact(fp): return bool(_ARTIFACT_RE.match(_os.path.basename(fp)))

STRONG_CLAIM = re.compile(
    r'(?i)(独家|唯一供应商|唯一|仅有的|垄断|exclusive|sole supplier|only vendor|confirmed|certified|验证过的唯一|全球独家|独占)'
)
SOURCE_ANCHOR = re.compile(r'\[(?:S\d+|I\d+|LBG\d+|P\d+|SRC\d+)\]')

# Financial numbers in table cells: %, multiples, currency amounts
FINANCIAL_CELL = re.compile(
    r'(?:(?<!\w)[\d,.]+%|'                # percentages: 14.2%
    r'(?<!\w)[\d,.]+x(?![/\w])|'          # multiples: 22.4x
    r'(?<!\w)[\d,.]+bps|'                 # basis points: +45bps
    r'(?<!\w)[\d,.]+pp|'                  # percentage points: +3pp
    r'(?<!\w)\$[\d,.]+[bmk]|'             # currency: $24bn, $45m
    r'(?<!\w)(?:EUR|USD|CNY|JPY|KRW|HKD|TWD|SEK)\s*[\d,.]+[bmk]?)'  # ISO currency
)
# Lines that are table data rows (not headers, not separators)
TABLE_DATA_ROW = re.compile(r'^\|(?![\s\-:]+\|)(?![\s\*\[#])')

SECTION_BOUNDARY = re.compile(r'^##\s', re.MULTILINE)

def _is_table_separator(line: str) -> bool:
    """Check if line is a GFM table separator (|---|...|---|)."""
    stripped = line.strip()
    if not stripped.startswith('|'):
        return False
    return bool(re.match(r'^\|[\s\-:]+\|[\s\-:\|]+\|$', stripped))

def _is_table_header(line: str) -> bool:
    """Heuristic: does this line look like a column header (contains typical header keywords)?"""
    header_keywords = {'Regime','Case','Scenario','Driver','维度','Bucket','Signal','Step','时间',
                       '事件','票','公司','Company','倍数','比率','指标','Value','Assumptions',
                       'PE ','EV/','估值','概率','回报','评分','Score','Total','定义','假设',
                       'Catalyst','KPI','Weight','Upside','Margin','Growth','Purity'}
    cells = [c.strip() for c in line.split('|')[1:-1]]
    return any(any(kw in c for kw in header_keywords) for c in cells if c)

def check(ctx):
    for t in ctx.get("targets", []):
        text = t.get("text", "")
        if not text:
            continue
        path = t.get("path", "") or ""
        leaf = os.path.basename(path) if path else ""
        display = t.get("display", "unknown")
        if not _is_artifact(leaf):
            continue

        # --- Rule 1: Strong claims must have source anchors ---
        sections = SECTION_BOUNDARY.split(text)
        issues = []
        for si, section in enumerate(sections):
            if not STRONG_CLAIM.search(section):
                continue
            if SOURCE_ANCHOR.search(section):
                continue
            claim = STRONG_CLAIM.search(section).group(0)
            heading = section.split('\n')[0][:80] if section.strip() else '(top)'
            issues.append(f"{claim} in section '{heading}'")

        if issues:
            warn(f"claim_source_proximity: {display} has strong claims without source anchors: {', '.join(issues[:3])}.")

        # --- Rule 2: Table rows with financial numbers must have source anchors ---
        lines = text.split('\n')
        unsourced_rows = []
        in_code_fence = False
        for i, line in enumerate(lines):
            # Skip code fences
            if line.lstrip().startswith('```') or line.lstrip().startswith('~~~'):
                in_code_fence = not in_code_fence
                continue
            if in_code_fence:
                continue

            stripped = line.strip()
            if not stripped.startswith('|'):
                continue
            # Skip separators and headers
            if _is_table_separator(stripped):
                continue
            if _is_table_header(stripped):
                continue

            # This is a data row — check for financial numbers
            if FINANCIAL_CELL.search(stripped):
                if not SOURCE_ANCHOR.search(stripped):
                    row_summary = stripped[:100] + ('...' if len(stripped) > 100 else '')
                    unsourced_rows.append(f"line {i+1}: {row_summary}")

        if unsourced_rows:
            block(f"Blocked by claim_source_proximity: {display} has {len(unsourced_rows)} table row(s) "
                 f"with financial numbers but no source anchor. "
                 f"Every row with valuation/metric/spread/price data must carry [S#] or [I#]. "
                 f"First 3: {' | '.join(unsourced_rows[:3])}")

        # --- Rule 3: Paragraph-level source density ---
        # Narrative paragraphs (>150 chars) with factual markers but zero source anchors
        # Strip code fences from text
        body_no_code = re.sub(r'```[^\n]*\n.*?```', '', text, flags=re.DOTALL)
        body_no_code = re.sub(r'~~~[^\n]*\n.*?~~~', '', body_no_code, flags=re.DOTALL)

        FACTUAL_MARKERS = re.compile(
            r'(?:(?<!\w)[\d,.]+%|'           # percentages
            r'(?<!\w)[\d,.]+x(?![/\w])|'      # multiples
            r'(?<!\w)[\d,.]+bps|'             # bps
            r'(?<!\w)\$[\d,.]+[bmk]|'         # $ amounts
            r'(?:EUR|USD|CNY|JPY|KRW|HKD|TWD|SEK)\s*[\d,.]+[bmk]?)'  # ISO amounts
        )

        # Split body into paragraphs (double newline), excluding tables and code
        body_paragraphs = []
        in_table = False
        in_fence = False
        current_para = []
        for line in body_no_code.split('\n'):
            stripped = line.strip()
            if stripped.startswith('```') or stripped.startswith('~~~'):
                in_fence = not in_fence
                if current_para:
                    body_paragraphs.append(' '.join(current_para))
                    current_para = []
                continue
            if in_fence:
                continue
            if stripped.startswith('|'):
                in_table = True
                continue
            if in_table and not stripped.startswith('|'):
                in_table = False
            if in_table:
                continue
            if not stripped:
                if current_para:
                    body_paragraphs.append(' '.join(current_para))
                    current_para = []
            else:
                current_para.append(stripped)
        if current_para:
            body_paragraphs.append(' '.join(current_para))

        low_density_paras = []
        for pi, para in enumerate(body_paragraphs):
            if len(para) < 150:
                continue
            facts = len(FACTUAL_MARKERS.findall(para))
            if facts < 2:
                continue
            sources = len(SOURCE_ANCHOR.findall(para))
            if sources == 0:
                preview = para[:120] + ('...' if len(para) > 120 else '')
                low_density_paras.append(f"0 sources, {facts} markers: {preview}")
            elif facts > 5 and sources < (facts // 3):
                preview = para[:120] + ('...' if len(para) > 120 else '')
                low_density_paras.append(f"low density ({sources} src/{facts} facts): {preview}")

        zero_source_paras = [p for p in low_density_paras if p.startswith('0 sources')]
        low_paras = [p for p in low_density_paras if not p.startswith('0 sources')]

        if zero_source_paras:
            block(f"Blocked by claim_source_proximity: {display} has {len(zero_source_paras)} paragraph(s) "
                 f"with factual claims but ZERO source anchors. "
                 f"Every paragraph with numbers/company names must carry [S#] or [I#]. "
                 f"First: {zero_source_paras[0][:150]}")

        if low_paras:
            warn(f"claim_source_proximity: {display} has {len(low_paras)} paragraph(s) "
                 f"with low source density (<1 source per 3 factual claims). "
                 f"First: {low_paras[0][:150]}")

sys.exit(0)
