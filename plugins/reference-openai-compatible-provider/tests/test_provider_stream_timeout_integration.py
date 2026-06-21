"""Integration tests for OpenAI-compatible provider streaming timeout behavior.

These tests start a real local HTTP server and exercise the full application
layer via :class:`agent_app.application_future.AgentApplication`. They verify
that the configured ``timeout`` is interpreted by ``requests`` as the
read-timeout silence window: it is not a total-response cap, but it is
enforced both before the first byte (TTFB) and between consecutive bytes.
"""

from __future__ import annotations

import json
import threading
import time
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Iterator

import pytest

from agent_app.application_future import AgentApplication
from agent_app.events import InMemoryEventStore


class _TimeoutTestHandler(BaseHTTPRequestHandler):
    """SSE streaming handler that sleeps to simulate slow servers."""

    def log_message(self, format: str, *args: Any) -> None:  # pragma: no cover
        return

    def _read_model(self) -> str:
        length = int(self.headers.get("Content-Length", 0))
        if length <= 0:
            return ""
        body = self.rfile.read(length)
        try:
            payload = json.loads(body.decode("utf-8"))
        except Exception:
            return ""
        return str(payload.get("model", ""))

    def _send_chunk(self, data: bytes) -> None:
        self.wfile.write(f"{len(data):x}\r\n".encode())
        self.wfile.write(data)
        self.wfile.write(b"\r\n")
        self.wfile.flush()

    def _sse_event(self, obj: dict[str, Any] | str) -> bytes:
        if isinstance(obj, dict):
            line = f"data: {json.dumps(obj)}\n\n"
        else:
            line = f"data: {obj}\n\n"
        return line.encode("utf-8")

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/v1/chat/completions":
            self.send_response(404)
            self.end_headers()
            return

        model = self._read_model()

        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Transfer-Encoding", "chunked")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()

        try:
            if model == "continuous-2s":
                # Send a chunk every ~0.25s for ~2s. With timeout=1s this must succeed.
                for i in range(8):
                    time.sleep(0.25)
                    self._send_chunk(
                        self._sse_event(
                            {"choices": [{"delta": {"content": f"part{i}"}}]}
                        )
                    )
                self._send_chunk(self._sse_event("[DONE]"))
                self._send_chunk(b"")

            elif model == "slow-ttfb":
                # Sleep longer than the 1s read timeout before sending any byte.
                time.sleep(1.5)
                self._send_chunk(
                    self._sse_event({"choices": [{"delta": {"content": "late"}}]})
                )
                self._send_chunk(self._sse_event("[DONE]"))
                self._send_chunk(b"")

            elif model == "slow-interchunk":
                # First chunk arrives immediately, then silence exceeds the timeout.
                self._send_chunk(
                    self._sse_event({"choices": [{"delta": {"content": "first"}}]})
                )
                time.sleep(1.5)
                self._send_chunk(
                    self._sse_event({"choices": [{"delta": {"content": "second"}}]})
                )
                self._send_chunk(self._sse_event("[DONE]"))
                self._send_chunk(b"")

            else:
                # Minimal immediate success fallback.
                self._send_chunk(
                    self._sse_event({"choices": [{"delta": {"content": "ok"}}]})
                )
                self._send_chunk(self._sse_event("[DONE]"))
                self._send_chunk(b"")

        except (BrokenPipeError, ConnectionResetError, OSError):
            # Client closed the connection (e.g. because of a timeout). Expected.
            pass


