#!/usr/bin/env python3
"""download-image.py — unified image download with logo mode and cache.

Usage:
  # Logo mode (auto cache check, auto naming)
  python download-image.py --logo MYCR.ST

  # Product/equipment image (manual URL + output slug)
  python download-image.py https://example.com/hero --output my-product
  python download-image.py https://example.com/hero --output my-product --selector "img.product-hero"

  # Check cache only (no download)
  python download-image.py --logo MYCR.ST --check

Cache: _cache/images/ + .cache.json index. Workspace-level, cross-skill shared.
"""
from __future__ import annotations

import sys
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

import argparse
import json
import os
import re
import sys
import subprocess
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError
from html.parser import HTMLParser


# ── config ────────────────────────────────────────────────

CACHE_DIR = "_cache/images"
CACHE_INDEX = f"{CACHE_DIR}/.cache.json"
LOGO_PRIORITY = [
    # Wikipedia first — reliably has high-quality SVG/PNG logos with og:image
    ("Wikipedia", "https://en.wikipedia.org/wiki/{ticker}"),
    # Company homepage — best quality when available, uses ticker→domain heuristic
    ("Company Homepage", None),
    # Google Finance last resort — og:image often generic, not official logo
    ("Google Finance", "https://www.google.com/finance/quote/{ticker}"),
]


# ── cache helpers ──────────────────────────────────────────

def _load_cache(workspace: Path) -> dict:
    idx_path = workspace / CACHE_INDEX
    if idx_path.is_file():
        with open(idx_path, encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save_cache(workspace: Path, cache: dict):
    img_dir = workspace / CACHE_DIR
    img_dir.mkdir(parents=True, exist_ok=True)
    with open(workspace / CACHE_INDEX, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)


def _cache_hit(workspace: Path, key: str) -> Path | None:
    """Check if an image is already cached. Returns path if found."""
    cache = _load_cache(workspace)
    if key in cache and cache[key].get("file"):
        fpath = workspace / CACHE_DIR / cache[key]["file"]
        if fpath.is_file():
            return fpath
    return None


def _cache_save(workspace: Path, key: str, filename: str, url: str, size: int):
    cache = _load_cache(workspace)
    cache[key] = {
        "file": filename,
        "url": url,
        "downloaded": subprocess.run(
            ["date", "+%Y-%m-%d"], capture_output=True, text=True
        ).stdout.strip() or "unknown",
        "size": size,
    }
    _save_cache(workspace, cache)


# ── Tier 1: HTTP ──────────────────────────────────────────

def _tier1_download(url: str, workspace: Path, filename: str) -> tuple[Path | None, str | None]:
    """Download image via HTTP. Returns (path, error)."""
    try:
        req = Request(url, headers={"User-Agent": "download-image/1.0"})
        with urlopen(req, timeout=30) as resp:
            data = resp.read()
    except URLError as e:
        return None, f"HTTP fetch failed: {e}"
    except Exception as e:
        return None, f"Unexpected error: {e}"

    if len(data) < 100:
        return None, "Downloaded file too small (<100 bytes)"

    fpath = workspace / CACHE_DIR / filename
    fpath.parent.mkdir(parents=True, exist_ok=True)
    with open(fpath, "wb") as f:
        f.write(data)
    return fpath, None


def _tier1_find_logo_url(page_url: str) -> str | None:
    """Fetch page and find the largest logo image URL."""
    try:
        req = Request(page_url, headers={"User-Agent": "download-image/1.0"})
        with urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="replace")
    except Exception:
        return None

    # Look for og:image meta tag first
    m = re.search(r'<meta[^>]+property="og:image"[^>]+content="([^"]+)"', html, re.IGNORECASE)
    if m:
        return m.group(1)

    # Look for apple-touch-icon
    m = re.search(r'<link[^>]+rel="apple-touch-icon"[^>]+href="([^"]+)"', html, re.IGNORECASE)
    if m:
        return _resolve_url(m.group(1), page_url)

    # Look for img with 'logo' in class/id/alt
    img_srcs = re.findall(r'<img[^>]+src="([^"]+)"', html, re.IGNORECASE)
    for src in img_srcs:
        full = _resolve_url(src, page_url)
        if full and any(kw in full.lower() for kw in ["logo", "icon", "brand", "symbol"]):
            return full

    # Fallback: first large img
    if img_srcs:
        return _resolve_url(img_srcs[0], page_url)
    return None


