# Playwright Image Download — 一站式方案

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 Playwright 产品图下载能力打包成可复用脚本，放进 `init-workspace` assets 自动分发，同时补上 Playwright MCP 插件的安装指引（CC + Codex），让所有需要产品图的 skill 有统一可执行方案。

**Architecture:** 核心是一段 JS 函数体（`download-product-image.js`），设计为传给 `browser_run_code_unsafe` 执行。Agent 读取它 → 替换 `{{TARGET_URL}}` → 调用 Playwright MCP → 拿回 base64 → 解码写文件。配合 `.mcp.json` 配置模板和 env-setup 指引，用户 workspace init 后即可用。

**Tech Stack:** Playwright MCP (`@playwright/mcp` via `npx`), Claude Code plugin system, Codex plugin system, pwsh (init script)

---

## File Structure

| File | Responsibility |
|---|---|
| `init-workspace/assets/_scripts/download-product-image.js` | 可复用 Playwright 脚本 — 导航到产品页、定位 hero image、下载原图、返回 base64 |
| `init-workspace/assets/.claude/mcp.json` | Claude Code MCP 配置模板 — 声明 playwright server |
| `init-workspace/assets/.codex/mcp.json` | Codex MCP 配置模板 — 声明 playwright server |
| `init-workspace/assets/env-setup.ps1.template` | 补 Playwright MCP 插件安装/配置说明 |
| `init-workspace/SKILL.md` | 补 assets 清单、Playwright 章节 |
| `init-workspace/scripts/init-research-workspace.ps1` | 补 script copying + mcp.json syncing |
| `stock-quickread/SKILL.md` | 图片下载指令改为引用脚本 |
| `driver-map/SKILL.md` | 同上 |
| `mechanism-insight/SKILL.md` | 同上 |
| `industry-landscape/SKILL.md` | 同上 |
| `teach-in/SKILL.md` | 同上 |
| `peer-deep-dive/SKILL.md` | logo 下载引用脚本 |
| `pair-trade/SKILL.md` | logo 下载引用脚本 |

---

### Task 1: Create the reusable Playwright image-download script

**Files:**
- Create: `plugins/buy-side-research-skills/skills/init-workspace/assets/_scripts/download-product-image.js`

- [ ] **Step 1: Write the script file**

