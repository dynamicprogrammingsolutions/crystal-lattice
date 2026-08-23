> Archived historical integration plan. It is not current implementation
> guidance. See the [archive index](../README.md) and current
> [application documentation](../../application/python/README.md).

Here’s a concrete plan based on a deep dive into `../bonjour-example-1` and your current `ai-agent-platform` server.

---

## 0. What we’re copying from `bonjour-example-1`

### Python server (`server-python/bonjour_server.py`)

Key behavior:

- Simple HTTP server (stdlib `HTTPServer`) exposing three endpoints:

    - `GET /api/data`
        - Returns JSON:
          ```json
          {
            "success": true,
            "data": { "message": "...", "count": 0, ... },
            "timestamp": "2025-01-01T00:00:00Z"
          }
          ```

    - `PUT /api/data`
        - Accepts JSON body (merged into a mutable in‑memory `DataStore`).
        - Returns:
          ```json
          {
            "success": true,
            "updated": { ... }
          }
          ```

    - `GET /api/hello`
        - Returns:
          ```json
          {
            "message": "Hello from Bonjour Server!",
            "timestamp": "...",
            "method": "GET"
          }
          ```

- Bonjour/mDNS announcement using `zeroconf`:
    - Service type: `_http._tcp.local.`
    - Service name: `<service_name>._http._tcp.local.`
    - Properties: `path=/`, etc.
    - Advertises the HTTP server on some port.

- Optional bridge mode:
    - `--bridge ws://host:4000/ws/websocket`
    - Starts a `BridgeClient` that:
        - Connects to the Elixir bridge over Phoenix WebSocket.
        - Joins topic `server:{server_id}`.
        - Registers server (`display_name`, `computer_name`, optional `location`).
        - Handles messages:
            - `pairing_requested` → prints/shows 6‑digit code.
            - `paired` → stores `session_id`.
            - `http_request` → executes local request via `execute_local_request(method, path, body)` and returns `http_response`.

    - `execute_local_request()` is **not HTTP**; it just knows how to handle `/api/data` and `/api/hello` against the in-memory `DataStore`.

### React Native app (`react-native-app/App.tsx`)

Transport abstraction:

```ts
interface ConnectionAdapter {
  connect(): Promise<void>;
  get(path: string): Promise<any>;
  put(path: string, data: any): Promise<any>;
  disconnect(): void;
  getDisplayName(): string;
}
```

Implementations:

- `HttpAdapter` (manual + Bonjour discovery):
    - `connect()` → test `GET /api/data`.
    - `get('/api/data')` → GET `http://host:port/api/data`.
    - `put('/api/data', data)` → PUT same.

- `BridgeAdapter` (cross-network via Elixir bridge):
    - Connects to WebSocket: `<bridgeUrl>?type=app`.
    - Joins `app:{client_id}` channel (Phoenix protocol).
    - Supports:
        - `listServers()` → `list_servers`.
        - `requestPairing(server_id)` → `pair_request`.
        - `submitPairingCode(server_id, code, name)` → `pair_submit` → gets `session_id`.
        - `get(path)` / `put(path, data)` → `http_request` with `session_id`.

- Three connection modes:
    - Manual: enter IP + port → HTTP to `/api/data`.
    - Discovery: `react-native-zeroconf` → `_http._tcp` → choose service → HTTP to `/api/data`.
    - Bridge: connect to Elixir bridge, list servers, pair, then HTTP via bridge to `/api/data`.

### Elixir bridge (`bridge-elixir`)

- Phoenix endpoint:
    - `GET /health` → JSON about cluster, sessions, etc.
    - WebSocket endpoint `/ws` (Phoenix Socket).

- Channels:
    - `ServerChannel` (`"server:{server_id}"`):
        - `register` → register server in `ServerRegistry`.
        - Receives pairing events (`pairing_requested`, `paired`) and HTTP requests via PubSub, pushes to server WebSocket.
        - Accepts `http_response` events to forward responses.

    - `AppChannel` (`"app:{client_id}"`):
        - `list_servers` → list registered servers.
        - `pair_request` → create pairing code, notify server (`pairing_requested`).
        - `pair_submit` → validate code, create `session_id`, notify server (`paired`).
        - `http_request` → route by `session_id`: broadcast to server, await `http_response`, return via `phx_reply`.

