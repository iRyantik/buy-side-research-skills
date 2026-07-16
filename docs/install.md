# Buy-Side Research Skills — 安装指南

你是 Claude Code 或 Codex agent。此文档只做一件事：把插件装好，让用户按 `/` 看到 39 个 research skill。

用户只需说：

```
按照 https://github.com/iRyantik/buy-side-research-skills/blob/main/docs/install.md 安装 buy-side-research-skills
```

---

## 前置检查

1. 用户已安装 Claude Code（VS Code 扩展或 CLI）
2. 不需要 git、Node.js、Python（agent 需要 Python 或 curl 来下载文件——你已经有这些）

---

## 方式 A：CC marketplace（首选）

```
/plugin marketplace add iRyantik/buy-side-research-skills
/plugin install buy-side-research-skills
```

两条都成功后，让用户按 `/` 查找 `stock-quickread`。能看到 → 完成。看不到 → 重启 CC → 仍看不到 → 方式 B。

如果第一条 `/plugin marketplace add` 报 `command not found`（CC 版本不支持），直接跳到方式 B。

> 如果 `/plugin install` 报 `already installed`，运行 `/update-agent-runtime` 升级到最新版。

---

## 方式 B：Agent 手动安装（A 失败时用）

你是 agent，以下步骤**你来执行**，用户不需要动手。

### B1. 下载最新 release

三条路径按顺序试，第一个成功就用哪个：

**路径 1（Python——最可靠）：**

```bash
python -c "
import urllib.request, zipfile, io, os, tempfile
url = 'https://api.github.com/repos/iRyantik/buy-side-research-skills/zipball/latest'
print('Downloading...')
with urllib.request.urlopen(url) as r:
    data = r.read()
with zipfile.ZipFile(io.BytesIO(data)) as z:
    z.extractall('/tmp/bsrs_extracted')
print('Extracted to /tmp/bsrs_extracted/')
"
```

**路径 2（curl——如果 Python 不可用）：**

```bash
curl -L -o /tmp/bsrs.zip https://api.github.com/repos/iRyantik/buy-side-research-skills/zipball/latest
unzip -o /tmp/bsrs.zip -d /tmp/bsrs_extracted
```

**路径 3（浏览器——兜底）：**

如果上面都失败，让用户浏览器打开 https://github.com/iRyantik/buy-side-research-skills/releases/latest ，下载 `Source code (zip)` 并告知你本地路径。你再用以下命令解压：

```bash
unzip /path/to/downloaded.zip -d /tmp/bsrs_extracted
```

> Windows 无 `unzip` 时用 PowerShell：`Expand-Archive -Path /tmp/bsrs.zip -DestinationPath /tmp/bsrs_extracted`

解压后 `/tmp/bsrs_extracted/` 下只有一个文件夹（如 `iRyantik-buy-side-research-skills-ab12cd3`），记下路径。

### B2. 获取版本号

```bash
cat /tmp/bsrs_extracted/iRyantik-buy-side-research-skills-*/plugins/buy-side-research-skills/.claude-plugin/plugin.json | python -c "import sys,json; print(json.load(sys.stdin)['version'])"
```

输出如 `7.6.29`——这就是版本号。

### B3. 复制到 CC 插件目录

```bash
VERSION="7.6.29"  # 用 B2 得到的值替换
SRC="/tmp/bsrs_extracted/iRyantik-buy-side-research-skills-*"
DST="$HOME/.claude/plugins/cache/buy-side-research-skills/buy-side-research-skills/$VERSION"

mkdir -p "$DST"
cp -r "$SRC"/* "$DST/"
```

复制后 `$DST/skills/` 目录应存在。用 `ls "$DST/skills/" | wc -l` 验证有 39 个 skill 目录。

### B4. 注册插件

```bash
INSTALLED="$HOME/.claude/plugins/installed_plugins.json"

# 如果已有文件，读出来合并
python -c "
import json, os, sys
v = '$VERSION'
p = os.path.expanduser('$INSTALLED')
data = {}
if os.path.exists(p):
    data = json.load(open(p))
data['buy-side-research-skills'] = {'version': v}
json.dump(data, open(p, 'w'), indent=2)
print(f'Registered v{v}')
"
```

### B5. 验证

让用户**退出并重新打开 Claude Code**，按 `/`，查找 `stock-quickread`。能看到 → 成功。看不到 → 检查 B3 复制路径。

---

## 安装完成后

告诉用户：

> 插件已安装。下一步：
> 1. 在一个空文件夹里打开 Claude Code，执行 `/init-workspace`（创建 research workspace）
> 2. 或者直接开始研究：按 `/` 选 `stock-quickread` 试一只股票