```javascript
/**
 * download-product-image.js
 * 
 * Reusable Playwright script for downloading product/logo images.
 * Designed to be executed via Playwright MCP's browser_run_code_unsafe.
 * 
 * Usage (agent-side):
 *   1. Read this file
 *   2. Replace {{TARGET_URL}} with the product page URL
 *   3. Optionally set SELECTOR to target a specific image element
 *   4. Call mcp__plugin_playwright_playwright__browser_run_code_unsafe with the code
 *   5. Decode returned base64 and save to _cache/images/<slug>-<product>.png
 * 
 * Parameters (replace before execution):
 *   {{TARGET_URL}}  - URL of the product page or media kit page
 *   {{SELECTOR}}    - CSS selector for the target image (default: 'img' — picks largest hero)
 *   {{MAX_IMAGES}}  - Max number of images to return (default: 1)
 */

async (page) => {
    const TARGET_URL = "{{TARGET_URL}}";
    const SELECTOR = "{{SELECTOR}}";
    const MAX_IMAGES = parseInt("{{MAX_IMAGES}}") || 1;

    // Step 1: Navigate to the page
    await page.goto(TARGET_URL, { 
        waitUntil: 'networkidle',
        timeout: 30000 
    });

    // Step 2: Find candidate images
    // Priority: hero images > product images > large images > any img
    let candidates;
    
    if (SELECTOR && SELECTOR !== "{{SELECTOR}}") {
        // User specified a selector — use it directly
        candidates = await page.locator(SELECTOR).all();
    } else {
        // Auto-detect: look for hero/product images by common selectors
        const heroSelectors = [
            '.hero img', '.hero-image img', '.product-hero img',
            '[class*="hero"] img', '[class*="Hero"] img',
            '.product-image img', '.product-gallery img',
            '.featured-image img', '.main-image img',
            '.media-kit img', '.media_kit img',
            'picture img', '.carousel .active img',
            'main img', 'article img'
        ];
        
        candidates = [];
        for (const sel of heroSelectors) {
            try {
                const found = await page.locator(sel).all();
                if (found.length > 0) {
                    candidates.push(...found);
                    break; // Use first matching selector group
                }
            } catch (e) {
                // selector not found, try next
            }
        }
        
        // Fallback: take all visible img elements
        if (candidates.length === 0) {
            candidates = await page.locator('img[src]').all();
        }
    }

    if (candidates.length === 0) {
        return { error: "NO_IMAGE_FOUND", url: TARGET_URL };
    }

    // Step 3: Score and sort candidates by size/position
    // Best = largest rendered area, closest to top of page (hero position)
    const scored = [];
    for (const img of candidates.slice(0, 20)) { // Cap at 20 to avoid O(n²)
        try {
            const box = await img.boundingBox();
            const src = await img.evaluate(el => el.currentSrc || el.src || '');
            if (!box || !src || src.startsWith('data:')) continue;
            
            const area = box.width * box.height;
            const y = box.y;
            // Score: area bonus, top-of-page bonus, exclude tiny icons
            if (area < 2500) continue; // skip < 50x50 thumbnails
            const score = area - (y * 10); // big + near top = best
            scored.push({ img, src, box, area, score });
        } catch (e) {
            continue;
        }
    }
    
    scored.sort((a, b) => b.score - a.score);

    // Step 4: Download top N images via page.request (preserves cookies/referer)
    const results = [];
    for (let i = 0; i < Math.min(MAX_IMAGES, scored.length); i++) {
        const { src, box, area } = scored[i];
        try {
            const response = await page.request.get(src, { timeout: 15000 });
            if (!response.ok()) {
                results.push({ index: i, src, error: `HTTP ${response.status()}`, area });
                continue;
            }
            
            const buffer = await response.body();
            const contentType = response.headers()['content-type'] || 'image/png';
            
            results.push({
                index: i,
                src,
                width: Math.round(box.width),
                height: Math.round(box.height),
                area: Math.round(area),
                contentType,
                sizeBytes: buffer.length,
                base64: buffer.toString('base64')
            });
        } catch (e) {
            results.push({ index: i, src, error: e.message, area: Math.round(area) });
        }
    }

    if (results.length === 0) {
        return { error: "DOWNLOAD_FAILED", url: TARGET_URL, candidates: scored.length };
    }

    return {
        url: TARGET_URL,
        images: results,
        totalFound: scored.length,
        selector: SELECTOR || 'auto-detect'
    };
}
```

- [ ] **Step 2: Verify the script is valid JavaScript (syntax check)**

Run: `node -e "require('fs').readFileSync('plugins/buy-side-research-skills/skills/init-workspace/assets/_scripts/download-product-image.js','utf8')" `
Expected: No syntax error (the file is a string of JS, not a module — just check the async function body parses)

- [ ] **Step 3: Commit**

```bash
git add plugins/buy-side-research-skills/skills/init-workspace/assets/_scripts/download-product-image.js
git commit -m "feat: add reusable Playwright product image download script for init-workspace"
```

---

### Task 2: Create MCP config templates for Claude Code and Codex

**Files:**
- Create: `plugins/buy-side-research-skills/skills/init-workspace/assets/.claude/mcp.json`
- Create: `plugins/buy-side-research-skills/skills/init-workspace/assets/.codex/mcp.json`

- [ ] **Step 1: Create Claude Code MCP config template**

File: `plugins/buy-side-research-skills/skills/init-workspace/assets/.claude/mcp.json`

```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["@playwright/mcp@latest"]
    }
  }
}
```

- [ ] **Step 2: Create Codex MCP config template**

File: `plugins/buy-side-research-skills/skills/init-workspace/assets/.codex/mcp.json`

```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["@playwright/mcp@latest"]
    }
  }
}
```

Note: Codex uses the same MCP config schema as Claude Code. If Codex discovers `.codex/mcp.json` at project root, it merges the servers. If Codex has a different convention, this file serves as a documented reference the user can copy.

- [ ] **Step 3: Commit**

```bash
git add plugins/buy-side-research-skills/skills/init-workspace/assets/.claude/mcp.json plugins/buy-side-research-skills/skills/init-workspace/assets/.codex/mcp.json
git commit -m "feat: add Playwright MCP config templates for Claude Code and Codex"
```

---

### Task 3: Add MCP/permission config merge logic to settings.json for Claude Code

