# 四设备无缝同步方案——研究报告

> 研究日期：2026-07-06
> 目标：3 台 Windows + 1 台 Mac mini，workspace 文件 + Claude Code session 无缝连续

---

## 1. 设备矩阵与约束

| # | 设备 | OS | 用户名 | 管理员 | 网络 |
|---|---|---|---|---|---|
| 1 | 自己 Win 台式 | Windows 11 | `M` | ✅ | 无限制 |
| 2 | 公司 Win 笔记本 | Windows | `yuzhe` | ❌ | 公司防火墙 |
| 3 | 公司 Win 主机 | Windows | `yuzhe` | ❌ | 公司防火墙 |
| 4 | Mac mini（新购） | macOS | 未知 | ✅ | 无限制 |

### Hash 分析——四设备全不同

Workspace 统一在 OneDrive 路径：

```
设备 1 (M):      C:\Users\M\OneDrive - Hel Ved Capital Management Limited\CC research workspace
              → c--Users-M-OneDrive---Hel-Ved-Capital-Management-Limited-CC-research-workspace

设备 2 (yuzhe):  C:\Users\yuzhe\OneDrive - Hel Ved Capital Management Limited\CC research workspace
              → c--Users-yuzhe-OneDrive---Hel-Ved-Capital-Management-Limited-CC-research-workspace

设备 3 (yuzhe):  同设备 2 → 相同 hash ✅（这两台之间互通）

设备 4 (Mac):    /Users/<xxx>/OneDrive - Hel Ved Capital Management Limited/CC research workspace
              → -Users-<xxx>-OneDrive---... （完全不同）
```

**结论**：设备 2 和 3（两台公司 Win，用户名相同）hash 一致，它们之间 session 天然共通。但设备 1（`M`）和 Mac 与其他设备 hash 不同。**没有"一套简单拷贝全搞定"的路径，必须系统性解决。**

### 核心约束

- **两台公司机器无管理员** → 不能 mklink/junction，不能改防火墙规则
- **公司网络可能屏蔽 P2P 流量** → Syncthing / Resilio 直连可能被挡
- **Mac ↔ Win 路径体系完全不同** → 始终需要路径重写
- **Mac mini 新购** → OneDrive on Mac 体验极差（见 §3.1），不应纳入长期方案

---

## 2. 需要同步的三层数据

| 层 | 数据 | 当前 | 目标 |
|---|---|---|---|
| **Workspace 文件** | markdown、cache、脚本、数据 | OneDrive（Win 可用，Mac 未知） | 四设备无缝 |
| **Claude Code session** | `~/.claude/projects/<hash>/` 下的 JSONL | 手动复制 | 自动同步 |
| **VS Code 设置** | `settings.json`、插件、keybindings | 手动维护 | 自动同步 + 每机差异 |

---

## 3. 研究发现

### 3.1 OneDrive on macOS ——坏消息

来源：Microsoft Q&A 社区、App Store 评价、Reddit（2024-2025）

| 问题 | 严重度 | 详情 |
|---|---|---|
| **过量 SSD 写入** | 🔴 致命 | 即使无文件变更也写入 ~1TB/天，对 Mac 焊死 SSD 有寿命风险 |
| **同步极慢** | 🔴 严重 | M4 MacBook Pro + 2Gb 光纤用户反馈小文件同步需数天 |
| **App 冻结** | 🔴 严重 | Microsoft 官方确认的 bug，导致 macOS 版冻结 |
| **Files On-Demand 问题** | 🟡 中等 | "始终保留在此设备上"不生效，文件被自动清退需重新下载 |
| **共享文件夹同步断裂** | 🔴 严重 | 2024 年 6 月以来已知问题，无修复时间表 |
| **搜索不可用** | 🟡 中等 | 不会索引未手动打开的文件夹，搜索等于废的 |

**结论：Mac 端不应用 OneDrive。**三台 Win 继续用 OneDrive 没问题，Mac 必须换方案。