- The bridge is **HTTP-agnostic**; it just transports abstract “HTTP request messages” over WebSocket.

---

## High-level integration goal

For the AI agent platform, we want:

- A **FastAPI** server (`application/python/agent_terminal_app/server.py`) that:
    - Exposes the same `/api/data` and `/api/hello` endpoints.
    - Can be discovered via Bonjour as `_http._tcp`.
    - Can be reached directly (`http://<ip>:<port>`) from the RN app.
    - Optionally connects to the Elixir bridge to allow the RN app to reach it via WebSocket + pairing.

- A **React Native app inside this repo** that:
    - Reuses the existing adapter abstraction and UI.
    - Initially only exercises `/api/data` via manual/direct IP.
    - Later can discover the server via Bonjour and use the bridge.

- The **Elixir bridge** living inside this repo, unchanged or minimally adapted.

We’ll follow your six steps; each will remain small and testable.

---

## Step 1 – Add Bonjour-example HTTP endpoints to our FastAPI server

**Goal:** Have our existing `agent_terminal_app.server` provide `/api/data` and `/api/hello` with the same behavior as `bonjour_server.py`. No Bonjour or bridge yet.

### Design

- Keep all current session/LLM endpoints.
- Add:
    - `GET /api/data`
    - `PUT /api/data`
    - `GET /api/hello`

- Implement a simple in‑memory `DataStore` that matches semantics of `server-python`:

  ```python
  class DataStore:
      def __init__(self, initial_data=None):
          self._data = initial_data or {"message": "Initial data", "count": 0}
          self._lock = threading.Lock()

      def get(self) -> dict:
          with self._lock:
              return dict(self._data)

      def update(self, new_data: dict) -> dict:
          with self._lock:
              self._data.update(new_data)
              return dict(self._data)
  ```

- Expose a single module-level instance, e.g. in `server.py`:

  ```python
  _bonjour_data_store = DataStore()
  ```

- Endpoint behavior:

    - `GET /api/data`:
        - Use `_bonjour_data_store.get()`.
        - Wrap in JSON response:
          ```json
          {
            "success": true,
            "data": { … },
            "timestamp": "<UTC ISO8601>Z"
          }
          ```
    - `PUT /api/data`:
        - Parse JSON body into `dict`.
        - Call `update()` on store.
        - Return `{"success": true, "updated": <dict>}`.

    - `GET /api/hello`:
        - Return same structure and content as bonjour example:
          ```json
          {
            "message": "Hello from Bonjour Server!",
            "timestamp": "...",
            "method": "GET"
          }
          ```

    - Use FastAPI idioms (pydantic models optional, but not required for parity).

### Files to touch

- `application/python/agent_terminal_app/server.py`:
    - Add `DataStore` and global instance.
    - Add the three new FastAPI routes.

- Optionally: a small doc note in `application/python/README.md` describing `/api/*` endpoints.

### Tests

Add tests in `application/python/tests/test_agent_terminal_app_server.py`:

- `test_get_api_data_returns_initial_state`:
    - Reset/patch DataStore to known initial value.
    - Use `TestClient(app)` to call `GET /api/data`.
    - Assert `200`, `success == True`, `data` matches initial state, `timestamp` is present.

- `test_put_api_data_updates_store`:
    - `PUT /api/data` with JSON body.
    - Then `GET /api/data` and verify contents changed as expected.

- `test_get_api_hello_matches_python_bonjour_shape`:
    - Call `GET /api/hello`.
    - Assert keys `message`, `timestamp`, `method`, and exact `message`.

**Result:** Our AI server now looks identical (from a REST perspective) to the Python bonjour server for these paths.

---

## Step 2 – Bring in the React Native app and test manual IP connection

**Goal:** Put the RN app into this repo and verify it can talk directly to our FastAPI `/api/data` endpoints over IP:port.

### Design / structure

- Create a new directory in this repo, e.g.:

    - `mobile/crystal-lattice-control-rn/` (or `mobile/react-native-bonjour`).

- Copy `../bonjour-example-1/react-native-app` contents into that directory.

