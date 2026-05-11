param(
    [switch]$CheckOnly,
    [switch]$Yes,
    [switch]$China,
    [ValidateSet("User", "System")]
    [string]$PythonScope = "User",
    [string]$EdgarIdentity
)

$ErrorActionPreference = "Stop"

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$requirementCandidates = @(
    (Join-Path $scriptRoot "requirements-ingest.txt"),
    (Join-Path $scriptRoot "..\assets\requirements-ingest.txt")
)
$requirementsPath = $null
foreach ($candidate in $requirementCandidates) {
    if (Test-Path -LiteralPath $candidate) {
        $requirementsPath = Resolve-Path $candidate
        break
    }
}

function Test-CommandAvailable { param([string]$Name); return $null -ne (Get-Command $Name -ErrorAction SilentlyContinue) }

function Find-Python {
    foreach ($name in @("python3.12", "python3.11", "python3.10", "python3", "python")) {
        if (-not (Test-CommandAvailable $name)) { continue }
        try {
            $ver = & $name -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>$null
            if ($LASTEXITCODE -eq 0) {
                $parts = $ver -split '\.'
                if ([int]$parts[0] -gt 3 -or ([int]$parts[0] -eq 3 -and [int]$parts[1] -ge 10)) {
                    return (Get-Command $name).Source
                }
            }
        } catch { }
    }
    return $null
}

function Test-PythonModule { param([string]$ModuleName)
    if (-not (Test-CommandAvailable "python")) { return $false }
    $code = "import importlib.util, sys; sys.exit(0 if importlib.util.find_spec('$ModuleName') else 1)"
    & python -c $code *> $null
    return $LASTEXITCODE -eq 0
}

function Get-DependencyStatus {
    $packages = [ordered]@{
        docling       = Test-PythonModule "docling"
        edgartools    = Test-PythonModule "edgar"
        pymupdf4llm   = Test-PythonModule "pymupdf4llm"
        akshare       = Test-PythonModule "akshare"
        "edinet-tools" = Test-PythonModule "edinet_tools"
        "dart-fss"    = Test-PythonModule "dart_fss"
        openesef      = Test-PythonModule "openesef"
        openpyxl      = Test-PythonModule "openpyxl"
        "python-pptx" = Test-PythonModule "pptx"
        "python-docx" = Test-PythonModule "docx"
        pdfplumber    = Test-PythonModule "pdfplumber"
        pypdf         = Test-PythonModule "pypdf"
        Pillow        = Test-PythonModule "PIL"
    }
    $pythonPath = Find-Python
    return [ordered]@{
        python = [ordered]@{ available = $null -ne $pythonPath; path = $pythonPath }
        packages = $packages
        requirements_path = if ($requirementsPath) { "$requirementsPath" } else { $null }
    }
}

function Write-StatusJson { param([hashtable]$Extra)
    $status = Get-DependencyStatus
    if ($Extra) { foreach ($key in $Extra.Keys) { $status[$key] = $Extra[$key] } }
    $status | ConvertTo-Json -Depth 8
}

if ($CheckOnly) { Write-StatusJson; exit 0 }

# ---------- find python ----------
$pythonExe = Find-Python
if (-not $pythonExe) {
    Write-Host "==============================================" -ForegroundColor Red
    Write-Host "  Python 3.10+ 未找到" -ForegroundColor Red
    Write-Host "==============================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "请先安装 Python，然后重新运行本脚本："
    Write-Host ""
    Write-Host "  winget install Python.Python.3.12" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "或从 https://www.python.org/downloads/ 下载"
    Write-Host ""
    Write-Host "注意: 不要使用 Microsoft Store 版本的 Python（路径权限问题）"
    exit 1
}
$pyVer = & $pythonExe --version 2>&1
Write-Host "[OK] Python: $pyVer ($pythonExe)" -ForegroundColor Green

# ---------- Microsoft Store check ----------
if ($pythonExe -match "WindowsApps") {
    Write-Host "[!] 检测到 Microsoft Store 版本 Python，可能导致权限问题。" -ForegroundColor Yellow
    Write-Host "    建议从 https://www.python.org/downloads/ 下载安装" -ForegroundColor Yellow
}

# ---------- conda check ----------
$condaCheck = & $pythonExe -c "import sys; print('conda' in sys.version or 'Continuum' in sys.version)" 2>$null
if ($condaCheck -eq "True") {
    Write-Host "[!] 检测到 Anaconda Python。建议在 conda 环境中安装。" -ForegroundColor Yellow
}

# ---------- requirements ----------
if (-not $requirementsPath) { throw "找不到 requirements-ingest.txt" }
Write-Host "[OK] 依赖文件: $requirementsPath"