**Files:**
- Modify: `plugins/buy-side-research-skills/skills/init-workspace/assets/.claude/settings.json`

The current `settings.json` only has `hooks`. We need to add `mcpServers` for the Playwright server, plus permissions to allow Playwright tools. However, the `.claude/settings.json` is the project-level config — we should NOT forcefully overwrite the user's MCP config. Instead, we add a **commented template** approach: ship a separate `.claude/mcp.json` (done in Task 2) and add a `permissions` section that allows Playwright tools.

- [ ] **Step 1: Add permissions for Playwright tools to settings.json**

File: `plugins/buy-side-research-skills/skills/init-workspace/assets/.claude/settings.json`

Old content:
```json
{
    "hooks": {
        ...
    }
}
```

New content — add `permissions` block after `hooks`:

```json
{
    "hooks": {
        "PreToolUse": [],
        "PostToolUse": [
            {
                "matcher": "Write|Edit|MultiEdit|Bash",
                "hooks": [
                    {
                        "type": "command",
                        "command": "python",
                        "args": [
                            "${CLAUDE_PROJECT_DIR}/.claude/hooks/hook_entry.py",
                            "--runtime", "claude",
                            "--event", "PostToolUse"
                        ],
                        "timeout": 20
                    }
                ]
            }
        ],
        "Stop": [
            {
                "matcher": "",
                "hooks": [
                    {
                        "type": "command",
                        "command": "python",
                        "args": [
                            "${CLAUDE_PROJECT_DIR}/.claude/hooks/hook_entry.py",
                            "--runtime", "claude",
                            "--event", "Stop"
                        ],
                        "timeout": 10
                    }
                ]
            }
        ]
    },
    "permissions": {
        "allow": [
            "mcp__plugin_playwright_playwright__browser_navigate",
            "mcp__plugin_playwright_playwright__browser_snapshot",
            "mcp__plugin_playwright_playwright__browser_run_code_unsafe",
            "mcp__plugin_playwright_playwright__browser_evaluate",
            "mcp__plugin_playwright_playwright__browser_take_screenshot",
            "mcp__plugin_playwright_playwright__browser_network_requests"
        ]
    }
}
```

- [ ] **Step 2: Commit**

```bash
git add plugins/buy-side-research-skills/skills/init-workspace/assets/.claude/settings.json
git commit -m "feat: add Playwright MCP tool permissions to Claude Code settings.json template"
```

---

### Task 4: Update env-setup.ps1.template with Playwright MCP installation guidance

**Files:**
- Modify: `plugins/buy-side-research-skills/skills/init-workspace/assets/env-setup.ps1.template`

- [ ] **Step 1: Add Playwright MCP section to env-setup template**

At the end of the file, after the reddit-sentiment line (line 78), add:

```powershell
# --- Playwright MCP 浏览器自动化（产品图/logo 下载需要）---
# Claude Code 安装: claude plugins install playwright
#   或手动: 将 .claude/mcp.json 复制到项目根目录
# Codex 安装: codex plugins install playwright
#   或手动: 将 .codex/mcp.json 复制到项目根目录
# 
# 安装后验证（CC）: claude mcp list  # 应看到 playwright server
# 安装后验证（Codex）: codex mcp list  # 应看到 playwright server
# 
# 前置条件: 系统需安装 Node.js >= 18（npx 需要）
# 首次运行会自动下载 Chromium，约 300MB
# 
# 如需禁用:
#   Claude Code: claude plugins disable playwright
#   Codex: codex plugins disable playwright
```

Also append to the final `Write-Host` section:
```powershell
Write-Host "  playwright (产品图/logo 下载):"
Write-Host "    Claude Code: claude plugins install playwright"
Write-Host "    Codex:      codex plugins install playwright"
Write-Host "    前置:       Node.js >= 18 (npx)"
```

- [ ] **Step 2: Commit**

```bash
git add plugins/buy-side-research-skills/skills/init-workspace/assets/env-setup.ps1.template
git commit -m "feat: add Playwright MCP plugin installation guidance to env-setup template"
```

---

### Task 5: Update init-research-workspace.ps1 to copy new assets

**Files:**
- Modify: `plugins/buy-side-research-skills/skills/init-workspace/scripts/init-research-workspace.ps1`

- [ ] **Step 1: Add `download-product-image.js` to script copying**