def _resolve_url(src: str, base_url: str) -> str:
    """Resolve relative URLs."""
    if src.startswith("http"):
        return src
    if src.startswith("//"):
        return "https:" + src
    if src.startswith("/"):
        from urllib.parse import urlparse
        parsed = urlparse(base_url)
        return f"{parsed.scheme}://{parsed.netloc}{src}"
    return f"{base_url.rstrip('/')}/{src.lstrip('/')}"


# ── Tier 2: Playwright MCP ───────────────────────────────

def _tier2_instruction(url: str, filename: str, selector: str | None = None) -> str:
    """Return instruction for the agent to use Playwright MCP."""
    sel = selector or "img[src*='logo'], img[src*='hero'], meta[property='og:image']"
    return (
        f"Tier 2 — Playwright MCP required:\n"
        f"  browser_navigate → {url}\n"
        f"  browser_evaluate → find largest image matching '{sel}'\n"
        f"    → extract src/srcset, pick best resolution\n"
        f"    → fetch image as base64\n"
        f"  Feed base64 to: python .scripts/shared/download-image.py "
        f"--base64 \"<data>\" --output {filename}"
    )


# ── main ──────────────────────────────────────────────────

def download_logo(ticker: str, workspace: Path) -> dict:
    """Download a company logo. Returns result dict."""
    logo_key = f"{ticker}-logo"

    # Check cache
    cached = _cache_hit(workspace, logo_key)
    if cached:
        return {
            "status": "cached",
            "key": logo_key,
            "filename": cached.name,
            "path": str(cached),
            "tier": "cache",
        }

    # Try each source in priority order
    for source_name, url_template in LOGO_PRIORITY:
        if url_template:
            page_url = url_template.format(ticker=ticker)
        else:
            # Company homepage — derive from ticker domain
            domain = _ticker_to_domain(ticker)
            if not domain:
                continue
            page_url = f"https://www.{domain}"

        logo_url = _tier1_find_logo_url(page_url)
        if logo_url:
            ext = _guess_ext(logo_url)
            filename = f"{ticker}-logo.{ext}"
            fpath, err = _tier1_download(logo_url, workspace, filename)
            if fpath:
                _cache_save(workspace, logo_key, filename, logo_url, fpath.stat().st_size)
                return {
                    "status": "downloaded",
                    "key": logo_key,
                    "filename": filename,
                    "path": str(fpath),
                    "tier": "HTTP",
                    "source": source_name,
                    "logo_url": logo_url,
                }

    # All HTTP sources failed → need Playwright
    page_url = f"https://www.google.com/finance/quote/{ticker}"
    return {
        "status": "needs_playwright",
        "key": logo_key,
        "next_action": _tier2_instruction(page_url, f"{ticker}-logo"),
    }


