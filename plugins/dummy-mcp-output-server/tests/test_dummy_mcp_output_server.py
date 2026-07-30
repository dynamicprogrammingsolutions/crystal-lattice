from __future__ import annotations

from dummy_mcp_output_server import (
    create_server,
    large_error_payload,
    large_text_payload,
)


def test_large_text_payload_contains_sentinels() -> None:
    payload = large_text_payload(size_chars=4096, line_length=80)

    assert payload.startswith("BEGIN_SENTINEL")
    assert "MIDDLE_SENTINEL" in payload
    assert "END_SENTINEL" in payload
    assert len(payload) <= 4096


def test_large_error_payload_contains_error_and_sentinels() -> None:
    payload = large_error_payload(size_chars=4096, line_length=80)

    assert payload.startswith("DUMMY_ERROR_START")
    assert "BEGIN_SENTINEL" in payload
    assert "END_SENTINEL" in payload


def test_create_server_exposes_streamable_http_app() -> None:
    server = create_server(log_level="error")

    app = server.streamable_http_app()
    paths = {getattr(route, "path", "") for route in app.routes}
    assert "/mcp" in paths