Find the existing `_scripts` copying section (around lines 324-331 where ingest scripts are copied). Add after the ingest script copying block:

```powershell
# Copy Playwright image download script
$playwrightScript = Join-Path $assetsRoot "_scripts/download-product-image.js"
if (Test-Path -LiteralPath $playwrightScript) {
    Copy-ScriptIfMissing `
        -SourcePath $playwrightScript `
        -RelativeTarget "_scripts/download-product-image.js"
}
```

- [ ] **Step 2: Add mcp.json to managed sync assets**

Find the managed file sync section (around lines 289-306 where `.claude/settings.json` and `.codex/hooks.json` are synced). Add after that block:

```powershell
# Sync MCP config templates (Playwright)
foreach ($mcpAsset in @(
    ".claude/mcp.json",
    ".codex/mcp.json"
)) {
    $sourceAsset = Join-Path $assetsRoot $mcpAsset
    if (Test-Path -LiteralPath $sourceAsset) {
        Copy-ScriptIfMissing `
            -SourcePath $sourceAsset `
            -RelativeTarget $mcpAsset

        Copy-ScriptIfMissing `
            -SourcePath $sourceAsset `
            -RelativeTarget (Join-Path "_scripts/init-assets" $mcpAsset)
    }
}
```

Note: Use `Copy-ScriptIfMissing` (not `Sync-ManagedFile`) for mcp.json — we don't want to overwrite the user's MCP config if they've customized it.

- [ ] **Step 3: Commit**

```bash
git add plugins/buy-side-research-skills/skills/init-workspace/scripts/init-research-workspace.ps1
git commit -m "feat: copy download-product-image.js and mcp.json templates during workspace init"
```

---

### Task 6: Update init-workspace SKILL.md to document new assets and Playwright setup

**Files:**
- Modify: `plugins/buy-side-research-skills/skills/init-workspace/SKILL.md`

- [ ] **Step 1: Add Playwright tooling to Responsibilities section**

In the "Responsible for" list (around line 38), add:
```markdown
- Copying Playwright image-download helper script into `_scripts/`.
- Copying Playwright MCP config templates (`.claude/mcp.json`, `.codex/mcp.json`) to workspace root and `_scripts/init-assets/`.
```

- [ ] **Step 2: Add Playwright to Environment Entry Point section**

In the "Environment Entry Point" section (around line 118), after the VLM/HF_ENDPOINT paragraph, add:
```markdown
- Optional browser automation:
  - Playwright MCP plugin (`@playwright/mcp`) — product image and logo download
  - Install: `claude plugins install playwright` (CC) or `codex plugins install playwright` (Codex)
  - MCP config templates: `.claude/mcp.json` / `.codex/mcp.json`
  - Helper script: `_scripts/download-product-image.js` (used by agent, not run directly)
```

- [ ] **Step 3: Update Tool Resources assets list**

In the "Runtime assets copied by the helper" list (around line 91), add:
```markdown
- `skills/init-workspace/assets/_scripts/download-product-image.js`
- `skills/init-workspace/assets/.claude/mcp.json`
- `skills/init-workspace/assets/.codex/mcp.json`
```

- [ ] **Step 4: Update Output Contract — Environment Next Steps**

In the "Environment Next Steps" section (around line 168), add after the reddit-sentiment line:
```markdown
- Playwright MCP (product image / logo download):
  - Install: `claude plugins install playwright` (CC) or `codex plugins install playwright` (Codex)
  - Verify: `claude mcp list` (CC) or `codex mcp list` (Codex)
  - Prerequisite: Node.js >= 18
```

- [ ] **Step 5: Commit**

```bash
git add plugins/buy-side-research-skills/skills/init-workspace/SKILL.md
git commit -m "docs: document Playwright MCP image download tooling in init-workspace"
```

---

### Task 7: Update stock-quickread SKILL.md to use the download script

**Files:**
- Modify: `plugins/buy-side-research-skills/skills/stock-quickread/SKILL.md`

- [ ] **Step 1: Replace image download instructions with executable reference**

Find the current image instruction block (lines 60-80). The key line is line 80:
```
> 图片只放焦点业务的。其他业务不配图。① 公司官网 Media Kit → ② web search 产品图 → ③ 找不到用行业代表性图 → ④ 实在没有标 [缺图]。下载到 `当前 topic 的 _cache/images/<slug>-<product>.png`。
```