- Keep the existing app logic initially:
    - It already has `HttpAdapter` that calls `/api/data`.
    - It defaults to port `8080`, but the user can override the port in the UI.

### Server-side expectations

- Run our FastAPI server with CORS allowed for dev (if we decide to serve mobile on device) – but RN uses native fetch, not webview, so CORS is not relevant.

- Make sure we can start the server on a known port, e.g.:

    - `uvicorn agent_terminal_app.server:app --host 0.0.0.0 --port 8080`
    - Or 8000; as long as we know what to type into the app.

### Minimal RN changes for this step

- Optionally, change the default port in `App.tsx`:

  ```ts
  const [manualPort, setManualPort] = useState('8080'); // maybe '8000'
  ```

  We can leave it as 8080 initially and just run FastAPI on 8080.

- Update `README` in the new RN project directory to point to this repo’s server instead of `../server-python`.

### Tests / validation

- No automated tests yet; this is largely manual:

    1. Start FastAPI server on `0.0.0.0:8080` (or chosen port).
    2. Run RN app (iOS Simulator / device or Android).
    3. Choose “Manual Address”.
    4. Enter host: `<server-ip>`, port: `8080`.
    5. Tap “Connect”:
        - App calls `GET /api/data` via `HttpAdapter.connect()`.
        - Should show “Connected” screen.
    6. Tap “GET /api/data” and “PUT /api/data” actions:
        - Confirm server logs and response display in app.

- Small sanity test for Android/iOS connectivity via `curl` from the same network before trying RN.

**Result:** We verify that our FastAPI `/api/data` endpoints are reachable from the RN app via direct IP.

---

## Step 3 – Add Bonjour/mDNS advertising to our FastAPI server

**Goal:** RN app can discover our server via Bonjour (Automatic Discovery method) using `react-native-zeroconf`, just like the bonjour example.

### Design

In the bonjour Python server, Bonjour is handled by `BonjourHTTPServer._advertise_service()` using `zeroconf.ServiceInfo`.

For FastAPI + uvicorn, we don’t control the HTTP server loop directly, but we can:

- Use FastAPI lifecycle hooks (`@app.on_event("startup")` / `@app.on_event("shutdown")`).
- Keep a global `Zeroconf` + `ServiceInfo` similar to `bonjour_server.py`.

Key points:

- Service type: `_http._tcp.local.`
- Service name: something like `"Agent Server"` or configurable.
- The port must match the actual uvicorn port.

We need a way to tell the Bonjour layer what port we’re using:

- Simplest: decide that for Bonjour mode we always run uvicorn on a known port (e.g. 8080) and pass that to the Bonjour module via an environment variable.

  Example:

    - `SERVER_PORT=8080 ENABLE_BONJOUR=1 uvicorn agent_terminal_app.server:app --host 0.0.0.0 --port 8080`

- At startup:

  ```python
  @app.on_event("startup")
  async def start_bonjour_advertising():
      if not os.getenv("ENABLE_BONJOUR"):
          return
      port = int(os.getenv("BONJOUR_PORT", os.getenv("SERVER_PORT", "8080")))
      # Initialize Zeroconf and register service.

  @app.on_event("shutdown")
  async def stop_bonjour_advertising():
      # unregister_service & close zeroconf
  ```

Implementation plan:

- Add a new helper in `server.py` or a small separate module, e.g. `agent_terminal_app/bonjour.py`:

    - `start_bonjour(service_name: str, port: int) -> (Zeroconf, ServiceInfo)`
    - `stop_bonjour(zc, info)`

- Wire these into FastAPI startup/shutdown only when enabled via env.

- Use similar `_get_local_ip()` logic from bonjour server to announce the correct IP in the `ServiceInfo`.

### Files to touch

- New: `application/python/agent_terminal_app/bonjour.py` (optional helper module).
- `application/python/agent_terminal_app/server.py`:
    - Add lifecycle hooks that call into `bonjour.py` when env flags are set.

### Tests / validation

Automated:

- A very light unit/integration test can use `unittest.mock` to patch `Zeroconf` and verify `register_service`/`unregister_service` are called when `ENABLE_BONJOUR=1` is set.

Manual E2E:

