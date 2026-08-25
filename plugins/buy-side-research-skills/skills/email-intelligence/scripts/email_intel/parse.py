"""Parse the folders written by the Power Automate email-preservation layer."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import base64
import re


@dataclass
class Email:
    folder: str
    path: str
    subject: str = ""
    sender: str = ""
    received_at: str = ""
    message_id: str = ""
    importance: str = ""
    has_attachments: str = ""
    body_text: str = ""
    outlook_link: str = ""
    attachments: list[tuple[str, str]] = field(default_factory=list)
    images: list[tuple[str, str]] = field(default_factory=list)  # (name, path) 图片附件（≤2/封）
    pdfs: list[tuple[str, str]] = field(default_factory=list)   # (name, path) PDF 附件（≤2/封）
    parse_ok: bool = True
    parse_error: str = ""

    @property
    def key(self) -> str:
        return self.message_id or self.folder


_META_FIELDS = {
    "subject": "subject",
    "from": "sender",
    "sender": "sender",
    "received_at": "received_at",
    "message_id": "message_id",
    "importance": "importance",
    "has_attachments": "has_attachments",
}


def parse_meta(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in (text or "").splitlines():
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        field_name = _META_FIELDS.get(key.strip().lower())
        if field_name:
            out[field_name] = value.strip()
    return out


def _matches(name: str, canonical: str) -> bool:
    return name == canonical or name.endswith(f".{canonical}")


_SELF_EMAIL_RE = re.compile(
    r"Daily Coverage Brief|Email Intelligence Brief|Intraday Coverage Alerts", re.I
)
# 自有发件域：SMTP 发件邮箱（qq）+ 公司域（内部邮件）——不是 sell-side 邮件
_SELF_SENDER_SUFFIXES = ("@1292145106.qq.com", "@helvedcapital.com")


def _harvest_inline_images(email: Email, html_path: Path, directory: Path, cache: Path | None = None) -> None:
    """body.html 内嵌图：data:base64 直接解码；cid: 引用找目录内对应文件（ATT00001.jpg 等）。

    提取结果 append 到 email.images（与附件图同一出口，review 前统一 base64 喂 vision）。
    """
    try:
        html_text = html_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return
    import re as _re
    # 1) data:image/...;base64,XXXX
    for m in _re.finditer(r'data:image/(\w+);base64,([A-Za-z0-9+/=]+)', html_text):
        if len(email.images) >= 2:
            break
        ext = {"png": "png", "jpeg": "jpg", "jpg": "jpg", "gif": "gif"}.get(m.group(1).lower(), "png")
        try:
            raw = base64.b64decode(m.group(2))
        except Exception:
            continue
        if not raw or len(raw) > 3_000_000:
            continue
        out = (cache or directory) / f"{html_path.stem}-inline-{len(email.images)}.{ext}"
        try:
            out.write_bytes(raw)
            email.images.append((out.name, str(out)))
        except OSError:
            continue
    # 2) cid:file
    cids = set(_re.findall(r"(?:src|poster)=[\"']cid:([^\"']+)[\"']", html_text, _re.I))
    for cid in cids:
        if len(email.images) >= 2:
            break
        cands = list(directory.glob(cid)) + list(directory.glob(f"ATT*")) + [directory / cid]
        for c in cands:
            if c.is_file() and c.suffix.lower() in (".png", ".jpg", ".jpeg"):
                email.images.append((c.name, str(c)))
                break


def _html_to_text(html_text: str) -> str:
    """body.txt 缺失时的 fallback：body.html → 纯文本（stdlib 解析，零依赖）。"""
    from html.parser import HTMLParser
    from html import unescape

    class _T(HTMLParser):
        def __init__(self):
            super().__init__()
            self.parts = []

        def handle_data(self, data):
            self.parts.append(data)

        def handle_starttag(self, tag, attrs):
            if tag in ("br", "p", "div", "tr", "li", "hr", "h1", "h2", "h3", "h4", "table"):
                self.parts.append(chr(10))

        def handle_endtag(self, tag):
            if tag in ("p", "div", "tr", "li", "h1", "h2", "h3", "h4"):
                self.parts.append(chr(10))

    parser = _T()
    try:
        parser.feed(html_text[:2_000_000])
    except Exception:
        pass
    text = unescape("".join(parser.parts))
    lines = [ln.strip() for ln in text.splitlines()]
    return chr(10).join(ln for ln in lines if ln)


def scan_email_dirs(base: str | Path) -> list[Email]:
    root = Path(base).expanduser()
    if not root.is_dir():
        return []

    emails: list[Email] = []
    for directory in sorted((p for p in root.iterdir() if p.is_dir()), key=lambda p: p.name):
        email = Email(folder=directory.name, path=str(directory))
        try:
            files = list(directory.iterdir())
        except OSError as exc:
            email.parse_ok = False
            email.parse_error = f"listdir: {exc}"
            emails.append(email)
            continue

        for path in files:
            try:
                if not path.is_file():
                    continue
                name = path.name
                if _matches(name, "meta.txt"):
                    for field_name, value in parse_meta(path.read_text(encoding="utf-8", errors="replace")).items():
                        setattr(email, field_name, value)
                elif _matches(name, "body.txt"):
                    email.body_text = path.read_text(encoding="utf-8", errors="replace")
                elif _matches(name, "outlook.link.txt") or name.endswith(".link.txt"):
                    email.outlook_link = path.read_text(encoding="utf-8", errors="replace").strip()
                elif _matches(name, "body.html"):
                    _harvest_inline_images(email, path, directory)
                    if not email.body_text:
                        email.body_text = _html_to_text(path.read_text(encoding="utf-8", errors="replace"))
                elif name.endswith(".eml"):
                    continue
                elif path.suffix.lower() in (".png", ".jpg", ".jpeg"):
                    if len(email.images) < 2:
                        email.images.append((name, str(path)))
                elif path.suffix.lower() == ".pdf" and len(email.pdfs) < 2:
                    email.pdfs.append((name, str(path)))
                else:
                    email.attachments.append((name, str(path)))
            except OSError:
                continue

        email.subject = email.subject or email.folder
        # 自有产物回环：Power Automate 会把 coverage-monitor / email-intelligence
        # 自己发出的邮件（[欧美盘后]/[亚盘盘后] Daily Coverage Brief / Email Intelligence
        # Brief）也保存进来——不是 sell-side 邮件，不参与 review。
        if _SELF_EMAIL_RE.search(email.subject or ""):
            continue
        sender = (email.sender or "").lower()
        if any(sender.endswith(sfx) for sfx in _SELF_SENDER_SUFFIXES):
            continue
        emails.append(email)
    return emails


def filter_new(emails: list[Email], seen_ids: set[str]) -> list[Email]:
    return [email for email in emails if email.key not in seen_ids]
