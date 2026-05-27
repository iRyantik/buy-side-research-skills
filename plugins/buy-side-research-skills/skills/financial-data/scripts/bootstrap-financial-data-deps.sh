#!/usr/bin/env bash
# One-command install of financial-data Python dependencies for buy-side research.
# Works on macOS: auto-detects Python, installs what's missing.
#
# Usage:
#   chmod +x bootstrap-financial-data-deps.sh
#   ./bootstrap-financial-data-deps.sh                # interactive
#   ./bootstrap-financial-data-deps.sh --yes          # skip confirmation
#   ./bootstrap-financial-data-deps.sh --check-only   # print dependency status JSON
#   ./bootstrap-financial-data-deps.sh --yes --china  # use China mirrors (pypi)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REQ_CANDIDATES=("$SCRIPT_DIR/requirements-financial-data.txt" "$SCRIPT_DIR/../assets/requirements-financial-data.txt")
REQ_PATH=""
for cand in "${REQ_CANDIDATES[@]}"; do
    if [ -f "$cand" ]; then
        REQ_PATH="$cand"
        break
    fi
done

YES=false
CHECK_ONLY=false
CHINA_MIRROR=false

for arg in "$@"; do
    case "$arg" in
        --yes|-y) YES=true ;;
        --check-only) CHECK_ONLY=true ;;
        --china) CHINA_MIRROR=true ;;
        *) echo "Unknown flag: $arg"; exit 1 ;;
    esac
done

# ---------- helpers ----------
find_python() {
    for candidate in python3.12 python3.11 python3.10 python3 python; do
        if command -v "$candidate" &>/dev/null; then
            if "$candidate" -c 'import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)' 2>/dev/null; then
                echo "$candidate"
                return
            fi
        fi
    done
    echo ""
}

check_module() {
    "$PYTHON" -c "import importlib.util; importlib.util.find_spec('$1')" &>/dev/null
}

get_deps_json() {
    local pkgs='{}'
    for pkg in edgartools akshare edinet-tools dart-fss openesef; do
        local name="$pkg"
        # akshare import name matches package name; dart-fss -> dart_fss; edinet-tools -> edinet_tools
        case "$pkg" in
            dart-fss) name="dart_fss" ;;
            edinet-tools) name="edinet_tools" ;;
        esac
        local avail="false"
        check_module "$name" 2>/dev/null && avail="true"
        pkgs=$(echo "$pkgs" | python3 -c "import json,sys; d=json.load(sys.stdin); d['$pkg']={'available':$avail}; print(json.dumps(d))" 2>/dev/null || echo "$pkgs")
    done
    echo "$pkgs"
}

# ---------- check ----------
PYTHON=$(find_python)

if [ "$CHECK_ONLY" = true ]; then
    if [ -z "$PYTHON" ]; then
        echo '{"python":{"available":false},"pip":{"available":false},"status":"no-python"}'
    else
        echo "{\"python\":{\"available\":true,\"version\":\"$("$PYTHON" --version 2>&1)\",\"path\":\"$(command -v "$PYTHON")\"},\"packages\":$(get_deps_json),\"requirements_path\":\"$REQ_PATH\"}"
    fi
    exit 0
fi

# ---------- python check ----------
if [ -z "$PYTHON" ]; then
    echo "=============================================="
    echo "  Python 3.10+ 未找到"
    echo "=============================================="
    echo ""
    echo "请先安装 Python，然后重新运行本脚本："
    echo ""
    echo "  brew install python@3.12"
    echo ""
    echo "或从 https://www.python.org/downloads/ 下载"
    echo ""
    exit 1
fi

echo "[OK] Python: $("$PYTHON" --version) ($(command -v "$PYTHON"))"

# ---------- conda check ----------
if "$PYTHON" -c "import sys; sys.exit(0 if 'conda' in sys.version or 'Continuum' in sys.version else 1)" 2>/dev/null; then
    echo "[!] 检测到 Anaconda Python。建议在 conda 环境中安装，或使用系统 Python。"
fi

# ---------- requirements check ----------
if [ -z "$REQ_PATH" ]; then
    echo "[ERROR] 找不到 requirements-financial-data.txt"
    exit 1
fi
echo "[OK] 依赖文件: $REQ_PATH"

# ---------- xcode CLI check (macOS) ----------
if [[ "$(uname)" == "Darwin" ]]; then
    if ! xcode-select -p &>/dev/null; then
        echo "[!] 未安装 Xcode Command Line Tools。部分包可能需要编译。"
        echo "    运行: xcode-select --install"
    fi
fi

# ---------- upgrade pip ----------
echo ""
echo "--- 升级 pip ---"
"$PYTHON" -m pip install --user --upgrade pip --quiet 2>/dev/null || true

# ---------- install ----------
echo ""
echo "--- 安装依赖 ---"

PIP_ARGS=(-m pip install --user -r "$REQ_PATH")
if [ "$CHINA_MIRROR" = true ]; then
    PIP_ARGS=(-m pip install --user -i https://pypi.tuna.tsinghua.edu.cn/simple -r "$REQ_PATH")
    echo "[China Mirror] PyPI: tsinghua"
fi

echo "Running: $PYTHON ${PIP_ARGS[*]}"
"$PYTHON" "${PIP_ARGS[@]}"

# ---------- verify ----------
echo ""
echo "--- 验证安装 ---"
FAILED=()
for pkg in edgar akshare edinet_tools dart_fss openesef; do
    if "$PYTHON" -c "import importlib.util; importlib.util.find_spec('$pkg') or exit(1)" 2>/dev/null; then
        echo "[OK] $pkg"
    else
        echo "[FAIL] $pkg"
        FAILED+=("$pkg")
    fi
done

if [ ${#FAILED[@]} -gt 0 ]; then
    echo ""
    echo "=============================================="
    echo "  部分包安装失败: ${FAILED[*]}"
    echo "=============================================="
    echo ""
    echo "请检查网络连接，或尝试中国镜像:"
    echo "  ./bootstrap-financial-data-deps.sh --yes --china"
    echo ""
    exit 1
fi

echo ""
echo "=============================================="
echo "  Financial-Data 环境安装完成"
echo "=============================================="