1. Start server with Bonjour enabled:

   ```bash
   ENABLE_BONJOUR=1 BONJOUR_PORT=8080 uvicorn agent_terminal_app.server:app --host 0.0.0.0 --port 8080
   ```

2. From a Mac terminal:

   ```bash
   dns-sd -B _http._tcp .
   # Should see your service name.
   ```

3. From RN app, choose “Automatic Discovery”:
    - It calls `zeroconf.scan('http', 'tcp', 'local.')`.
    - Our service should show up in the list with the host and port from ServiceInfo.
    - Select it → connects with `HttpAdapter` to `/api/data`.

**Result:** Our server can be found via Bonjour in the RN app, matching the original example’s discovery flow.

---

## Step 4 – Bring the Elixir bridge into this repo

**Goal:** Have the bridge service (`bridge-elixir`) live under this repository so we can treat it as part of the project and run it easily in CI or dev.

### Design

- Create a top-level directory, e.g.:

    - `bridge/bridge-elixir/` or simply `bridge-elixir/` at repo root.

- Copy `../bonjour-example-1/bridge-elixir` into it, preserving structure:
    - `lib/bridge/*`
    - `config/*`
    - `docker-compose.yml`, `Dockerfile`, `Makefile`, etc.
    - `README.md`, `BRIDGE_PLAN.md`.

- Optionally adjust names/ports only if necessary:
    - In most cases we can keep:
        - WebSocket: `ws://<host>:4000/ws/websocket`
        - Health: `http://<host>:4000/health`

- Integrate minimal tooling:

    - Add a short doc section in this repo’s root `README.md` or `docs` about:
        - How to start the bridge:
          ```bash
          cd bridge-elixir
          docker-compose up -d
          curl http://localhost:4000/health
          ```
        - How the mobile app & Python server use it.

- Optionally define a `make` target or small script for convenience (`scripts/start-bridge.sh`).

### Tests / validation

- Run the bridge’s own tests inside our new location (if we keep them):
    - `cd bridge-elixir && mix test`
- Check `docker-compose up -d` + `curl http://localhost:4000/health`.

No integration with our AI server yet; just making sure the bridge is locally managed.

**Result:** Elixir bridge lives in this repo and works as in the original bonjour example.

---

## Step 5 – Add bridge features to our FastAPI server

**Goal:** Allow the RN app to reach our server through the Elixir bridge, including pairing and proxied HTTP requests, preserving the same protocol.

### Design choices

The original `BonjourHTTPServer` handles `http_request` messages by calling `execute_local_request` directly against its `DataStore`. For our AI server, we already have a real HTTP API. Best approach:

- Implement a bridge client that:
    - Connects to the bridge (like `server-python/bonjour_server.py:BridgeClient`).
    - On `http_request` messages:
        - It **makes an internal HTTP request** to our FastAPI server (`http://localhost:<port><path>`) using `requests` or `httpx`.
        - Forwards the response back as `http_response`.

That gives us a generic proxy: whatever endpoints the RN app calls (for now `/api/data`, later `/sessions/...`) will work through the bridge without changing the bridge itself.

### Concrete plan

1. **Create a bridge client module in this repo**

    - New file, e.g.:

        - `application/python/agent_terminal_app/bridge_client.py`

    - Base it on `../bonjour-example-1/server-python/bonjour_server.py`’s `BridgeClient`:

        - Reuse:
            - WebSocket connection handling with `websockets`.
            - Phoenix message format (`phoenix_message`).
            - `join_channel`, `register_server`, `handle_messages`, `handle_pairing_requested`, `handle_paired`.
        - Replace `execute_local_request()` implementation:

          ```python
          import requests
   
          class BridgeClient:
              def __init__(..., local_http_base: str, ...):
                  self.local_http_base = local_http_base.rstrip("/")
   
              def execute_local_request(self, method, path, body):
                  url = self.local_http_base + path
                  try:
                      resp = requests.request(
                          method=method,
                          url=url,
                          headers={},  # or forward from bridge if needed
                          data=body,
                          timeout=10,
                      )
                      return {
                          "status": resp.status_code,
                          "headers": dict(resp.headers),
                          "body": resp.text,
                      }
                  except Exception as e:
                      return {
                          "status": 500,
                          "headers": {"Content-Type": "application/json"},
                          "body": json.dumps({"error": str(e)}),
                      }
          ```

        - Keep `test_mode` for unit tests, as in original.

