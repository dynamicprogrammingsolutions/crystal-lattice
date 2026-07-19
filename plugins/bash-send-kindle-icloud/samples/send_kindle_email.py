#!/usr/bin/env python3
"""Send an attachment through SMTP using a password stored in macOS Keychain."""

from __future__ import annotations

import argparse
import mimetypes
import smtplib
import ssl
import subprocess
from email.message import EmailMessage
from pathlib import Path


def keychain_password(service: str, account: str) -> str:
    result = subprocess.run(
        [
            "security",
            "find-generic-password",
            "-s",
            service,
            "-a",
            account,
            "-w",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def add_attachment(message: EmailMessage, attachment_path: Path) -> None:
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--smtp-host", default="smtp.mail.me.com")
    parser.add_argument("--smtp-port", type=int, default=587)
    parser.add_argument("--smtp-user", required=True)
    parser.add_argument("--keychain-service", default="kindle-smtp")
    parser.add_argument("--from", dest="from_addr", required=True)
    parser.add_argument("--to", dest="to_addr", required=True)
    parser.add_argument("--subject", required=True)
    parser.add_argument("--body", default="")
    parser.add_argument("--attachment", type=Path, required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    password = keychain_password(args.keychain_service, args.smtp_user)

    message = EmailMessage()
    message["From"] = args.from_addr
    message["To"] = args.to_addr
    message["Subject"] = args.subject
    message.set_content(args.body)
    add_attachment(message, args.attachment)

    context = ssl.create_default_context()
    with smtplib.SMTP(args.smtp_host, args.smtp_port) as smtp:
        smtp.ehlo()
        smtp.starttls(context=context)
        smtp.ehlo()
        smtp.login(args.smtp_user, password)
        smtp.send_message(message)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())