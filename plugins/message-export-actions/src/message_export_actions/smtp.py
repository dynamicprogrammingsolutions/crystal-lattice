from __future__ import annotations

import mimetypes
import smtplib
import ssl
import subprocess
from email.message import EmailMessage
from pathlib import Path


def keychain_password(*, account: str, service: str) -> str:
    result = subprocess.run(
        ["security", "find-generic-password", "-a", account, "-s", service, "-w"],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "unknown error").strip()
        raise RuntimeError(f"macOS Keychain lookup failed: {detail}")
    password = result.stdout.rstrip("\r\n")
    if not password:
        raise RuntimeError("macOS Keychain lookup returned an empty password")
    return password


def _add_attachment(message: EmailMessage, attachment_path: Path) -> None:
    mime_type, _ = mimetypes.guess_type(str(attachment_path))
    if mime_type is None:
        maintype, subtype = "application", "octet-stream"
    else:
        maintype, subtype = mime_type.split("/", 1)

    message.add_attachment(
        attachment_path.read_bytes(),
        maintype=maintype,
        subtype=subtype,
        filename=attachment_path.name,
    )


def send_icloud_attachment(
    *,
    smtp_user: str,
    from_addr: str,
    to_addr: str,
    subject: str,
    body: str,
    attachment_path: Path,
    keychain_service: str,
    smtp_host: str = "smtp.mail.me.com",
    smtp_port: int = 587,
) -> None:
    password = keychain_password(account=smtp_user, service=keychain_service)

    message = EmailMessage()
    message["From"] = from_addr
    message["To"] = to_addr
    message["Subject"] = subject
    message.set_content(body)
    _add_attachment(message, attachment_path)

    context = ssl.create_default_context()
    with smtplib.SMTP(smtp_host, smtp_port) as smtp:
        smtp.ehlo()
        smtp.starttls(context=context)
        smtp.ehlo()
        smtp.login(smtp_user, password)
        smtp.send_message(message)