def download_image(url: str, output: str, workspace: Path,
                   selector: str | None = None, base64: str | None = None) -> dict:
    """Download an image from a URL. Returns result dict."""
    key = output

    # Check cache
    cached = _cache_hit(workspace, key)
    if cached:
        return {
            "status": "cached",
            "key": key,
            "filename": cached.name,
            "path": str(cached),
            "tier": "cache",
        }

    # Base64 mode (from Tier 2 retry)
    if base64:
        import base64 as b64
        try:
            data = b64.b64decode(base64)
        except Exception as e:
            return {"status": "error", "key": key, "error": f"Base64 decode failed: {e}"}

        ext = _detect_ext(data)
        filename = f"{output}.{ext}"
        fpath = workspace / CACHE_DIR / filename
        fpath.parent.mkdir(parents=True, exist_ok=True)
        with open(fpath, "wb") as f:
            f.write(data)
        _cache_save(workspace, key, filename, url, len(data))
        return {
            "status": "downloaded",
            "key": key,
            "filename": filename,
            "path": str(fpath),
            "tier": "Playwright",
        }

    # Tier 1: HTTP
    ext = "png"  # default
    filename = f"{output}.{ext}"
    fpath, err = _tier1_download(url, workspace, filename)
    if fpath:
        # Detect real extension
        real_ext = _detect_ext(open(fpath, "rb").read(100))
        if real_ext != ext:
            new_path = fpath.with_suffix(f".{real_ext}")
            fpath.rename(new_path)
            fpath = new_path
            filename = fpath.name
        _cache_save(workspace, key, filename, url, fpath.stat().st_size)
        return {
            "status": "downloaded",
            "key": key,
            "filename": filename,
            "path": str(fpath),
            "tier": "HTTP",
        }

    # Tier 1 failed → need Playwright
    return {
        "status": "needs_playwright",
        "key": key,
        "next_action": _tier2_instruction(url, output, selector),
    }


# ── helpers ────────────────────────────────────────────────

