from __future__ import annotations

import inspect
from typing import Any

import pytest
import requests

import reference_openai_compatible_provider.provider as provider_module
from reference_openai_compatible_provider.provider import OpenAICompatibleProvider


def _patch_session_post(monkeypatch, fake_post) -> None:
    parameters = inspect.signature(fake_post).parameters
    accepts_kwargs = any(
        parameter.kind is inspect.Parameter.VAR_KEYWORD
        for parameter in parameters.values()
    )

    def session_post(_session, *args, **kwargs):
        filtered = (
            kwargs
            if accepts_kwargs
            else {key: value for key, value in kwargs.items() if key in parameters}
        )
        return fake_post(*args, **filtered)

    monkeypatch.setattr(provider_module.requests.Session, "post", session_post)


class _Resp:
    def __init__(
        self,
        *,
        ok: bool,
        payload: Any = None,
        status_code: int = 200,
        text: str = "",
        headers: dict[str, str] | None = None,
        lines: list[str] | None = None,
    ):
        self.ok = ok
        self._payload = payload
        self.status_code = status_code
        self.text = text
        self.headers = headers or {}
        self._lines = lines or []
        self.encoding = "utf-8"

    def json(self) -> Any:
        return self._payload

    def iter_lines(self, decode_unicode: bool = True):
        assert decode_unicode is True
        yield from self._lines

    def close(self) -> None:
        return None


def test_call_api_retries_429_with_backoff(monkeypatch):
    provider_module._next_request_time_by_scope.clear()
    responses = iter(
        [
            _Resp(ok=False, status_code=429, text="too many requests"),
            _Resp(
                ok=True,
                payload={
                    "choices": [{"message": {"role": "assistant", "content": "pong"}}],
                    "usage": {
                        "prompt_tokens": 2,
                        "completion_tokens": 1,
                        "total_tokens": 3,
                    },
                },
            ),
        ]
    )
    sleeps: list[float] = []

    def fake_post(
        url: str,
        headers: dict[str, str],
        json: dict[str, Any],
        timeout: float,
    ):
        assert url == "http://example.com/v1/chat/completions"
        assert json["stream"] is False
        return next(responses)

    _patch_session_post(monkeypatch, fake_post)
    monkeypatch.setattr(provider_module.time, "sleep", sleeps.append)

    provider = OpenAICompatibleProvider()
    native_messages, state = provider.initialize_request(
        [],
        {
            "config": {
                "base_url": "http://example.com/v1",
                "model": "demo-model",
                "rate_limit_retry_delays_seconds": [1],
            }
        },
    )
    _partials, finals, _history, _state = provider.call_api(native_messages, state)

    assert sleeps == [1.0]
    assert finals[0]["content"] == "pong"


def test_call_api_enforces_min_request_interval_between_calls(monkeypatch):
    provider_module._next_request_time_by_scope.clear()
    sleeps: list[float] = []
    monotonic_values = iter([0.0, 0.25])

    def fake_post(
        url: str,
        headers: dict[str, str],
        json: dict[str, Any],
        timeout: float,
    ):
        return _Resp(
            ok=True,
            payload={
                "choices": [{"message": {"role": "assistant", "content": "ok"}}]
            },
        )

    _patch_session_post(monkeypatch, fake_post)
    monkeypatch.setattr(provider_module.time, "sleep", sleeps.append)
    monkeypatch.setattr(provider_module.time, "monotonic", lambda: next(monotonic_values))

    provider = OpenAICompatibleProvider()
    native_messages, state = provider.initialize_request(
        [],
        {
            "config": {
                "base_url": "http://example.com/v1",
                "model": "demo-model",
                "min_request_interval_seconds": 1.0,
            }
        },
    )

    provider.call_api(native_messages, state)
    provider.call_api(native_messages, state)

    assert sleeps == [0.75]