Replace with:
```markdown
> 图片只放焦点业务的。其他业务不配图。下载到 `当前 topic 的 _cache/images/<slug>-<product>.png`。
> 
> **下载方法**（需要 Playwright MCP 插件）：
> 1. 读 `_scripts/download-product-image.js`
> 2. 替换 `{{TARGET_URL}}` 为目标页面 URL（公司 Media Kit → 产品页 → Google Images 搜索）
> 3. 调用 `browser_run_code_unsafe`（code=替换后的脚本）
> 4. 用 `base64 -d` 解码返回的 `images[0].base64` 写入目标路径
> 5. 所有途径都失败 → 标 `[缺图]`
> 
> **图片来源优先级**：① 公司官网 Media Kit → ② 产品页 hero image → ③ web search 产品图 → ④ 行业代表性图 → ⑤ `[缺图]`
```

- [ ] **Step 2: Commit**

```bash
git add plugins/buy-side-research-skills/skills/stock-quickread/SKILL.md
git commit -m "docs: update stock-quickread image download to reference Playwright script"
```

---

### Task 8: Update driver-map SKILL.md image instructions

**Files:**
- Modify: `plugins/buy-side-research-skills/skills/driver-map/SKILL.md`

- [ ] **Step 1: Replace image download instructions**

Find the image instruction on line 77 (and the repeated one on line 141):
```
> 每个核心 segment 配产品/设备图：下载到当前 topic 的 `_cache/images/<slug>-<product>.png`——① 公司 Media Kit → ② web search 产品图 → ③ 找不到用行业代表图 → ④ 标 [缺图]。
```

Replace both occurrences with:
```markdown
> 每个核心 segment 配产品/设备图：下载到当前 topic 的 `_cache/images/<slug>-<product>.png`。
> 
> **下载方法**：读 `_scripts/download-product-image.js` → 替换 `{{TARGET_URL}}` → `browser_run_code_unsafe` → base64 解码写文件。图片来源优先级：① 公司 Media Kit → ② 产品页 hero → ③ web search → ④ 行业代表图 → ⑤ `[缺图]`。详见 `stock-quickread` SKILL.md。
```

- [ ] **Step 2: Commit**

```bash
git add plugins/buy-side-research-skills/skills/driver-map/SKILL.md
git commit -m "docs: update driver-map image download to reference Playwright script"
```

---

### Task 9: Update mechanism-insight, industry-landscape, teach-in, peer-deep-dive, pair-trade image instructions

**Files:**
- Modify: `plugins/buy-side-research-skills/skills/mechanism-insight/SKILL.md`
- Modify: `plugins/buy-side-research-skills/skills/industry-landscape/SKILL.md`
- Modify: `plugins/buy-side-research-skills/skills/teach-in/SKILL.md`
- Modify: `plugins/buy-side-research-skills/skills/peer-deep-dive/SKILL.md`
- Modify: `plugins/buy-side-research-skills/skills/pair-trade/SKILL.md`

- [ ] **Step 1: Update mechanism-insight SKILL.md**

Find the image requirements section (lines 158-160):
```
**产品/设备实物图必须**。来源优先级：公司产品页 hero image → web search → `[缺图]`。
```

Replace with:
```markdown
**产品/设备实物图必须**。来源优先级：公司产品页 hero image → web search → `[缺图]`。

**下载方法**：读 `_scripts/download-product-image.js` → 替换 `{{TARGET_URL}}` → `browser_run_code_unsafe` → base64 解码写 `_cache/images/<slug>-<product>.png`。详见 `stock-quickread` SKILL.md §1 焦点业务图片段。
```

- [ ] **Step 2: Update industry-landscape SKILL.md**

Find the image requirements section (lines 124-126):
```
## 图片要求

| 图片类型 | 必须 | 来源 |
```

Replace with:
```markdown
## 图片要求

**下载方法**：读 `_scripts/download-product-image.js` → 替换 `{{TARGET_URL}}` → `browser_run_code_unsafe` → base64 解码写文件。详见 `stock-quickread` SKILL.md §1。

| 图片类型 | 必须 | 来源 |
```

- [ ] **Step 3: Update teach-in SKILL.md**

