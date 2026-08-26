"""Parse the folders written by the Power Automate email-preservation layer (纯 body.txt)。

邮件源即 Power Automate 保存的 body.txt（+meta.txt/outlook.link.txt）。
不做任何 html 解析/内嵌图采集——只认 body.txt 纯文本；body.txt 缺失的邮件 body_text 为空，
由 upstream（weak_signal/gate）自然跳过。图片仍认真实附件（.png/.jpg 文件）供 vision。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import re
import time


_STABLE_AGE_SECONDS = 30


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
# 自产物回环：daily/email 自己发出去的邮件（发送邮箱在 workspace .env 的 SMTP_USER /
# COVERAGE_EMAIL_TO）不是 sell-side 邮件，忽略。
# 运行时从 .env 动态读取（而非硬编码），发送邮箱变化也生效。


def _workspace_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _is_self_sender(sender: str, workspace: Path | None = None) -> bool:
    """自产物判据：**只看发送机器人（env 的 SMTP_USER）精确匹配**；
    自产标题(self_subject)另在 scan 里单独判。**不按公司域排除**——同事(@helvedcapital.com)
    转发的 sell-side 报告 sender 也是公司域，但不能当自产物丢掉。"""
    s = (sender or "").lower().strip()
    if not s:
        return False
    # daily 发送箱 = env 的 SMTP_USER（动态识别，不硬编码——发送邮箱变了也跟随）
    ws = workspace or _workspace_root()
    try:
        for line in (ws / ".env").read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and "=" in line and not line.startswith("#"):
                k, _, v = line.partition("=")
                if k.strip() == "SMTP_USER" and "@" in v:
                    if s == v.strip().strip('"').strip("'").lower():
                        return True
    except OSError:
        pass
    return False


def scan_email_dirs(base: str | Path) -> list[Email]:
    root = Path(base).expanduser()
    if not root.is_dir():
        return []

    emails: list[Email] = []
    for directory in sorted((p for p in root.iterdir() if p.is_dir()), key=lambda p: p.name):
        email = Email(folder=directory.name, path=str(directory))
        body_path: Path | None = None
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
                    body_path = path
                elif _matches(name, "outlook.link.txt") or name.endswith(".link.txt"):
                    email.outlook_link = path.read_text(encoding="utf-8", errors="replace").strip()
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
        # 保存层稳定性：body.txt 缺失/为空 = 尚未写完；mtime 太新 = Power Automate
        # 或 OneDrive 仍在写入。这类邮件本轮不 review、也不标 seen，下次自动重试。
        if not (email.body_text or "").strip():
            email.parse_ok = False
            email.parse_error = "missing or empty body.txt"
        elif body_path is not None:
            try:
                if time.time() - body_path.stat().st_mtime < _STABLE_AGE_SECONDS:
                    email.parse_ok = False
                    email.parse_error = "body.txt still being written (mtime too recent)"
            except OSError:
                email.parse_ok = False
                email.parse_error = "body.txt unreadable"
        if not email.parse_ok:
            emails.append(email)
            continue
        # 自有产物回环：Power Automate 会把 coverage-monitor / email-intelligence
        # 自己发出的邮件（[欧美盘后]/[亚盘盘后] Daily Coverage Brief / Email Intelligence
        # Brief）也保存进来——不是 sell-side 邮件，不参与 review。
        if _SELF_EMAIL_RE.search(email.subject or ""):
            continue
        sender = (email.sender or "").lower()
        if _is_self_sender(sender):
            continue
        emails.append(email)
    return emails


def filter_new(emails: list[Email], seen_ids: set[str]) -> list[Email]:
    return [email for email in emails if email.key not in seen_ids]
