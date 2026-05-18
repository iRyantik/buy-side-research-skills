#!/usr/bin/env python3
"""Promote company-scoped files from a workbench topic into topics/company/<slug>/."""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
import re
import shutil
from typing import Any


DATE_PREFIX = r"\d{4}-\d{2}-\d{2}"


def normalize_topic(topic: str) -> str:
    topic = topic.replace("\\", "/").strip().strip("/")
    if topic.startswith("topics/"):
        topic = topic[len("topics/") :]
    return topic


def collision_safe(path: Path) -> Path:
    if not path.exists():
        return path
    stem = path.stem
    suffix = path.suffix
    idx = 2
    while True:
        candidate = path.with_name(f"{stem}-{idx}{suffix}")
        if not candidate.exists():
            return candidate
        idx += 1


def token_match(path: Path, tokens: list[str]) -> bool:
    haystack = path.name.lower()
    return any(token and token.lower() in haystack for token in tokens)


def ensure_company_topic(workspace: Path, company_slug: str, display_name: str | None, apply: bool) -> tuple[Path, Path]:
    company_root = workspace / "topics" / "company" / company_slug
    index_path = company_root / "index.md"
    inbox_path = company_root / "_inbox"
    if apply:
        company_root.mkdir(parents=True, exist_ok=True)
        inbox_path.mkdir(parents=True, exist_ok=True)
        if not index_path.exists():
            title = display_name or company_slug
            index_path.write_text(
                f"# {title}\n\n## Topic Map\n\n- namespace: company\n- slug: {company_slug}\n\n## Promotion Provenance\n\n",
                encoding="utf-8",
            )
    return company_root, index_path


def root_markdown_moves(source_root: Path, company_root: Path, company_slug: str) -> list[dict[str, Any]]:
    pattern = re.compile(rf"^({DATE_PREFIX})-{re.escape(company_slug)}-(.+)\.md$", re.IGNORECASE)
    moves: list[dict[str, Any]] = []
    for path in sorted(source_root.glob("*.md")):
        match = pattern.match(path.name)
        if not match:
            continue
        dest_name = f"{match.group(1)}-{match.group(2)}.md"
        moves.append(
            {
                "kind": "research_markdown",
                "from": path,
                "to": collision_safe(company_root / dest_name),
                "reason": "company-prefixed dated markdown",
            }
        )
    return moves


def attributed_tree_moves(source_root: Path, company_root: Path, subdir: str, tokens: list[str]) -> list[dict[str, Any]]:
    base = source_root / subdir
    if not base.exists():
        return []
    moves: list[dict[str, Any]] = []
    for path in sorted(p for p in base.rglob("*") if p.is_file()):
        if not token_match(path, tokens):
            continue
        rel = path.relative_to(base)
        moves.append(
            {
                "kind": subdir.strip("_"),
                "from": path,
                "to": collision_safe(company_root / subdir / rel),
                "reason": "filename matched company slug or alias",
            }
        )
    return moves


def cache_provenance_moves(
    source_root: Path,
    company_root: Path,
    planned_source_moves: list[dict[str, Any]],
    existing_moves: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    cache_root = source_root / "_cache"
    if not cache_root.exists():
        return []
    old_source_paths = [str(item["from"]) for item in planned_source_moves]
    already = {Path(item["from"]).resolve() for item in existing_moves}
    moves: list[dict[str, Any]] = []
    for path in sorted(p for p in cache_root.rglob("*.md") if p.is_file()):
        if path.resolve() in already:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if not any(old_path in text for old_path in old_source_paths):
            continue
        rel = path.relative_to(cache_root)
        moves.append(
            {
                "kind": "cache",
                "from": path,
                "to": collision_safe(company_root / "_cache" / rel),
                "reason": "cache source_path matched a promoted source file",
            }
        )
    return moves


def apply_move(item: dict[str, Any], source_path_updates: dict[str, str]) -> None:
    src = Path(item["from"])
    dest = Path(item["to"])
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src), str(dest))
    if item["kind"] == "cache" and dest.suffix.lower() == ".md":
        text = dest.read_text(encoding="utf-8", errors="replace")
        for old, new in source_path_updates.items():
            text = text.replace(old, new)
        dest.write_text(text, encoding="utf-8")


