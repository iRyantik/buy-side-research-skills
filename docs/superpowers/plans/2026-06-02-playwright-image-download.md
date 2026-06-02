# Playwright Image Download — 一站式方案（修正版）

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 Playwright 产品图下载能力打包成可复用脚本，放进 `init-workspace` assets 自动分发，同时补上 Claude Code / Codex 的可验证配置指引，让所有需要产品图的 skill 有统一可执行方案。

**Architecture:** 核心是一段 JS 函数体（`download-product-image.js`），设计为传给当前宿主已暴露的 Playwright MCP `browser_run_code_unsafe` 执行。Agent 读取它 → 替换 `{{TARGET_URL}}` / `{{SELECTOR}}` / `{{MAX_IMAGES}}` → 调用当前 session 里真实可用的 Playwright MCP tool → 拿回 base64 + extension → 解码写文件。Claude Code 使用 `.claude/mcp.json` 模板；Codex 使用 `.codex/mcp.example.json` 作为参考配置，不假设 project-level `.codex/mcp.json` 会自动加载。

**Tech Stack:** Playwright MCP (`@playwright/mcp` via `npx`), Claude Code plugin system, Codex plugin system, `pwsh` on Windows/macOS, Node.js >= 18, Python 3 for portable base64 decode fallback.

---

## File Structure

| File | Responsibility |
|---|---|
| `init-workspace/assets/_scripts/download-product-image.js` | 可复用 Playwright 脚本 — 导航到产品页、定位 hero image、下载原图、返回 base64 |
| `init-workspace/assets/.claude/mcp.json` | Claude Code MCP 配置模板 — 声明 playwright server |
| `init-workspace/assets/.codex/mcp.example.json` | Codex MCP 参考模板 — 不承诺自动加载，供用户迁移到 Codex 官方支持的 config surface |
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

## Hard Contracts

- 不硬编码 `mcp__plugin_playwright_playwright__browser_run_code_unsafe`。实际调用时，agent 必须使用当前 session 暴露的 Playwright MCP `browser_run_code_unsafe` tool；如果 tool 名称不同，以 tool list 为准。
- 不在本轮修改 `plugins/buy-side-research-skills/skills/init-workspace/assets/.claude/settings.json` 的 `permissions`。该文件当前由 init helper 作为 managed config 同步，直接加权限会覆盖用户自定义设置。
- Codex 不假设会自动读取 project-level `.codex/mcp.json`。本轮只提供 `.codex/mcp.example.json` 参考模板，并在文档里说明实际启用应走 Codex 当前支持的 plugin / MCP config 入口。
- 下载结果保存时使用脚本返回的 `extension`，不要强制写成 `.png`。如果 host 或页面返回 `jpg` / `webp` / `svg`，artifact 的 image link 要使用实际扩展名。
- Base64 解码指令必须同时支持 Windows 和 macOS。Windows 主路径用 PowerShell `[Convert]::FromBase64String(...)`；macOS 主路径用 `python3` 解码；文档不要只写 Unix-only 的 `base64 -d`。
- `init-research-workspace.ps1` 是 PowerShell 脚本。Windows 可以用 PowerShell / `pwsh`；macOS 必须用 `pwsh`，不能假设系统默认 shell 能直接执行 `.ps1`。

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
 *   4. Call the Playwright MCP browser_run_code_unsafe tool exposed in the current session
 *   5. Decode returned base64 and save to _cache/images/<slug>-<product>.<extension>
 * 
 * Parameters (replace before execution):
 *   {{TARGET_URL}}  - URL of the product page or media kit page
 *   {{SELECTOR}}    - CSS selector for the target image (default: 'img' — picks largest hero)
 *   {{MAX_IMAGES}}  - Max number of images to return (default: 1)
 */

