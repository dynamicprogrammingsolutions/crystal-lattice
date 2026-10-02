"""Explicit application settings for server-owned integrations."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import math
from typing import Any


DEFAULT_BRIDGE_WS_MAX_SIZE_BYTES = 16 * 1024 * 1024
DEFAULT_BRIDGE_HTTP_TIMEOUT_SECONDS = 120.0
DEFAULT_BRIDGE_HTTP_CHUNK_SIZE_BYTES = 900 * 1024
DEFAULT_BRIDGE_HTTP_CHUNK_THRESHOLD_BYTES = 256 * 1024
DEFAULT_BRIDGE_HTTP_MAX_BODY_BYTES = 10 * 1024 * 1024
DEFAULT_BRIDGE_DEBUG = False


@dataclass(frozen=True)
class BridgeApplicationSettings:
    """Validated process-start settings from the application config."""

    bridge_url: str | None = None
    ws_max_size_bytes: int | None = DEFAULT_BRIDGE_WS_MAX_SIZE_BYTES
    http_timeout_seconds: float = DEFAULT_BRIDGE_HTTP_TIMEOUT_SECONDS
    http_chunk_size_bytes: int = DEFAULT_BRIDGE_HTTP_CHUNK_SIZE_BYTES
    http_chunk_threshold_bytes: int = DEFAULT_BRIDGE_HTTP_CHUNK_THRESHOLD_BYTES
    http_max_body_bytes: int = DEFAULT_BRIDGE_HTTP_MAX_BODY_BYTES
    debug: bool = DEFAULT_BRIDGE_DEBUG


def _positive_int(
    values: Mapping[str, Any],
    key: str,
    default: int,
    *,
    nullable: bool = False,
) -> int | None:
    value = values.get(key, default)
    if nullable and value is None:
        return None
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        expected = "a positive integer or null" if nullable else "a positive integer"
        raise ValueError(f"application.bridge.{key} must be {expected}")
    return value


def _positive_number(
    values: Mapping[str, Any],
    key: str,
    default: float,
) -> float:
    value = values.get(key, default)
    message = f"application.bridge.{key} must be a positive finite number"
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError(message)
    try:
        number = float(value)
    except (OverflowError, ValueError) as exc:
        raise ValueError(message) from exc
    if not math.isfinite(number) or number <= 0:
        raise ValueError(message)
    return number


def parse_bridge_application_settings(
    resolved_config: Mapping[str, Any],
) -> BridgeApplicationSettings:
    """Parse bridge process-start settings from resolved application config."""

    raw_application = resolved_config.get("application")
    if raw_application is None:
        application: Mapping[str, Any] = {}
    elif isinstance(raw_application, Mapping):
        application = raw_application
    else:
        raise ValueError("application must be an object")

    raw_url = application.get("bridge_url")
    if raw_url is None or raw_url == "":
        bridge_url = None
    elif isinstance(raw_url, str):
        bridge_url = raw_url
    else:
        raise ValueError("application.bridge_url must be a string or null")

    if "bridge" not in application:
        bridge: Mapping[str, Any] = {}
    elif isinstance(application["bridge"], Mapping):
        bridge = application["bridge"]
    else:
        raise ValueError("application.bridge must be an object")

    raw_debug = bridge.get("debug", DEFAULT_BRIDGE_DEBUG)
    if not isinstance(raw_debug, bool):
        raise ValueError("application.bridge.debug must be a boolean")

    ws_max_size_bytes = _positive_int(
        bridge,
        "ws_max_size_bytes",
        DEFAULT_BRIDGE_WS_MAX_SIZE_BYTES,
        nullable=True,
    )
    http_chunk_size_bytes = _positive_int(
        bridge,
        "http_chunk_size_bytes",
        DEFAULT_BRIDGE_HTTP_CHUNK_SIZE_BYTES,
    )
    http_chunk_threshold_bytes = _positive_int(
        bridge,
        "http_chunk_threshold_bytes",
        DEFAULT_BRIDGE_HTTP_CHUNK_THRESHOLD_BYTES,
    )
    http_max_body_bytes = _positive_int(
        bridge,
        "http_max_body_bytes",
        DEFAULT_BRIDGE_HTTP_MAX_BODY_BYTES,
    )

    assert isinstance(http_chunk_size_bytes, int)
    assert isinstance(http_chunk_threshold_bytes, int)
    assert isinstance(http_max_body_bytes, int)

    return BridgeApplicationSettings(
        bridge_url=bridge_url,
        ws_max_size_bytes=ws_max_size_bytes,
        http_timeout_seconds=_positive_number(
            bridge,
            "http_timeout_seconds",
            DEFAULT_BRIDGE_HTTP_TIMEOUT_SECONDS,
        ),
        http_chunk_size_bytes=http_chunk_size_bytes,
        http_chunk_threshold_bytes=http_chunk_threshold_bytes,
        http_max_body_bytes=http_max_body_bytes,
        debug=raw_debug,
    )


__all__ = [
    "BridgeApplicationSettings",
    "DEFAULT_BRIDGE_DEBUG",
    "DEFAULT_BRIDGE_HTTP_CHUNK_SIZE_BYTES",
    "DEFAULT_BRIDGE_HTTP_CHUNK_THRESHOLD_BYTES",
    "DEFAULT_BRIDGE_HTTP_MAX_BODY_BYTES",
    "DEFAULT_BRIDGE_HTTP_TIMEOUT_SECONDS",
    "DEFAULT_BRIDGE_WS_MAX_SIZE_BYTES",
    "parse_bridge_application_settings",
]