def _ticker_to_domain(ticker: str) -> str | None:
    """Guess company domain from ticker. Known mappings + dynamic heuristic."""
    clean = ticker.split(".")[0].lower().strip()
    if not clean:
        return None

    # Known ticker→domain mappings (non-obvious ones)
    known = {
        # US
        "aapl": "apple.com", "msft": "microsoft.com", "nvda": "nvidia.com",
        "intc": "intel.com", "amzn": "amazon.com", "googl": "google.com",
        "meta": "meta.com", "tsla": "tesla.com", "jpm": "jpmorganchase.com",
        "bac": "bankofamerica.com", "xom": "exxonmobil.com", "cvx": "chevron.com",
        "wmt": "walmart.com", "pg": "pg.com", "ko": "coca-cola.com",
        "pep": "pepsico.com", "mcd": "mcdonalds.com", "nke": "nike.com",
        "dis": "disney.com", "nflx": "netflix.com", "adbe": "adobe.com",
        "crm": "salesforce.com", "orcl": "oracle.com", "ibm": "ibm.com",
        "csco": "cisco.com", "qcom": "qualcomm.com", "amd": "amd.com",
        "txn": "ti.com", "mu": "micron.com", "amat": "amat.com",
        "lrcx": "lamresearch.com", "klac": "kla.com", "snps": "synopsys.com",
        "cdns": "cadence.com", "anet": "arista.com", "now": "servicenow.com",
        "panw": "paloaltonetworks.com", "crwd": "crowdstrike.com",
        "ftnt": "fortinet.com", "zs": "zscaler.com", "okta": "okta.com",
        "ddoG": "datadoghq.com", "snow": "snowflake.com", "uber": "uber.com",
        "abnb": "airbnb.com", "sq": "squareup.com", "shop": "shopify.com",
        "pypl": "paypal.com", "ma": "mastercard.com", "v": "visa.com",
        "axp": "americanexpress.com", "gs": "goldmansachs.com", "ms": "morganstanley.com",
        "c": "citigroup.com", "wfc": "wellsfargo.com", "blk": "blackrock.com",
        "ge": "ge.com", "honeywell": "honeywell.com", "mmm": "3m.com",
        "cat": "caterpillar.com", "de": "deere.com", "lmt": "lockheedmartin.com",
        "rtx": "rtx.com", "noc": "northropgrumman.com", "gd": "gd.com",
        "ba": "boeing.com", "air": "airbus.com", "siemens": "siemens.com",
        "abb": "abb.com", "ph": "parker.com", "etn": "eaton.com",
        "emr": "emerson.com", "rok": "rockwellautomation.com", "ame": "ametek.com",
        "itw": "itw.com", "dhr": "danaher.com", "tdy": "teledyne.com",
        # EU
        "asml": "asml.com", "sap": "sap.com", "lvmh": "lvmh.com",
        "bmw": "bmwgroup.com", "mbg": "mercedes-benz.com", "vow3": "volkswagen.com",
        "sieg": "siemens.com", "saf": "safran-group.com", "air": "airbus.com",
        "rhm": "rheinmetall.com", "leo": "leonardo.com", "bae": "baesystems.com",
        "rr": "rolls-royce.com", "mtd": "mtu.de", "hag": "hensoldt.net",
        "thales": "thalesgroup.com", "dsy": "dassault-aviation.com",
        "sgo": "saint-gobain.com", "su": "schneider-electric.com",
        "leg": "legrand.com", "knin": "kuehne-nagel.com",
        "novo-b": "novonordisk.com", "nesn": "nestle.com", "ro": "roche.com",
        "novn": "novartis.com", "azon": "astrazeneca.com", "gsk": "gsk.com",
        "san": "sanofi.com", "bayn": "bayer.com", "bas": "basf.com",
        # JP — suffix controls common name
        "7203": "honda.co.jp", "7267": "honda.co.jp", "7201": "nissan.co.jp",
        "7202": "isuzu.co.jp", "7269": "suzuki.co.jp", "7270": "subaru.co.jp",
        "6501": "hitachi.co.jp", "6502": "toshiba.co.jp", "6503": "mitsubishielectric.co.jp",
        "6701": "nec.com", "6702": "fujitsu.com", "6752": "panasonic.com",
        "6753": "sharp.co.jp", "6758": "sony.com", "6762": "tdk.com",
        "6861": "keyence.com", "6954": "fanuc.co.jp", "7974": "nintendo.co.jp",
        "8031": "mitsui.com", "8058": "mitsubishicorp.com", "8001": "itochu.co.jp",
        "8053": "sumitomocorp.com", "8316": "smfg.co.jp", "8411": "mizuho-fg.co.jp",
        "8766": "tokiomarinehd.com", "9984": "softbank.jp",
        # KR
        "005930": "samsung.com", "000660": "skhynix.com", "005380": "hyundai.com",
        "000270": "kia.com", "035420": "naver.com", "035720": "kakao.com",
        "051910": "lgchem.com", "066570": "lge.com", "003550": "lghnh.com",
        # TW
        "2330": "tsmc.com", "2317": "foxconn.com", "2454": "mediatek.com",
        # HK/CN
        "0700": "tencent.com", "9988": "alibaba.com", "1810": "xiaomi.com",
        "3690": "meituan.com", "9618": "jd.com", "9888": "baidu.com",
        "2015": "li-auto.com", "9868": "xpeng.com", "9866": "nio.com",
        "1211": "byd.com", "300750": "catl.com",
        # SE
        "mycr": "mycronic.com", "keys": "keysight.com",
        "besi": "besi.com", "asm": "asm.com",
        # Nordic
        "eric-b": "ericsson.com", "nokia": "nokia.com",
        "hex": "hexagon.com", "atco-a": "atlasCopco.com",
        "sand": "sandvik.com", "skf-b": "skf.com",
        "volv-b": "volvogroup.com", "sca-b": "sca.com",
        "essity-b": "essity.com", "aliv-sdb": "autoliv.com",
        "ndase": "nordea.com", "shb-a": "handelsbanken.com",
        "seb-a": "seb.se", "swe-a": "swedbank.se",
        # Singapore
        "d05": "dbs.com", "o39": "ocbc.com", "u11": "uob.com.sg",
        "z74": "singtel.com", "c52": "comfortdelgro.com",
        # AU
        "bhp": "bhp.com", "rio": "riotinto.com", "cba": "commbank.com.au",
        "wbc": "westpac.com.au", "nab": "nab.com.au", "anz": "anz.com.au",
        "wes": "wesfarmers.com.au", "wow": "woolworthsgroup.com.au",
        # CA
        "ry": "rbc.com", "td": "td.com", "bns": "scotiabank.com",
        "bmo": "bmo.com", "cm": "cibc.com", "cnr": "cn.ca",
        "cp": "cpr.ca", "shop": "shopify.com",
        # IN
        "reliance": "ril.com", "tcs": "tcs.com", "infy": "infosys.com",
        "hdfcbank": "hdfcbank.com", "icicibank": "icicibank.com",
        # Commodity / Oil
        "cop": "conocophillips.com", "bp": "bp.com", "rds-a": "shell.com",
        "ttE": "totalenergies.com", "eqnr": "equinor.com",
        "glen": "glencore.com", "aAl": "angloamerican.com",
        "fmg": "fmgl.com.au", "sto": "santos.com", "wds": "woodside.com",
    }

    if clean in known:
        return known[clean]

    # Dynamic heuristic: try www.<ticker_clean>.com for simple tickers
    # Only for alphabetic tickers 2-6 chars that aren't pure numbers
    if re.match(r'^[a-zA-Z]{2,6}$', clean):
        return f"{clean}.com"

    return None