def append_index(path: Path, title: str, lines: list[str], apply: bool) -> None:
    if not apply:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(f"# {path.parent.name}\n\n", encoding="utf-8")
    existing = path.read_text(encoding="utf-8", errors="replace")
    block = "\n".join(["", f"## {title}", "", *lines, ""])
    path.write_text(existing.rstrip() + "\n" + block, encoding="utf-8")


def build_plan(args: argparse.Namespace) -> dict[str, Any]:
    workspace = Path(args.workspace).expanduser().resolve()
    source_topic = normalize_topic(args.source_topic)
    company_slug = args.company_slug.lower().strip()
    aliases = [company_slug, *(alias.lower().strip() for alias in args.alias)]

    source_root = workspace / "topics" / source_topic
    if not (source_root / "index.md").exists():
        raise SystemExit(f"Source topic missing index.md: {source_root / 'index.md'}")

    company_root, company_index = ensure_company_topic(workspace, company_slug, args.company_display_name, args.apply)

    research_moves = root_markdown_moves(source_root, company_root, company_slug)
    inbox_moves = attributed_tree_moves(source_root, company_root, "_inbox", aliases)
    raw_moves = attributed_tree_moves(source_root, company_root, "_raw", aliases)
    cache_name_moves = attributed_tree_moves(source_root, company_root, "_cache", aliases)
    cache_prov_moves = cache_provenance_moves(source_root, company_root, inbox_moves + raw_moves, cache_name_moves)

    moves = research_moves + inbox_moves + raw_moves + cache_name_moves + cache_prov_moves
    source_path_updates = {str(item["from"]): str(item["to"]) for item in inbox_moves + raw_moves}

    left = []
    for path in sorted(source_root.glob("*.md")):
        if path.name == "index.md":
            continue
        if not any(Path(item["from"]).resolve() == path.resolve() for item in research_moves):
            left.append({"file": str(path), "reason": "mixed or source-topic-level markdown"})

    if args.apply:
        for item in moves:
            apply_move(item, source_path_updates)

        date = dt.date.today().isoformat()
        moved_lines = [f"- {Path(item['from']).name} -> {Path(item['to']).relative_to(company_root)} ({item['reason']})" for item in moves]
        if not moved_lines:
            moved_lines = ["- No deterministic company-scoped files were moved."]

        append_index(
            source_root / "index.md",
            f"Promoted Company: {company_slug} ({date})",
            [
                f"- company topic: `topics/company/{company_slug}/`",
                "- moved files:",
                *moved_lines,
            ],
            apply=True,
        )
        append_index(
            company_index,
            f"Promotion Provenance ({date})",
            [
                f"- source topic: `topics/{source_topic}/`",
                "- moved files:",
                *moved_lines,
                "- source-topic files left in place should be treated as backlinks, not duplicated company canonical artifacts.",
            ],
            apply=True,
        )

    return {
        "status": "applied" if args.apply else "dry_run",
        "workspace": str(workspace),
        "source_topic": source_topic,
        "company_topic": f"company/{company_slug}",
        "moves": [
            {**item, "from": str(item["from"]), "to": str(item["to"])}
            for item in moves
        ],
        "left_in_source": left,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Promote company-scoped research into topics/company/<slug>/")
    parser.add_argument("--workspace", required=True, help="Research workspace root")
    parser.add_argument("--source-topic", required=True, help="Source topic, e.g. industry/space-launch")
    parser.add_argument("--company-slug", required=True, help="Canonical company slug, e.g. rklb")
    parser.add_argument("--company-display-name", help="Optional display name for new company index")
    parser.add_argument("--alias", action="append", default=[], help="Additional alias used for file matching")
    parser.add_argument("--apply", action="store_true", help="Apply the move plan. Omit for dry-run JSON.")
    return parser.parse_args()


def main() -> int:
    plan = build_plan(parse_args())
    print(json.dumps(plan, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
