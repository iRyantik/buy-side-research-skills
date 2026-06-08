#!/usr/bin/env python3
"""verify-runtime.py — one-click runtime verification for buy-side-research-skills.

Checks 12 components across 3 layers. Any failure → INSTALLS the missing
dependency (winget on Windows, brew on macOS), then re-checks. If auto-install
fails, prints the manual command and exits non-zero.

Usage:
  python verify-runtime.py          # verify + auto-install missing
  python verify-runtime.py --json   # machine-readable output
"""
from __future__ import annotations

import sys
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

import json
import os
import subprocess
import sys
import importlib
import platform
from pathlib import Path

# ── config ────────────────────────────────────────────────

PYTHON_MIN = (3, 10)
NODE_MIN = 18

CORE_PACKAGES = [
    ("yfinance", "yfinance"),
    ("openpyxl", "openpyxl"),
    ("requests", "requests"),
    ("dotenv", "python-dotenv"),
    ("yaml", "pyyaml"),
    ("lxml", "lxml"),
    ("docx", "python-docx"),
    ("pptx", "python-pptx"),
]

IS_WINDOWS = sys.platform == "win32"
IS_MACOS = sys.platform == "darwin"

# ── helpers ────────────────────────────────────────────────

def _run(cmd: list[str], timeout: int = 60) -> tuple[int, str, str]:
    """Run a command, return (returncode, stdout, stderr)."""
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout.strip(), r.stderr.strip()
    except FileNotFoundError:
        return -1, "", f"command not found: {cmd[0]}"
    except subprocess.TimeoutExpired:
        return -2, "", f"timeout: {' '.join(cmd)}"


def _try_install(pkg_name: str, platform_cmds: dict[str, list[str]]) -> bool:
    """Try to install a system package. Returns True if install succeeded."""
    if IS_WINDOWS and "win" in platform_cmds:
        cmd = platform_cmds["win"]
    elif IS_MACOS and "mac" in platform_cmds:
        cmd = platform_cmds["mac"]
    else:
        return False

    print(f"  → Installing {pkg_name}: {' '.join(cmd)}")
    rc, _, err = _run(cmd, timeout=300)
    if rc == 0:
        print(f"  ✅ {pkg_name} installed")
        return True
    else:
        print(f"  ❌ Install failed: {err[:200]}")
        return False


def _try_pip_install(pkg_name: str) -> bool:
    """Try pip install a package. Returns True if succeeded."""
    print(f"  → pip install {pkg_name}")
    rc, _, err = _run([sys.executable, "-m", "pip", "install", pkg_name], timeout=120)
    if rc == 0:
        print(f"  ✅ {pkg_name} installed")
        return True
    else:
        print(f"  ❌ pip install failed: {err[:200]}")
        return False


# ── layer 1: system ────────────────────────────────────────

def check_python() -> tuple[bool, str]:
    v = sys.version_info
    if v >= PYTHON_MIN:
        return True, f"Python {v.major}.{v.minor}.{v.micro}"
    return False, f"Python {v.major}.{v.minor}.{v.micro} (need 3.10+)"


def install_python() -> str | None:
    if IS_WINDOWS:
        ok = _try_install("Python 3.12", {"win": ["winget", "install", "Python.Python.3.12", "--accept-source-agreements"]})
    elif IS_MACOS:
        ok = _try_install("Python 3.12", {"mac": ["brew", "install", "python@3.12"]})
    else:
        return "Please install Python 3.10+ from https://python.org"
    return None if ok else manual_python()


def manual_python() -> str:
    if IS_WINDOWS:
        return "winget install Python.Python.3.12 --accept-source-agreements"
    elif IS_MACOS:
        return "brew install python@3.12"
    return "Install Python 3.10+ from https://python.org"