Find lines 99-103:
```
### 图片要求

**实物图下载优先级**：公司官网 Media Kit → 产品页 hero image → web search 产品图 → 行业代表性图 → `[缺图]`

下载到 `_cache/images/teach-in/`；产物内嵌 `![描述](相对路径)`。
```

Replace with:
```markdown
### 图片要求

**实物图下载优先级**：公司官网 Media Kit → 产品页 hero image → web search 产品图 → 行业代表性图 → `[缺图]`

下载到 `_cache/images/teach-in/`；产物内嵌 `![描述](相对路径)`。

**下载方法**：读 `_scripts/download-product-image.js` → 替换 `{{TARGET_URL}}` + 设 `{{MAX_IMAGES}}` → `browser_run_code_unsafe` → base64 解码写文件。详见 `stock-quickread` SKILL.md §1。
```

- [ ] **Step 4: Update peer-deep-dive SKILL.md**

Find line 237:
```
> 竞争力指标、核心客户、护城河等已经在 §4.3 表里，这里不重复。每公司配 logo（下载到 _cache/images/<ticker>-logo.png），找不到标 [缺 logo]。
```

Replace with:
```markdown
> 竞争力指标、核心客户、护城河等已经在 §4.3 表里，这里不重复。每公司配 logo（下载到 _cache/images/<ticker>-logo.png），找不到标 [缺 logo]。
> 
> **Logo 下载**：读 `_scripts/download-product-image.js`，设 `{{SELECTOR}}` 为 logo 选择器（如 `.logo img`），其余流程同产品图下载。
```

- [ ] **Step 5: Update pair-trade SKILL.md**

Find line 107 (logo references in table):
The pair-trade template uses `![logo](当前 topic 的 _cache/images/asml-logo.png)`. The download instruction is implicit. Add a note near the logo row:

In the table template section, after the logo row, add a footnote:
```markdown
> Logo 下载：读 `_scripts/download-product-image.js`，设 `{{SELECTOR}}` 为 `.logo img` 或公司首页 logo 选择器，下载到 `_cache/images/<ticker>-logo.png`。详见 `stock-quickread` SKILL.md §1。
```

- [ ] **Step 6: Commit**

```bash
git add plugins/buy-side-research-skills/skills/mechanism-insight/SKILL.md
git add plugins/buy-side-research-skills/skills/industry-landscape/SKILL.md
git add plugins/buy-side-research-skills/skills/teach-in/SKILL.md
git add plugins/buy-side-research-skills/skills/peer-deep-dive/SKILL.md
git add plugins/buy-side-research-skills/skills/pair-trade/SKILL.md
git commit -m "docs: update all image-requiring skills to reference Playwright download script"
```

---

### Task 10: Update update-agent-runtime SKILL.md to include Playwright MCP in workspace sync

**Files:**
- Modify: `plugins/buy-side-research-skills/skills/update-agent-runtime/SKILL.md`

- [ ] **Step 1: Add Playwright to workspace sync list**

In the "Workspace Sync" section (around line 77), add after "copy `references/` to workspace root":
```markdown
- copy `_scripts/download-product-image.js` to workspace `_scripts/`
- copy `.claude/mcp.json` and `.codex/mcp.json` to workspace root (never overwrite existing)
```

- [ ] **Step 2: Commit**

```bash
git add plugins/buy-side-research-skills/skills/update-agent-runtime/SKILL.md
git commit -m "docs: add Playwright MCP assets to update-agent-runtime workspace sync scope"
```

---

## Self-Review

### 1. Spec Coverage
- ✅ Reusable script: `download-product-image.js` (Task 1)
- ✅ init-workspace assets packaging: Tasks 5, 6
- ✅ Playwright MCP plugin install guidance for CC: Tasks 3, 4
- ✅ Playwright MCP plugin install guidance for Codex: Tasks 2, 4
- ✅ All skills updated with executable references: Tasks 7-9
- ✅ update-agent-runtime sync scope: Task 10
- ✅ One-stop: env-setup template is the entry point, script is the executable

### 2. Placeholder Scan
- No TBD, TODO, or "implement later" found
- All code blocks contain actual code, not descriptions
- All file paths are exact

### 3. Type Consistency
- `{{TARGET_URL}}`, `{{SELECTOR}}`, `{{MAX_IMAGES}}` used consistently in script and skill docs
- return shape `{ url, images: [{ base64, contentType, ... }] }` used consistently
- No signature mismatches across tasks
