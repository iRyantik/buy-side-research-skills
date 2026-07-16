# Buy-Side Research Skills — 安装指南

你是 Claude Code 或 Codex agent。此文档只做一件事：把插件装好，让用户按 `/` 看到 39 个 research skill。

用户只需说：

```
按照 https://github.com/iRyantik/buy-side-research-skills/blob/main/docs/install.md 安装 buy-side-research-skills
```

---

## Step 0: 确保 Python 可用

先检查 Python 是否存在：

```bash
python --version
```

如果报错 `command not found`，自动安装：

**Windows**：
```bash
winget install Python.Python.3.12 --silent
```
安装后重启终端或把 `%LOCALAPPDATA%\Programs\Python\Python312` 加入 PATH。重新运行 `python --version` 确认。

> `winget` 是 Windows 10/11 自带。如果 `winget` 也不可用，让用户从 https://www.python.org/downloads/ 下载安装。

**macOS**：
```bash
brew install python
```

---

## Step 1: CC marketplace（首选）

```
/plugin marketplace add iRyantik/buy-side-research-skills
/plugin install buy-side-research-skills
```

两条都成功后，让用户按 `/` 查找 `stock-quickread`。能看到 → 完成。看不到 → 重启 CC → 仍看不到 → Step 2。

如果第一条 `/plugin marketplace add` 报 `command not found`（CC 版本不支持），直接跳到 Step 2。

> 如果 `/plugin install` 报 `already installed`，运行 `/update-agent-runtime` 升级。

---

## Step 2: Python 全自动安装（兜底）

你是 agent，**你来执行**，用户不需要动手。以下是一个完整的 Python 脚本，一次性完成：下载 → 解压 → 获取版本号 → 复制 → 注册。

```bash
python -c "
import urllib.request, zipfile, io, tempfile, shutil, json, os
from pathlib import Path

print('=== Step 1/5: Downloading latest release... ===')
url = 'https://api.github.com/repos/iRyantik/buy-side-research-skills/zipball/latest'
with urllib.request.urlopen(url) as r:
    data = r.read()
print(f'  Downloaded {len(data)//1024} KB')

print('=== Step 2/5: Extracting... ===')
tmp = Path(tempfile.gettempdir()) / 'bsrs_install'
shutil.rmtree(tmp, ignore_errors=True)
tmp.mkdir()
with zipfile.ZipFile(io.BytesIO(data)) as z:
    z.extractall(tmp)
# Find the inner folder (GitHub wraps everything in iRyantik-xxx/)
inner = next(tmp.iterdir())
print(f'  Extracted to {inner}')

print('=== Step 3/5: Getting version... ===')
plugin_json = inner / 'plugins' / 'buy-side-research-skills' / '.claude-plugin' / 'plugin.json'
info = json.loads(plugin_json.read_text(encoding='utf-8'))
version = info['version']
print(f'  Version: {version}')

print('=== Step 4/5: Installing to CC plugin directory... ===')
plugin_dir = Path.home() / '.claude' / 'plugins' / 'cache' / 'buy-side-research-skills' / 'buy-side-research-skills' / version
shutil.rmtree(plugin_dir, ignore_errors=True)
shutil.copytree(inner, plugin_dir)
print(f'  Installed to {plugin_dir}')
print(f'  Skills: {len(list((plugin_dir / \"skills\").iterdir()))} dirs')

print('=== Step 5/5: Registering plugin... ===')
installed_file = Path.home() / '.claude' / 'plugins' / 'installed_plugins.json'
installed = {}
if installed_file.exists():
    installed = json.loads(installed_file.read_text(encoding='utf-8'))
installed['buy-side-research-skills'] = {'version': version}
installed_file.parent.mkdir(parents=True, exist_ok=True)
installed_file.write_text(json.dumps(installed, ensure_ascii=False, indent=2), encoding='utf-8')
print(f'  Registered v{version}')

# Cleanup
shutil.rmtree(tmp, ignore_errors=True)
print()
print('=== Done. Restart Claude Code and press / to find stock-quickread. ===')
"
```

脚本跑完后，让用户**退出并重新打开 Claude Code**，按 `/`，查找 `stock-quickread`。能看到 → 成功。

---

## 安装完成后

告诉用户：

> 插件已安装。下一步：
> 1. 在一个空文件夹里打开 Claude Code，执行 `/init-workspace`（创建 research workspace）
> 2. 或者直接开始研究：按 `/` 选 `stock-quickread` 试一只股票