def test_stream_api_retries_429_before_stream_starts(monkeypatch):
    provider_module._next_request_time_by_scope.clear()
    responses = iter(
        [
            _Resp(
                ok=False,
                status_code=429,
                text="busy",
                headers={"Retry-After": "2"},
            ),
            _Resp(
                ok=True,
                lines=[
                    'data: {"choices":[{"delta":{"role":"assistant","content":"hel"}}]}',
                    'data: {"choices":[{"delta":{"content":"lo"}}]}',
                    "data: [DONE]",
                ],
            ),
        ]
    )
    sleeps: list[float] = []

    def fake_post(
        url: str,
        headers: dict[str, str],
        json: dict[str, Any],
        timeout: float,
        stream: bool,
    ):
        assert stream is True
        return next(responses)

    _patch_session_post(monkeypatch, fake_post)
    monkeypatch.setattr(provider_module.time, "sleep", sleeps.append)

    provider = OpenAICompatibleProvider()
    native_messages, state = provider.initialize_request(
        [],
        {
            "config": {
                "base_url": "http://example.com/v1",
                "model": "demo-model",
                "rate_limit_retry_delays_seconds": [1],
            }
        },
    )
    chunks = list(provider.stream_api(native_messages, state))

    assert sleeps == [2.0]
    assert [chunk["choices"][0]["delta"].get("content", "") for chunk in chunks] == [
        "hel",
        "lo",
    ]


def test_initialize_request_uses_selected_base_url_verbatim():
    provider = OpenAICompatibleProvider()
    native_messages, state = provider.initialize_request(
        [],
        {
            "config": {
                "base_url": "https://api.z.ai/api/coding/paas/v4",
                "model": "glm-4.5-air",
            }
        },
    )

    assert native_messages == []
    assert state["request"]["url"] == "https://api.z.ai/api/coding/paas/v4/chat/completions"
    assert state["rate_limit_policy"]["scope_key"] == "https://api.z.ai/api/coding/paas/v4"


def test_call_api_retries_500_with_configured_delays(monkeypatch):
    provider_module._next_request_time_by_scope.clear()
    responses = iter(
        [
            _Resp(ok=False, status_code=500, text="internal error"),
            _Resp(ok=False, status_code=500, text="still broken"),
            _Resp(
                ok=True,
                payload={
                    "choices": [{"message": {"role": "assistant", "content": "recovered"}}],
                },
            ),
        ]
    )
    sleeps: list[float] = []

    def fake_post(url, headers, json, timeout):
        return next(responses)

    _patch_session_post(monkeypatch, fake_post)
    monkeypatch.setattr(provider_module.time, "sleep", sleeps.append)

    provider = OpenAICompatibleProvider()
    native_messages, state = provider.initialize_request(
        [],
        {
            "config": {
                "base_url": "http://example.com/v1",
                "model": "demo-model",
                "retry_on_status": {"500": [2, 5]},
            }
        },
    )
    _partials, finals, _history, _state = provider.call_api(native_messages, state)

    assert sleeps == [2.0, 5.0]
    assert finals[0]["content"] == "recovered"


def test_call_api_mixed_status_codes_uses_global_attempt_counter(monkeypatch):
    provider_module._next_request_time_by_scope.clear()
    responses = iter(
        [
            _Resp(ok=False, status_code=500, text="error"),
            _Resp(ok=False, status_code=502, text="bad gateway"),
            _Resp(
                ok=True,
                payload={
                    "choices": [{"message": {"role": "assistant", "content": "ok"}}],
                },
            ),
        ]
    )
    sleeps: list[float] = []

    def fake_post(url, headers, json, timeout):
        return next(responses)

    _patch_session_post(monkeypatch, fake_post)
    monkeypatch.setattr(provider_module.time, "sleep", sleeps.append)

    provider = OpenAICompatibleProvider()
    native_messages, state = provider.initialize_request(
        [],
        {
            "config": {
                "base_url": "http://example.com/v1",
                "model": "demo-model",
                "retry_on_status": {"500": [2, 5], "502": [1, 3, 5]},
            }
        },
    )
    _partials, finals, _history, _state = provider.call_api(native_messages, state)

    # attempt 0 → 500: delay from 500 list at index 0 = 2.0
    # attempt 1 → 502: delay from 502 list at index 1 = 3.0
    assert sleeps == [2.0, 3.0]
    assert finals[0]["content"] == "ok"


