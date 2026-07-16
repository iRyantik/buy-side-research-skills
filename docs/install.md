# 安装指南（Agent 执行版）

你是 Claude Code 或 Codex agent。按以下步骤为用户安装 buy-side-research-skills。

用户只需说一句：

```
按照 https://github.com/iRyantik/buy-side-research-skills/blob/main/docs/install.md 安装 buy-side-research-skills
```

---

## Step 1: 安装插件

目标：用户按 `/` 能看到 39 个 research skill（stock-quickread、driver-map、industry-landscape...）。

### 1.1 添加 marketplace

```
/plugin marketplace add iRyantik/buy-side-research-skills
```

**如果成功**：输出会显示 marketplace 已添加。进入 1.2。

**如果报错 "command not found"**：说明 CC 版本不支持 `/plugin` 命令。跳到 1.3 手动安装。

**如果报错 "already exists"**：说明之前添加过。进入 1.2。

**如果网络报错**：重试一次。仍失败则跳到 1.3 手动安装。

### 1.2 安装插件

```
/plugin install buy-side-research-skills
```

**如果成功**：输出会显示安装完成 + 版本号。按 `/` 应该能看到 skill 列表。如果看不到，让用户**重启 Claude Code**。重启后仍看不到 → 跳到 1.3。

**如果报错**：跳到 1.3。

### 1.3 手动安装（兜底）

1. 让用户浏览器打开 https://github.com/iRyantik/buy-side-research-skills/releases/latest
2. 下载 `Source code (zip)`
3. 解压 zip → 得到一个文件夹（如 `iRyantik-buy-side-research-skills-xxxxx`）→ 进入该文件夹 → 把里面的 **全部内容** 复制到：
   - **Windows**：`%USERPROFILE%\.claude\plugins\cache\buy-side-research-skills\buy-side-research-skills\<latest-version>\`
   - **macOS**：`~/.claude/plugins/cache/buy-side-research-skills/buy-side-research-skills/<latest-version>/`
4. `<latest-version>` = zip 里 `plugins/buy-side-research-skills/.claude-plugin/plugin.json` 中的 `version` 字段
5. 复制完成后，还需创建/更新 `%USERPROFILE%\.claude\plugins\installed_plugins.json`，内容：
   ```json
   {
     "buy-side-research-skills": {
       "version": "<latest-version>"
     }
   }
   ```
6. 重启 Claude Code，按 `/` 验证 skill 列表出现
