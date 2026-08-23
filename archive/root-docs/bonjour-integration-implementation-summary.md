> Archived historical implementation summary. It is not current implementation
> guidance. See the [archive index](../README.md) and current
> [application documentation](../../application/python/README.md).

s a developer, I’ll keep it straightforward and clear!
Here’s what I implemented for steps 3–5, and how to use it.

---

## Step 3 – Bonjour/mDNS advertising for the FastAPI server

### 3.1 New dependency

In `application/python/pyproject.toml`:

```toml
[project]
dependencies = [
    "agent-core>=0.3.0",
    "fastapi",
    "uvicorn[standard]",
    "prompt_toolkit>=3.0.0",
    "python-dotenv>=1.0.0",
    "zeroconf>=0.132.2",      # NEW
    "websockets>=12.0",       # also used in Step 5
    "httpx>=0.27.0",          # also used in Step 5
]
```

`zeroconf` is used for Bonjour/mDNS; `websockets` and `httpx` are for the bridge.

---

### 3.2 Bonjour helper module

**File:** `application/python/agent_terminal_app/bonjour.py`

Key parts:

```python
from dataclasses import dataclass
from typing import Any, Optional
import logging
import socket

try:
    from zeroconf import ServiceInfo, Zeroconf  # type: ignore[import-not-found]
except Exception:  # graceful fallback when zeroconf missing
    ServiceInfo = None  # type: ignore[assignment]
    Zeroconf = None     # type: ignore[assignment]

log = logging.getLogger(__name__)

@dataclass
class BonjourServiceHandle:
    zeroconf: Any
    info: Any

def _get_local_ip() -> str:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("10.255.255.255", 1))
        ip = sock.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        try:
            sock.close()
        except Exception:
            pass
    return ip

def start_bonjour(service_name: str, port: int) -> Optional[BonjourServiceHandle]:
    if Zeroconf is None or ServiceInfo is None:
        log.warning("zeroconf is not installed; Bonjour advertising disabled")
        return None

    zc = Zeroconf()
    properties = {
        b"path": b"/",
        b"txtvers": b"1",
        b"description": b"Agent Terminal App HTTP API",
    }
    local_ip = _get_local_ip()

    info = ServiceInfo(
        "_http._tcp.local.",
        f"{service_name}._http._tcp.local.",
        addresses=[socket.inet_aton(local_ip)],
        port=port,
        properties=properties,
        server=f"{socket.gethostname()}.local.",
    )

    zc.register_service(info)
    log.info("Advertising Bonjour service '%s' on port %s", service_name, port)
    return BonjourServiceHandle(zeroconf=zc, info=info)

def stop_bonjour(handle: Optional[BonjourServiceHandle]) -> None:
    if handle is None:
        return

    zc = handle.zeroconf
    info = handle.info
    try:
        if zc is not None and info is not None:
            zc.unregister_service(info)
    except Exception:
        log.debug("Error while unregistering Bonjour service", exc_info=True)
    finally:
        try:
            if zc is not None:
                zc.close()
        except Exception:
            log.debug("Error while closing Zeroconf instance", exc_info=True)
```

This is a thin wrapper; no side effects until `start_bonjour` is called.

---

### 3.3 Wiring Bonjour into the FastAPI app

**File:** `application/python/agent_terminal_app/server.py`

New imports and globals:

```python
import asyncio
import json
import os
import threading
from datetime import datetime
...
from agent_terminal_app import bonjour as bonjour_mod
from agent_terminal_app import bridge_client as bridge_mod  # Step 5

app = FastAPI(title="Agent Terminal App - Echo provider (AgentApplication)")

# Optional integrations: Bonjour/mDNS and bridge client
_bonjour_handle: Optional[bonjour_mod.BonjourServiceHandle] = None
_bridge_client: Optional[bridge_mod.BridgeClient] = None
_bridge_task: Optional[asyncio.Task[None]] = None
```

Startup/shutdown hooks:

```python
@app.on_event("startup")
async def _on_startup() -> None:
    """FastAPI startup hook.

    * Optionally advertise the HTTP API via Bonjour/mDNS when
      ENABLE_BONJOUR is set.
    * Optionally start the bridge client when BRIDGE_URL is set.
    """

    global _bonjour_handle, _bridge_client, _bridge_task

    # Bonjour advertising
    if os.getenv("ENABLE_BONJOUR"):
        port_str = os.getenv("BONJOUR_PORT") or os.getenv("SERVER_PORT") or "8000"
        try:
            port = int(port_str)
        except ValueError:
            port = 8000

        service_name = os.getenv("BONJOUR_SERVICE_NAME") or "Agent Terminal App"
        _bonjour_handle = bonjour_mod.start_bonjour(service_name, port)

    # Bridge client (Step 5 – see below)
    client = bridge_mod.create_bridge_client_from_env()
    if client is not None:
        _bridge_client = client
        _bridge_task = asyncio.create_task(client.run())


@app.on_event("shutdown")
async def _on_shutdown() -> None:
    """FastAPI shutdown hook for cleaning up integrations."""

    global _bonjour_handle, _bridge_client, _bridge_task

    # Stop bridge first
    if _bridge_client is not None:
        try:
            await _bridge_client.stop()
        except Exception:
            pass

    if _bridge_task is not None:
        try:
            await _bridge_task
        except Exception:
            pass

    _bridge_client = None
    _bridge_task = None

    # Then tear down Bonjour advertisement
    if _bonjour_handle is not None:
        bonjour_mod.stop_bonjour(_bonjour_handle)
        _bonjour_handle = None
```

Also, in `run_api` we now propagate host/port to env so Bonjour/bridge can infer them when you run via `python -m agent_terminal_app`:

```python
def run_api(host: str = "127.0.0.1", port: int = 8000, app_instance: Optional[AgentApplication] = None) -> None:
    ...
    global _agent_app
    if app_instance is not None:
        _agent_app = app_instance

    os.environ.setdefault("SERVER_HOST", host)
    os.environ.setdefault("SERVER_PORT", str(port))

    uvicorn.run("agent_terminal_app.server:app", host=host, port=port, reload=False)
```

---

### 3.4 Bonjour unit test

**File:** `application/python/tests/test_bonjour_module.py`

Mocks `Zeroconf` and `ServiceInfo` to ensure `register_service`, `unregister_service`, and `close` are called:

```python
from agent_terminal_app import bonjour as bonjour_mod

class _DummyZeroconf:
    ...

class _DummyServiceInfo:
    ...

def test_start_and_stop_bonjour_registers_and_unregisters(monkeypatch) -> None:
    monkeypatch.setattr(bonjour_mod, "Zeroconf", _DummyZeroconf)
    monkeypatch.setattr(bonjour_mod, "ServiceInfo", _DummyServiceInfo)

    handle = bonjour_mod.start_bonjour("Test Service", 12345)
    assert isinstance(handle, bonjour_mod.BonjourServiceHandle)

    zc = handle.zeroconf
    assert len(zc.register_calls) == 1

    bonjour_mod.stop_bonjour(handle)
    assert len(zc.unregister_calls) == 1
    assert zc.closed is True
```

---

### 3.5 How to use Bonjour with the server

Run the FastAPI server with Bonjour enabled:

```bash
cd application/python
ENABLE_BONJOUR=1 \
BONJOUR_PORT=8080 \
uvicorn agent_terminal_app.server:app --host 0.0.0.0 --port 8080
```

Or, using the CLI wrapper:

```bash
cd application/python
ENABLE_BONJOUR=1 \
BONJOUR_PORT=8080 \
python -m agent_terminal_app --server --host 0.0.0.0 --port 8080
```

Because `run_api` sets `SERVER_PORT`, Bonjour will advertise the correct port when you use `python -m`.

To verify from a Mac:

```bash
dns-sd -B _http._tcp .
# You should see "Agent Terminal App" (or your BONJOUR_SERVICE_NAME).
```

The RN app (already copied into `mobile/crystal-lattice-control-rn`) can now discover this `_http._tcp` service via its “Automatic Discovery” mode and talk to `/api/data`.

---

## Step 4 – Elixir bridge brought into this repo

I copied the Elixir bridge from `../bonjour-example-1/bridge-elixir` into the root of this repo.

**New directory:** `bridge-elixir/`

Contents (unchanged from the original):

- `_build/`
- `BRIDGE_PLAN.md`
- `config/`
- `deps/`
- `docker-compose.yml`
- `docker-entrypoint.sh`
- `Dockerfile`
- `haproxy.cfg`
- `lib/`
- `Makefile`
- `mix.exs`, `mix.lock`
- `README.md`
- `requirements.txt`
- `run-integration-tests.sh`
- `scripts/`
- `test/`, `test_docker.py`

Usage is the same as in the original bonjour example:

```bash
cd bridge-elixir
docker-compose up -d
curl http://localhost:4000/health
```

The bridge exposes the same Phoenix WebSocket endpoint expected by the RN app and by our new Python bridge client (next section):

- WebSocket: `ws://<bridge-host>:4000/ws/websocket`
- Health: `http://<bridge-host>:4000/health`

---

## Step 5 – Python bridge client wired to FastAPI

### 5.1 Bridge client module

**File:** `application/python/agent_terminal_app/bridge_client.py`

Core pieces:

```python
from dataclasses import dataclass
from typing import Any, Dict, Optional
import asyncio
import json
import logging
import os
import socket
import uuid

try:
    import websockets  # type: ignore[import-not-found]
except Exception:
    websockets = None  # type: ignore[assignment]

import httpx

log = logging.getLogger(__name__)

@dataclass
class BridgeConfig:
    bridge_url: str
    server_id: str
    display_name: str
    computer_name: str
    location: Optional[str]
    local_http_base: str
```

Bridge client implementation (simplified view):

```python
class BridgeClient:
    def __init__(self, config: BridgeConfig, *, test_mode: bool = False) -> None:
        self.config = config
        self.test_mode = test_mode
        self._ws: Optional[websockets.WebSocketClientProtocol] = None  # type: ignore[name-defined]
        self._connected = False
        self._registered = False
        self._ref_counter = 0
        self._stopped = False
        self.pairing_code: Optional[str] = None
        self.session_id: Optional[str] = None

    def _next_ref(self) -> str: ...
    def _phoenix_message(self, topic: str, event: str, payload: Dict[str, Any]) -> str: ...

    async def run(self) -> None:
        if websockets is None:
            log.warning("websockets is not installed; bridge client disabled")
            return

        ws_url = f"{self.config.bridge_url}?type=server"
        log.info("Connecting to bridge at %s", ws_url)

        try:
            self._ws = await websockets.connect(ws_url)
            self._connected = True
            log.info("Connected to bridge WebSocket")

            await self._join_channel()
            await self._register_server()
            await self._handle_messages()
        except asyncio.CancelledError:
            raise
        except Exception:
            log.exception("Bridge client error")
        finally:
            await self._close_ws()
            self._connected = False

    async def stop(self) -> None:
        self._stopped = True
        await self._close_ws()
```

Phoenix protocol helpers:

```python
async def _join_channel(self) -> None:
    assert self._ws is not None
    join_msg = self._phoenix_message(f"server:{self.config.server_id}", "phx_join", {})
    await self._ws.send(join_msg)

    raw = await self._ws.recv()
    data = json.loads(raw)
    if data.get("event") == "phx_reply" and data.get("payload", {}).get("status") == "ok":
        log.info("Joined server channel server:%s", self.config.server_id)
    else:
        log.warning("Unexpected join reply from bridge: %s", data)

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
    else:
        log.warning("Unexpected register reply from bridge: %s", data)
```

Main message loop:

```python
async def _handle_messages(self) -> None:
    assert self._ws is not None
    if not self.test_mode:
        log.info("Listening for messages from bridge…")

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
            elif event == "phx_reply":
                continue

            if self._stopped:
                break
    except asyncio.CancelledError:
        raise
    except Exception:
        log.exception("Error while handling messages from bridge")
```

Pairing and HTTP request handlers:

```python
def _handle_pairing_requested(self, payload: Dict[str, Any]) -> None:
    code = payload.get("code")
    self.pairing_code = code
    log.info("Bridge pairing requested; code=%s", code)

def _handle_paired(self, payload: Dict[str, Any]) -> None:
    session_id = payload.get("session_id")
    self.session_id = session_id
    log.info("Client paired successfully; session_id=%s", session_id)

async def _handle_http_request(self, payload: Dict[str, Any]) -> None:
    if self._ws is None:
        return

    request_id = payload.get("request_id")
    method = (payload.get("method") or "GET").upper()
    path = payload.get("path") or "/"
    body = payload.get("body")

    response = await self.execute_local_request(method, path, body)

    msg = self._phoenix_message(
        f"server:{self.config.server_id}",
        "http_response",
        {
            "request_id": request_id,
            "status": response["status"],
            "headers": response.get("headers", {}),
            "body": response.get("body", ""),
        },
    )
    await self._ws.send(msg)
```

Local HTTP proxy (to our FastAPI server) via `httpx.AsyncClient`:

```python
async def execute_local_request(self, method: str, path: str, body: Optional[str]) -> Dict[str, Any]:
    base = self.config.local_http_base.rstrip("/")
    if not path.startswith("/"):
        path = "/" + path
    url = base + path

    headers: Dict[str, str] = {}
    content: Optional[bytes] = None

    if body is not None:
        headers["Content-Type"] = "application/json"
        content = body.encode("utf-8")

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.request(method, url, headers=headers, content=content)

        return {
            "status": resp.status_code,
            "headers": dict(resp.headers),
            "body": resp.text,
        }
    except Exception as exc:
        log.exception("Error executing local HTTP request via bridge: %s", exc)
        return {
            "status": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": str(exc)}),
        }
```

This means any path the mobile app sends (`/api/data`, `/sessions`, etc.) is forwarded to the local FastAPI HTTP server.

