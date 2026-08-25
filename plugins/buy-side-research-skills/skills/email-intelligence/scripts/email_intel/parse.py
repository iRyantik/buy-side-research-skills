"""Parse the folders written by the Power Automate email-preservation layer."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
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
                elif _matches(name, "body.html") or name.endswith(".eml"):
                    continue
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
