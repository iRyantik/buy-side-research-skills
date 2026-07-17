# Buy-Side Research Skills — 安装指南

你是 Claude Code agent。大部分用户用的是 VS Code 扩展版。

---

## Step 1: 装 git（便携版，免管理员，60MB）

CC 的插件系统需要 git。没有就自动装：

```bash
# 下载便携版 git
curl -L -o %TEMP%\PortableGit.exe https://github.com/git-for-windows/git/releases/download/v2.47.1.windows.2/PortableGit-2.47.1.2-64-bit.7z.exe
# 自解压到用户目录
%TEMP%\PortableGit.exe -o"%USERPROFILE%\.local\git" -y
# 加入 PATH
set PATH=%USERPROFILE%\.local\git\bin;%PATH%
git --version
```

## Step 2: 用户操作 CC UI（Agent 指导）

告诉用户：

> 在 Claude Code 面板里：
> 1. 右上角 ⚙ → **Manage Plugins**
> 2. **Add Marketplace** → 输入 `iRyantik/buy-side-research-skills`
> 3. 找到 buy-side-research-skills → 点 **Install**
> 4. 重启 Claude Code

## Step 3: 验证

重启后按 `/` → 搜 `stock-quickread`。能看到即成功。

## Step 4: 初始化 workspace

新建文件夹 → CC 打开 → `/init-workspace`

---

> **CC Terminal 用户**：跳过 Step 1-2，直接 `/plugin marketplace add iRyantik/buy-side-research-skills` → `/plugin install buy-side-research-skills`。
