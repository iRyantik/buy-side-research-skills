#!/usr/bin/env bash
# One-command install of ingest Python dependencies for buy-side research.
# Works on a brand-new macOS machine: auto-detects Python, installs what's missing.
#
# Usage:
#   chmod +x bootstrap-ingest-deps.sh
#   ./bootstrap-ingest-deps.sh                # interactive
#   ./bootstrap-ingest-deps.sh --yes          # skip confirmation
#   ./bootstrap-ingest-deps.sh --check-only   # print dependency status JSON
#   ./bootstrap-ingest-deps.sh --yes --china  # use China mirrors (huggingface + pypi)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REQ_CANDIDATES=("$SCRIPT_DIR/requirements-ingest.txt" "$SCRIPT_DIR/../assets/requirements-ingest.txt")
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
    for pkg in docling edgartools pymupdf4llm akshare edinet_tools dart_fss openesef openpyxl pptx docx pdfplumber pypdf PIL; do
        local name="$pkg"
        if [ "$pkg" = "edgartools" ]; then name="edgar"; fi
        if [ "$pkg" = "edinet_tools" ]; then name="edinet_tools"; fi
        if [ "$pkg" = "dart_fss" ]; then name="dart_fss"; fi
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
    echo "[ERROR] 找不到 requirements-ingest.txt"
    exit 1
fi
echo "[OK] 依赖文件: $REQ_PATH"

# ---------- disk space ----------
FREE_GB=$(df -g . | awk 'NR==2 {print $4}')
if [ "${FREE_GB:-0}" -lt 5 ]; then
    echo "[!] 可用磁盘空间不足 5GB (当前: ${FREE_GB}GB)。docling 模型需要下载空间。"
fi

# ---------- xcode CLI check (macOS) ----------
if [[ "$(uname)" == "Darwin" ]]; then
    if ! xcode-select -p &>/dev/null; then
        echo "[!] 未安装 Xcode Command Line Tools。部分包可能需要编译。"
        echo "    运行: xcode-select --install"
        echo "    或等待 pip 使用预编译 wheel (推荐)"
    fi
fi

# ---------- upgrade pip ----------
echo ""
echo "--- 升级 pip ---"
"$PYTHON" -m pip install --user --upgrade pip --quiet 2>/dev/null || true

# ---------- install ----------
echo ""
echo "--- 安装依赖 ---"

PIP_ARGS=(-m pip install --user --only-binary :all: -r "$REQ_PATH")
if [ "$CHINA_MIRROR" = true ]; then
    PIP_ARGS=(-m pip install --user --only-binary :all: -i https://pypi.tuna.tsinghua.edu.cn/simple -r "$REQ_PATH")
    export HF_ENDPOINT="https://hf-mirror.com"
    echo "[China Mirror] PyPI: tsinghua, HuggingFace: hf-mirror.com"
fi

echo "Running: $PYTHON ${PIP_ARGS[*]}"
"$PYTHON" "${PIP_ARGS[@]}"

# ---------- verify docling ----------
echo ""
echo "--- 验证 docling (首次运行下载模型 ~1GB) ---"
if [ "$CHINA_MIRROR" = true ]; then
    export HF_ENDPOINT="https://hf-mirror.com"
fi

if "$PYTHON" -c "
from docling.document_converter import DocumentConverter
print('下载模型中...')
converter = DocumentConverter()
print('OK - docling 就绪')
" 2>&1; then
    echo ""
    echo "=============================================="
    echo "  Ingest 环境安装完成"
    echo "=============================================="
else
    echo ""
    echo "=============================================="
    echo "  pip 安装成功，但 docling 模型下载失败"
    echo "=============================================="
    echo ""
    echo "可能原因："
    echo "  1. 无法访问 huggingface.co (国内常见)"
    echo "     → 重新运行: ./bootstrap-ingest-deps.sh --yes --china"
    echo "  2. 磁盘空间不足"
    echo "  3. 网络代理/防火墙拦截"
    echo ""
    exit 1
fi
