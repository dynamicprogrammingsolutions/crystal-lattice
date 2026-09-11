from __future__ import annotations

import gzip
import socket
import zlib

import pytest

from embedded_tools_shared import FetchError, FetchPolicy, extract_html_text
from embedded_tools_shared import fetch as fetch_module


def test_extract_html_text_omits_scripts_and_normalizes_blocks() -> None:
    title, text = extract_html_text(
        """
        <html>
          <head><title> Example title </title><style>hidden</style></head>
          <body><h1>Hello</h1><p>Alpha <strong>beta</strong>.</p>
          <script>secret()</script></body>
        </html>
        """
    )

    assert title == "Example title"
    assert "Hello" in text
    assert "Alpha beta." in text
    assert "hidden" not in text
    assert "secret" not in text


@pytest.mark.parametrize(
    "url",
    [
        "file:///tmp/example",
        "http://127.0.0.1",
        "http://[::1]",
        "http://169.254.1.1",
        "http://10.0.0.1",
    ],
)
def test_validate_public_url_rejects_non_public_destinations(url: str) -> None:
    with pytest.raises(FetchError):
        fetch_module.validate_public_url(url)


def test_validate_public_url_rejects_mixed_dns_answers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_getaddrinfo(*args, **kwargs):
        _ = args, kwargs
        return [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443)),
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 443)),
        ]

    monkeypatch.setattr(socket, "getaddrinfo", fake_getaddrinfo)
    with pytest.raises(FetchError, match="non-public"):
        fetch_module.validate_public_url("https://example.test")


def test_fetch_revalidates_redirect_and_extracts_html(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []
    responses = iter(
        [
            fetch_module._RawResponse(
                status_code=302,
                reason="Found",
                headers=(("Location", "https://final.test/page"),),
                body=b"",
                truncated=False,
            ),
            fetch_module._RawResponse(
                status_code=200,
                reason="OK",
                headers=(("Content-Type", "text/html; charset=utf-8"),),
                body=(
                    b"<html><head><title>Final</title></head>"
                    b"<body><p>hello world</p></body></html>"
                ),
                truncated=False,
            ),
        ]
    )

    def fake_resolve(host: str, port: int) -> str:
        calls.append(f"resolve:{host}:{port}")
        return "93.184.216.34"

    def fake_request(validated, **kwargs):
        calls.append(f"request:{validated.url}")
        return next(responses)

    monkeypatch.setattr(fetch_module, "_resolve_public_address", fake_resolve)
    monkeypatch.setattr(fetch_module, "_request_once", fake_request)

    result = fetch_module.fetch_public_url("https://start.test")
    assert calls == [
        "resolve:start.test:443",
        "request:https://start.test",
        "resolve:final.test:443",
        "request:https://final.test/page",
    ]
    assert result.final_url == "https://final.test/page"
    assert result.title == "Final"
    assert result.extracted_text == "Final\nhello world"


def test_fetch_clamps_text_and_rejects_unsupported_content(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        fetch_module,
        "_resolve_public_address",
        lambda host, port: "93.184.216.34",
    )
    monkeypatch.setattr(
        fetch_module,
        "_request_once",
        lambda validated, **kwargs: fetch_module._RawResponse(
            status_code=200,
            reason="OK",
            headers=(("Content-Type", "text/plain"),),
            body=b"x" * 2000,
            truncated=False,
        ),
    )
    result = fetch_module.fetch_public_url(
        "https://example.test",
        policy=FetchPolicy(max_text_chars=1000),
    )
    assert len(result.extracted_text) == 1000
    assert result.truncated_text

    monkeypatch.setattr(
        fetch_module,
        "_request_once",
        lambda validated, **kwargs: fetch_module._RawResponse(
            status_code=200,
            reason="OK",
            headers=(("Content-Type", "image/png"),),
            body=b"png",
            truncated=False,
        ),
    )
    with pytest.raises(FetchError, match="Unsupported"):
        fetch_module.fetch_public_url("https://example.test/image")


def test_decode_content_encoding_is_bounded() -> None:
    html = b"<html><head><title>Compressed</title></head><body>hello</body></html>"

    decoded_gzip, gzip_truncated = fetch_module._decode_content_encoding(
        gzip.compress(html),
        {"content-encoding": "gzip"},
        max_bytes=1024,
    )
    decoded_deflate, deflate_truncated = fetch_module._decode_content_encoding(
        zlib.compress(html),
        {"content-encoding": "deflate"},
        max_bytes=1024,
    )
    truncated, was_truncated = fetch_module._decode_content_encoding(
        gzip.compress(b"x" * 4096),
        {"content-encoding": "gzip"},
        max_bytes=1024,
    )

    assert decoded_gzip == html
    assert decoded_deflate == html
    assert not gzip_truncated
    assert not deflate_truncated
    assert truncated == b"x" * 1024
    assert was_truncated

    with pytest.raises(FetchError, match="Unsupported Content-Encoding"):
        fetch_module._decode_content_encoding(
            b"payload",
            {"content-encoding": "br"},
            max_bytes=1024,
        )