def test_call_api_exhausted_retries_raises_on_status(monkeypatch):
    provider_module._next_request_time_by_scope.clear()
    responses = iter(
        [
            _Resp(ok=False, status_code=500, text="error 1"),
            _Resp(ok=False, status_code=500, text="error 2"),
            _Resp(ok=False, status_code=500, text="error 3"),
        ]
    )
    sleeps: list[float] = []

    def fake_post(url, headers, json, timeout):
        return next(responses)

    _patch_session_post(monkeypatch, fake_post)
    monkeypatch.setattr(provider_module.time, "sleep", sleeps.append)

    provider = OpenAICompatibleProvider()
    native_messages, state = provider.initialize_request(
        [],
        {
            "config": {
                "base_url": "http://example.com/v1",
                "model": "demo-model",
                "retry_on_status": {"500": [1]},
            }
        },
    )
    # Only 1 retry delay configured, so: attempt 0 retries, attempt 1 returns response.

    with pytest.raises(RuntimeError, match="OpenAI-compatible call failed: 500 error 2"):
        provider.call_api(native_messages, state)

    assert sleeps == [1.0]


def test_stream_api_retries_500_before_stream_starts(monkeypatch):
    provider_module._next_request_time_by_scope.clear()
    responses = iter(
        [
            _Resp(ok=False, status_code=500, text="server error"),
            _Resp(
                ok=True,
                lines=[
                    'data: {"choices":[{"delta":{"role":"assistant","content":"hi"}}]}',
                    "data: [DONE]",
                ],
            ),
        ]
    )
    sleeps: list[float] = []

    def fake_post(url, headers, json, timeout, stream):
        return next(responses)

    _patch_session_post(monkeypatch, fake_post)
    monkeypatch.setattr(provider_module.time, "sleep", sleeps.append)

    provider = OpenAICompatibleProvider()
    native_messages, state = provider.initialize_request(
        [],
        {
            "config": {
                "base_url": "http://example.com/v1",
                "model": "demo-model",
                "retry_on_status": {"500": [3]},
            }
        },
    )
    chunks = list(provider.stream_api(native_messages, state))

    assert sleeps == [3.0]
    assert chunks[0]["choices"][0]["delta"]["content"] == "hi"


def test_parse_retry_on_status_from_config():
    provider = OpenAICompatibleProvider()
    _native_messages, state = provider.initialize_request(
        [],
        {
            "config": {
                "base_url": "http://example.com/v1",
                "model": "demo-model",
                "retry_on_status": {"500": [1, 3], "502": "0.5, 1, 2", "bad": [1]},
            }
        },
    )
    retry_on_status = state["rate_limit_policy"]["retry_on_status"]
    assert retry_on_status == {500: (1.0, 3.0), 502: (0.5, 1.0, 2.0)}
    assert "bad" not in retry_on_status


def test_no_retry_on_status_without_config(monkeypatch):
    provider_module._next_request_time_by_scope.clear()

    def fake_post(url, headers, json, timeout):
        return _Resp(ok=False, status_code=500, text="no retry configured")

    _patch_session_post(monkeypatch, fake_post)
    sleeps: list[float] = []
    monkeypatch.setattr(provider_module.time, "sleep", sleeps.append)

    provider = OpenAICompatibleProvider()
    native_messages, state = provider.initialize_request(
        [],
        {"config": {"base_url": "http://example.com/v1", "model": "demo-model"}},
    )

    with pytest.raises(RuntimeError, match="OpenAI-compatible call failed: 500"):
        provider.call_api(native_messages, state)

    assert sleeps == []


# --- retry_on_timeout tests ---


def test_call_api_retries_timeout_with_configured_delays(monkeypatch):
    provider_module._next_request_time_by_scope.clear()
    call_count = 0
    sleeps: list[float] = []

    def fake_post(url, headers, json, timeout):
        nonlocal call_count
        call_count += 1
        if call_count <= 2:
            raise requests.exceptions.Timeout("connection timed out")
        return _Resp(
            ok=True,
            payload={
                "choices": [{"message": {"role": "assistant", "content": "finally"}}],
            },
        )

    _patch_session_post(monkeypatch, fake_post)
    monkeypatch.setattr(provider_module.time, "sleep", sleeps.append)

    provider = OpenAICompatibleProvider()
    native_messages, state = provider.initialize_request(
        [],
        {
            "config": {
                "base_url": "http://example.com/v1",
                "model": "demo-model",
                "retry_on_timeout": [1, 3],
            }
        },
    )
    _partials, finals, _history, _state = provider.call_api(native_messages, state)

    assert sleeps == [1.0, 3.0]
    assert finals[0]["content"] == "finally"


