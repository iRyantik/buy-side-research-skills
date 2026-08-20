#!/usr/bin/env python3
"""image-path-check.py — validate + repair artifact image references.

Canonical image pool: <workspace>/.cache/images/  (download-image.py, cross-skill
shared, flat). Every artifact image ref must resolve (relative to the artifact
file) to a file in the root pool. Topic-level / industry-level .cache pools,
absolute paths, and '/' rooted paths are all error classes — the pool is one,
depth is computed by this script, never hand-typed.

Reference classes:
  OK              resolves to root pool with minimal relpath
  NON_CANONICAL   resolves (any pool) but ref != minimal relpath to root pool
  ROOTED          starts with '/' — renderer-dependent
  ABSOLUTE        Windows absolute path (e.g. Typora paste from another machine)
  MISSING         no such file in any pool

Usage:
    python image-path-check.py            # report only
    python image-path-check.py --fix      # copy into root pool + rewrite refs
    python image-path-check.py --json     # machine-readable

Exit code: 0 clean, 1 problems remaining (after --fix, 0 = all repaired).

Note: MISSING refs are never auto-touched — decide per case (redownload or
mark [缺图] manually).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

IMG_RE = re.compile(r'!\[[^\]]*\]\(([^)]+)\)')
IMG_EXT = re.compile(r'\.(png|jpe?g|webp|gif|svg|ico)$', re.IGNORECASE)
SKIP_PREFIX = ("http://", "https://", "data:", "mailto:")


def find_workspace_root():
    p = Path.cwd()
    for _ in range(10):
        if (p / ".claude" / "hooks" / "hook_entry.py").exists():
            return p
        if p.parent == p:
            break
        p = p.parent
    return None


def find_pools(workspace: Path) -> list[Path]:
    """Root pool first, then all nested .cache/images pools (search fallback)."""
    pools = [workspace / ".cache" / "images"]
    for d in sorted(workspace.glob("industry/**/.cache/images")):
        pools.append(d)
    return pools


def locate_in_pools(pools: list[Path], basename: str) -> Path | None:
    """Find file by exact (case-insensitive) name in any pool."""
    want = basename.lower()
    for pool in pools:
        for f in pool.rglob(basename):
            if f.is_file():
                return f
        # case-insensitive fallback (Windows FS is CI, but keep it explicit)
        for f in pool.rglob("*"):
            if f.is_file() and f.name.lower() == want:
                return f
    return None


def collect_refs(workspace: Path):
    """Yield (md_file, lineno, target, raw_md_line)."""
    for f in sorted(workspace.glob("industry/**/*.md")):
        rel = f.relative_to(workspace)
        if ".cache" in rel.parts or f.name == "RESEARCH.md":
            continue
        text = f.read_text(encoding="utf-8")
        for m in IMG_RE.finditer(text):
            target = m.group(1).strip()
            if not IMG_EXT.search(target):
                continue
            if target.lower().startswith(SKIP_PREFIX):
                continue
            lineno = text.count("\n", 0, m.start()) + 1
            yield f, lineno, target, m.group(0)


def resolve_target(workspace: Path, md_file: Path, target: str):
    """Resolve a ref to an existing file or None. Returns (kind, resolved)."""
    if re.match(r'^[A-Za-z]:[\\/]', target):
        return "ABSOLUTE", None
    if target.startswith("/"):
        cand = workspace / target.lstrip("/")
        return ("ROOTED", cand if cand.is_file() else None)
    cand = (md_file.parent / target).resolve()
    return ("REL", cand if cand.is_file() else None)


def canonical_ref(md_file: Path, pool_file: Path) -> str:
    return str(Path(os_relpath(pool_file, md_file.parent)).as_posix())


def os_relpath(target: Path, base: Path) -> str:
    import os
    return os.path.relpath(str(target), str(base))


def scan(workspace: Path, fix: bool = False, verbose: bool = True):
    pools = find_pools(workspace)
    root_pool = pools[0]
    problems = {"NON_CANONICAL": [], "ROOTED": [], "ABSOLUTE": [], "MISSING": []}
    n_ok = 0

    for md_file, lineno, target, raw in collect_refs(workspace):
        kind, resolved = resolve_target(workspace, md_file, target)
        pool_file = None

        if kind in ("REL", "ROOTED") and resolved:
            # resolves already — but must be in root pool, ref must be minimal
            if str(resolved).startswith(str(root_pool)):
                ref = canonical_ref(md_file, resolved)
                if ref == target:
                    n_ok += 1
                    continue
                pool_file = resolved
            else:
                pool_file = resolved
        elif kind in ("REL", "ROOTED", "ABSOLUTE"):
            # try pools by basename
            pool_file = locate_in_pools(pools, Path(target).name)
            if pool_file is None:
                problems["MISSING"].append((md_file, lineno, target, raw))
                continue

        # pool_file found somewhere — ensure it's in root pool, then rewrite
        if pool_file and not str(pool_file).startswith(str(root_pool)):
            dst = root_pool / pool_file.name
            if not dst.exists():
                root_pool.mkdir(parents=True, exist_ok=True)
                import shutil
                shutil.copy2(pool_file, dst)
            pool_file = dst

        ref = canonical_ref(md_file, pool_file)
        cls = "NON_CANONICAL" if kind != "MISSING" else "MISSING"
        if target == ref:
            n_ok += 1
            continue
        problems[cls].append((md_file, lineno, target, raw, ref))

    return problems, n_ok


def report(workspace: Path, fix: bool = False):
    problems, n_ok = scan(workspace, fix=fix)

    total = n_ok + sum(len(v) for v in problems.values())
    print(f"Image refs: {total}  OK: {n_ok}")
    for cls, items in problems.items():
        if not items:
            continue
        print(f"\n=== {cls} ({len(items)}) ===")
        for item in items:
            md_file, lineno, target, raw = item[:4]
            rel = str(md_file.relative_to(workspace))
            print(f"  {rel}:{lineno}")
            print(f"    {target}")
            if len(item) == 5:
                print(f"    → {item[4]}")

    if problems["MISSING"]:
        print("\n=== MISSING files were NOT auto-fixed — decide: redownload or mark [缺图] ===")
    return 0 if not any(problems.values()) else 1


def fix_all(workspace: Path):
    pools = find_pools(workspace)
    root_pool = pools[0]
    fixed = 0
    rewritten = 0
    missing = []

    for md_file, lineno, target, raw in collect_refs(workspace):
        kind, resolved = resolve_target(workspace, md_file, target)
        pool_file = None

        if kind in ("REL", "ROOTED") and resolved:
            pool_file = resolved
        elif kind in ("REL", "ROOTED", "ABSOLUTE"):
            pool_file = locate_in_pools(pools, Path(target).name)

        if pool_file is None:
            missing.append((md_file, lineno, target))
            continue

        if not str(pool_file).startswith(str(root_pool)):
            dst = root_pool / pool_file.name
            if not dst.exists():
                root_pool.mkdir(parents=True, exist_ok=True)
                import shutil
                shutil.copy2(pool_file, dst)
                fixed += 1
            pool_file = dst

        ref = canonical_ref(md_file, pool_file)
        if ref == target:
            continue

        text = md_file.read_text(encoding="utf-8")
        new_raw = raw.replace(target, ref, 1)
        if new_raw == raw:
            continue
        updated = text.replace(raw, new_raw, 1)
        if updated == text:
            continue
        md_file.write_text(updated, encoding="utf-8", newline="")
        print(f"  {md_file.relative_to(workspace)}:{lineno}")
        print(f"    {target} → {ref}")
        rewritten += 1

    print(f"\nCopied into root pool: {fixed}  Rewritten refs: {rewritten}")
    if missing:
        print(f"MISSING (not touched, {len(missing)}):")
        for md_file, lineno, target in missing:
            print(f"  {md_file.relative_to(workspace)}:{lineno}  {target}")


def main():
    p = argparse.ArgumentParser(description="Validate + repair artifact image refs")
    p.add_argument("--fix", action="store_true", help="Copy into root pool + rewrite refs")
    p.add_argument("--json", action="store_true", help="Machine-readable report")
    args = p.parse_args()

    ws = find_workspace_root()
    if not ws:
        print("Not in a workspace.", file=sys.stderr)
        return 2

    if args.fix:
        fix_all(ws)
    elif args.json:
        problems, n_ok = scan(ws)
        print(json.dumps({
            "ok": n_ok,
            "problems": {k: len(v) for k, v in problems.items()},
            "details": {k: [[str(m.relative_to(ws)), ln, t] for m, ln, t, *_ in v]
                        for k, v in problems.items()},
        }, ensure_ascii=False, indent=2))
    else:
        return report(ws)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