---

### 5.2 Bridge config from environment

Helper factory:

```python
def create_bridge_client_from_env() -> Optional[BridgeClient]:
    bridge_url = os.getenv("BRIDGE_URL")
    if not bridge_url:
        return None

    display_name = os.getenv("BRIDGE_DISPLAY_NAME") or "Agent Terminal App"
    location = os.getenv("BRIDGE_LOCATION")

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
    )

    return BridgeClient(cfg)
```

So:

- If `BRIDGE_URL` is not set → no bridge.
- If `BRIDGE_URL` is set, we:
    - Use `BRIDGE_LOCAL_HTTP_BASE` if provided (recommended).
    - Otherwise build `http://<SERVER_HOST>:<SERVER_PORT>` (defaults to `127.0.0.1:8000` if unset).

This is used from the FastAPI startup event as shown in Step 3.

---

### 5.3 Bridge client unit test

**File:** `application/python/tests/test_bridge_client_local_request.py`

Mocks `httpx.AsyncClient` and validates URL composition:

```python
from agent_terminal_app import bridge_client as bridge_mod

class _DummyResponse: ...

class _DummyAsyncClient:
    last_request: Optional[tuple[Any, ...]] = None
    ...
    async def request(self, method, url, headers=None, content=None):
        _DummyAsyncClient.last_request = (method, url, headers, content)
        return _DummyResponse()

def test_execute_local_request_builds_url_and_invokes_httpx(monkeypatch) -> None:
    monkeypatch.setattr(
        bridge_mod,
        "httpx",
        types.SimpleNamespace(AsyncClient=_DummyAsyncClient),
    )

    cfg = bridge_mod.BridgeConfig(
        bridge_url="ws://example.test/ws/websocket",
        server_id="server-1",
        display_name="Test Server",
        computer_name="test-host",
        location=None,
        local_http_base="http://127.0.0.1:9000/",  # trailing slash handled
    )

    client = bridge_mod.BridgeClient(cfg, test_mode=True)

    async def _run() -> Dict[str, Any]:
        return await client.execute_local_request("GET", "/api/data", None)

    result = asyncio.run(_run())

    assert result["status"] == 200
    assert result["body"] == "ok"
    assert result["headers"]["X-Test"] == "1"

    method, url, headers, content = _DummyAsyncClient.last_request
    assert method == "GET"
    assert url == "http://127.0.0.1:9000/api/data"
    assert headers == {}
    assert content is None
```

---

### 5.4 How to run the server with the bridge

1. Start the Elixir bridge:

   ```bash
   cd bridge-elixir
   docker-compose up -d
   # optional check:
   curl http://localhost:4000/health
   ```

2. Start the FastAPI server with bridge enabled:

   ```bash
   cd application/python

   BRIDGE_URL=ws://localhost:4000/ws/websocket \
   BRIDGE_DISPLAY_NAME="My Agent Server" \
   BRIDGE_LOCATION="Office" \
   BRIDGE_LOCAL_HTTP_BASE="http://127.0.0.1:8080" \
   ENABLE_BONJOUR=1 \
   BONJOUR_PORT=8080 \
   uvicorn agent_terminal_app.server:app --host 0.0.0.0 --port 8080
   ```

    - `BRIDGE_URL` points to the Elixir bridge.
    - `BRIDGE_LOCAL_HTTP_BASE` tells the bridge client where your FastAPI server is.
    - `ENABLE_BONJOUR`/`BONJOUR_PORT` keep Bonjour active at the same time, if you want.

3. From the RN app:

    - Use the “Bridge Service” connection mode.
    - Point it at `ws://<bridge-host>:4000/ws/websocket`.
    - It will:
        - List servers (you should see `"My Agent Server"`).
        - Pair using the 6-digit code shown in server logs.
        - Forward HTTP requests (e.g. `GET /api/data`, `PUT /api/data`) through the bridge into your FastAPI server.

---

## Status

- **Step 3 – Bonjour/mDNS**: Implemented and wired into FastAPI startup/shutdown via `ENABLE_BONJOUR`, `BONJOUR_PORT`, etc. Unit-tested with a mocked Zeroconf.
- **Step 4 – Elixir bridge**: Copied into repo at `bridge-elixir/`, ready to run with `docker-compose up -d`.
- **Step 5 – Bridge client**: Implemented as `agent_terminal_app.bridge_client.BridgeClient`, integrated into FastAPI startup via `BRIDGE_URL` and `BRIDGE_LOCAL_HTTP_BASE`, with unit tests for the local HTTP proxying.

If you want, the next step is Step 6: extend the React Native app to call your real `/sessions` endpoints over the same adapters (manual, Bonjour, bridge).