@contextmanager
def _local_streaming_server() -> Iterator[str]:
    server = ThreadingHTTPServer(("127.0.0.1", 0), _TimeoutTestHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address
        yield f"http://{host}:{port}/v1"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def _write_config(tmp_path: Path, base_url: str, model: str) -> Path:
    cfg: dict[str, Any] = {
        "plugin_cache_dir": str(tmp_path / ".plugin_cache"),
        "providers": {
            "test_provider": {
                "provider": "reference_openai_compatible",
                "base_url": base_url,
                "model": model,
                "timeout": 1,
                "retry_on_timeout": [],
                "min_request_interval_seconds": 0,
                "stream_recovery": {"mode": "disabled"},
            }
        },
        "plugins": [
            "reference_openai_compatible_provider.provider.OpenAICompatibleProvider",
            "reference_openai_compatible_provider.tools_extension.OpenAICompatibleToolsExtension",
            "reference_openai_compatible_provider.reasoning_extension.OpenAICompatibleReasoningExtension",
            "reference_openai_compatible_provider.usage_extension.OpenAICompatibleUsageExtension",
        ],
        "agents": {"default": {"provider": "test_provider"}},
    }
    config_path = tmp_path / "config_stream_timeout.json"
    config_path.write_text(json.dumps(cfg), encoding="utf-8")
    return config_path


def _send_streaming_request(app: AgentApplication) -> list[dict[str, Any]]:
    core, base_config, session = app.create_session("default")
    session = core.add_message(session, "user", "hello", {}, base_config)
    app.save_session(session)
    return list(app.send_request(core, session, base_config, stream=True))


pytestmark = [pytest.mark.integration]


@pytest.mark.timeout(20)
def test_stream_timeout_not_hit_when_bytes_arrive_continuously(tmp_path: Path) -> None:
    """A 1s read timeout must not fail when chunks keep arriving for ~2s."""
    with _local_streaming_server() as base_url:
        config_path = _write_config(tmp_path, base_url, "continuous-2s")
        app = AgentApplication(
            str(config_path),
            str(tmp_path / "sessions"),
            event_store=InMemoryEventStore(),
        )
        try:
            start = time.monotonic()
            events = _send_streaming_request(app)
            elapsed = time.monotonic() - start

            assert not [e for e in events if e.get("type") == "error"]

            partials = [e for e in events if e.get("type") == "partial"]
            assert len(partials) == 8
            messages = [e.get("message") or {} for e in partials]
            assert [m.get("content") for m in messages] == [
                f"part{i}" for i in range(8)
            ]

            finals = [e for e in events if e.get("type") == "final"]
            assert finals

            assert elapsed >= 1.8, f"expected ~2s of streaming, got {elapsed:.2f}s"
            assert elapsed < 4.0, f"streaming took too long: {elapsed:.2f}s"
        finally:
            app.close()


@pytest.mark.timeout(20)
def test_stream_timeout_hit_when_ttfb_exceeds_timeout(tmp_path: Path) -> None:
    """A 1s read timeout must raise when the first byte takes >1s."""
    with _local_streaming_server() as base_url:
        config_path = _write_config(tmp_path, base_url, "slow-ttfb")
        app = AgentApplication(
            str(config_path),
            str(tmp_path / "sessions"),
            event_store=InMemoryEventStore(),
        )
        try:
            start = time.monotonic()
            events = _send_streaming_request(app)
            elapsed = time.monotonic() - start

            error_events = [e for e in events if e.get("type") == "error"]
            assert error_events, "expected an error event for TTFB timeout"
            detail = " ".join(str(e.get("detail", "")) for e in error_events)
            assert (
                "OpenAI-compatible stream failed" in detail
                or "Read timed out" in detail
            )

            # The read timeout fires after ~1s; allow generous margin for thread scheduling.
            assert 0.8 <= elapsed < 2.5, f"unexpected elapsed time: {elapsed:.2f}s"
        finally:
            app.close()


@pytest.mark.timeout(20)
def test_stream_timeout_hit_when_interchunk_gap_exceeds_timeout(tmp_path: Path) -> None:
    """A 1s read timeout must raise when silence between chunks exceeds 1s."""
    with _local_streaming_server() as base_url:
        config_path = _write_config(tmp_path, base_url, "slow-interchunk")
        app = AgentApplication(
            str(config_path),
            str(tmp_path / "sessions"),
            event_store=InMemoryEventStore(),
        )
        try:
            start = time.monotonic()
            events = _send_streaming_request(app)
            elapsed = time.monotonic() - start

            error_events = [e for e in events if e.get("type") == "error"]
            assert error_events, "expected an error event for interchunk timeout"
            detail = " ".join(str(e.get("detail", "")) for e in error_events)
            assert (
                "OpenAI-compatible stream failed" in detail
                or "Read timed out" in detail
            )

            # First chunk is immediate, then ~1s of silence triggers the timeout.
            assert 0.8 <= elapsed < 2.5, f"unexpected elapsed time: {elapsed:.2f}s"
        finally:
            app.close()