def test_call_api_timeout_without_config_raises_immediately(monkeypatch):
    provider_module._next_request_time_by_scope.clear()

    def fake_post(url, headers, json, timeout):
        raise requests.exceptions.Timeout("connection timed out")

    _patch_session_post(monkeypatch, fake_post)
    sleeps: list[float] = []
    monkeypatch.setattr(provider_module.time, "sleep", sleeps.append)

    provider = OpenAICompatibleProvider()
    native_messages, state = provider.initialize_request(
        [],
        {"config": {"base_url": "http://example.com/v1", "model": "demo-model"}},
    )

    with pytest.raises(
        RuntimeError,
        match="OpenAI-compatible call failed: connection timed out",
    ):
        provider.call_api(native_messages, state)

    assert sleeps == []


def test_call_api_exhausted_timeout_retries_raises(monkeypatch):
    provider_module._next_request_time_by_scope.clear()

    def fake_post(url, headers, json, timeout):
        raise requests.exceptions.Timeout("still timing out")

    _patch_session_post(monkeypatch, fake_post)
    sleeps: list[float] = []
    monkeypatch.setattr(provider_module.time, "sleep", sleeps.append)

    provider = OpenAICompatibleProvider()
    native_messages, state = provider.initialize_request(
        [],
        {
            "config": {
                "base_url": "http://example.com/v1",
                "model": "demo-model",
                "retry_on_timeout": [1],
            }
        },
    )

    with pytest.raises(
        RuntimeError,
        match="OpenAI-compatible call failed: still timing out",
    ):
        provider.call_api(native_messages, state)

    assert sleeps == [1.0]


def test_timeout_and_status_share_global_attempt_counter(monkeypatch):
    provider_module._next_request_time_by_scope.clear()
    call_count = 0
    sleeps: list[float] = []

    def fake_post(url, headers, json, timeout):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return _Resp(ok=False, status_code=500, text="error")
        if call_count == 2:
            raise requests.exceptions.Timeout("timeout")
        return _Resp(
            ok=True,
            payload={
                "choices": [{"message": {"role": "assistant", "content": "ok"}}],
            },
        )

    _patch_session_post(monkeypatch, fake_post)
    monkeypatch.setattr(provider_module.time, "sleep", sleeps.append)

    provider = OpenAICompatibleProvider()
    native_messages, state = provider.initialize_request(
        [],
        {
            "config": {
                "base_url": "http://example.com/v1",
                "model": "demo-model",
                "retry_on_status": {"500": [2, 5, 8]},
                "retry_on_timeout": [1, 3, 5],
            }
        },
    )
    _partials, finals, _history, _state = provider.call_api(native_messages, state)

    # attempt 0 → 500: delay from retry_on_status[0] = 2.0
    # attempt 1 → Timeout: delay from retry_on_timeout[1] = 3.0
    assert sleeps == [2.0, 3.0]
    assert finals[0]["content"] == "ok"


def test_parse_retry_on_timeout_from_config():
    provider = OpenAICompatibleProvider()
    _native_messages, state = provider.initialize_request(
        [],
        {
            "config": {
                "base_url": "http://example.com/v1",
                "model": "demo-model",
                "retry_on_timeout": [1, 3, 5],
            }
        },
    )
    assert state["rate_limit_policy"]["retry_on_timeout"] == (1.0, 3.0, 5.0)


def test_parse_retry_on_timeout_string_config():
    provider = OpenAICompatibleProvider()
    _native_messages, state = provider.initialize_request(
        [],
        {
            "config": {
                "base_url": "http://example.com/v1",
                "model": "demo-model",
                "retry_on_timeout": "0.5, 1, 2",
            }
        },
    )
    assert state["rate_limit_policy"]["retry_on_timeout"] == (0.5, 1.0, 2.0)


# --- stream_recovery tests ---


