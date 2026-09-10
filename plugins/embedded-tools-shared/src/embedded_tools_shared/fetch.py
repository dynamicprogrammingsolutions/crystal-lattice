from __future__ import annotations

import http.client
import ipaddress
import re
import socket
import ssl
import time
from dataclasses import dataclass
from email.message import Message
from html.parser import HTMLParser
from typing import Mapping
from urllib.parse import urljoin, urlsplit


DEFAULT_FETCH_TIMEOUT_SECONDS = 20.0
DEFAULT_FETCH_MAX_BYTES = 1024 * 1024
DEFAULT_FETCH_MAX_REDIRECTS = 5
DEFAULT_FETCH_MAX_TEXT_CHARS = 100_000
DEFAULT_USER_AGENT = "CrystalLatticeEmbedded/0.1"
REDIRECT_STATUSES = {301, 302, 303, 307, 308}


class FetchError(ValueError):
    """A URL is invalid, unsafe, unreachable, or outside fetch limits."""


@dataclass(frozen=True)
class FetchPolicy:
    timeout_seconds: float = DEFAULT_FETCH_TIMEOUT_SECONDS
    max_bytes: int = DEFAULT_FETCH_MAX_BYTES
    max_redirects: int = DEFAULT_FETCH_MAX_REDIRECTS
    max_text_chars: int = DEFAULT_FETCH_MAX_TEXT_CHARS
    user_agent: str = DEFAULT_USER_AGENT

    def bounded(self) -> FetchPolicy:
        return FetchPolicy(
            timeout_seconds=max(1.0, min(float(self.timeout_seconds), 60.0)),
            max_bytes=max(1024, min(int(self.max_bytes), 5 * 1024 * 1024)),
            max_redirects=max(0, min(int(self.max_redirects), 10)),
            max_text_chars=max(1000, min(int(self.max_text_chars), 250_000)),
            user_agent=self.user_agent or DEFAULT_USER_AGENT,
        )


@dataclass(frozen=True)
class FetchedPage:
    requested_url: str
    final_url: str
    status_code: int
    reason: str
    headers: tuple[tuple[str, str], ...]
    content_type: str
    body_text: str
    extracted_text: str
    title: str | None
    truncated_bytes: bool
    truncated_text: bool
    duration_seconds: float

    def header_map(self) -> dict[str, str]:
        return {name.lower(): value for name, value in self.headers}


@dataclass(frozen=True)
class _ValidatedURL:
    url: str
    scheme: str
    host: str
    port: int
    target: str


@dataclass(frozen=True)
class _RawResponse:
    status_code: int
    reason: str
    headers: tuple[tuple[str, str], ...]
    body: bytes
    truncated: bool


