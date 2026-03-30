from __future__ import annotations

from typing import Any

import reference_openai_compatible_provider.provider as provider_module
from reference_openai_compatible_provider.provider import OpenAICompatibleProvider


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

    monkeypatch.setattr(provider_module.requests, "post", fake_post)
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

    monkeypatch.setattr(provider_module.requests, "post", fake_post)
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

    monkeypatch.setattr(provider_module.requests, "post", fake_post)
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
