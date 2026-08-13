from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import threading
import time

import pytest

from agent_app.application_future import AsyncRuntimeHost
from openai_responses_plugins.openai_responses_native_compaction import (
    CancellableAsyncOpenAIResponsesCompactionTransport,
)


class _QuietServer(ThreadingHTTPServer):
    def handle_error(self, request, client_address) -> None:
        _ = request, client_address


class _DelayedCompactHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    mode = "before_headers"
    entered = threading.Event()
    release = threading.Event()

    def log_message(self, format, *args) -> None:
        _ = format, args

    def do_POST(self) -> None:
        length = int(self.headers.get("content-length", "0"))
        if length:
            self.rfile.read(length)
        type(self).entered.set()
        if self.path.endswith("/responses"):
            payload = (
                'event: response.completed\n'
                'data: {"type":"response.completed","response":'
                '{"id":"resp_test","output":[{"type":"compaction",'
                '"encrypted_content":"opaque"}]}}\n\n'
                "data: [DONE]\n\n"
            ).encode()
            content_type = "text/event-stream"
        else:
            payload = json.dumps(
                {
                    "id": "cmp_test",
                    "created_at": 1,
                    "object": "response.compaction",
                    "output": [],
                    "usage": {
                        "input_tokens": 0,
                        "output_tokens": 0,
                        "total_tokens": 0,
                    },
                }
            ).encode()
            content_type = "application/json"
        if type(self).mode == "after_headers":
            self.send_response(200)
            self.send_header("content-type", content_type)
            self.send_header("content-length", str(len(payload)))
            self.end_headers()
            self.wfile.flush()
        type(self).release.wait(10)
        try:
            if type(self).mode == "before_headers":
                self.send_response(200)
                self.send_header("content-type", content_type)
                self.send_header("content-length", str(len(payload)))
                self.end_headers()
            self.wfile.write(payload)
        except (BrokenPipeError, ConnectionResetError):
            pass


@pytest.mark.parametrize("mode", ["before_headers", "after_headers"])
@pytest.mark.parametrize("auth_mode", ["api", "chatgpt"])
def test_async_compact_transport_cancels_delayed_http_exchange(
    mode: str,
    auth_mode: str,
) -> None:
    _DelayedCompactHandler.mode = mode
    _DelayedCompactHandler.entered = threading.Event()
    _DelayedCompactHandler.release = threading.Event()
    server = _QuietServer(("127.0.0.1", 0), _DelayedCompactHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    runtime = AsyncRuntimeHost()
    transport = CancellableAsyncOpenAIResponsesCompactionTransport(
        run_awaitable_blocking=runtime.run_blocking,
        max_retries=0,
    )
    base_url = f"http://127.0.0.1:{server.server_port}/v1"
    if auth_mode == "chatgpt":
        transport.configure(
            {
                "auth_mode": "chatgpt",
                "_openai_responses_effective_auth_mode": "chatgpt",
                "chatgpt_access_token": "test",
                "chatgpt_base_url": base_url,
            }
        )
    else:
        transport.configure(
            {
                "api_key": "test",
                "base_url": base_url,
            }
        )
    outcome: dict[str, BaseException] = {}

    def _run() -> None:
        try:
            transport.compact(
                model="gpt-5-mini",
                input_items=[
                    {
                        "type": "message",
                        "role": "user",
                        "content": [{"type": "input_text", "text": "hello"}],
                    }
                ],
                instructions=None,
                timeout=30,
            )
        except BaseException as exc:
            outcome["error"] = exc

    worker = threading.Thread(target=_run)
    worker.start()
    assert _DelayedCompactHandler.entered.wait(5)
    started = time.monotonic()
    transport.cancel()
    worker.join(timeout=3)
    elapsed = time.monotonic() - started

    _DelayedCompactHandler.release.set()
    runtime.close()
    server.shutdown()
    server.server_close()

    assert not worker.is_alive()
    assert elapsed < 3
    assert isinstance(outcome.get("error"), BaseException)


def test_async_compact_transport_requires_configuration() -> None:
    runtime = AsyncRuntimeHost()
    transport = CancellableAsyncOpenAIResponsesCompactionTransport(
        run_awaitable_blocking=runtime.run_blocking,
        max_retries=0,
    )

    try:
        with pytest.raises(RuntimeError, match="must be configured before use"):
            transport.compact(
                model="gpt-5-mini",
                input_items=[],
                instructions=None,
                timeout=1,
            )
    finally:
        runtime.close()
