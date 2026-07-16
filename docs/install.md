# Buy-Side Research Skills — 安装指南

你是 Claude Code agent。此文档做两件事：**装 Python + 装插件**。

用户只需说：

```
按照 https://github.com/iRyantik/buy-side-research-skills/blob/main/docs/install.md 安装 buy-side-research-skills
```

---

## Step 1: 装 Python（如果没有）

```bash
python --version
```

报错 → 自动装：

**Windows**（无需管理员）：
```bash
curl -L -o %TEMP%\python-installer.exe https://www.python.org/ftp/python/3.12.10/python-3.12.10-amd64.exe
%TEMP%\python-installer.exe /quiet InstallAllUsers=0 PrependPath=1
powershell -Command "Remove-Item $env:LOCALAPPDATA\Microsoft\WindowsApps\python.exe -ErrorAction SilentlyContinue"
%LOCALAPPDATA%\Programs\Python\Python312\python.exe --version
```

**macOS**：
```bash
brew install python
```

---

## Step 2: 安装插件

VS Code 扩展版不支持 `/plugin` 命令——以下 Python 脚本是唯一路径。

```bash
python -c "
import urllib.request, zipfile, io, shutil, json
from pathlib import Path

# Download
url = 'https://api.github.com/repos/iRyantik/buy-side-research-skills/zipball/main'
with urllib.request.urlopen(url) as r: data = r.read()

# Extract
tmp = Path.home() / '.claude' / 'plugins' / '_tmp_install'
shutil.rmtree(tmp, ignore_errors=True); tmp.mkdir(parents=True)
with zipfile.ZipFile(io.BytesIO(data)) as z: z.extractall(tmp)
inner = next(tmp.iterdir())

# Get version
plugin_json = inner / 'plugins' / 'buy-side-research-skills' / '.claude-plugin' / 'plugin.json'
ver = json.loads(plugin_json.read_text('utf-8'))['version']

# Install
dst = Path.home() / '.claude' / 'plugins' / 'cache' / 'buy-side-research-skills' / 'buy-side-research-skills' / ver
shutil.rmtree(dst, ignore_errors=True); shutil.copytree(inner, dst)

# Register
reg = Path.home() / '.claude' / 'plugins' / 'installed_plugins.json'
data = json.loads(reg.read_text('utf-8')) if reg.exists() else {}
data['buy-side-research-skills'] = {'version': ver}
reg.parent.mkdir(parents=True, exist_ok=True)
reg.write_text(json.dumps(data, ensure_ascii=False, indent=2), 'utf-8')

shutil.rmtree(tmp, ignore_errors=True)
print(f'Installed v{ver}. Restart CC and press /.')
"
```

> 如果使用 CC Terminal（非 VS Code），可尝试：`/plugin marketplace add iRyantik/buy-side-research-skills` → `/plugin install buy-side-research-skills`

---

## Step 3: 初始化 Workspace

新建文件夹 → 用 CC 打开 → 执行：

```
/init-workspace
```

---

## 安装完成后

按 `/` 应该看到 `stock-quickread` 等 38 个 skill。各 skill 的额外依赖（ffmpeg、whisper 等）首次使用时自动安装。
