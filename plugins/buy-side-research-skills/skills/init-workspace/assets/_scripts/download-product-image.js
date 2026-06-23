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
 *   {{SELECTOR}}    - CSS selector for the target image (default: 'img' - picks largest hero)
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

    await page.goto(TARGET_URL, {
        waitUntil: "domcontentloaded",
        timeout: 30000
    });
    try {
        await page.waitForLoadState("networkidle", { timeout: 5000 });
    } catch (e) {
        // Many product pages keep analytics/streaming requests open. domcontentloaded is enough.
    }

    let candidates;

    if (SELECTOR) {
        candidates = await page.locator(SELECTOR).all();
    } else {
        const heroSelectors = [
            ".hero img", ".hero-image img", ".product-hero img",
            "[class*=\"hero\"] img", "[class*=\"Hero\"] img",
            ".product-image img", ".product-gallery img",
            ".featured-image img", ".main-image img",
            ".media-kit img", ".media_kit img",
            "picture img", ".carousel .active img",
            "main img", "article img"
        ];

        candidates = [];
        for (const sel of heroSelectors) {
            try {
                const found = await page.locator(sel).all();
                if (found.length > 0) {
                    candidates.push(...found);
                    break;
                }
            } catch (e) {
                // selector not found, try next
            }
        }

        if (candidates.length === 0) {
            candidates = await page.locator("img[src]").all();
        }
    }

    if (candidates.length === 0) {
        return { error: "NO_IMAGE_FOUND", url: TARGET_URL };
    }

    const scored = [];
    for (const img of candidates.slice(0, 20)) {
        try {
            const box = await img.boundingBox();
            const src = await img.evaluate((el) => el.currentSrc || el.src || "");
            if (!box || !src || src.startsWith("data:")) {
                continue;
            }

            const area = box.width * box.height;
            const y = box.y;
            if (area < 2500) {
                continue;
            }

            const score = area - (y * 10);
            scored.push({ src, box, area, score });
        } catch (e) {
            continue;
        }
    }

    scored.sort((a, b) => b.score - a.score);

    const results = [];
    for (let i = 0; i < Math.min(MAX_IMAGES, scored.length); i++) {
        const { src, box, area } = scored[i];
        try {
            const response = await page.request.get(src, { timeout: 15000 });
            if (!response.ok()) {
                results.push({ index: i, src, error: `HTTP ${response.status()}`, area: Math.round(area) });
                continue;
            }

            const buffer = await response.body();
            const contentType = (response.headers()["content-type"] || "image/png").split(";")[0].trim().toLowerCase();
            const extensionByContentType = {
                "image/jpeg": "jpg",
                "image/jpg": "jpg",
                "image/png": "png",
                "image/webp": "webp",
                "image/svg+xml": "svg",
                "image/gif": "gif"
            };
            const extension = extensionByContentType[contentType] || "png";

            results.push({
                index: i,
                src,
                width: Math.round(box.width),
                height: Math.round(box.height),
                area: Math.round(area),
                contentType,
                extension,
                sizeBytes: buffer.length,
                base64: buffer.toString("base64")
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
        selector: SELECTOR || "auto-detect"
    };
}
