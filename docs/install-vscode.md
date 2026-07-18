# Buy-Side Research Skills — 安装指南（VS Code 扩展版）

你是 Claude Code agent。大部分用户用的是 VS Code 扩展版。

---

## Step 1: 装 git + Python

Agent 先检查环境，缺什么装什么。

### Windows

```bash
# git（CC 插件系统需要，~60MB）
git --version || (
  curl -L -o %TEMP%\PortableGit.exe https://github.com/git-for-windows/git/releases/download/v2.47.1.windows.2/PortableGit-2.47.1.2-64-bit.7z.exe
  %TEMP%\PortableGit.exe -o"%USERPROFILE%\.local\git" -y
  set PATH=%USERPROFILE%\.local\git\bin;%PATH%
)

# Python（~26MB，免管理员）
python --version || (
  curl -L -o %TEMP%\python-installer.exe https://www.python.org/ftp/python/3.12.10/python-3.12.10-amd64.exe
  %TEMP%\python-installer.exe /quiet InstallAllUsers=0 PrependPath=1
  powershell -Command "Remove-Item $env:LOCALAPPDATA\Microsoft\WindowsApps\python.exe -ErrorAction SilentlyContinue"
  %LOCALAPPDATA%\Programs\Python\Python312\python.exe --version
)
```

### macOS

```bash
# git（Xcode CLT 自带，或 brew 装）
git --version || xcode-select --install

# Python
python3 --version || brew install python
```

## Step 2: Agent 装 Playwright MCP

日本/韩国/台湾/欧洲市场的 IR 财报下载需要浏览器引擎。Agent 执行：

```bash
npx -y @playwright/mcp@latest --version
npx playwright install chromium
```

## Step 3: 用户操作 CC UI（Agent 指导）

告诉用户：

> 在 Claude Code 面板里：
> 1. ⚙ → **Manage Plugins**
> 2. 切换到 **Marketplace** tab → **Add Marketplace** → 输入 `iRyantik/buy-side-research-skills`
> 3. 切回 **Plugins** tab → 搜索 `buyside` → 找到 buy-side-research-skills
> 4. 点 **Install**
> 5. 重启 Claude Code

## Step 4: 验证

重启后按 `/` → 搜 `stock-quickread`。能看到即成功。

## Step 5: 初始化 workspace

新建文件夹 → CC 打开 → `/init-workspace`

---

> **CC Terminal 用户**：跳过 Step 1-3，直接 `/plugin marketplace add iRyantik/buy-side-research-skills` → `/plugin install buy-side-research-skills`。