2. **Wire bridge client into server startup**

    - Decide on configuration mechanism:
        - Environment variables or CLI for:
            - `BRIDGE_URL` (e.g. `ws://localhost:4000/ws/websocket`)
            - `BRIDGE_DISPLAY_NAME`
            - `BRIDGE_LOCATION`

    - Extend `agent_terminal_app.server.run_api` (or create a new `run_bonjour_server.py` script) to:

        - Start uvicorn on `host`/`port`.
        - In a background thread, start an event loop and run `BridgeClient.connect()` (same pattern as `BonjourHTTPServer._start_bridge_connection`):

          ```python
          def _start_bridge_thread(bridge_url, display_name, location, local_port):
              client = BridgeClient(
                  bridge_url=bridge_url,
                  server_id=str(uuid.uuid4()),
                  display_name=display_name,
                  computer_name=socket.gethostname(),
                  location=location,
                  local_http_base=f"http://127.0.0.1:{local_port}",
              )
              # run client.connect() in its own event loop/thread
          ```

    - This keeps:
        - FastAPI/uvicorn running on the main process.
        - Bridge WebSocket client running independently in another thread, just like in the original example.

3. **Compatibility with RN BridgeAdapter**

    - The RN app’s `BridgeAdapter` expects the **same Phoenix channel protocol**:
        - `list_servers`
        - `pair_request`
        - `pair_submit`
        - `http_request` / `http_response`
    - Since we are reusing the Elixir bridge and essentially the same `BridgeClient` logic, the RN app should work unchanged.

4. **Tests / validation**

   Automated-ish (in Python):

    - Add an integration test similar to `test_bridge_integration_refactored.py`, but using:

        - Our new `bridge_client.BridgeClient`.
        - Our FastAPI server running locally on an ephemeral port.
        - The Elixir bridge running (or skip test if not reachable).

   High-level flow:

    - Start bridge (or skip if `localhost:4000` is not up).
    - Start FastAPI server on e.g. port 8090 (maybe via `uvicorn` in a subprocess or `TestClient` + override; for full E2E, a real port is simpler).
    - Start BridgeClient in test mode pointing to `http://localhost:8090`.
    - From a test `BridgeAppClient` (can reuse `../bonjour-example-1/server-python/bridge_client.py:BridgeAppClient` or reimplement minimal one):
        - Connect to bridge.
        - `list_servers` → find our server.
        - `pair_request`, capture `pairing_code` from server logs/state.
        - `pair_submit`.
        - `http_request("GET", "/api/data")` and `http_request("PUT", "/api/data")`.
    - Assert success and body shapes.

Manual:

- Start bridge: `cd bridge-elixir && docker-compose up -d`.
- Start FastAPI server with bridge:

  ```bash
  BRIDGE_URL=ws://<bridge-host>:4000/ws/websocket \
  BRIDGE_DISPLAY_NAME="My Agent Server" \
  BRIDGE_LOCATION="Office" \
  ENABLE_BONJOUR=1 BONJOUR_PORT=8080 \
  uvicorn agent_terminal_app.server:app --host 0.0.0.0 --port 8080
  ```

- From RN app:
    - Choose “Bridge Service”.
    - Enter bridge URL `ws://<bridge-host>:4000/ws/websocket`.
    - Connect, select our server, request pairing, enter 6‑digit code from server logs.
    - Test `GET /api/data` / `PUT /api/data`.

**Result:** End-to-end transport via bridge is working against our FastAPI API.

---

## Step 6 – Extend mobile app for AI-agent-specific endpoints

**Goal:** Use the same transport mechanisms (manual, Bonjour, bridge) to talk to our existing AI endpoints (e.g. `/sessions`, `/sessions/{id}/messages`, `/sessions/{id}/send`, etc.) with basic UI.

### Design

We already have a transport abstraction:

```ts
interface ConnectionAdapter {
  connect(): Promise<void>;
  get(path: string): Promise<any>;
  put(path: string, data: any): Promise<any>;
  disconnect(): void;
  getDisplayName(): string;
}
```

