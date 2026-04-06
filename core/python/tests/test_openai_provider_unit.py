from __future__ import annotations

import threading
import time

from agent_core.types import ProviderRequestCancelled
from plugins.openai_provider import OpenAICompatibleProvider


class _BlockingResponse:
    def __init__(self) -> None:
        self.closed = threading.Event()
        self.encoding = "utf-8"
        self.status_code = 200
        self.reason = "OK"

    def close(self) -> None:
        self.closed.set()

    def json(self):
        while not self.closed.wait(0.05):
            continue
        raise RuntimeError("response closed")

    def raise_for_status(self) -> None:
        return None

    def iter_lines(self, decode_unicode: bool = True):
        _ = decode_unicode
        while not self.closed.wait(0.05):
            continue
        raise RuntimeError("response closed")


class _BlockingSession:
    def __init__(self) -> None:
        self.response: _BlockingResponse | None = None
        self.stream_calls: list[bool] = []

    def post(self, *args, **kwargs):
        _ = args
        stream = bool(kwargs.get("stream"))
        self.stream_calls.append(stream)
        self.response = _BlockingResponse()
        return self.response

    def close(self) -> None:
        if self.response is not None:
            self.response.close()


def test_cancel_request_returns_false_for_unknown_request():
    provider = OpenAICompatibleProvider()

    assert provider.cancel_request("missing") is False


def test_stream_api_can_be_cancelled_by_request_id(monkeypatch):
    provider = OpenAICompatibleProvider()
    session = _BlockingSession()
    monkeypatch.setattr("plugins.openai_provider.requests.Session", lambda: session)

    state = provider.init({"model": "test-model"})
    native_messages, state = provider.initialize_request(
        [{"role": "user", "content": "hello"}],
        state,
        request_id="stream-request",
    )

    outcome: dict[str, object] = {}

    def _consume() -> None:
        try:
            list(
                provider.stream_api(
                    native_messages,
                    state,
                    request_id="stream-request",
                )
            )
        except Exception as exc:  # noqa: BLE001
            outcome["error"] = exc

    worker = threading.Thread(target=_consume)
    worker.start()

    deadline = time.time() + 5.0
    while time.time() < deadline:
        if provider.cancel_request("stream-request"):
            break
        time.sleep(0.02)
    else:
        raise AssertionError("stream request was never registered as active")

    worker.join(timeout=5.0)
    assert not worker.is_alive()
    assert isinstance(outcome.get("error"), ProviderRequestCancelled)


def test_call_api_can_be_cancelled_by_request_id(monkeypatch):
    provider = OpenAICompatibleProvider()
    session = _BlockingSession()
    monkeypatch.setattr("plugins.openai_provider.requests.Session", lambda: session)

    state = provider.init({"model": "test-model"})
    native_messages, state = provider.initialize_request(
        [{"role": "user", "content": "hello"}],
        state,
        request_id="call-request",
    )

    outcome: dict[str, object] = {}

    def _consume() -> None:
        try:
            provider.call_api(
                native_messages,
                state,
                request_id="call-request",
            )
        except Exception as exc:  # noqa: BLE001
            outcome["error"] = exc

    worker = threading.Thread(target=_consume)
    worker.start()

    deadline = time.time() + 5.0
    while time.time() < deadline:
        if provider.cancel_request("call-request"):
            break
        time.sleep(0.02)
    else:
        raise AssertionError("call request was never registered as active")

    worker.join(timeout=5.0)
    assert not worker.is_alive()
    assert isinstance(outcome.get("error"), ProviderRequestCancelled)