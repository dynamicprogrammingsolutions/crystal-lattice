from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

from agent_terminal_app.bridge_client import BridgeConfig
from agent_terminal_app.server_integration_settings import (
    DEFAULT_BRIDGE_DEBUG,
    DEFAULT_BRIDGE_HTTP_CHUNK_SIZE_BYTES,
    DEFAULT_BRIDGE_HTTP_CHUNK_THRESHOLD_BYTES,
    DEFAULT_BRIDGE_HTTP_MAX_BODY_BYTES,
    DEFAULT_BRIDGE_HTTP_TIMEOUT_SECONDS,
    DEFAULT_BRIDGE_WS_MAX_SIZE_BYTES,
    parse_bridge_application_settings,
)


def _default_config() -> dict[str, object]:
    path = (
        Path(__file__).resolve().parents[1]
        / "agent_terminal_app"
        / "default_config"
        / "config.json"
    )
    return json.loads(path.read_text(encoding="utf-8"))


def test_bridge_application_settings_use_documented_defaults() -> None:
    settings = parse_bridge_application_settings(
        {"application": {"bridge_url": "wss://bridge.example/ws/websocket"}}
    )

    assert settings.bridge_url == "wss://bridge.example/ws/websocket"
    assert settings.ws_max_size_bytes == DEFAULT_BRIDGE_WS_MAX_SIZE_BYTES
    assert settings.http_timeout_seconds == DEFAULT_BRIDGE_HTTP_TIMEOUT_SECONDS
    assert settings.http_chunk_size_bytes == DEFAULT_BRIDGE_HTTP_CHUNK_SIZE_BYTES
    assert (
        settings.http_chunk_threshold_bytes == DEFAULT_BRIDGE_HTTP_CHUNK_THRESHOLD_BYTES
    )
    assert settings.http_max_body_bytes == DEFAULT_BRIDGE_HTTP_MAX_BODY_BYTES
    assert settings.debug is DEFAULT_BRIDGE_DEBUG


def test_default_config_and_bridge_config_share_canonical_defaults() -> None:
    raw_config = _default_config()
    settings = parse_bridge_application_settings(raw_config)
    bridge = BridgeConfig(
        bridge_url="wss://bridge.example/ws/websocket",
        server_id="server-id",
        display_name="Server",
        computer_name="host",
        location=None,
        local_http_base="http://127.0.0.1:8000",
    )

    assert settings.ws_max_size_bytes == bridge.ws_max_size_bytes
    assert settings.http_timeout_seconds == bridge.http_timeout_seconds
    assert settings.http_chunk_size_bytes == bridge.request_chunk_size_bytes
    assert (
        settings.http_chunk_threshold_bytes == bridge.response_chunking_threshold_bytes
    )
    assert settings.http_max_body_bytes == bridge.max_body_bytes
    assert settings.debug is bridge.debug


def test_bridge_application_settings_accept_explicit_values() -> None:
    settings = parse_bridge_application_settings(
        {
            "application": {
                "bridge_url": "wss://bridge.example/ws/websocket",
                "bridge": {
                    "ws_max_size_bytes": None,
                    "http_timeout_seconds": 45,
                    "http_chunk_size_bytes": 8192,
                    "http_chunk_threshold_bytes": 4096,
                    "http_max_body_bytes": 65536,
                    "debug": True,
                },
            }
        }
    )

    assert settings.bridge_url == "wss://bridge.example/ws/websocket"
    assert settings.ws_max_size_bytes is None
    assert settings.http_timeout_seconds == 45.0
    assert settings.http_chunk_size_bytes == 8192
    assert settings.http_chunk_threshold_bytes == 4096
    assert settings.http_max_body_bytes == 65536
    assert settings.debug is True


@pytest.mark.parametrize(
    ("config", "message"),
    [
        ({"application": []}, "application must be an object"),
        (
            {"application": {"bridge_url": 42}},
            "application.bridge_url must be a string or null",
        ),
        (
            {"application": {"bridge": []}},
            "application.bridge must be an object",
        ),
        (
            {"application": {"bridge": None}},
            "application.bridge must be an object",
        ),
        (
            {"application": {"bridge": {"ws_max_size_bytes": True}}},
            "application.bridge.ws_max_size_bytes must be a positive integer or null",
        ),
        (
            {"application": {"bridge": {"ws_max_size_bytes": 0}}},
            "application.bridge.ws_max_size_bytes must be a positive integer or null",
        ),
        (
            {"application": {"bridge": {"http_timeout_seconds": math.inf}}},
            "application.bridge.http_timeout_seconds must be a positive finite number",
        ),
        (
            {"application": {"bridge": {"http_timeout_seconds": 0}}},
            "application.bridge.http_timeout_seconds must be a positive finite number",
        ),
        (
            {"application": {"bridge": {"http_timeout_seconds": 10**1000}}},
            "application.bridge.http_timeout_seconds must be a positive finite number",
        ),
        (
            {"application": {"bridge": {"http_chunk_size_bytes": 1.5}}},
            "application.bridge.http_chunk_size_bytes must be a positive integer",
        ),
        (
            {"application": {"bridge": {"http_chunk_threshold_bytes": -1}}},
            "application.bridge.http_chunk_threshold_bytes must be a positive integer",
        ),
        (
            {"application": {"bridge": {"http_max_body_bytes": False}}},
            "application.bridge.http_max_body_bytes must be a positive integer",
        ),
        (
            {"application": {"bridge": {"debug": "true"}}},
            "application.bridge.debug must be a boolean",
        ),
    ],
)
def test_bridge_application_settings_reject_invalid_values(
    config: dict[str, object],
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message.replace(".", r"\.")):
        parse_bridge_application_settings(config)
