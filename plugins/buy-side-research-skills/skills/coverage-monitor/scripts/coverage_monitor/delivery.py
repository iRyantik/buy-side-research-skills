from __future__ import annotations

from email.message import EmailMessage
import json
import os
import smtplib
from typing import Iterable
from urllib.request import Request, urlopen


def _missing_env(names: Iterable[str], env: dict[str, str]) -> list[str]:
    return [name for name in names if not env.get(name)]


def send_email(subject: str, body_text: str, body_html: str | None = None, env: dict[str, str] | None = None) -> list[str]:
    environment = env or dict(os.environ)
    required = ["SMTP_HOST", "SMTP_USER", "SMTP_PASSWORD", "COVERAGE_EMAIL_TO"]
    missing = _missing_env(required, environment)
    if missing:
        return [f"{name} missing" for name in missing]

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = environment["SMTP_USER"]
    message["To"] = environment["COVERAGE_EMAIL_TO"]
    message.set_content(body_text)
    if body_html:
        message.add_alternative(body_html, subtype="html")

    port = int(environment.get("SMTP_PORT", "587"))
    try:
        with smtplib.SMTP(environment["SMTP_HOST"], port, timeout=20) as smtp:
            if port == 587:
                smtp.starttls()
            smtp.login(environment["SMTP_USER"], environment["SMTP_PASSWORD"])
            smtp.send_message(message)
    except Exception as exc:  # pragma: no cover - external system dependent
        return [f"email_delivery_failed ({exc.__class__.__name__})"]
    return []


def send_wecom(subject: str, body_markdown: str, env: dict[str, str] | None = None) -> list[str]:
    environment = env or dict(os.environ)
    webhook_url = environment.get("WECOM_WEBHOOK_URL")
    if not webhook_url:
        return ["WECOM_WEBHOOK_URL missing"]

    payload = json.dumps(
        {
            "msgtype": "markdown",
            "markdown": {
                "content": f"## {subject}\n\n{body_markdown}",
            },
        }
    ).encode("utf-8")
    request = Request(webhook_url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urlopen(request, timeout=20) as response:  # pragma: no cover - external system dependent
            response.read()
    except Exception as exc:  # pragma: no cover - external system dependent
        return [f"wecom_delivery_failed ({exc.__class__.__name__})"]
    return []