class _BrokenStreamResp(_Resp):
    """Response whose iter_lines raises after emitting some lines."""

    def __init__(self, *, lines_before_break: list[str], error: Exception | None = None):
        super().__init__(ok=True, lines=[])
        self._lines_before_break = lines_before_break
        self._error = error or requests.exceptions.ConnectionError("connection lost")

    def iter_lines(self, decode_unicode: bool = True):
        yield from self._lines_before_break
        raise self._error


def test_stream_recovery_early_only_recovers_when_no_content(monkeypatch):
    provider_module._next_request_time_by_scope.clear()

    broken = _BrokenStreamResp(
        lines_before_break=[
            'data: {"choices":[{"delta":{"role":"assistant","content":""}}]}',
        ],
    )
    good = _Resp(
        ok=True,
        lines=[
            'data: {"choices":[{"delta":{"role":"assistant","content":"recovered"}}]}',
            "data: [DONE]",
        ],
    )
    responses = iter([broken, good])
    sleeps: list[float] = []

    def fake_post(url, headers, json, timeout, stream):
        return next(responses)

    _patch_session_post(monkeypatch, fake_post)
    monkeypatch.setattr(provider_module.time, "sleep", sleeps.append)

    provider = OpenAICompatibleProvider()
    native_messages, state = provider.initialize_request(
        [],
        {
            "config": {
                "base_url": "http://example.com/v1",
                "model": "demo-model",
                "stream_recovery": {"mode": "early_only", "max_retries": 3},
            }
        },
    )
    chunks = list(provider.stream_api(native_messages, state))

    # First (broken) stream yields the empty-content chunk before dying,
    # then recovery re-issues the request and yields the "recovered" chunk.
    assert len(chunks) == 2
    assert chunks[0]["choices"][0]["delta"]["content"] == ""
    assert chunks[1]["choices"][0]["delta"]["content"] == "recovered"


def test_stream_recovery_early_only_does_not_recover_after_content(monkeypatch):
    provider_module._next_request_time_by_scope.clear()

    broken = _BrokenStreamResp(
        lines_before_break=[
            'data: {"choices":[{"delta":{"role":"assistant","content":"part"}}]}',
        ],
    )

    def fake_post(url, headers, json, timeout, stream):
        return broken

    sleeps: list[float] = []
    _patch_session_post(monkeypatch, fake_post)
    monkeypatch.setattr(provider_module.time, "sleep", sleeps.append)

    provider = OpenAICompatibleProvider()
    native_messages, state = provider.initialize_request(
        [],
        {
            "config": {
                "base_url": "http://example.com/v1",
                "model": "demo-model",
                "stream_recovery": {"mode": "early_only", "max_retries": 3},
            }
        },
    )
    with pytest.raises(RuntimeError, match="OpenAI-compatible stream failed"):
        list(provider.stream_api(native_messages, state))


def test_stream_recovery_aggressive_recovers_after_content(monkeypatch):
    provider_module._next_request_time_by_scope.clear()

    broken = _BrokenStreamResp(
        lines_before_break=[
            'data: {"choices":[{"delta":{"role":"assistant","content":"part"}}]}',
        ],
    )
    good = _Resp(
        ok=True,
        lines=[
            'data: {"choices":[{"delta":{"role":"assistant","content":"full"}}]}',
            "data: [DONE]",
        ],
    )
    responses = iter([broken, good])
    sleeps: list[float] = []

    def fake_post(url, headers, json, timeout, stream):
        return next(responses)

    _patch_session_post(monkeypatch, fake_post)
    monkeypatch.setattr(provider_module.time, "sleep", sleeps.append)

    provider = OpenAICompatibleProvider()
    native_messages, state = provider.initialize_request(
        [],
        {
            "config": {
                "base_url": "http://example.com/v1",
                "model": "demo-model",
                "stream_recovery": {"mode": "aggressive", "max_retries": 3},
            }
        },
    )
    chunks = list(provider.stream_api(native_messages, state))

    # First broken stream yields "part", then recovery yields "full"
    assert len(chunks) == 2
    assert chunks[0]["choices"][0]["delta"]["content"] == "part"
    assert chunks[1]["choices"][0]["delta"]["content"] == "full"