async (page) => {
    const TARGET_URL = "{{TARGET_URL}}";
    const RAW_SELECTOR = "{{SELECTOR}}";
    const RAW_MAX_IMAGES = "{{MAX_IMAGES}}";
    const SELECTOR = RAW_SELECTOR && !RAW_SELECTOR.startsWith("{{") ? RAW_SELECTOR : "";
    const parsedMaxImages = Number.parseInt(RAW_MAX_IMAGES, 10);
    const MAX_IMAGES = Number.isFinite(parsedMaxImages) && parsedMaxImages > 0 ? parsedMaxImages : 1;

    if (!TARGET_URL || TARGET_URL.startsWith("{{")) {
        return { error: "TARGET_URL_NOT_SET" };
    }

    // Step 1: Navigate to the page
    await page.goto(TARGET_URL, { 
        waitUntil: 'domcontentloaded',
        timeout: 30000 
    });
    try {
        await page.waitForLoadState('networkidle', { timeout: 5000 });
    } catch (e) {
        // Many product pages keep analytics/streaming requests open. domcontentloaded is enough.
    }

    // Step 2: Find candidate images
    // Priority: hero images > product images > large images > any img
    let candidates;
    
    if (SELECTOR) {
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
            const contentType = (response.headers()['content-type'] || 'image/png').split(';')[0].trim().toLowerCase();
            const extensionByContentType = {
                'image/jpeg': 'jpg',
                'image/jpg': 'jpg',
                'image/png': 'png',
                'image/webp': 'webp',
                'image/svg+xml': 'svg',
                'image/gif': 'gif'
            };
            const extension = extensionByContentType[contentType] || 'png';
            
            results.push({
                index: i,
                src,
                width: Math.round(box.width),
                height: Math.round(box.height),
                area: Math.round(area),
                contentType,
                extension,
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

- [ ] **Step 2: Verify the script is valid JavaScript on Windows and macOS**

Run on Windows PowerShell:

```bash
node -e "const fs=require('fs'); const code=fs.readFileSync('plugins/buy-side-research-skills/skills/init-workspace/assets/_scripts/download-product-image.js','utf8'); new Function('return (' + code + ')');"
```

Run on macOS shell:

```bash
node -e 'const fs=require("fs"); const code=fs.readFileSync("plugins/buy-side-research-skills/skills/init-workspace/assets/_scripts/download-product-image.js","utf8"); new Function("return (" + code + ")");'
```

Expected: both commands exit 0 with no output. This parses the async arrow function; plain `readFileSync` is not a syntax check.

- [ ] **Step 3: Commit**

```bash
git add plugins/buy-side-research-skills/skills/init-workspace/assets/_scripts/download-product-image.js
git commit -m "feat: add reusable Playwright product image download script for init-workspace"
```

---

### Task 2: Create MCP config templates for Claude Code and Codex

**Files:**
- Create: `plugins/buy-side-research-skills/skills/init-workspace/assets/.claude/mcp.json`
- Create: `plugins/buy-side-research-skills/skills/init-workspace/assets/.codex/mcp.example.json`

- [ ] **Step 1: Create Claude Code MCP config template**

File: `plugins/buy-side-research-skills/skills/init-workspace/assets/.claude/mcp.json`

```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["-y", "@playwright/mcp@latest"]
    }
  }
}
```

- [ ] **Step 2: Create Codex MCP reference template**

File: `plugins/buy-side-research-skills/skills/init-workspace/assets/.codex/mcp.example.json`

```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["-y", "@playwright/mcp@latest"]
    }
  }
}
```

Note: This Codex file is a reference template, not an activation guarantee. The repo currently treats Codex host config as `~/.codex/config.toml`; do not claim project `.codex/mcp.json` is auto-discovered unless Codex docs / local runtime prove it in this release.

- [ ] **Step 3: Commit**

```bash
git add plugins/buy-side-research-skills/skills/init-workspace/assets/.claude/mcp.json plugins/buy-side-research-skills/skills/init-workspace/assets/.codex/mcp.example.json
git commit -m "feat: add Playwright MCP config templates for Claude Code and Codex"
```

---

### Task 3: Preserve host settings and lock the MCP tool-name contract

**Files:**
- Verify unchanged: `plugins/buy-side-research-skills/skills/init-workspace/assets/.claude/settings.json`
- Verify unchanged: `plugins/buy-side-research-skills/skills/init-workspace/assets/.codex/hooks.json`

- [ ] **Step 1: Do not edit managed host settings**

Do not add Playwright `permissions` or `mcpServers` to `plugins/buy-side-research-skills/skills/init-workspace/assets/.claude/settings.json`.

Reason: `init-research-workspace.ps1` syncs `.claude/settings.json` as a managed rendered text file. Adding a Playwright allowlist there couples hook delivery to optional browser automation and risks overwriting user-customized permissions.

- [ ] **Step 2: Keep tool names host-discovered**

All later docs must use this wording, not a hard-coded MCP tool id:

```markdown
调用当前 session 暴露的 Playwright MCP `browser_run_code_unsafe` tool。不要硬编码 `mcp__plugin_playwright_playwright__browser_run_code_unsafe`；如果 tool name 不同，以当前 tool list 为准。
```

- [ ] **Step 3: Verify no settings files changed**

Run:

```bash
git diff -- plugins/buy-side-research-skills/skills/init-workspace/assets/.claude/settings.json plugins/buy-side-research-skills/skills/init-workspace/assets/.codex/hooks.json
```

Expected: no output.

---

### Task 4: Update env-setup.ps1.template with Playwright MCP installation guidance

**Files:**
- Modify: `plugins/buy-side-research-skills/skills/init-workspace/assets/env-setup.ps1.template`

- [ ] **Step 1: Add Playwright MCP section to env-setup template**

At the end of the file, after the reddit-sentiment line (line 78), add:

```powershell
# --- Playwright MCP 浏览器自动化（产品图/logo 下载需要）---
# 用途: 让 agent 通过 Playwright MCP 读取网页并下载产品图/logo。
# 前置条件:
#   Windows: PowerShell 或 pwsh, Node.js >= 18（npx 需要）, Python 3 optional
#   macOS:   pwsh, Node.js >= 18（npx 需要）, Python 3
#
# Claude Code:
#   参考模板: _scripts/init-assets/.claude/mcp.json
#   如果当前 Claude Code 支持 project-level .claude/mcp.json，可复制到 workspace .claude/mcp.json。
#
# Codex:
#   参考模板: _scripts/init-assets/.codex/mcp.example.json
#   不假设 project-level .codex/mcp.json 会自动加载；按当前 Codex 支持的 plugin / MCP config 入口启用。
#
# 验证:
#   在当前 agent session 的 tool list 中确认存在 Playwright MCP 的 browser_run_code_unsafe tool。
#   实际 tool id 由宿主决定，不要硬编码 mcp__plugin_playwright_playwright__browser_run_code_unsafe。
#
# 首次运行 Playwright MCP 可能会通过 npx 下载 package / browser runtime。
```

Also append to the final `Write-Host` section:
```powershell
Write-Host "  playwright (产品图/logo 下载，可选):"
Write-Host "    Windows:    PowerShell/pwsh + Node.js >= 18 (npx); Python 3 optional"
Write-Host "    macOS:      pwsh + Node.js >= 18 (npx) + Python 3"
Write-Host "    Claude:     see _scripts/init-assets/.claude/mcp.json"
Write-Host "    Codex:      see _scripts/init-assets/.codex/mcp.example.json; use current Codex MCP/plugin config surface"
Write-Host "    Verify:     current agent session exposes Playwright MCP browser_run_code_unsafe"
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

    Copy-ScriptIfMissing `
        -SourcePath $playwrightScript `
        -RelativeTarget "_scripts/init-assets/_scripts/download-product-image.js"
}
```

- [ ] **Step 2: Add mcp.json to managed sync assets**

Find the managed file sync section (around lines 289-306 where `.claude/settings.json` and `.codex/hooks.json` are synced). Add after that block:

```powershell
# Sync MCP config templates (Playwright)
foreach ($mcpAsset in @(
    ".claude/mcp.json",
    ".codex/mcp.example.json"
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

Note: Use `Copy-ScriptIfMissing` (not `Sync-ManagedFile`) for MCP templates — we don't want to overwrite the user's MCP config if they've customized it. `.codex/mcp.example.json` is intentionally an example file, not an active config.

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
- Copying Playwright MCP config templates (`.claude/mcp.json`, `.codex/mcp.example.json`) to workspace root and `_scripts/init-assets/`.
```

- [ ] **Step 2: Add Playwright to Environment Entry Point section**

In the "Environment Entry Point" section (around line 118), after the VLM/HF_ENDPOINT paragraph, add:
```markdown
- Optional browser automation:
  - Playwright MCP plugin (`@playwright/mcp`) — product image and logo download
  - Claude Code template: `.claude/mcp.json`
  - Codex reference template: `.codex/mcp.example.json` (not assumed auto-loaded)
  - Helper script: `_scripts/download-product-image.js` (used by agent, not run directly)
  - Runtime check: current agent session must expose a Playwright MCP `browser_run_code_unsafe` tool
```

- [ ] **Step 3: Update Tool Resources assets list**

In the "Runtime assets copied by the helper" list (around line 91), add:
```markdown
- `skills/init-workspace/assets/_scripts/download-product-image.js`
- `skills/init-workspace/assets/.claude/mcp.json`
- `skills/init-workspace/assets/.codex/mcp.example.json`
```

- [ ] **Step 4: Update Output Contract — Environment Next Steps**

In the "Environment Next Steps" section (around line 168), add after the reddit-sentiment line:
```markdown
- Playwright MCP (product image / logo download):
  - Prerequisite: Node.js >= 18
  - Claude Code: see `.claude/mcp.json`
  - Codex: see `.codex/mcp.example.json`; enable through current Codex-supported MCP / plugin config surface
  - Verify: current agent session exposes Playwright MCP `browser_run_code_unsafe`
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
> 图片只放焦点业务的。其他业务不配图。下载到 `当前 topic 的 _cache/images/<slug>-<product>.<ext>`，`<ext>` 使用脚本返回的 `images[0].extension`。
> 
> **下载方法**（需要 Playwright MCP 插件）：
> 1. 读 `_scripts/download-product-image.js`
> 2. 替换 `{{TARGET_URL}}` 为目标页面 URL（公司 Media Kit → 产品页 → Google Images 搜索）
> 3. 调用当前 session 暴露的 Playwright MCP `browser_run_code_unsafe` tool（code=替换后的脚本；tool id 以当前 tool list 为准）
> 4. 解码返回的 `images[0].base64`，写入带实际 extension 的目标路径
>    - Windows PowerShell: `[IO.File]::WriteAllBytes($outPath, [Convert]::FromBase64String($image.base64))`
>    - macOS: `IMAGE_BASE64="$base64" OUT_PATH="$outPath" python3 -c 'import base64,os,pathlib; pathlib.Path(os.environ["OUT_PATH"]).write_bytes(base64.b64decode(os.environ["IMAGE_BASE64"]))'`
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
> 每个核心 segment 配产品/设备图：下载到当前 topic 的 `_cache/images/<slug>-<product>.<ext>`，`<ext>` 使用脚本返回的 `extension`。
> 
> **下载方法**：读 `_scripts/download-product-image.js` → 替换 `{{TARGET_URL}}` → 调用当前 session 的 Playwright MCP `browser_run_code_unsafe` → Windows 用 PowerShell 解码、macOS 用 `python3` 解码写文件。图片来源优先级：① 公司 Media Kit → ② 产品页 hero → ③ web search → ④ 行业代表图 → ⑤ `[缺图]`。详见 `stock-quickread` SKILL.md。
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

**下载方法**：读 `_scripts/download-product-image.js` → 替换 `{{TARGET_URL}}` → 调用当前 session 的 Playwright MCP `browser_run_code_unsafe` → Windows 用 PowerShell 解码、macOS 用 `python3` 解码写 `_cache/images/<slug>-<product>.<ext>`。`<ext>` 使用脚本返回的 `extension`。详见 `stock-quickread` SKILL.md §1 焦点业务图片段。
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

**下载方法**：读 `_scripts/download-product-image.js` → 替换 `{{TARGET_URL}}` → 调用当前 session 的 Playwright MCP `browser_run_code_unsafe` → Windows 用 PowerShell 解码、macOS 用 `python3` 解码写文件，文件扩展名用脚本返回的 `extension`。详见 `stock-quickread` SKILL.md §1。

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

**下载方法**：读 `_scripts/download-product-image.js` → 替换 `{{TARGET_URL}}` + 设 `{{MAX_IMAGES}}` → 调用当前 session 的 Playwright MCP `browser_run_code_unsafe` → Windows 用 PowerShell 解码、macOS 用 `python3` 解码写文件，文件扩展名用脚本返回的 `extension`。详见 `stock-quickread` SKILL.md §1。
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
> **Logo 下载**：读 `_scripts/download-product-image.js`，设 `{{SELECTOR}}` 为 logo 选择器（如 `.logo img`），调用当前 session 的 Playwright MCP `browser_run_code_unsafe`，其余流程同产品图下载。
```

- [ ] **Step 5: Update pair-trade SKILL.md**

Find line 107 (logo references in table):
The pair-trade template uses `![logo](当前 topic 的 _cache/images/asml-logo.png)`. The download instruction is implicit. Add a note near the logo row:

In the table template section, after the logo row, add a footnote:
```markdown
> Logo 下载：读 `_scripts/download-product-image.js`，设 `{{SELECTOR}}` 为 `.logo img` 或公司首页 logo 选择器，调用当前 session 的 Playwright MCP `browser_run_code_unsafe`，下载到 `_cache/images/<ticker>-logo.<ext>`。`<ext>` 使用脚本返回的 `extension`。详见 `stock-quickread` SKILL.md §1。
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
- copy `_scripts/init-assets/_scripts/download-product-image.js` for local repair
- copy `.claude/mcp.json` and `.codex/mcp.example.json` to workspace root (never overwrite existing)
```

- [ ] **Step 2: Commit**

```bash
git add plugins/buy-side-research-skills/skills/update-agent-runtime/SKILL.md
git commit -m "docs: add Playwright MCP assets to update-agent-runtime workspace sync scope"
```

---

### Task 11: Cross-platform verification

**Files:**
- Verify: `plugins/buy-side-research-skills/skills/init-workspace/scripts/init-research-workspace.ps1`
- Verify: `plugins/buy-side-research-skills/skills/init-workspace/assets/_scripts/download-product-image.js`

- [ ] **Step 1: Run Windows init asset copy smoke test**

Run on Windows PowerShell from repo root:

```powershell
$ws = Join-Path $env:TEMP "bsrs-playwright-init-test"
Remove-Item -LiteralPath $ws -Recurse -Force -ErrorAction SilentlyContinue
pwsh -NoProfile -File plugins/buy-side-research-skills/skills/init-workspace/scripts/init-research-workspace.ps1 -WorkspacePath $ws
@(
  "_scripts/download-product-image.js",
  "_scripts/init-assets/_scripts/download-product-image.js",
  ".claude/mcp.json",
  ".codex/mcp.example.json"
) | ForEach-Object {
  $path = Join-Path $ws $_
  if (-not (Test-Path -LiteralPath $path)) { throw "Missing expected asset: $_" }
}
```

Expected: command exits 0 and all four expected files exist.

- [ ] **Step 2: Run macOS init asset copy smoke test**

Run on macOS shell from repo root:

```bash
ws="$(mktemp -d)"
pwsh -NoProfile -File plugins/buy-side-research-skills/skills/init-workspace/scripts/init-research-workspace.ps1 -WorkspacePath "$ws"
test -f "$ws/_scripts/download-product-image.js"
test -f "$ws/_scripts/init-assets/_scripts/download-product-image.js"
test -f "$ws/.claude/mcp.json"
test -f "$ws/.codex/mcp.example.json"
```

Expected: command exits 0 and all four expected files exist. If `pwsh` is missing, install PowerShell for macOS before marking this task complete.

- [ ] **Step 3: Run JavaScript parse check on both platforms**

Run Windows command from Task 1 Step 2 and macOS command from Task 1 Step 2.

Expected: both commands exit 0 with no output.

- [ ] **Step 4: Commit cross-platform verification updates if Task 11 required doc changes**

If executing Task 11 required adjusting docs or commands, commit those changes:

```bash
git add plugins/buy-side-research-skills/skills/init-workspace/SKILL.md plugins/buy-side-research-skills/skills/init-workspace/assets/env-setup.ps1.template docs/superpowers/plans/2026-06-02-playwright-image-download.md
git commit -m "docs: add cross-platform Playwright image tooling verification"
```

If no files changed, do not create an empty commit.

---

## Self-Review

### 1. Spec Coverage
- ✅ Reusable script: `download-product-image.js` (Task 1)
- ✅ init-workspace assets packaging: Tasks 5, 6
- ✅ Claude Code MCP template: Task 2
- ✅ Codex reference-only MCP template, without auto-discovery claim: Task 2
- ✅ Managed settings preserved; no hard-coded Playwright permissions: Task 3
- ✅ Tool-name contract is host-discovered, not hard-coded: Tasks 3, 4, 7-9
- ✅ All skills updated with executable references: Tasks 7-9
- ✅ update-agent-runtime sync scope: Task 10
- ✅ Windows + macOS verification: Task 11
- ✅ One-stop: env-setup template is the entry point, script is the executable

### 2. Placeholder Scan
- No TBD, TODO, or "implement later" found
- All code blocks contain actual code, not descriptions
- All file paths are exact

### 3. Type Consistency
- `{{TARGET_URL}}`, `{{SELECTOR}}`, `{{MAX_IMAGES}}` used consistently in script and skill docs
- return shape `{ url, images: [{ base64, contentType, extension, ... }] }` used consistently
- No signature mismatches across tasks
