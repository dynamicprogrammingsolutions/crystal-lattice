"""Bridge client for routing HTTP requests via the Elixir bridge.

This module implements the *server* side of the bridge protocol used by
the React Native client and the Elixir bridge service from the
``bonjour-example-1`` project. It is heavily inspired by the
``BridgeClient`` class in ``server-python/bonjour_server.py`` but
adapted to proxy requests to a local FastAPI server instead of an
in-memory :class:`DataStore`.

High-level behaviour
--------------------

* Connect to the bridge WebSocket (Phoenix protocol) as a ``type=server``
  client.
* Join the ``server:{server_id}`` channel and register this server with a
  human-readable display name and optional location.
* Receive ``http_request`` messages from paired clients, forward them to
  the local HTTP API (FastAPI) via :mod:`httpx`, and respond with
  ``http_response`` messages containing status, headers, and body.

The FastAPI application wires this client up from an ``@app.on_event``
startup handler using environment variables, so that the bridge can be
enabled or disabled without changing application code.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

import asyncio
import json
import logging
import os
import socket
import uuid

try:  # Optional import; the package is declared as a dependency.
    import websockets  # type: ignore[import-not-found]
except Exception:  # pragma: no cover - handled at runtime
    websockets = None  # type: ignore[assignment]

import httpx


log = logging.getLogger(__name__)


@dataclass
class BridgeConfig:
    """Configuration for :class:`BridgeClient`.

    ``local_http_base`` should be the base URL of the FastAPI server as
    seen from where this process is running, for example
    ``"http://127.0.0.1:8000"``.
    """

    bridge_url: str
    server_id: str
    display_name: str
    computer_name: str
    location: Optional[str]
    local_http_base: str

    ws_max_size_bytes: Optional[int] = 16 * 1024 * 1024
    http_timeout_seconds: float = 120.0
    # Keep a safe headroom so the Phoenix envelope stays < ~1MiB.
    request_chunk_size_bytes: int = 900 * 1024
    request_chunking_threshold_bytes: int = 256 * 1024
    response_chunking_threshold_bytes: int = 256 * 1024
    max_body_bytes: int = 10 * 1024 * 1024

    debug: bool = False


class BridgeClient:
    """WebSocket client that proxies bridge HTTP requests to FastAPI.

    The lifecycle for normal use is::

        client = BridgeClient(config)
        asyncio.create_task(client.run())

    The :meth:`run` coroutine will connect once and then process
    messages until the WebSocket is closed or an error occurs. When the
    FastAPI server is shutting down, :meth:`stop` should be awaited to
    close the connection cleanly.
    """

    def __init__(self, config: BridgeConfig, *, test_mode: bool = False) -> None:
        self.config = config
        self.test_mode = test_mode

        self._ws: Optional[websockets.WebSocketClientProtocol] = None  # type: ignore[name-defined]
        self._connected: bool = False
        self._registered: bool = False
        self._ref_counter: int = 0
        self._stopped: bool = False

        # For tests / observability
        self.pairing_code: Optional[str] = None
        self.session_id: Optional[str] = None

        # Chunked HTTP request buffering keyed by request_id.
        self._chunked_requests: Dict[str, Dict[str, Any]] = {}

    def _debug_print(self, message: str) -> None:
        if self.config.debug and not self.test_mode:
            print(f"[bridge][debug] {message}")

    # ------------------------------------------------------------------
    # Phoenix wire protocol helpers
    # ------------------------------------------------------------------

    def _next_ref(self) -> str:
        self._ref_counter += 1
        return str(self._ref_counter)

    def _phoenix_message(self, topic: str, event: str, payload: Dict[str, Any]) -> str:
        return json.dumps(
            {
                "topic": topic,
                "event": event,
                "payload": payload,
                "ref": self._next_ref(),
            }
        )

    # ------------------------------------------------------------------
    # Public lifecycle
    # ------------------------------------------------------------------

    async def run(self) -> None:
        """Connect to the bridge and process messages until closed.

        The method returns when the WebSocket is closed or an unrecoverable
        error occurs. It is designed to be used as a background task started
        from a FastAPI startup hook.
        """

        if websockets is None:  # pragma: no cover - environment issue
            log.warning("websockets is not installed; bridge client disabled")
            if not self.test_mode:
                print("[bridge] websockets is not installed; bridge client disabled")
            return

        ws_url = f"{self.config.bridge_url}?type=server"
        # Keep trying to connect until stopped; this lets the server recover
        # from transient bridge outages without a full restart.
        backoff = 1.0

        while not self._stopped:
            log.info("Connecting to bridge at %s", ws_url)
            if not self.test_mode:
                print(
                    f"[bridge] connecting to {ws_url} as server '{self.config.display_name}'…"
                )

            try:
                self._ws = await websockets.connect(
                    ws_url,
                    max_size=self.config.ws_max_size_bytes,
                )
                self._connected = True
                log.info("Connected to bridge WebSocket")
                if not self.test_mode:
                    print("[bridge] connected to WebSocket")

                await self._join_channel()
                await self._register_server()

                await self._handle_messages()
            except asyncio.CancelledError:  # pragma: no cover - cooperative shutdown
                raise
            except Exception:
                log.exception("Bridge client error")
                if not self.test_mode:
                    print("[bridge] error in bridge client; will retry shortly")
            finally:
                await self._close_ws()
                self._connected = False

            if self._stopped:
                break

            await asyncio.sleep(backoff)

    async def stop(self) -> None:
        """Request graceful shutdown of the bridge connection."""

        self._stopped = True
        await self._close_ws()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _close_ws(self) -> None:
        ws = self._ws
        self._ws = None
        if ws is None:
            return
        try:
            await ws.close()
        except Exception:  # pragma: no cover - defensive
            log.debug("Error while closing bridge WebSocket", exc_info=True)

    async def _join_channel(self) -> None:
        assert self._ws is not None
        join_msg = self._phoenix_message(f"server:{self.config.server_id}", "phx_join", {})
        await self._ws.send(join_msg)

        raw = await self._ws.recv()
        data = json.loads(raw)
        if data.get("event") == "phx_reply" and data.get("payload", {}).get("status") == "ok":
            log.info("Joined server channel server:%s", self.config.server_id)
            if not self.test_mode:
                print(f"[bridge] joined channel server:{self.config.server_id}")
        else:  # pragma: no cover - protocol error
            log.warning("Unexpected join reply from bridge: %s", data)
            if not self.test_mode:
                print("[bridge] unexpected join reply from bridge; see logs for details")

    async def _register_server(self) -> None:
        assert self._ws is not None
        payload = {
            "server_id": self.config.server_id,
            "display_name": self.config.display_name,
            "computer_name": self.config.computer_name,
            "location": self.config.location,
        }
        msg = self._phoenix_message(f"server:{self.config.server_id}", "register", payload)
        await self._ws.send(msg)

        raw = await self._ws.recv()
        data = json.loads(raw)
        if data.get("event") == "phx_reply" and data.get("payload", {}).get("status") == "ok":
            self._registered = True
            log.info("Registered server with bridge as '%s'", self.config.display_name)
            if not self.test_mode:
                print(
                    f"[bridge] registered as '{self.config.display_name}' "
                    f"on computer '{self.config.computer_name}'"
                )
                if self.config.location:
                    print(f"[bridge] location: {self.config.location}")
                print(f"[bridge] local HTTP base: {self.config.local_http_base}")
                print("[bridge] waiting for pairing requests…")
        else:  # pragma: no cover - protocol error
            log.warning("Unexpected register reply from bridge: %s", data)
            if not self.test_mode:
                print("[bridge] unexpected register reply from bridge; see logs for details")

    async def _handle_messages(self) -> None:
        """Main message loop: handle events from the bridge."""

        assert self._ws is not None
        if not self.test_mode:
            log.info("Listening for messages from bridge…")
            print("[bridge] listening for messages from bridge…")

        try:
            async for message in self._ws:
                data = json.loads(message)
                event = data.get("event")
                payload = data.get("payload") or {}

                if event == "pairing_requested":
                    self._handle_pairing_requested(payload)
                elif event == "paired":
                    self._handle_paired(payload)
                elif event == "http_request":
                    await self._handle_http_request(payload)
                elif event == "http_request_init":
                    await self._handle_http_request_init(payload)
                elif event == "http_request_chunk":
                    await self._handle_http_request_chunk(payload)
                elif event == "http_request_end":
                    await self._handle_http_request_end(payload)
                elif event == "phx_reply":
                    # Replies are handled synchronously where needed.
                    continue

                if self._stopped:
                    break
        except asyncio.CancelledError:  # pragma: no cover - cooperative shutdown
            raise
        except Exception:
            log.exception("Error while handling messages from bridge")

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def _handle_pairing_requested(self, payload: Dict[str, Any]) -> None:
        code = payload.get("code")
        self.pairing_code = code

        if self.test_mode:
            log.info("Bridge pairing requested with code %s", code)
            return

        log.info("Bridge pairing requested; code=%s", code)
        # User-facing banner so the 6-digit code is always visible even
        # when logging is not configured for this module.
        print("\n" + "=" * 70)
        print("PAIRING CODE: " + str(code))
        print("=" * 70)
        print("A client is requesting to pair with this server.")
        print("\nEnter this 6-digit code in the client app:")
        print(f"\n    >>> {code} <<<")
        print("\nOnce paired, the client will be able to send HTTP requests ")
        print("through the bridge to this server.")
        print("=" * 70 + "\n")

    def _handle_paired(self, payload: Dict[str, Any]) -> None:
        session_id = payload.get("session_id")
        self.session_id = session_id

        if self.test_mode:
            log.info("Bridge pairing completed; session_id=%s", session_id)
            return

        log.info("Client paired successfully; session_id=%s", session_id)
        print("\n" + "=" * 70)
        print("✅ Client paired successfully")
        print("=" * 70)
        print(f"Session ID: {session_id}")
        print("\nThe client can now make HTTP requests through the bridge.")
        print("Use the mobile app to issue requests to this server.")
        print("=" * 70 + "\n")

    async def _handle_http_request(self, payload: Dict[str, Any]) -> None:
        """Handle ``http_request`` forwarded from the bridge."""

        if self._ws is None:  # pragma: no cover - defensive
            return

        request_id = payload.get("request_id")
        method = (payload.get("method") or "GET").upper()
        path = payload.get("path") or "/"
        body = payload.get("body")

        if self.test_mode:
            log.info("Bridge HTTP %s %s (request_id=%s)", method, path, request_id)
        else:
            self._debug_print(f"http_request request_id={request_id} {method} {path}")

        headers = payload.get("headers") or {}
        response = await self.execute_local_request(method, path, body, headers=headers)
        await self._send_http_response_maybe_chunked(
            str(request_id),
            int(response["status"]),
            response.get("headers") or {},
            response.get("body") or "",
        )

    async def _handle_http_request_init(self, payload: Dict[str, Any]) -> None:
        if self._ws is None:  # pragma: no cover - defensive
            return

        request_id = payload.get("request_id")
        method = (payload.get("method") or "GET").upper()
        path = payload.get("path") or "/"
        headers = payload.get("headers") or {}

        if not isinstance(request_id, str) or not request_id:
            return

        self._debug_print(
            f"http_request_init request_id={request_id} {method} {path} body_length_bytes={payload.get('body_length_bytes')}"
        )

        self._chunked_requests[request_id] = {
            "method": method,
            "path": path,
            "headers": headers,
            "chunks": [],
            "bytes_received": 0,
            "error": None,
        }

    async def _handle_http_request_chunk(self, payload: Dict[str, Any]) -> None:
        request_id = payload.get("request_id")
        seq = payload.get("seq")
        chunk = payload.get("chunk")

        if not isinstance(request_id, str) or not request_id:
            return

        state = self._chunked_requests.get(request_id)
        if state is None:
            return

        if state.get("error") is not None:
            return

        if not isinstance(seq, int) or seq != len(state["chunks"]):
            state["error"] = {
                "status": 400,
                "body": json.dumps({"error": "invalid_chunk_sequence"}),
            }
            # Stop buffering to avoid unbounded memory growth.
            state["chunks"] = []
            return

        if not isinstance(chunk, str):
            chunk = ""

        # Enforce a maximum total body size.
        chunk_size = len(chunk.encode("utf-8"))
        next_size = int(state.get("bytes_received") or 0) + chunk_size
        if next_size > self.config.max_body_bytes:
            state["error"] = {
                "status": 413,
                "body": json.dumps({"error": "payload_too_large"}),
            }
            state["chunks"] = []
            return

        state["chunks"].append(chunk)
        state["bytes_received"] = next_size

        self._debug_print(
            f"http_request_chunk request_id={request_id} seq={seq} bytes_received={next_size}"
        )

    async def _handle_http_request_end(self, payload: Dict[str, Any]) -> None:
        if self._ws is None:  # pragma: no cover - defensive
            return

        request_id = payload.get("request_id")
        final_seq = payload.get("final_seq")

        if not isinstance(request_id, str) or not request_id:
            return

        self._debug_print(
            f"http_request_end request_id={request_id} final_seq={final_seq}"
        )

        state = self._chunked_requests.pop(request_id, None)
        if state is None:
            return

        error = state.get("error")
        chunks = state.get("chunks") or []

        if not isinstance(final_seq, int) or final_seq != len(chunks) - 1:
            error = {
                "status": 400,
                "body": json.dumps({"error": "invalid_final_seq"}),
            }

        if error is not None:
            await self._send_http_response(request_id, error["status"], {}, error["body"])
            return

        method = state.get("method") or "GET"
        path = state.get("path") or "/"
        headers = state.get("headers") or {}
        body = "".join(chunks)

        self._debug_print(
            f"http_request_reassembled request_id={request_id} body_bytes={len(body.encode('utf-8'))}"
        )

        response = await self.execute_local_request(method, path, body, headers=headers)
        await self._send_http_response_maybe_chunked(
            request_id,
            response["status"],
            response.get("headers") or {},
            response.get("body") or "",
        )

    async def _send_http_response(self, request_id: str, status: int, headers: Dict[str, Any], body: str) -> None:
        assert self._ws is not None
        msg = self._phoenix_message(
            f"server:{self.config.server_id}",
            "http_response",
            {
                "request_id": request_id,
                "status": status,
                "headers": headers,
                "body": body,
            },
        )
        await self._ws.send(msg)

    async def _send_http_response_maybe_chunked(
        self,
        request_id: str,
        status: int,
        headers: Dict[str, Any],
        body: str,
    ) -> None:
        assert self._ws is not None

        body_bytes = len(body.encode("utf-8"))
        if body_bytes <= self.config.response_chunking_threshold_bytes:
            self._debug_print(
                f"http_response request_id={request_id} status={status} body_bytes={body_bytes} threshold={self.config.response_chunking_threshold_bytes}"
            )
            await self._send_http_response(request_id, status, headers, body)
            return

        self._debug_print(
            f"http_response_chunked request_id={request_id} status={status} body_bytes={body_bytes} threshold={self.config.response_chunking_threshold_bytes} chunk_size_bytes={self.config.request_chunk_size_bytes}"
        )

        init_msg = self._phoenix_message(
            f"server:{self.config.server_id}",
            "http_response_init",
            {
                "request_id": request_id,
                "status": status,
                "headers": headers,
                "body_encoding": "utf8",
                "body_length_bytes": body_bytes,
                "chunk_size_bytes": self.config.request_chunk_size_bytes,
            },
        )
        await self._ws.send(init_msg)

        chunk_size = max(1, int(self.config.request_chunk_size_bytes - 2048))
        chunks = [body[i : i + chunk_size] for i in range(0, len(body), chunk_size)]
        for idx, chunk in enumerate(chunks):
            chunk_msg = self._phoenix_message(
                f"server:{self.config.server_id}",
                "http_response_chunk",
                {
                    "request_id": request_id,
                    "seq": idx,
                    "chunk": chunk,
                },
            )
            await self._ws.send(chunk_msg)

            self._debug_print(f"http_response_chunk request_id={request_id} seq={idx}/{len(chunks) - 1}")

        end_msg = self._phoenix_message(
            f"server:{self.config.server_id}",
            "http_response_end",
            {
                "request_id": request_id,
                "final_seq": len(chunks) - 1,
            },
        )
        await self._ws.send(end_msg)

    # ------------------------------------------------------------------
    # Local HTTP proxying
    # ------------------------------------------------------------------

    async def execute_local_request(
        self,
        method: str,
        path: str,
        body: Optional[str],
        *,
        headers: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Execute an HTTP request against the local FastAPI server.

        ``path`` is appended to the configured ``local_http_base``; it is
        expected to be an absolute path such as ``"/api/data"`` or
        ``"/sessions"``.
        """

        base = self.config.local_http_base.rstrip("/")
        if not path.startswith("/"):
            path = "/" + path
        url = base + path

        outgoing_headers: Dict[str, str] = {}
        if headers and isinstance(headers, dict):
            for key, value in headers.items():
                if not isinstance(key, str):
                    continue
                if isinstance(value, str):
                    outgoing_headers[key] = value
        content: Optional[bytes] = None

        if body is not None:
            # The bridge payload always represents JSON as a UTF-8 string.
            if not any(k.lower() == "content-type" for k in outgoing_headers.keys()):
                outgoing_headers["Content-Type"] = "application/json"
            content = body.encode("utf-8")

        try:
            async with httpx.AsyncClient(timeout=self.config.http_timeout_seconds) as client:
                resp = await client.request(method, url, headers=outgoing_headers, content=content)

            return {
                "status": resp.status_code,
                "headers": dict(resp.headers),
                "body": resp.text,
            }
        except Exception as exc:  # pragma: no cover - environment / connectivity
            log.exception("Error executing local HTTP request via bridge: %s", exc)
            return {
                "status": 500,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": str(exc)}),
            }