def check_node() -> tuple[bool, str]:
    rc, out, _ = _run(["node", "--version"])
    if rc == 0:
        v = out.lstrip("v")
        try:
            major = int(v.split(".")[0])
            if major >= NODE_MIN:
                return True, f"Node.js {out}"
            return False, f"Node.js {out} (need ≥v{NODE_MIN})"
        except ValueError:
            return False, f"Node.js {out} (cannot parse version)"
    return False, "Node.js not found"


def install_node() -> str | None:
    if IS_WINDOWS:
        ok = _try_install("Node.js LTS", {"win": ["winget", "install", "OpenJS.NodeJS.LTS", "--accept-source-agreements"]})
    elif IS_MACOS:
        ok = _try_install("Node.js", {"mac": ["brew", "install", "node"]})
    else:
        return "Please install Node.js ≥18 from https://nodejs.org"
    return None if ok else manual_node()


def manual_node() -> str:
    if IS_WINDOWS:
        return "winget install OpenJS.NodeJS.LTS --accept-source-agreements"
    elif IS_MACOS:
        return "brew install node"
    return "Install Node.js ≥18 from https://nodejs.org"


def check_npx() -> tuple[bool, str]:
    # On Windows, Anaconda Python's subprocess may fail to resolve npx.cmd
    # via PATHEXT even when it's on PATH. Try bare name first, then .cmd.
    rc, out, _ = _run(["npx", "--version"])
    if rc != 0 and IS_WINDOWS:
        rc, out, _ = _run(["npx.cmd", "--version"])
    if rc == 0:
        return True, f"npx {out}"
    return False, "npx not found (re-install Node.js)"


def check_curl() -> tuple[bool, str]:
    rc, out, _ = _run(["curl", "--version"])
    if rc == 0:
        ver = out.split("\n")[0] if out else "ok"
        return True, ver[:80]
    return False, "curl not found"


def install_curl() -> str | None:
    if IS_WINDOWS:
        ok = _try_install("curl", {"win": ["winget", "install", "curl.curl", "--accept-source-agreements"]})
    elif IS_MACOS:
        ok = True  # macOS ships curl
    else:
        return "Please install curl via your package manager"
    return None if ok else manual_curl()


def manual_curl() -> str:
    if IS_WINDOWS:
        return "winget install curl.curl --accept-source-agreements"
    return "Install curl via your package manager"


# ── layer 2: python packages ───────────────────────────────

def check_package(import_name: str, pkg_name: str) -> tuple[bool, str]:
    try:
        mod = importlib.import_module(import_name)
        ver = getattr(mod, "__version__", "installed")
        return True, f"{pkg_name} {ver}"
    except ImportError:
        return False, f"{pkg_name} not installed"


def install_package(pkg_name: str) -> str | None:
    ok = _try_pip_install(pkg_name)
    return None if ok else f"pip install {pkg_name}"


# ── layer 3: config ────────────────────────────────────────