def _guess_ext(url: str) -> str:
    """Guess file extension from URL."""
    m = re.search(r"\.(png|jpg|jpeg|svg|webp|ico|gif)(?:\?|$)", url, re.IGNORECASE)
    if m:
        ext = m.group(1).lower()
        return "jpg" if ext == "jpeg" else ext
    return "png"


def _detect_ext(data: bytes) -> str:
    """Detect image type from magic bytes."""
    if data[:4] == b"\x89PNG":
        return "png"
    if data[:2] == b"\xff\xd8":
        return "jpg"
    if data[:3] == b"GIF":
        return "gif"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    if data[:4] == b"<svg":
        return "svg"
    return "png"


def _check_mode(workspace: Path, ticker: str | None, key: str | None) -> dict:
    """Check cache only."""
    cache = _load_cache(workspace)
    if ticker:
        key = f"{ticker}-logo"
    if key and key in cache:
        return {"status": "cached", "key": key, "entry": cache[key]}
    return {"status": "not_cached", "key": key}


# ── CLI ────────────────────────────────────────────────────

def cli():
    parser = argparse.ArgumentParser(description="Unified image download with cache")
    parser.add_argument("url", nargs="?", help="Image or page URL")
    parser.add_argument("--logo", help="Ticker for logo download (e.g., MYCR.ST)")
    parser.add_argument("--output", help="Output filename slug (without extension)")
    parser.add_argument("--selector", help="CSS selector for the target image")
    parser.add_argument("--base64", help="Base64 image data (from Tier 2 retry)")
    parser.add_argument("--check", action="store_true", help="Check cache only, no download")
    parser.add_argument("--workspace", default=None, help="Workspace root path")
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args()

    ws = Path(args.workspace) if args.workspace else Path.cwd()

    if args.check:
        result = _check_mode(ws, args.logo, args.output)
    elif args.logo:
        result = download_logo(args.logo, ws)
    elif args.url and args.output:
        result = download_image(args.url, args.output, ws,
                                selector=args.selector, base64=args.base64)
    else:
        parser.print_help()
        sys.exit(1)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        if result["status"] == "cached":
            print(f"✅ Cached: {result['path']}")
        elif result["status"] == "downloaded":
            print(f"✅ Downloaded ({result['tier']}): {result['path']}")
        elif result.get("next_action"):
            print(f"⚠️  {result['next_action']}")
        else:
            print(f"❌ {result.get('error', 'Download failed')}")

    sys.exit(0 if result["status"] in ("cached", "downloaded") else 1)


if __name__ == "__main__":
    cli()