class _TextExtractor(HTMLParser):
    _BLOCK_TAGS = {
        "article",
        "aside",
        "blockquote",
        "br",
        "div",
        "footer",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "header",
        "li",
        "main",
        "nav",
        "ol",
        "p",
        "pre",
        "section",
        "table",
        "td",
        "th",
        "tr",
        "ul",
    }
    _SKIP_TAGS = {"script", "style", "noscript", "template"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._skip_depth = 0
        self._in_title = False
        self._title_parts: list[str] = []
        self._parts: list[str] = []

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        _ = attrs
        lowered = tag.lower()
        if lowered in self._SKIP_TAGS:
            self._skip_depth += 1
            return
        if lowered == "title":
            self._in_title = True
        if lowered in self._BLOCK_TAGS:
            self._parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        lowered = tag.lower()
        if lowered in self._SKIP_TAGS:
            self._skip_depth = max(0, self._skip_depth - 1)
            return
        if lowered == "title":
            self._in_title = False
        if lowered in self._BLOCK_TAGS:
            self._parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return
        if self._in_title:
            self._title_parts.append(data)
        self._parts.append(data)

    def result(self) -> tuple[str | None, str]:
        title = _normalize_whitespace(" ".join(self._title_parts))
        text = _normalize_document_text("".join(self._parts))
        return title or None, text


class _PinnedHTTPConnection(http.client.HTTPConnection):
    def __init__(
        self,
        host: str,
        port: int,
        address: str,
        timeout: float,
    ) -> None:
        super().__init__(host=host, port=port, timeout=timeout)
        self._address = address

    def connect(self) -> None:
        self.sock = socket.create_connection(
            (self._address, self.port),
            self.timeout,
        )


class _PinnedHTTPSConnection(http.client.HTTPSConnection):
    def __init__(
        self,
        host: str,
        port: int,
        address: str,
        timeout: float,
    ) -> None:
        super().__init__(
            host=host,
            port=port,
            timeout=timeout,
            context=_verified_ssl_context(),
        )
        self._address = address

    def connect(self) -> None:
        raw_socket = socket.create_connection(
            (self._address, self.port),
            self.timeout,
        )
        self.sock = self._context.wrap_socket(raw_socket, server_hostname=self.host)


def _verified_ssl_context() -> ssl.SSLContext:
    try:
        import certifi
    except ImportError:
        return ssl.create_default_context()
    return ssl.create_default_context(cafile=certifi.where())


def _normalize_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _normalize_document_text(value: str) -> str:
    lines = [_normalize_whitespace(line) for line in value.splitlines()]
    output: list[str] = []
    previous_blank = True
    for line in lines:
        if line:
            output.append(line)
            previous_blank = False
        elif not previous_blank:
            output.append("")
            previous_blank = True
    while output and not output[-1]:
        output.pop()
    return "\n".join(output)


def extract_html_text(html: str) -> tuple[str | None, str]:
    parser = _TextExtractor()
    parser.feed(html)
    parser.close()
    return parser.result()


def _validated_url(raw_url: str) -> _ValidatedURL:
    if not isinstance(raw_url, str) or not raw_url.strip():
        raise FetchError("URL must be a non-empty string")
    candidate = raw_url.strip()
    parsed = urlsplit(candidate)
    if parsed.scheme not in {"http", "https"}:
        raise FetchError("Only public HTTP(S) URLs are allowed")
    if parsed.username is not None or parsed.password is not None:
        raise FetchError("URLs containing credentials are not allowed")
    host = parsed.hostname
    if not host:
        raise FetchError("URL host is required")
    try:
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
    except ValueError as error:
        raise FetchError("URL port is invalid") from error
    target = parsed.path or "/"
    if parsed.query:
        target = f"{target}?{parsed.query}"
    return _ValidatedURL(
        url=candidate,
        scheme=parsed.scheme,
        host=host,
        port=port,
        target=target,
    )


def _resolve_public_address(host: str, port: int) -> str:
    try:
        literal = ipaddress.ip_address(host)
        addresses = [literal]
    except ValueError:
        try:
            records = socket.getaddrinfo(
                host,
                port,
                type=socket.SOCK_STREAM,
            )
        except OSError as error:
            raise FetchError(f"Could not resolve URL host: {host}") from error
        addresses = []
        for record in records:
            address = record[4][0]
            try:
                parsed = ipaddress.ip_address(address)
            except ValueError:
                continue
            if parsed not in addresses:
                addresses.append(parsed)

    if not addresses:
        raise FetchError(f"Could not resolve URL host: {host}")
    if any(not address.is_global for address in addresses):
        raise FetchError("URL resolves to a non-public network address")
    return str(addresses[0])


def validate_public_url(raw_url: str) -> str:
    validated = _validated_url(raw_url)
    _resolve_public_address(validated.host, validated.port)
    return validated.url


def _request_once(
    validated: _ValidatedURL,
    *,
    address: str,
    policy: FetchPolicy,
    include_headers: Mapping[str, str] | None = None,
) -> _RawResponse:
    connection_type = (
        _PinnedHTTPSConnection
        if validated.scheme == "https"
        else _PinnedHTTPConnection
    )
    connection = connection_type(
        validated.host,
        validated.port,
        address,
        policy.timeout_seconds,
    )
    headers = {
        "Accept": "text/html,text/plain,application/json,application/xml;q=0.9,*/*;q=0.1",
        "Accept-Encoding": "identity",
        "Connection": "close",
        "Host": validated.host,
        "User-Agent": policy.user_agent,
        **dict(include_headers or {}),
    }
    try:
        connection.request("GET", validated.target, headers=headers)
        response = connection.getresponse()
        body = response.read(policy.max_bytes + 1)
        truncated = len(body) > policy.max_bytes
        if truncated:
            body = body[: policy.max_bytes]
        return _RawResponse(
            status_code=response.status,
            reason=response.reason or "",
            headers=tuple(response.getheaders()),
            body=body,
            truncated=truncated,
        )
    except (OSError, http.client.HTTPException, ssl.SSLError) as error:
        raise FetchError(f"Fetch failed: {error}") from error
    finally:
        connection.close()


def _content_type_and_charset(headers: Mapping[str, str]) -> tuple[str, str]:
    raw = headers.get("content-type", "text/plain")
    message = Message()
    message["content-type"] = raw
    content_type = message.get_content_type().lower()
    charset = message.get_content_charset() or "utf-8"
    return content_type, charset


def _is_text_content_type(content_type: str) -> bool:
    return (
        content_type.startswith("text/")
        or content_type.endswith("+json")
        or content_type.endswith("+xml")
        or content_type
        in {
            "application/json",
            "application/javascript",
            "application/xml",
            "application/xhtml+xml",
        }
    )


def fetch_public_url(
    raw_url: str,
    *,
    policy: FetchPolicy | None = None,
    include_headers: Mapping[str, str] | None = None,
) -> FetchedPage:
    bounded = (policy or FetchPolicy()).bounded()
    requested_url = raw_url.strip()
    current_url = requested_url
    started = time.monotonic()
    raw_response: _RawResponse | None = None

    for redirect_count in range(bounded.max_redirects + 1):
        validated = _validated_url(current_url)
        address = _resolve_public_address(validated.host, validated.port)
        raw_response = _request_once(
            validated,
            address=address,
            policy=bounded,
            include_headers=include_headers,
        )
        headers = {
            name.lower(): value for name, value in raw_response.headers
        }
        if raw_response.status_code not in REDIRECT_STATUSES:
            break
        location = headers.get("location")
        if not location:
            raise FetchError("Redirect response is missing a Location header")
        if redirect_count >= bounded.max_redirects:
            raise FetchError("Too many redirects")
        current_url = urljoin(current_url, location)

    if raw_response is None:
        raise FetchError("Fetch produced no response")

    header_map = {name.lower(): value for name, value in raw_response.headers}
    content_type, charset = _content_type_and_charset(header_map)
    if not _is_text_content_type(content_type):
        raise FetchError(f"Unsupported response content type: {content_type}")
    try:
        body_text = raw_response.body.decode(charset)
    except (LookupError, UnicodeDecodeError):
        body_text = raw_response.body.decode("utf-8", errors="replace")

    if content_type in {"text/html", "application/xhtml+xml"}:
        title, extracted = extract_html_text(body_text)
    else:
        title = None
        extracted = body_text

    truncated_text = len(extracted) > bounded.max_text_chars
    if truncated_text:
        extracted = extracted[: bounded.max_text_chars]
    return FetchedPage(
        requested_url=requested_url,
        final_url=current_url,
        status_code=raw_response.status_code,
        reason=raw_response.reason,
        headers=raw_response.headers,
        content_type=content_type,
        body_text=body_text,
        extracted_text=extracted,
        title=title,
        truncated_bytes=raw_response.truncated,
        truncated_text=truncated_text,
        duration_seconds=time.monotonic() - started,
    )