def test_stream_recovery_disabled_does_not_recover(monkeypatch):
    provider_module._next_request_time_by_scope.clear()

    broken = _BrokenStreamResp(
        lines_before_break=[
            'data: {"choices":[{"delta":{"role":"assistant","content":""}}]}',
        ],
    )

    def fake_post(url, headers, json, timeout, stream):
        return broken

    _patch_session_post(monkeypatch, fake_post)
    sleeps: list[float] = []
    monkeypatch.setattr(provider_module.time, "sleep", sleeps.append)

    provider = OpenAICompatibleProvider()
    native_messages, state = provider.initialize_request(
        [],
        {
            "config": {
                "base_url": "http://example.com/v1",
                "model": "demo-model",
                "stream_recovery": {"mode": "disabled", "max_retries": 3},
            }
        },
    )
    with pytest.raises(RuntimeError, match="OpenAI-compatible stream failed"):
        list(provider.stream_api(native_messages, state))


def test_stream_recovery_exhausted_retries_raises(monkeypatch):
    provider_module._next_request_time_by_scope.clear()

    call_count = 0

    broken = _BrokenStreamResp(
        lines_before_break=[
            'data: {"choices":[{"delta":{"role":"assistant","content":""}}]}',
        ],
    )

    def fake_post(url, headers, json, timeout, stream):
        nonlocal call_count
        call_count += 1
        return broken

    _patch_session_post(monkeypatch, fake_post)
    sleeps: list[float] = []
    monkeypatch.setattr(provider_module.time, "sleep", sleeps.append)

    provider = OpenAICompatibleProvider()
    native_messages, state = provider.initialize_request(
        [],
        {
            "config": {
                "base_url": "http://example.com/v1",
                "model": "demo-model",
                "stream_recovery": {"mode": "early_only", "max_retries": 2},
            }
        },
    )
    with pytest.raises(RuntimeError, match="OpenAI-compatible stream failed"):
        list(provider.stream_api(native_messages, state))
    # 1 initial + 2 retries = 3 calls total
    assert call_count == 3


def test_stream_recovery_no_config_does_not_recover(monkeypatch):
    provider_module._next_request_time_by_scope.clear()

    broken = _BrokenStreamResp(
        lines_before_break=[],
    )

    def fake_post(url, headers, json, timeout, stream):
        return broken

    _patch_session_post(monkeypatch, fake_post)
    sleeps: list[float] = []
    monkeypatch.setattr(provider_module.time, "sleep", sleeps.append)

    provider = OpenAICompatibleProvider()
    native_messages, state = provider.initialize_request(
        [],
        {"config": {"base_url": "http://example.com/v1", "model": "demo-model"}},
    )
    with pytest.raises(RuntimeError, match="OpenAI-compatible stream failed"):
        list(provider.stream_api(native_messages, state))
    assert sleeps == []


def test_parse_stream_recovery_from_config():
    provider = OpenAICompatibleProvider()
    _native_messages, state = provider.initialize_request(
        [],
        {
            "config": {
                "base_url": "http://example.com/v1",
                "model": "demo-model",
                "stream_recovery": {"mode": "aggressive", "max_retries": 5},
            }
        },
    )
    sr = state["rate_limit_policy"]["stream_recovery"]
    assert sr["mode"] == "aggressive"
    assert sr["max_retries"] == 5


def test_parse_stream_recovery_defaults_to_disabled():
    provider = OpenAICompatibleProvider()
    _native_messages, state = provider.initialize_request(
        [],
        {"config": {"base_url": "http://example.com/v1", "model": "demo-model"}},
    )
    sr = state["rate_limit_policy"]["stream_recovery"]
    assert sr["mode"] == "disabled"
    assert sr["max_retries"] == 0


def test_parse_stream_recovery_invalid_mode_uses_defaults():
    provider = OpenAICompatibleProvider()
    _native_messages, state = provider.initialize_request(
        [],
        {
            "config": {
                "base_url": "http://example.com/v1",
                "model": "demo-model",
                "stream_recovery": {"mode": "invalid_mode", "max_retries": 5},
            }
        },
    )
    sr = state["rate_limit_policy"]["stream_recovery"]
    assert sr["mode"] == "disabled"
    assert sr["max_retries"] == 0
