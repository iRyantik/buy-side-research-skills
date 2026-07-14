"""Check: reddit-sentiment outputs must not upgrade social chatter into confirmed facts."""
import re, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from common import block, warn

SOCIAL = re.compile(r'(?i)(reddit|subreddit|forum|social post|community|thread|post|comment|social chatter|论坛|社区|帖子|评论|社媒|社交媒体|小作文|舆情)')
STRONG_FACT = re.compile(r'(?i)(proves|confirms|verified|shows that.+(direct supplier|customer|order|demand)|direct supplier|customer of|confirmed relationship|证明|证实|确认|实锤|坐实|直接供应商|客户是|确认关系|确认订单|需求被证实)')
SAFE_CLUE = re.compile(r'(?i)(clue-only|sentiment-only|social-evidence-only|suggests|may indicate|cannot confirm|not independently confirmed|for follow-up only|仅作线索|情绪线索|社交线索|提示|暗示|不能确认|未独立确认|仅供后续验证|仅反映社区叙事)')
SKILL_FILE = re.compile(r'reddit-sentiment')

def check(ctx):
    for t in ctx.get("targets", []):
        text = t.get("text", "")
        if not text:
            continue
        path = t.get("path", "") or ""
        leaf = os.path.basename(path) if path else ""
        is_target = (t.get("kind") == "file" and bool(SKILL_FILE.search(leaf))) or bool(re.search(r'(?im)^#\s*Reddit Sentiment\b', text))
        if not is_target:
            continue
        for line in text.split("\n"):
            if not SOCIAL.search(line):
                continue
            if not STRONG_FACT.search(line):
                continue
            if SAFE_CLUE.search(line):
                continue
            block(f"social_clue_only: {t.get('display','?')} cannot upgrade Reddit, forum, or social chatter into confirmed company, demand, or customer facts.")