**来源**：[Microsoft Q&A - OneDrive on Mac useless](https://learn.microsoft.com/en-us/answers/questions/5288355/onedrive-for-mac-is-useless) · [Microsoft Q&A - 1TB writes per day](https://learn.microsoft.com/en-us/answers/questions/5269530/onedrive-on-mac-writing-over-1tb-per-day) · [MEFMobile - OneDrive macOS freeze confirmed](https://mefmobile.org/microsoft-confirms-onedrive-issue-is-causing-macos-app-to-freeze/)

---

### 3.2 文件同步工具对比

| | Syncthing | Resilio Sync | rclone | Git | OneDrive | Dropbox |
|---|---|---|---|---|---|---|
| **类型** | P2P 开源 | P2P 闭源 | CLI 云同步 | 版本控制 | 云盘 | 云盘 |
| **费用** | 免费 | 免费版可用 | 免费 | 免费 | 含 M365 | 付费 |
| **实时同步** | ✅ | ✅ | ❌（定时） | ❌（commit/push） | ✅ | ✅ |
| **无管理员安装** | ✅ portable .zip | ✅ 提取 exe 便携运行 | ✅ 单文件 | ✅ | ✅ | ✅ |
| **需开防火墙端口** | ⚠️ 是（否则依赖 relay） | ⚠️ 是（否则依赖 relay） | ❌ 不需要 | ❌ | ❌ | ❌ |
| **Mac 支持** | ✅ 一等公民 | ✅ | ✅ | ✅ | ⚠️ 体验差 | ✅ |
| **iOS 支持** | ❌ | ✅ | ❌ | ❌ | ✅ | ✅ |
| **选择性同步** | 基础 | ✅ 强大 | ✅ | ✅ | ✅ | ✅ |
| **加密** | TLS 端到端 | AES | crypt backend | ❌（公开 repo） | 传输加密 | 传输加密 |
| **公司网络穿透** | ⚠️ relay 可能被挡 | ⚠️ relay 可能被挡 | ✅ HTTPS | ✅ HTTPS | ✅ HTTPS | ✅ HTTPS |

**关键发现**：
- P2P 工具（Syncthing、Resilio）在公司网络可能被防火墙阻挡 → 需要 relay 服务器中转
- 基于 HTTPS 的工具（Git、Dropbox）在公司网络必然可用
- Syncthing 的 relay 走 443 端口，伪装成普通 HTTPS 流量，穿透概率最高
- **Git + 私有 repo 是唯一在所有网络环境中零摩擦的方案**

**来源**：[Syncthing 论坛 - Enterprise Defender blocking](https://forum.syncthing.net/t/app-blocked-by-enterprise-windows-defender-settings/21512/23) · [Syncthing Windows Setup - /currentuser mode](https://github.com/Bill-Stewart/SyncthingWindowsSetup)

---

### 3.3 Claude Code Session 同步——社区方案

社区已有多个专门工具：

#### 方案一：`subst S:` —— 从源头统一 hash（Windows 端最优解）

| 维度 | 详情 |
|---|---|
| **原理** | 三台 Win 都把 OneDrive workspace 映射到 `S:\`，hash 统一为 `s-` |
| **命令** | `subst S: "C:\Users\%USERNAME%\OneDrive - ...\workspace"` |
| **权限** | 不需要管理员 |
| **开机自启** | HKCU Run 注册表项，不需要管理员 |
| **Mac** | 无法 `subst`，但 Mac 可用 symlink 到同一 hash |
| **风险** | Claude Code 如果用 `fs.realpath()` 解析，会穿透 subst 拿到真实路径 → hash 又不同了。需实测 |

#### 方案二：CodeTeleport（路径重写，跨 OS）

| 维度 | 详情 |
|---|---|
| **原理** | Session 打包上传云端 → 拉取时自动路径重写 |
| **安装** | `npm install -g codeteleport`，无需管理员 |
| **使用** | 命令行 `teleport push` / `teleport pull` |
| **免费额度** | 25 sessions，3 设备 |
| **限制** | ⚠️ 免费版 3 设备不够用（需要 4 设备），需考虑付费或替代 |

#### 方案三：claude-nomad（Git 同步，无设备限制）

| 维度 | 详情 |
|---|---|
| **原理** | Git 仓库同步所有 Claude Code 配置（sessions, settings, agents, skills, CLAUDE.md） |
| **路径处理** | 支持 per-machine setting overrides |
| **安装** | `npm install -g claude-nomad`，无需管理员 |
| **使用** | `nomad push` / `nomad pull` / `nomad doctor` |
| **优势** | 纯 Git，四设备无限制，公司网络必然可用（HTTPS） |
| **安全** | gitleaks 扫描防止泄露密钥，可存私有 repo |

#### 方案四：session-roam（Syncthing P2P） 

| 维度 | 详情 |
|---|---|
| **原理** | Syncthing 同步 `~/.claude/projects/` 目录 |
| **限制** | ⚠️ 需要相同用户名和路径，四设备 hash 不同 → 不适用 |
| **优势** | 无云依赖、实时同步 |

#### 方案五：claude-session-sync（加密 Git）

| 维度 | 详情 |
|---|---|
| **原理** | age 加密 → 私有 GitHub repo |
| **路径处理** | 支持路径 remapping |
| **使用** | `claude-roam push` / `pull` / `<id>` |

#### 其他轻量方案

- **claude-sync-cli**：多 provider（GitHub / Dropbox / iCloud / OneDrive），strip home dir 前缀
- **claude-device-sync**：Claude Code 插件，`/sync` `/resume`，Git 后端 + E2E 加密
- **claude-recent**：fzf TUI 从共享文件夹索引 session

**来源**：[GitHub: VirelNode/session-roam](https://github.com/VirelNode/session-roam) · [npm: codeteleport](https://www.npmjs.com/package/codeteleport) · [npm: claude-nomad](https://www.npmjs.com/package/claude-nomad) · [GitHub: claude-session-sync](https://github.com/sirajeddineaissa/claude-session-sync) · [npm: claude-device-sync](https://www.npmjs.com/package/claude-device-sync) · [npm: claude-sync-cli](https://www.npmjs.com/package/claude-sync-cli)

---

### 3.4 跨 OS Session Hash 问题——有解

Claude Code 的 session 存储结构：

```
~/.claude/projects/<encoded-path>/<session-uuid>.jsonl
```

`<encoded-path>` 是 absolute workspace path，所有非字母数字字符替换为 `-`：

```
设备 1 (M):     c--Users-M-OneDrive---...
设备 2/3 (yuzhe): c--Users-yuzhe-OneDrive---...
设备 4 (Mac):   -Users-<xxx>-OneDrive---...
```

**四台设备有 3-4 个不同的 hash。**

#### 解法矩阵

| 解法 | 原理 | Win-Win | Win-Mac | 无需管理员 |
|---|---|---|---|---|
| `subst S:` | 统一盘符 → 统一 hash | ✅ | ❌（Mac 无 subst） | ✅ |
| Mac symlink 桥接 | `~/.claude/projects/s-` → Mac 真实 hash | — | ✅（单向） | ✅ |
| CodeTeleport | 路径重写 | ✅ | ✅ | ✅ |
| claude-nomad | Git + remapping | ✅ | ✅ | ✅ |
| claude-session-sync | 加密 Git + remapping | ✅ | ✅ | ✅ |

#### 关键判断：Git-based 方案 vs P2P 方案

| | Git-based（nomad / session-sync） | P2P（Syncthing / Resilio） |
|---|---|---|
| 公司网络 | ✅ 必通（HTTPS） | ⚠️ 可能被挡（P2P + relay） |
| 无管理员 | ✅ 完全不需要 | ⚠️ 不能开防火墙 |
| 实时性 | ❌ 手动 push/pull | ✅ 实时 |
| 冲突处理 | Git merge | Last-write-wins |
| 学习成本 | 低（两条命令） | 中（web UI 配置） |
| 跨 OS | ✅ 路径重写 | ❌ 不解决路径差异 |

**公司网络限制是决定性因素**：两台公司机器无管理员 + 防火墙限流 → P2P 方案有实质性风险。Git-based 方案没有这个风险。

---

### 3.5 VS Code Settings Sync

| 方案 | 跨平台 | 每机差异 | 推荐 |
|---|---|---|---|
| **内置 Settings Sync**（Microsoft 账号） | ✅ | Profiles 实现 | ✅ 主力 |
| **Profiles** | ✅ | 每机一 profile | ✅ 配合使用 |
| **平台条件 keybindings** | ✅ | `"when": "isWindows"` / `"isMac"` | ✅ |
| **Settings Sync 扩展**（Gist） | ✅ | Gist ignore 规则 | 备选 |
| **`.vscode/settings.json`** + gitignore | 项目级 | 手动维护 | 备选 |

**来源**：[VS Code Profiles 文档](https://code.visualstudio.com/docs/editor/profiles) · [franmastromarino/vs-code-settings-os](https://github.com/franmastromarino/vs-code-settings-os)

---

## 4. 方案推荐

### 4.1 方案 A：`subst S:` + Git sync（推荐优先试）

**核心思路**：`subst` 从源头统一三台 Win 的 hash，Mac 用 symlink 桥接，claude-nomad 做跨 OS 路径转换。

#### 第一步：`subst S:` 统一 Windows

三台 Win 都执行（不需要管理员）：

```powershell
# 一次性挂载
subst S: "C:\Users\%USERNAME%\OneDrive - Hel Ved Capital Management Limited\CC research workspace"

# 开机自动挂载（写 HKCU，不需要管理员）
$cmd = "subst S: `"C:\Users\$env:USERNAME\OneDrive - Hel Ved Capital Management Limited\CC research workspace`""
Set-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run" -Name "MapResearchDrive" -Value $cmd
```

效果：三台 Win 的 hash 全部统一为 `s-`。

> ⚠️ **需要先实测**：Claude Code 是否跟随 `subst` 映射的盘符，还是会解析真实路径。如果穿透 subst → hash 仍不同 → 方案 A 失效。

#### 第二步：Mac symlink 桥接

```bash
# Mac 上，创建 symlink 使 s- hash 指向 Mac 的真实 hash
MAC_HASH="$HOME/.claude/projects/-Users-$(whoami)-OneDrive---Hel-Ved-Capital-Management-Limited-CC-research-workspace"
mkdir -p "$MAC_HASH"
ln -sf "$MAC_HASH" "$HOME/.claude/projects/s-"
```

效果：`~/claude/projects/s-/` → 实际指向 Mac 的 hash 目录。Session 物理上在 Mac hash 里，但逻辑上 `s-` 对 claude-nomad 透明。

#### 第三步：claude-nomad 做跨设备同步

```bash
npm install -g claude-nomad
nomad init    # 初始化配置
nomad push    # 推送本地 sessions
nomad pull    # 拉取其他设备 sessions
```

Git 私有 repo 做后端，四设备无限制，公司网络必通。

#### 架构总览

```
┌────────────────────────────────────────────────┐
│              Workspace 文件同步                   │
│                                                │
│  三台 Win ←──OneDrive──→ workspace 文件          │
│  Mac ←──Syncthing──→ 自己 Win 台式              │
│       (Mac 不与 OneDrive 直接交互)                │
└────────────────────────────────────────────────┘

┌────────────────────────────────────────────────┐
│              Session 同步                        │
│                                                │
│  三台 Win: subst S: → hash 统一为 s-            │
│  Mac: symlink s- → 真实 Mac hash               │
│  所有设备: claude-nomad push/pull via Git       │
└────────────────────────────────────────────────┘
```

---

### 4.2 方案 B：纯 claude-nomad（如果 subst 被穿透）

如果 Claude Code 穿透 `subst`（即使用 `fs.realpath()`），hash 仍不同 → 放弃方案 A，直接用 claude-nomad。

每台设备独立维护自己的 hash 目录，claude-nomad 负责：
- 同步 `~/.claude/projects/` 下所有 hash 目录
- Push/pull 时做路径映射
- 不依赖 hash 相同

Workspace 文件仍按方案 A 处理（Win 用 OneDrive，Mac 用 Syncthing 桥接）。

---

### 4.3 方案 C：完全替代 OneDrive——全切 Syncthing

适合不再想依赖 OneDrive 的用户。

**架构**：

```
       自己 Win 台式                Mac mini
      (完整权限)                   (完整权限)
           │                           │
           │  Syncthing P2P + relay     │
           │         ╲   ╱             │
           │       ╲   ╱               │
           │     ╲   ╱                 │
           │   ╲   ╱                   │
           │ ╲   ╱                     │
      公司 Win 笔记本          公司 Win 主机
     (无 admin, relay)       (无 admin, relay)
```

**优势**：完全自控、开源免费、不依赖第三方云
**风险**：公司网络可能屏蔽 relay → 两台公司机器无法同步

**建议**：先在方案 A 稳定运行 2-4 周后，在公司网络测试 Syncthing relay 穿透。确认可行再迁移。

---

### 4.4 方案对比

| | 方案 A: subst + nomad | 方案 B: 纯 nomad | 方案 C: Syncthing 全家 |
|---|---|---|---|
| **hash 统一** | ✅（Win 端） | ❌（各自不同） | ❌（各自不同） |
| **需管理员** | ❌ | ❌ | ❌ |
| **公司网络** | ✅ Git HTTPS | ✅ Git HTTPS | ⚠️ 需 relay 穿透 |
| **Mac 支持** | ✅ symlink + nomad | ✅ nomad | ✅ |
| **实时同步** | ❌ 手动 push/pull | ❌ 手动 push/pull | ✅ |
| **复杂度** | 低 | 低 | 中 |
| **OneDrive 依赖** | Win 保留，Mac 脱离 | Win 保留，Mac 脱离 | 完全脱离 |
| **风险** | subst 可能被穿透 | 每条 session 都要 push/pull | 公司网络 relay 可能不通 |

---

## 5. 行动清单

### Phase 0 ——现在就做（15 分钟）

- [ ] 在**当前这台电脑**（公司 Win 笔记本，`yuzhe`）上实测 `subst S:`：
  ```powershell
  subst S: "$env:USERPROFILE\OneDrive - Hel Ved Capital Management Limited\CC research workspace"
  ```
- [ ] `cd S:\` 然后打开 Claude Code，创建一个测试 session
- [ ] 检查 `~/.claude/projects/` 下是否生成了 `s-` 目录（而非 `c--Users-yuzhe-...`）
- [ ] 如果是 `s-` → 方案 A 成立；如果仍是 `c--Users-yuzhe-...` → Claude Code 穿透了 subst，转方案 B

### Phase 1 ——过渡期（本周）

- [ ] 三台 Win 设 `subst S:` 并开机自启（如果 Phase 0 成功）
- [ ] 选一个 claude-nomad 或 claude-session-sync 作为 session 同步工具
- [ ] 初始化 Git 私有 repo
- [ ] Mac mini 开箱后：装 Syncthing 与自用 Win 台式 sync workspace 文件
- [ ] Mac 上建 `s-` symlink 桥接
- [ ] 四台设备跑通 push/pull 循环

### Phase 2 ——验证稳定（2-4 周）

- [ ] 日常使用中观察 session 同步是否无误
- [ ] 公司网络测试 Syncthing relay 连通性
- [ ] 决定是否保留 OneDrive 还是全切 Syncthing

### Phase 3 ——收尾

- [ ] 评估 OneDrive 去留
- [ ] VS Code Profiles 配置每机差异
- [ ] 写一个 5 行的 cheat sheet 贴桌面上

---

## 6. 关键参考

- [Syncthing Windows Setup (/currentuser 模式，无需管理员)](https://github.com/Bill-Stewart/SyncthingWindowsSetup)
- [Syncthing Relay 协议说明](https://docs.syncthing.net/users/relaying.html)
- [CodeTeleport npm](https://www.npmjs.com/package/codeteleport)
- [claude-nomad npm](https://www.npmjs.com/package/claude-nomad)
- [session-roam (Syncthing-based session sync)](https://github.com/VirelNode/session-roam)
- [Anthropic Issue #41630: path-independent session identity](https://github.com/anthropics/claude-code/issues/41630)
- [Anthropic Issue #24864: session-ID-based storage](https://github.com/anthropics/claude-code/issues/24864)
- [VS Code Profiles 官方文档](https://code.visualstudio.com/docs/editor/profiles)
- [Syncthing 论坛：Enterprise Defender 屏蔽解决方案](https://forum.syncthing.net/t/app-blocked-by-enterprise-windows-defender-settings/21512)

---

*报告生成：2026-07-06，deep research via Claude Code*
*中间产物见本目录下其他文件*
