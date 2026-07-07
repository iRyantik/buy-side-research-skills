#!/usr/bin/env python3
"""browser-cdp — browser-harness wrapper for buy-side-research-skills.

Connects to the user's real Chrome via CDP (Chrome DevTools Protocol).
Inherits all cookies, logins, and browser fingerprints — bypasses
Cloudflare and other anti-bot detection that blocks headless Playwright.

Requires: browser-harness CLI (pip install browser-harness) +
          Chrome remote debugging enabled (chrome://inspect/#remote-debugging)

Core functions:
  browser_cdp_navigate(url)         → {"url", "title", "w", "h"}
  browser_cdp_extract_visible(url)  → visible text from JS-rendered page
  browser_cdp_extract_markdown()    → current page as markdown
  browser_cdp_js(code)              → eval JS, return string result
  browser_cdp_screenshot(path)      → save PNG to path
  browser_cdp_page_info()           → current page info (no navigation)

Usage:
  from browser_cdp import browser_cdp_navigate, browser_cdp_extract_visible

  # Quick JS-rendered page extraction
  text = browser_cdp_extract_visible("https://www.perplexity.ai/finance/HWM")
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

# ── locate browser-harness ──────────────────────────────────

def _find_harness() -> str:
    """Find browser-harness executable. Raises RuntimeError if not found."""
    # 1. Try PATH
    found = shutil.which("browser-harness")
    if found:
        return found

    # 2. Try common Python Scripts locations
    candidates = []
    if sys.platform == "win32":
        candidates.extend([
            Path.home() / "AppData" / "Roaming" / "Python" / "Python312" / "Scripts" / "browser-harness.exe",
            Path.home() / "AppData" / "Roaming" / "Python" / "Python311" / "Scripts" / "browser-harness.exe",
            Path.home() / "AppData" / "Local" / "Programs" / "Python" / "Python312" / "Scripts" / "browser-harness.exe",
        ])
    else:
        candidates.extend([
            Path.home() / ".local" / "bin" / "browser-harness",
            Path("/usr/local/bin/browser-harness"),
        ])

    # 3. Try pip show to find location
    try:
        r = subprocess.run(
            [sys.executable, "-m", "pip", "show", "browser-harness"],
            capture_output=True, text=True, timeout=15
        )
        if r.returncode == 0:
            for line in r.stdout.split("\n"):
                if line.startswith("Location:"):
                    loc = Path(line.split(":", 1)[1].strip())
                    exe = loc.parent / "Scripts" / "browser-harness.exe" if sys.platform == "win32" else loc.parent / "bin" / "browser-harness"
                    if exe.exists():
                        return str(exe)
    except Exception:
        pass

    for c in candidates:
        if c.exists():
            return str(c)

    raise RuntimeError(
        "browser-harness not found. Install: pip install browser-harness\n"
        "Then enable Chrome remote debugging: chrome://inspect/#remote-debugging"
    )


_BH: str | None = None

def _get_bh() -> str:
    global _BH
    if _BH is None:
        _BH = _find_harness()
    return _BH


# ── low-level execution ─────────────────────────────────────

def _run_bh(code: str, timeout: int = 60) -> str:
    """Pipe Python code to browser-harness, return stdout."""
    try:
        r = subprocess.run(
            [_get_bh()],
            input=code,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"browser-harness timed out after {timeout}s")

    stderr = r.stderr.strip()
    stdout = r.stdout.strip()

    if r.returncode != 0:
        # browser-harness often prints useful error to stderr
        err_msg = stderr if stderr else stdout
        if "chrome running" in err_msg and "daemon alive" in err_msg and "FAIL" in err_msg:
            raise RuntimeError(
                "Chrome remote debugging not enabled.\n"
                "Open chrome://inspect/#remote-debugging and tick 'Allow remote debugging'."
            )
        raise RuntimeError(f"browser-harness error (exit {r.returncode}): {err_msg[:500]}")

    return stdout


def _bh_is_available() -> bool:
    """Quick check if browser-harness + Chrome CDP are ready."""
    try:
        result = _run_bh("print(page_info())", timeout=15)
        info = json.loads(result.strip().split("\n")[-1])
        return "url" in info
    except Exception:
        return False


# ── public API ──────────────────────────────────────────────

def browser_cdp_navigate(url: str, wait: float = 3.0) -> dict[str, Any]:
    """Navigate to URL and return page_info dict. Uses new_tab on first call."""
    code = f"""import time
new_tab("{url}")
wait_for_load()
time.sleep({wait})
info = page_info()
print("__PAGE_INFO__")
print(info)
"""
    stdout = _run_bh(code)
    # Extract the dict line
    for line in stdout.split("\n"):
        if line.startswith("{") and "'url'" in line:
            return json.loads(line.replace("'", '"'))
    return {"error": "could not parse page_info", "raw": stdout[:500]}


def browser_cdp_goto(url: str, wait: float = 3.0) -> dict[str, Any]:
    """Navigate in current tab (use after first new_tab)."""
    code = f"""import time
goto_url("{url}")
wait_for_load()
time.sleep({wait})
info = page_info()
print("__PAGE_INFO__")
print(info)
"""
    stdout = _run_bh(code)
    for line in stdout.split("\n"):
        if line.startswith("{") and "'url'" in line:
            return json.loads(line.replace("'", '"'))
    return {"error": "could not parse page_info", "raw": stdout[:500]}


def browser_cdp_extract_visible(url: str, wait: float = 4.0) -> str:
    """Navigate to URL and extract visible text content (JS-rendered)."""
    browser_cdp_navigate(url, wait=wait)
    # Scroll down to trigger lazy loading
    _run_bh("js('window.scrollBy(0, 800)')", timeout=10)
    time.sleep(0.5)
    _run_bh("js('window.scrollBy(0, 800)')", timeout=10)
    time.sleep(0.5)

    text = _run_bh("""