def create_bridge_client_from_env() -> Optional[BridgeClient]:
    """Create a :class:`BridgeClient` from environment variables.

    Recognised variables::

        BRIDGE_URL            WebSocket URL to the bridge, e.g.
                              ``ws://localhost:4000/ws/websocket``.
        BRIDGE_DISPLAY_NAME   Optional human-friendly server name
                              (default: ``Agent Terminal App``).
        BRIDGE_LOCATION       Optional freeform location string
                              (e.g., ``"Office"``).
        BRIDGE_LOCAL_HTTP_BASE
                              Base URL of the local FastAPI server as
                              seen from this process
                              (default: ``http://127.0.0.1:<PORT>`` where
                              PORT comes from ``SERVER_PORT`` or ``8000``).

    Returns ``None`` when ``BRIDGE_URL`` is not defined so that callers
    can treat bridge support as entirely optional.
    """

    bridge_url = os.getenv("BRIDGE_URL")
    if not bridge_url:
        return None

    display_name = os.getenv("BRIDGE_DISPLAY_NAME") or "Agent Terminal App"
    location = os.getenv("BRIDGE_LOCATION")

    # Default to a local uvicorn instance when BRIDGE_LOCAL_HTTP_BASE is
    # not provided explicitly.
    local_http_base = os.getenv("BRIDGE_LOCAL_HTTP_BASE")
    if not local_http_base:
        port = int(os.getenv("SERVER_PORT", os.getenv("PORT", "8000")))
        host = os.getenv("SERVER_HOST", "127.0.0.1")
        local_http_base = f"http://{host}:{port}"

    server_id = os.getenv("BRIDGE_SERVER_ID") or str(uuid.uuid4())
    computer_name = socket.gethostname() or "localhost"

    cfg = BridgeConfig(
        bridge_url=bridge_url,
        server_id=server_id,
        display_name=display_name,
        computer_name=computer_name,
        location=location,
        local_http_base=local_http_base,
        ws_max_size_bytes=_parse_optional_int(os.getenv("BRIDGE_WS_MAX_SIZE_BYTES"), default=16 * 1024 * 1024),
        http_timeout_seconds=_parse_float(os.getenv("BRIDGE_HTTP_TIMEOUT_SECONDS"), default=120.0),
        request_chunk_size_bytes=int(os.getenv("BRIDGE_HTTP_CHUNK_SIZE_BYTES", str(900 * 1024))),
        request_chunking_threshold_bytes=int(os.getenv("BRIDGE_HTTP_CHUNK_THRESHOLD_BYTES", str(256 * 1024))),
        response_chunking_threshold_bytes=int(os.getenv("BRIDGE_HTTP_CHUNK_THRESHOLD_BYTES", str(256 * 1024))),
        max_body_bytes=int(os.getenv("BRIDGE_HTTP_MAX_BODY_BYTES", str(10 * 1024 * 1024))),
        debug=os.getenv("BRIDGE_DEBUG", "").strip() in {"1", "true", "True", "yes", "YES"},
    )

    return BridgeClient(cfg)


def _parse_optional_int(value: Optional[str], *, default: Optional[int]) -> Optional[int]:
    if value is None or value == "":
        return default


def _parse_float(value: Optional[str], *, default: float) -> float:
    if value is None or value == "":
        return default
    try:
        return float(value)
    except ValueError:
        return default
    try:
        return int(value)
    except ValueError:
        return default