To call our agent endpoints, we need:

- `POST` capability (for `/sessions`, `/sessions/{id}/messages`, `/sessions/{id}/send`).
- Possibly `GET` beyond `/api/data` (we already have `get`).
- Maybe `DELETE` or `PATCH` later.

Plan:

1. **Extend `ConnectionAdapter` interface**

    - Add a general `request` method:

      ```ts
      interface ConnectionAdapter {
        connect(): Promise<void>;
        get(path: string): Promise<any>;
        put(path: string, data: any): Promise<any>;
        post(path: string, data: any): Promise<any>;   // new
        disconnect(): void;
        getDisplayName(): string;
      }
      ```

    - Update `HttpAdapter` and `BridgeAdapter` to implement `post(path, data)`:
        - `HttpAdapter` → `fetch` with method `POST`.
        - `BridgeAdapter` → uses `http_request` with method `POST` and JSON body.

2. **Define minimal AI flows to support**

   For a “basic” first version:

    - Create session:
        - `POST /sessions` with `{ "agent_id": "default" }` (optionally system message).
    - Add message:
        - `POST /sessions/{session_id}/messages` with `{role: "user", content: "..." }`.
    - Send:
        - `POST /sessions/{session_id}/send` with `{"config_overrides": {}}`.
    - Poll events:
        - `GET /events?session_id=...` or just use final `send` response.

   We can start simpler: call `/sessions` → `/sessions/{id}/messages` → `/sessions/{id}/send` non-streaming and show final messages.

3. **Add UI screens in RN app**

   Minimal new UI (preserve existing screen for `/api/data`):

    - When connected (in `renderConnectedScreen`), add a second section:

        - “Agent Chat”:
            - Button: “Create Session” → calls `adapter.post('/sessions', { agent_id: 'default' })` and stores `session_id` in state.
            - TextInput for user message.
            - Button: “Send Message”:
                - `adapter.post(`/sessions/${session_id}/messages`, { role: 'user', content: message })`
                - `adapter.post(`/sessions/${session_id}/send`, { config_overrides: {} })`
                - Display response (assistant message) in the UI.

    - Reuse the current `response` area to show AI conversation JSON, or add a dedicated chat log.

   Because the adapters are transport-agnostic, these calls will work:

    - Over manual IP (direct HTTP).
    - Over Bonjour (same as manual, but host/port discovered).
    - Over bridge (paths are the same; only transport changes).

4. **Tests / validation**

    - For now, manual:

        - Run server and (optionally) bridge.
        - Connect RN app via manual IP or bridge.
        - Create a session, send a message, see assistant response.

    - Later, we can add low-level automated tests:

        - RN unit tests for `HttpAdapter.post` and `BridgeAdapter.post` (with mocks).
        - Optionally an e2e test harness (detox/Appium) if desired.

---

## Summary of phases and dependencies

- **Step 1: Server endpoints parity**
    - Dependencies: none.
    - Risk: very low; just add 3 endpoints + tests.

- **Step 2: RN app, manual IP**
    - Dependencies: Node 20+, RN toolchain.
    - Risk: environment setup; app logic already solid.

- **Step 3: Bonjour advertisement**
    - Dependencies: `zeroconf` Python package.
    - Risk: medium (lifecycle & shutdown), but implementation is straightforward and well-modeled by `bonjour_server.py`.

- **Step 4: Elixir bridge in repo**
    - Dependencies: Elixir, Docker.
    - Risk: low; mostly copy/paste and path changes.

- **Step 5: Bridge integration in server**
    - Dependencies: `websockets` Python lib, running bridge.
    - Risk: moderate — need to get event loops/threads right and ensure local HTTP proxying is robust. We can lean heavily on the existing `BridgeClient` design.

- **Step 6: Mobile UI for AI features**
    - Dependencies: working `/sessions` endpoints (already there), plus new `post` in adapters.
    - Risk: mostly UI/UX and some error handling; transport layer is reused.

If you want, the next concrete action I’d take is Step 1: draft the `DataStore` and the three FastAPI routes plus tests in `test_agent_terminal_app_server.py`, and show you the exact patch.