# ---------- confirm ----------
if (-not $Yes) {
    Write-Host "将要从 $requirementsPath 安装 Python ingest 依赖。" -ForegroundColor Yellow
    Write-Host "--user 安装范围: $PythonScope" -ForegroundColor Yellow
    if ($China) { Write-Host "使用中国镜像 (PyPI: tsinghua, HuggingFace: hf-mirror)" -ForegroundColor Yellow }
    $answer = Read-Host "继续? [y/N]"
    if ($answer -notin @("y", "Y", "yes", "YES")) { Write-StatusJson @{ status = "cancelled" }; exit 1 }
}

# ---------- VC++ Redistributable check (Windows) ----------
$vcredist = Test-Path "C:\Windows\System32\vcruntime140_1.dll"
if (-not $vcredist) {
    Write-Host "==============================================" -ForegroundColor Red
    Write-Host "  缺少 Visual C++ Redistributable" -ForegroundColor Red
    Write-Host "==============================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "PyTorch 需要 VC++ 运行时。请下载安装："
    Write-Host "  https://aka.ms/vs/17/release/vc_redist.x64.exe"
    Write-Host ""
    Write-Host "下载后双击安装，然后重新运行本脚本。"
    exit 1
}
Write-Host "[OK] VC++ Redistributable: $vcredist" -ForegroundColor Green

# ---------- upgrade pip ----------
Write-Host "--- 升级 pip ---"
& $pythonExe -m pip install --user --upgrade pip --quiet 2>$null
if ($LASTEXITCODE -ne 0) { Write-Host "[!] pip 升级失败，继续使用当前版本" -ForegroundColor Yellow }

# ---------- install torch CPU (avoid CUDA DLL error on Windows) ----------
# torch >=2.6 has DLL issues on some Windows configs; pin 2.5.1 which is stable
Write-Host "--- 安装 PyTorch CPU ---"
& $pythonExe -m pip install --user torch==2.5.1 torchvision==0.20.1 --index-url https://download.pytorch.org/whl/cpu --quiet 2>$null
if ($LASTEXITCODE -ne 0) { Write-Host "[!] PyTorch CPU 安装失败，继续尝试" -ForegroundColor Yellow }

# ---------- install ----------
Write-Host "--- 安装依赖 ---"
$pipArgs = @("-m", "pip", "install", "--user", "-r", "$requirementsPath")
if ($China) {
    $pipArgs = @("-m", "pip", "install", "--user", "-i", "https://pypi.tuna.tsinghua.edu.cn/simple", "-r", "$requirementsPath")
    $env:HF_ENDPOINT = "https://hf-mirror.com"
    Write-Host "[China Mirror] PyPI: tsinghua, HuggingFace: hf-mirror.com"
}

Write-Host "Running: $pythonExe $($pipArgs -join ' ')"
& $pythonExe @pipArgs
if ($LASTEXITCODE -ne 0) {
    Write-Host ""; Write-Host "==============================================" -ForegroundColor Red
    Write-Host "  pip install 失败" -ForegroundColor Red
    Write-Host "==============================================" -ForegroundColor Red
    Write-Host ""; Write-Host "常见原因:"
    Write-Host "  1. 网络问题 → 重试: bootstrap-ingest-deps.ps1 -Yes -China"
    Write-Host "  2. 磁盘空间不足"
    Write-Host "  3. Python 版本问题 → 确保使用 python.org 版本 (不是 Microsoft Store)"
    exit 1
}

# ---------- vet ----------
if ($EdgarIdentity) { $env:EDGAR_IDENTITY = $EdgarIdentity; & setx EDGAR_IDENTITY "$EdgarIdentity" | Out-Null }

# ---------- verify docling ----------
Write-Host "--- 验证 docling (首次运行下载模型 ~1GB) ---"
if ($China) { $env:HF_ENDPOINT = "https://hf-mirror.com" }
$verifyCode = @"
from docling.document_converter import DocumentConverter
print('下载模型中...')
converter = DocumentConverter()
print('OK - docling 就绪')
"@
$verifyResult = & $pythonExe -c $verifyCode 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host ""; Write-Host "==============================================" -ForegroundColor Green
    Write-Host "  Ingest 环境安装完成" -ForegroundColor Green
    Write-Host "==============================================" -ForegroundColor Green
} else {
    Write-Host ""; Write-Host "==============================================" -ForegroundColor Red
    Write-Host "  pip 安装成功，但 docling 模型下载失败" -ForegroundColor Red
    Write-Host "==============================================" -ForegroundColor Red
    Write-Host ""; Write-Host "可能原因:"
    Write-Host "  1. 无法访问 huggingface.co → 重试: bootstrap-ingest-deps.ps1 -Yes -China"
    Write-Host "  2. 磁盘空间不足"
    Write-Host "  3. 网络代理/防火墙拦截"
    Write-Host ""; Write-Host "错误详情: $verifyResult"
    exit 1
}
