# Buy-Side Research Skills — 安装指南（VS Code 扩展版）

你是 Claude Code agent。大部分用户用的是 VS Code 扩展版。

---

## Step 1: 装 git + Python（便携版，免管理员）

Agent 先检查环境，缺什么装什么：

```bash
# ── git（CC 插件系统需要） ──
git --version
# 没有 → 下载便携版（60MB）：
curl -L -o %TEMP%\PortableGit.exe https://github.com/git-for-windows/git/releases/download/v2.47.1.windows.2/PortableGit-2.47.1.2-64-bit.7z.exe
%TEMP%\PortableGit.exe -o"%USERPROFILE%\.local\git" -y
set PATH=%USERPROFILE%\.local\git\bin;%PATH%

# ── Python（hooks/scripts 需要，26MB） ──
python --version
# 没有 → 下载安装（免管理员）：
curl -L -o %TEMP%\python-installer.exe https://www.python.org/ftp/python/3.12.10/python-3.12.10-amd64.exe
%TEMP%\python-installer.exe /quiet InstallAllUsers=0 PrependPath=1
# 禁用 Store 别名：
powershell -Command "Remove-Item $env:LOCALAPPDATA\Microsoft\WindowsApps\python.exe -ErrorAction SilentlyContinue"
# 验证：
%LOCALAPPDATA%\Programs\Python\Python312\python.exe --version
```

## Step 2: 用户操作 CC UI（Agent 指导）

告诉用户：

> 在 Claude Code 面板里：
> 1. ⚙ → **Manage Plugins**
> 2. 切换到 **Marketplace** tab → **Add Marketplace** → 输入 `iRyantik/buy-side-research-skills`
> 3. 切回 **Plugins** tab → 搜索 `buyside` → 找到 buy-side-research-skills
> 4. 点 **Install**
> 5. 重启 Claude Code

## Step 3: 验证

重启后按 `/` → 搜 `stock-quickread`。能看到即成功。

## Step 4: 初始化 workspace

新建文件夹 → CC 打开 → `/init-workspace`

---

> **CC Terminal 用户**：跳过 Step 1-2，直接 `/plugin marketplace add iRyantik/buy-side-research-skills` → `/plugin install buy-side-research-skills`。
