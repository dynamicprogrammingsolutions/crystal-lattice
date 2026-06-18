from __future__ import annotations

import os
import time
from functools import lru_cache
from typing import Any

import pytest
import requests

from agent_core.core import AgentCore
from hosted_test_utils import (
    REASONING_TEST_DIR,
    build_reference_core,  # noqa: F401 - re-exported for Fireworks tests
    load_root_env,
)

DEFAULT_FIREWORKS_BASE_URL = "https://api.fireworks.ai/inference/v1"
DEFAULT_FIREWORKS_TIMEOUT = 180.0
_FIREWORKS_MIN_REQUEST_INTERVAL_SECONDS = 1.0
_FIREWORKS_RATE_LIMIT_RETRY_DELAYS_SECONDS = (1.0, 2.0, 4.0)

_next_fireworks_request_time = 0.0

FIREWORKS_QWEN_MODEL = "fireworks/qwen3-8b"
FIREWORKS_GLM_MODEL = "accounts/fireworks/models/glm-5p1"
FIREWORKS_KIMI_MODEL = "fireworks/kimi-k2p5"


def _load_root_env() -> None:
    load_root_env()


def fireworks_api_key() -> str | None:
    _load_root_env()
    value = os.environ.get("FIREWORKS_API_KEY")
    return value if isinstance(value, str) and value else None


def fireworks_base_url() -> str:
    _load_root_env()
    return os.environ.get("FIREWORKS_BASE_URL", DEFAULT_FIREWORKS_BASE_URL)


def fireworks_model(env_var: str, default: str) -> str:
    _load_root_env()
    return os.environ.get(env_var, default)


def _fireworks_headers(api_key: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {api_key}"}


def _is_rate_limited_message(message: str) -> bool:
    lowered = message.lower()
    return "rate_limit_exceeded" in lowered or "rate limit" in lowered


def _wait_for_fireworks_request_slot(*, delay_seconds: float = 0.0) -> None:
    global _next_fireworks_request_time

    target = max(_next_fireworks_request_time, time.monotonic() + delay_seconds)
    now = time.monotonic()
    wait_seconds = target - now
    if wait_seconds > 0:
        time.sleep(wait_seconds)
    _next_fireworks_request_time = (
        time.monotonic() + _FIREWORKS_MIN_REQUEST_INTERVAL_SECONDS
    )


def _retry_delay_for_attempt(attempt_index: int) -> float | None:
    if attempt_index >= len(_FIREWORKS_RATE_LIMIT_RETRY_DELAYS_SECONDS):
        return None
    return _FIREWORKS_RATE_LIMIT_RETRY_DELAYS_SECONDS[attempt_index]


def _fail_rate_limit_exhausted(action: str) -> None:
    pytest.fail(
        f"Fireworks rate limit persisted after paced retries while {action}",
        pytrace=False,
    )


@lru_cache(maxsize=8)
def _fireworks_models_available(base_url: str, api_key: str) -> tuple[bool, str]:
    retry_index = 0
    while True:
        delay = _retry_delay_for_attempt(retry_index - 1) if retry_index > 0 else 0.0
        _wait_for_fireworks_request_slot(delay_seconds=delay)
        try:
            response = requests.get(
                f"{base_url.rstrip('/')}/models",
                headers=_fireworks_headers(api_key),
                timeout=10,
            )
        except (
            Exception
        ) as exc:  # pragma: no cover - network failures are environment-specific
            return False, str(exc)

        if response.status_code != 429:
            if not response.ok:
                return False, f"HTTP {response.status_code}: {response.text[:500]}"
            return True, ""

        next_delay = _retry_delay_for_attempt(retry_index)
        if next_delay is None:
            return False, "RATE_LIMIT_EXCEEDED"
        retry_index += 1


def ensure_fireworks_available() -> str:
    api_key = fireworks_api_key()
    if not api_key:
        pytest.skip("FIREWORKS_API_KEY not set")

    base_url = fireworks_base_url()
    ok, message = _fireworks_models_available(base_url, api_key)
    if not ok:
        if _is_rate_limited_message(message):
            _fail_rate_limit_exhausted("checking Fireworks availability")
        pytest.skip(f"Fireworks endpoint not reachable: {message}")
    return api_key


def build_fireworks_cfg(
    model: str,
    *,
    request_options: dict[str, Any] | None = None,
    timeout: float = DEFAULT_FIREWORKS_TIMEOUT,
) -> dict[str, Any]:
    api_key = ensure_fireworks_available()
    cfg: dict[str, Any] = {
        "base_url": fireworks_base_url(),
        "api_key": api_key,
        "model": model,
        "timeout": timeout,
    }
    if isinstance(request_options, dict) and request_options:
        cfg["request_options"] = request_options
    return cfg

def send_request_or_skip(core: AgentCore, session: Any, cfg: dict[str, Any]):
    retry_index = 0
    while True:
        delay = _retry_delay_for_attempt(retry_index - 1) if retry_index > 0 else 0.0
        _wait_for_fireworks_request_slot(delay_seconds=delay)
        try:
            return core.send_request(session, cfg)
        except RuntimeError as exc:
            if not _is_rate_limited_message(str(exc)):
                raise
            next_delay = _retry_delay_for_attempt(retry_index)
            if next_delay is None:
                _fail_rate_limit_exhausted("sending Fireworks request")
            retry_index += 1


def iter_request_stream_or_skip(core: AgentCore, session: Any, cfg: dict[str, Any]):
    retry_index = 0
    while True:
        delay = _retry_delay_for_attempt(retry_index - 1) if retry_index > 0 else 0.0
        _wait_for_fireworks_request_slot(delay_seconds=delay)
        yielded = False
        try:
            for event in core.send_request_stream(session, cfg):
                yielded = True
                yield event
            return
        except RuntimeError as exc:
            if yielded or not _is_rate_limited_message(str(exc)):
                raise
            next_delay = _retry_delay_for_attempt(retry_index)
            if next_delay is None:
                _fail_rate_limit_exhausted("starting Fireworks streaming request")
            retry_index += 1


def reasoning_test_prompt() -> str:
    return (REASONING_TEST_DIR / "prompt.txt").read_text()
