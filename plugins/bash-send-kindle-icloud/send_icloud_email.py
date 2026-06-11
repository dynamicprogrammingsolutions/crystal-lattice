#!/usr/bin/env python3
"""Send an attachment through iCloud SMTP using a password from stdin."""

from __future__ import annotations

import argparse
import mimetypes
import smtplib
import ssl
import sys
from email.message import EmailMessage
from pathlib import Path


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
    parser.add_argument("--from", dest="from_addr", required=True)
    parser.add_argument("--to", dest="to_addr", required=True)
    parser.add_argument("--subject", required=True)
    parser.add_argument("--body", default="")
    parser.add_argument("--attachment", type=Path, required=True)
    parser.add_argument("--password-stdin", action="store_true")
    return parser


def read_password(args: argparse.Namespace) -> str:
    if not args.password_stdin:
        raise SystemExit("--password-stdin is required")
    password = sys.stdin.read()
    if not password:
        raise SystemExit("missing SMTP password on stdin")
    return password.rstrip("\r\n")


def main() -> int:
    args = build_parser().parse_args()
    password = read_password(args)

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