import json
result = js(\"(function(){var m=document.querySelector('main,[role=\\\"main\\\"],.main-content');if(m)return m.textContent.substring(0,15000);return document.body.textContent.substring(0,15000);})()\")
print(result)
""")
    return text.strip()


def browser_cdp_extract_markdown() -> str:
    """Extract current page as readable text (title + body)."""
    text = _run_bh("""
import json
title = js("document.title")
body = js("(function(){var m=document.querySelector('main,[role=\\\"main\\\"],.main-content');if(m)return m.textContent.trim().substring(0,10000);return document.body.textContent.trim().substring(0,10000);})()")
print("# " + title)
print("")
print(body)
""")
    return text.strip()


def browser_cdp_js(code: str, timeout: int = 30) -> str:
    """Execute JavaScript in the current page context. Returns result string."""
    # Escape for safe embedding
    escaped = code.replace("\\", "\\\\").replace('"', '\\"')
    py_code = f'result = js("{escaped}")\nprint(result)'
    return _run_bh(py_code, timeout=timeout).strip()


def browser_cdp_screenshot(path: str) -> bool:
    """Take screenshot and save to path. Returns True on success."""
    _run_bh(f'capture_screenshot("{path}")')
    return Path(path).exists()


def browser_cdp_page_info() -> dict[str, Any]:
    """Get current page URL, title, viewport without navigation."""
    stdout = _run_bh("print(page_info())")
    for line in stdout.split("\n"):
        if line.startswith("{") and "'url'" in line:
            return json.loads(line.replace("'", '"'))
    return {"error": "could not parse page_info", "raw": stdout[:500]}


def browser_cdp_scroll(amount: int = 800, times: int = 1, wait: float = 1.0) -> None:
    """Scroll page down to trigger lazy loading."""
    for _ in range(times):
        _run_bh(f"js('window.scrollBy(0, {amount})')", timeout=10)
        time.sleep(wait)


def browser_cdp_search_tweets(handle: str, count: int = 5) -> list[str]:
    """Navigate to X.com profile and extract latest tweets."""
    browser_cdp_navigate(f"https://x.com/{handle}", wait=3)
    browser_cdp_scroll(800, times=2, wait=1.5)

    result = _run_bh(f"""
import json
tweets = js("(function(){{var tweets=document.querySelectorAll('div[data-testid=\\\"tweetText\\\"]');var r=[];tweets.forEach(function(t,i){{if(i<{count}){{r.push(t.textContent.trim());}}}});if(r.length===0){{r.push('no tweets found');}}return JSON.stringify(r);}})()")
print(tweets)
""")
    try:
        return json.loads(result)
    except json.JSONDecodeError:
        return [result[:500]]


# ── availability check ──────────────────────────────────────

def browser_cdp_available() -> tuple[bool, str]:
    """Check if browser-harness + Chrome CDP are ready. Returns (ok, detail)."""
    try:
        bh = _find_harness()
    except RuntimeError as e:
        return False, str(e)

    try:
        _run_bh("print(page_info())", timeout=15)
        return True, f"browser-harness ready ({bh})"
    except RuntimeError as e:
        msg = str(e)
        if "remote debugging" in msg.lower():
            return False, "Chrome remote debugging not enabled: chrome://inspect/#remote-debugging"
        return False, msg[:200]
    except Exception as e:
        return False, str(e)[:200]


# ── CLI ─────────────────────────────────────────────────────

def cli():
    """CLI entry point for standalone usage."""
    import argparse
    parser = argparse.ArgumentParser(
        description="browser-cdp — browser-harness wrapper for buy-side research"
    )
    sub = parser.add_subparsers(dest="cmd")

    nav = sub.add_parser("navigate", help="Navigate to URL and print page info")
    nav.add_argument("url")

    ext = sub.add_parser("extract", help="Extract visible text from URL")
    ext.add_argument("url")

    md = sub.add_parser("markdown", help="Extract current page as markdown")
    ss = sub.add_parser("screenshot", help="Take screenshot")
    ss.add_argument("path")

    sub.add_parser("check", help="Check if browser-harness is available")

    js_cmd = sub.add_parser("js", help="Execute JS in current page")
    js_cmd.add_argument("code")

    args = parser.parse_args()

    if args.cmd == "navigate":
        info = browser_cdp_navigate(args.url)
        print(json.dumps(info, ensure_ascii=False, indent=2))
    elif args.cmd == "extract":
        text = browser_cdp_extract_visible(args.url)
        print(text)
    elif args.cmd == "markdown":
        text = browser_cdp_extract_markdown()
        print(text)
    elif args.cmd == "screenshot":
        ok = browser_cdp_screenshot(args.path)
        print("saved" if ok else "failed")
    elif args.cmd == "check":
        ok, detail = browser_cdp_available()
        print(f"{'OK' if ok else 'FAIL'}: {detail}")
    elif args.cmd == "js":
        result = browser_cdp_js(args.code)
        print(result)
    else:
        parser.print_help()


if __name__ == "__main__":
    cli()
