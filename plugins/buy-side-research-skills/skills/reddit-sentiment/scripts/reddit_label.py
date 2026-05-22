#!/usr/bin/env python3
"""Label ScrapiReddit output and export source-tracked Reddit sentiment datasets."""

from __future__ import annotations

import argparse
import json
import os
import re
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


USER_AGENT = "buy-side-research/reddit-sentiment (public Reddit JSON; clue-only research)"


def utc_now_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")


def parse_terms(value: str | None) -> list[str]:
    if not value:
        return []
    terms: list[str] = []
    for part in re.split(r"[,;\n]", value):
        term = part.strip()
        if term and term.lower() not in {t.lower() for t in terms}:
            terms.append(term)
    return terms


def load_config(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def walk_posts(scrapi_dir: Path):
    """Yield every Reddit post from ScrapiReddit posts.json files."""
    for root, _dirs, files in os.walk(scrapi_dir):
        for filename in files:
            if filename != "posts.json":
                continue
            filepath = Path(root) / filename
            try:
                with filepath.open(encoding="utf-8") as f:
                    listing = json.load(f)
                for child in listing.get("data", {}).get("children", []):
                    if child.get("kind") == "t3":
                        post = child.get("data", {})
                        post["_scrapi_source_file"] = str(filepath)
                        yield post
            except (OSError, KeyError, json.JSONDecodeError) as exc:
                print(f"[WARN] Failed to read {filepath}: {exc}")


def dedup_posts(posts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    for post in posts:
        post_id = post.get("name") or post.get("id") or ""
        if not post_id or post_id in seen:
            continue
        seen.add(post_id)
        unique.append(post)
    return unique


def date_to_ts(value: str, end_of_day: bool = False) -> float:
    dt = datetime.strptime(value, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    if end_of_day:
        dt = dt.replace(hour=23, minute=59, second=59)
    return dt.timestamp()


def filter_by_time(posts: list[dict[str, Any]], from_date: str, to_date: str) -> list[dict[str, Any]]:
    start_ts = date_to_ts(from_date)
    end_ts = date_to_ts(to_date, end_of_day=True)
    return [p for p in posts if start_ts <= float(p.get("created") or 0) <= end_ts]


def post_text(post: dict[str, Any]) -> str:
    fields = [
        post.get("title") or "",
        post.get("selftext") or "",
        post.get("url") or "",
        post.get("subreddit") or "",
    ]
    return " ".join(fields).lower()


def has_any(text: str, terms: list[str]) -> bool:
    return any(term.lower() in text for term in terms if term)


def classify_post(post: dict[str, Any], config: dict[str, Any], topic_terms: list[str]) -> tuple[str, str]:
    cls = config.get("classification", {})
    exclusions = config.get("exclusion_patterns", {})
    title = post.get("title") or ""
    author = post.get("author") or ""

    if author in exclusions.get("auto_moderator", ["AutoModerator", "VisualMod"]):
        return "exclude", "automoderator"
    if title in exclusions.get("deleted_removed", ["[deleted]", "[removed]"]):
        return "exclude", "removed_title"

    text = post_text(post)
    if topic_terms and not has_any(text, topic_terms):
        return "false_positive", "no topic term matched"

    comments = int(post.get("num_comments") or 0)
    core_min = int(cls.get("core_min_comments", 10))
    context_min = int(cls.get("context_min_comments", 5))

    if comments >= core_min:
        return "core", f"comments>={core_min} + topic match"
    if comments >= context_min:
        return "context", f"comments>={context_min} + topic match"
    return "tiny", f"comments<{context_min}"


def fetch_comments(subreddit: str, post_id: str, cache_path: Path, delay: float) -> dict[str, Any] | None:
    if cache_path.exists():
        try:
            with cache_path.open(encoding="utf-8") as f:
                cached = json.load(f)
            if isinstance(cached, list):
                return cached[1] if len(cached) >= 2 else None
            if isinstance(cached, dict):
                return cached
        except (OSError, json.JSONDecodeError):
            pass

    reddit_id = post_id.replace("t3_", "")
    url = f"https://www.reddit.com/r/{subreddit}/comments/{reddit_id}.json?limit=500&sort=top&raw_json=1"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    time.sleep(delay)
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read())
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        with cache_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
        return data[1] if len(data) >= 2 else None
    except urllib.error.HTTPError as exc:
        if exc.code == 429:
            print(f"[RATE-LIMIT] Waiting 30s for {post_id}")
            time.sleep(30)
            return fetch_comments(subreddit, post_id, cache_path, delay)
        print(f"[HTTP {exc.code}] Failed to fetch comments for {post_id}")
        return None
    except Exception as exc:
        print(f"[ERR] Failed to fetch comments for {post_id}: {exc}")
        return None


def flatten_comments(comment_listing: dict[str, Any] | None, depth: int = 0) -> list[dict[str, Any]]:
    if not comment_listing:
        return []
    results: list[dict[str, Any]] = []
    for child in comment_listing.get("data", {}).get("children", []):
        if child.get("kind") == "t1":
            data = child.get("data", {}).copy()
            data["depth"] = depth
            results.append(data)
            replies = data.get("replies")
            if isinstance(replies, dict):
                results.extend(flatten_comments(replies, depth + 1))
    return results


def clean_comment(comment: dict[str, Any], config: dict[str, Any]) -> tuple[bool, str]:
    exclusions = config.get("exclusion_patterns", {})
    author = comment.get("author") or ""
    body = comment.get("body") or ""
    if author in exclusions.get("auto_moderator", ["AutoModerator", "VisualMod"]):
        return False, "automod"
    if body in exclusions.get("deleted_removed", ["[deleted]", "[removed]"]):
        return False, "deleted_or_removed"
    if len(body.strip()) < int(exclusions.get("min_comment_length", 20)):
        return False, "too_short"
    if int(comment.get("score") or 0) < -10:
        return False, "low_score"
    return True, "ok"


def label_text(body: str, clusters: list[dict[str, Any]]) -> tuple[list[str], dict[str, list[str]]]:
    lowered = body.lower()
    matched: dict[str, list[str]] = {}
    for cluster in clusters:
        name = cluster["name"]
        for keyword in cluster.get("keywords", []):
            if keyword.lower() in lowered:
                matched.setdefault(name, []).append(keyword)
    labels = list(matched) or ["other"]
    return labels, matched


def post_record(post: dict[str, Any], classification: str, reasoning: str) -> dict[str, Any]:
    return {
        "post_id": post.get("name") or "",
        "reddit_id": post.get("id") or "",
        "subreddit": post.get("subreddit") or "",
        "title": post.get("title") or "",
        "author": post.get("author") or "",
        "score": int(post.get("score") or 0),
        "upvote_ratio": post.get("upvote_ratio"),
        "num_comments": int(post.get("num_comments") or 0),
        "created_utc": float(post.get("created") or 0),
        "permalink": post.get("permalink") or "",
        "url": post.get("url") or "",
        "selftext_preview": (post.get("selftext") or "")[:500],
        "selftext_length": len(post.get("selftext") or ""),
        "classification": classification,
        "classification_reasoning": reasoning,
        "scrapi_source_file": post.get("_scrapi_source_file") or "",
    }


def comment_record(comment: dict[str, Any], post_id: str, subreddit: str, labels: list[str], matched: dict[str, list[str]]) -> dict[str, Any]:
    return {
        "comment_id": comment.get("name") or "",
        "post_id": post_id,
        "subreddit": subreddit,
        "author": comment.get("author") or "",
        "body": comment.get("body") or "",
        "body_length": len(comment.get("body") or ""),
        "score": int(comment.get("score") or 0),
        "created_utc": float(comment.get("created_utc") or 0),
        "depth": int(comment.get("depth") or 0),
        "parent_id": comment.get("parent_id") or "",
        "permalink": comment.get("permalink") or "",
        "cluster_labels": labels,
        "matching_keywords": matched,
    }


def reddit_url(permalink: str) -> str:
    if not permalink:
        return ""
    if permalink.startswith("http"):
        return permalink
    return f"https://www.reddit.com{permalink}"


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(value, f, indent=2, ensure_ascii=False)


def cluster_counts(comments: list[dict[str, Any]]) -> tuple[dict[str, int], dict[str, dict[str, int]]]:
    totals: dict[str, int] = {}
    by_subreddit: dict[str, dict[str, int]] = {}
    for comment in comments:
        subreddit = comment["subreddit"]
        by_subreddit.setdefault(subreddit, {})
        for label in comment["cluster_labels"]:
            totals[label] = totals.get(label, 0) + 1
            by_subreddit[subreddit][label] = by_subreddit[subreddit].get(label, 0) + 1
    return totals, by_subreddit


def generate_coverage_summary(
    subject: str,
    from_date: str,
    to_date: str,
    all_posts: list[dict[str, Any]],
    core_posts: list[dict[str, Any]],
    comments: list[dict[str, Any]],
    totals: dict[str, int],
    output_path: Path,
) -> None:
    usable_total = len(comments)
    reported_total = sum(int(p["num_comments"]) for p in core_posts)
    lines = [
        f"# {subject} Reddit Data Collection Coverage Report",
        "",
        "## Run Details",
        f"- **Time window**: {from_date} to {to_date}",
        f"- **Discovered posts (deduped, in window)**: {len(all_posts):,}",
        f"- **Core posts**: {len(core_posts):,}",
        f"- **Reported comments on core posts**: {reported_total:,}",
        f"- **Usable comments fetched**: {usable_total:,}",
        "",
        "## Core Posts by Subreddit",
        "| Subreddit | Core Posts | Reported Comments | Usable Comments |",
        "|---|---:|---:|---:|",
    ]
    by_sub: dict[str, dict[str, int]] = {}
    for post in core_posts:
        subreddit = post["subreddit"]
        by_sub.setdefault(subreddit, {"posts": 0, "reported": 0, "usable": 0})
        by_sub[subreddit]["posts"] += 1
        by_sub[subreddit]["reported"] += int(post["num_comments"])
    for comment in comments:
        by_sub.setdefault(comment["subreddit"], {"posts": 0, "reported": 0, "usable": 0})
        by_sub[comment["subreddit"]]["usable"] += 1
    for subreddit, counts in sorted(by_sub.items(), key=lambda item: (-item[1]["posts"], item[0].lower())):
        lines.append(f"| r/{subreddit} | {counts['posts']} | {counts['reported']:,} | {counts['usable']:,} |")

    lines.extend(["", "## Cluster Distribution", "| Cluster | Count | % of Usable |", "|---|---:|---:|"])
    denom = usable_total or 1
    for name, count in sorted(totals.items(), key=lambda item: -item[1]):
        lines.append(f"| {name} | {count:,} | {count / denom * 100:.1f}% |")

    lines.extend(["", "## Exclusions"])
    class_counts: dict[str, int] = {}
    for post in all_posts:
        class_counts[post["classification"]] = class_counts.get(post["classification"], 0) + 1
    for name in sorted(class_counts):
        lines.append(f"- {name}: {class_counts[name]:,} posts")

    lines.extend([
        "",
        "## Notes",
        "- Comments fetched via Reddit public JSON API without OAuth.",
        "- Deeply nested `more` comment nodes may not be fully resolved.",
        "- Deleted, removed, very short, automoderator, and heavily downvoted comments are excluded from usable comments.",
        "- Source quality: Reddit is a social / clue-only source, not company evidence.",
    ])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def generate_evidence_cards(
    subject: str,
    core_posts: list[dict[str, Any]],
    comments_by_post: dict[str, list[dict[str, Any]]],
    output_path: Path,
) -> None:
    lines = [f"# {subject} Reddit Sentiment - Evidence Cards", ""]
    for index, post in enumerate(core_posts, 1):
        post_id = post["post_id"]
        comments = comments_by_post.get(post_id, [])
        permalink = reddit_url(post["permalink"])
        created = datetime.fromtimestamp(post["created_utc"], tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        lines.extend([
            f"## [R{index:03d}] r/{post['subreddit']} - \"{post['title']}\"",
            f"- Score: {post['score']:,} | Comments: {post['num_comments']:,} reported / {len(comments):,} usable",
            f"- Permalink: {permalink or 'N/A'}",
            f"- Created: {created}",
        ])
        counts: dict[str, int] = {}
        for comment in comments:
            for label in comment["cluster_labels"]:
                counts[label] = counts.get(label, 0) + 1
        denom = len(comments) or 1
        top_clusters = sorted(counts.items(), key=lambda item: -item[1])[:5]
        cluster_text = ", ".join(f"{name} ({count / denom * 100:.0f}%)" for name, count in top_clusters) or "none"
        lines.append(f"- Dominant clusters: {cluster_text}")
        if comments:
            lines.append("- Representative comments:")
            for comment in sorted(comments, key=lambda item: -item["score"])[:5]:
                body = re.sub(r"\s+", " ", comment["body"]).strip()[:220]
                labels = " + ".join(comment["cluster_labels"])
                lines.append(f"  - (+{comment['score']}) u/{comment['author']}: \"{body}\" - {labels}")
        lines.extend(["", "---", ""])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Label and export Reddit sentiment data")
    parser.add_argument("--scrapi-dir", required=True, type=Path, help="ScrapiReddit output directory")
    parser.add_argument("--labels", required=True, type=Path, help="Cluster labels JSON config")
    parser.add_argument("--topic", required=True, type=Path, help="Topic output root, e.g. topics/company/spacex")
    parser.add_argument("--subject", required=True, help="Research subject shown in outputs")
    parser.add_argument("--topic-terms", default="", help="Comma-separated topic relevance terms")
    parser.add_argument("--from", dest="from_date", required=True, help="Start date YYYY-MM-DD")
    parser.add_argument("--to", dest="to_date", required=True, help="End date YYYY-MM-DD")
    parser.add_argument("--run-id", default="", help="Stable run id shared with ScrapiReddit output")
    parser.add_argument("--min-comments", type=int, default=10, help="Minimum comments for core posts")
    parser.add_argument("--delay", type=float, default=2.5, help="Delay between Reddit comment API calls")
    args = parser.parse_args()

    config = load_config(args.labels)
    config.setdefault("classification", {})["core_min_comments"] = args.min_comments
    clusters = config.get("clusters", [])
    run_id = args.run_id or utc_now_id()
    topic_terms = parse_terms(args.topic_terms) or [args.subject]

    raw_dir = args.topic / "_raw" / "datasets" / "reddit-sentiment" / run_id
    cache_dir = args.topic / "_cache" / "datasets" / "reddit-sentiment" / run_id
    comment_cache_dir = raw_dir / "comments-cache"
    raw_dir.mkdir(parents=True, exist_ok=True)
    cache_dir.mkdir(parents=True, exist_ok=True)

    print(f"=== Phase 1: Loading posts from {args.scrapi_dir}")
    raw_posts = list(walk_posts(args.scrapi_dir))
    print(f"  Raw posts loaded: {len(raw_posts):,}")
    unique_posts = dedup_posts(raw_posts)
    time_filtered = filter_by_time(unique_posts, args.from_date, args.to_date)
    print(f"  Deduped in window: {len(time_filtered):,}")

    print("=== Phase 2: Classifying posts")
    all_records: list[dict[str, Any]] = []
    core_posts: list[dict[str, Any]] = []
    for post in time_filtered:
        classification, reasoning = classify_post(post, config, topic_terms)
        record = post_record(post, classification, reasoning)
        all_records.append(record)
        if classification == "core":
            core_posts.append(record)
    print(f"  Core posts: {len(core_posts):,}")

    print("=== Phase 3: Fetching and labeling comments")
    all_comments: list[dict[str, Any]] = []
    comments_by_post: dict[str, list[dict[str, Any]]] = {}
    for idx, post in enumerate(core_posts, 1):
        post_id = post["post_id"]
        subreddit = post["subreddit"]
        print(f"  [{idx}/{len(core_posts)}] r/{subreddit} {post_id}")
        comment_listing = fetch_comments(subreddit, post_id, comment_cache_dir / f"{post_id}.json", args.delay)
        usable: list[dict[str, Any]] = []
        for comment in flatten_comments(comment_listing):
            ok, _reason = clean_comment(comment, config)
            if not ok:
                continue
            labels, matched = label_text(comment.get("body") or "", clusters)
            usable.append(comment_record(comment, post_id, subreddit, labels, matched))
        comments_by_post[post_id] = usable
        all_comments.extend(usable)
        print(f"    Usable comments: {len(usable):,}")

    totals, by_subreddit = cluster_counts(all_comments)

    print("=== Phase 4: Writing outputs")
    write_jsonl(raw_dir / "post-universe.jsonl", all_records)
    write_jsonl(raw_dir / "posts-core.jsonl", core_posts)
    write_jsonl(raw_dir / "comments-clean.jsonl", all_comments)
    write_json(
        raw_dir / "cluster-counts.json",
        {
            "run_id": run_id,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "subject": args.subject,
            "topic_terms": topic_terms,
            "total_core_posts": len(core_posts),
            "total_usable_comments": len(all_comments),
            "cluster_counts": totals,
            "cluster_by_subreddit": by_subreddit,
        },
    )
    manifest = {
        "run_id": run_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "subject": args.subject,
        "topic_terms": topic_terms,
        "time_window": {"from": args.from_date, "to": args.to_date},
        "scrapi_dir": str(args.scrapi_dir),
        "labels": str(args.labels),
        "min_comments": args.min_comments,
        "delay_seconds": args.delay,
        "raw_dir": str(raw_dir),
        "cache_dir": str(cache_dir),
        "source_caveats": [
            "Reddit is a social / clue-only source, not company evidence.",
            "Comments are fetched through public JSON without OAuth.",
            "Deleted, removed, short, automoderator, and heavily downvoted comments are excluded.",
            "Deeply nested `more` comment nodes may not be fully resolved.",
        ],
    }
    write_json(raw_dir / "manifest.json", manifest)
    write_json(cache_dir / "manifest.json", manifest)
    generate_coverage_summary(args.subject, args.from_date, args.to_date, all_records, core_posts, all_comments, totals, cache_dir / "coverage-summary.md")
    generate_evidence_cards(args.subject, core_posts, comments_by_post, cache_dir / "evidence-cards.md")

    print("=== Complete ===")
    print(f"  Run ID: {run_id}")
    print(f"  Raw data: {raw_dir}")
    print(f"  Cache: {cache_dir}")
    print(f"  Core posts: {len(core_posts):,}")
    print(f"  Usable comments: {len(all_comments):,}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
