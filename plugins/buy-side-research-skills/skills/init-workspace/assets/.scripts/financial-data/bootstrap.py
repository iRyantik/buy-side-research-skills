#!/usr/bin/env python3
"""Bootstrap financial-data dependencies (replaces bootstrap-financial-data-deps.ps1).

Usage:
  python bootstrap.py              # Install dependencies
  python bootstrap.py --check      # Check status only
  python bootstrap.py --yes        # Skip confirmation
  python bootstrap.py --china      # Use Tsinghua PyPI mirror (China users)
"""

import sys
import os
import subprocess
import importlib.util
import argparse
import json

REQUIRED_PYTHON = (3, 10)
PACKAGES = ["edgar", "akshare", "edinet_tools", "dart_fss", "openesef"]
PROVIDER_ENV_VARS = {
    "EDGAR_IDENTITY": "SEC EDGAR (美股) — 格式: 'Name email@domain.com'",
    "DART_API_KEY": "DART (韩股) — 免费申请: https://opendart.fss.or.kr/",
    "EDINET_API_KEY": "EDINET (日股) — 免费申请: https://disclosure2.edinet-fsa.go.jp/",
    "FINMIND_TOKEN": "FinMind (台股) — 免费申请: https://finmindtrade.com/",
    "FMP_API_KEY": "FMP (全市场行情/三表/estimates) — workspace .env; news 仅美股",
}

def find_python():
    for name in ["python3", "python"]:
        try:
            result = subprocess.run([name, "-c",
                "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"],
                capture_output=True, text=True)
            if result.returncode == 0:
                ver = tuple(map(int, result.stdout.strip().split(".")))
                if ver >= REQUIRED_PYTHON:
                    return name
        except Exception:
            continue
    return None

def find_requirements():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(script_dir, "requirements.txt"),
        os.path.join(script_dir, "..", "assets", "requirements-financial-data.txt"),
    ]
    for c in candidates:
        if os.path.isfile(c):
            return os.path.normpath(c)
    return None

def check_deps():
    result = {"python": {"available": False, "version": None}, "packages": {}, "env": {}}
    python = find_python()
    if python:
        result["python"]["available"] = True
        v = subprocess.run([python, "-c", "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"],
                          capture_output=True, text=True)
        result["python"]["version"] = v.stdout.strip()
        result["python"]["executable"] = python
    for pkg in PACKAGES:
        name = pkg.replace("-", "_")
        spec = None
        try:
            spec = importlib.util.find_spec(name)
        except Exception:
            pass
        result["packages"][pkg] = spec is not None
    for var, desc in PROVIDER_ENV_VARS.items():
        result["env"][var] = {"configured": bool(os.environ.get(var)), "description": desc}
    req_path = find_requirements()
    result["requirements_path"] = req_path
    return result

def main():
    parser = argparse.ArgumentParser(description="Bootstrap financial-data dependencies")
    parser.add_argument("--check", action="store_true", help="Check dependency status only")
    parser.add_argument("--yes", action="store_true", help="Skip confirmation prompt")
    parser.add_argument("--china", action="store_true", help="Use Tsinghua PyPI mirror")
    args = parser.parse_args()

    if args.check:
        print(json.dumps(check_deps(), indent=2))
        return

    python = find_python()
    if not python:
        print("ERROR: Python 3.10+ not found. Install from https://python.org", file=sys.stderr)
        sys.exit(1)
    deps = check_deps()
    print(f"[OK] Python: {python} ({deps['python']['version']})")

    req_path = deps["requirements_path"]
    if not req_path:
        print("ERROR: requirements-financial-data.txt not found", file=sys.stderr)
        sys.exit(1)
    print(f"[..] Requirements: {req_path}")

    if not args.yes:
        missing = [p for p, ok in deps["packages"].items() if not ok]
        if missing:
            print(f"Will install: {', '.join(missing)}")
        else:
            print("All Python packages already installed.")
        missing_env = [v for v, info in deps["env"].items() if not info["configured"]]
        if missing_env:
            print(f"[!] Missing provider env vars: {', '.join(missing_env)}")
            for v in missing_env:
                print(f"    {v}: {PROVIDER_ENV_VARS[v]}")
        if not missing:
            if not missing_env:
                print("Nothing to do.")
            return
        answer = input("Continue? [y/N] ").strip()
        if answer.lower() not in ("y", "yes"):
            print("Cancelled.")
            sys.exit(1)

    pip_cmd = [python, "-m", "pip", "install"]
    if args.china:
        pip_cmd += ["-i", "https://pypi.tuna.tsinghua.edu.cn/simple"]
    pip_cmd += ["-r", req_path]

    print(f"[..] Running: {' '.join(pip_cmd)}")
    result = subprocess.run(pip_cmd)
    if result.returncode != 0:
        print("ERROR: pip install failed", file=sys.stderr)
        sys.exit(1)

    print("[OK] financial-data dependencies ready.")
    final = check_deps()
    print(json.dumps({"packages": final["packages"], "env": {k: v["configured"] for k, v in final["env"].items()}}, indent=2))

if __name__ == "__main__":
    main()