def check_mcp_json(workspace: Path) -> tuple[bool, str]:
    mcp_path = workspace / ".claude" / "mcp.json"
    if not mcp_path.is_file():
        return False, ".claude/mcp.json not found"

    try:
        with open(mcp_path, encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return False, f".claude/mcp.json invalid JSON: {e}"

    servers = data.get("mcpServers", {})
    if "playwright" not in servers:
        return False, ".claude/mcp.json missing playwright key"

    pw = servers["playwright"]
    cmd = pw.get("command", "")
    if cmd != "npx":
        return False, f"playwright command is '{cmd}', expected 'npx'"

    return True, "playwright key present"


def check_hooks(workspace: Path) -> tuple[bool, str]:
    hook_entry = workspace / ".claude" / "hooks" / "hook_entry.py"
    if not hook_entry.is_file():
        return False, ".claude/hooks/hook_entry.py not found"

    hooks_dir = str(hook_entry.parent)
    if hooks_dir not in sys.path:
        sys.path.insert(0, hooks_dir)

    try:
        importlib.import_module("hook_entry")
        return True, "hook_entry importable"
    except Exception as e:
        return False, f"hook_entry import failed: {e}"


# ── main ───────────────────────────────────────────────────

def verify(workspace: Path | None = None, auto_install: bool = True) -> dict:
    """Run all checks. Returns result dict with status for each check."""
    if workspace is None:
        workspace = Path.cwd()

    results = {
        "python": None,
        "node": None,
        "npx": None,
        "curl": None,
        "packages": {},
        "mcp_json": None,
        "hooks": None,
        "all_pass": False,
    }

    failed = False

    # Layer 1: System
    print("Layer 1 — System")
    for name, check_fn, install_fn in [
        ("Python", check_python, install_python),
        ("Node.js", check_node, install_node),
        ("npx", check_npx, None),  # npx comes with Node.js, no separate install
        ("curl", check_curl, install_curl),
    ]:
        ok, detail = check_fn()
        if ok:
            print(f"  {detail:<40} ✅")
        else:
            print(f"  {detail:<40} ❌")
            if auto_install and install_fn:
                err = install_fn()
                if err is None:
                    # Re-check after install
                    ok2, detail2 = check_fn()
                    if ok2:
                        print(f"  {detail2:<40} ✅ (auto-installed)")
                        results[name.lower().replace(".", "_")] = True
                        continue
            failed = True
            results[name.lower().replace(".", "_")] = False
            if name == "npx":
                print(f"  → Fix: re-install Node.js LTS ({manual_node()})")
        results[name.lower().replace(".", "_")] = ok

    print()

    # Layer 2: Python Packages
    print("Layer 2 — Python Packages")
    for import_name, pkg_name in CORE_PACKAGES:
        ok, detail = check_package(import_name, pkg_name)
        results["packages"][pkg_name] = ok
        if ok:
            print(f"  {detail:<40} ✅")
        else:
            print(f"  {detail:<40} ❌")
            if auto_install:
                err = install_package(pkg_name)
                if err is None:
                    ok2, detail2 = check_package(import_name, pkg_name)
                    if ok2:
                        print(f"  {detail2:<40} ✅ (auto-installed)")
                        results["packages"][pkg_name] = True
                        continue
            failed = True
            results["packages"][pkg_name] = False
    print()

    # Layer 3: Config
    print("Layer 3 — Config")
    for name, check_fn in [
        (".claude/mcp.json", lambda: check_mcp_json(workspace)),
        (".claude/hooks/", lambda: check_hooks(workspace)),
    ]:
        ok, detail = check_fn()
        key = "mcp_json" if "mcp" in name else "hooks"
        results[key] = ok
        if ok:
            print(f"  {detail:<50} ✅")
        else:
            print(f"  {detail:<50} ❌")
            failed = True
    print()

    results["all_pass"] = not failed

    # Summary
    total = 4 + len(CORE_PACKAGES) + 2  # 4 system + 6 packages + 2 config = 12
    passed = (
        sum(1 for v in [results["python"], results["node_js"], results["npx"], results["curl"]] if v)
        + sum(1 for v in results["packages"].values() if v)
        + sum(1 for v in [results["mcp_json"], results["hooks"]] if v)
    )

    if failed:
        print(f"Result: {passed}/{total} ✅ — ❌ dependencies missing. Fix above and re-run.")
    else:
        print(f"Result: {passed}/{total} ✅ — workspace ready.")

    return results


def cli():
    import argparse
    parser = argparse.ArgumentParser(description="Verify buy-side-research-skills runtime")
    parser.add_argument("--json", action="store_true", help="Machine-readable output")
    parser.add_argument("--workspace", default=None, help="Workspace root path")
    args = parser.parse_args()

    ws = Path(args.workspace) if args.workspace else Path.cwd()

    if args.json:
        results = verify(ws, auto_install=False)
        print(json.dumps(results, indent=2, ensure_ascii=False))
    else:
        results = verify(ws, auto_install=True)

    sys.exit(0 if results["all_pass"] else 1)


if __name__ == "__main__":
    cli()
