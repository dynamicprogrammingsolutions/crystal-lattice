# Agent Guidelines – `agent_terminal_app`

This file applies to everything under `application/python/agent_terminal_app/`.
It describes what lives here, how server/terminal/bridge pieces fit together,
and how to extend them without breaking existing flows.

---

## 1. Scope & Responsibilities

This package contains the **application layer for end-users**:

- A **FastAPI HTTP server** exposing JSON APIs for sessions, messages, and
  streaming events.
- A **prompt_toolkit terminal client** used for interactive conversations.
- Shared application glue (`app_core.py`, `terminal_app.py`) on top of the
  core SDK (`agent_core`, `agent_app`).
- Integrations that let a **mobile app discover and reach the server in three
  ways**:
  - Direct HTTP by IP/hostname + port.
  - Bonjour/mDNS discovery on the local network.
  - A bridge service with a Phoenix server-control WebSocket and
    WebSocket/HTTP/hybrid frontend paths.

When working in this directory, you are primarily wiring UX (HTTP + terminal)
to the core engine, not changing core algorithms.

---

## 2. Key Modules & Responsibilities

- `server.py`
  - Defines the FastAPI app and HTTP routes.
  - Maps JSON requests to `AgentApplication` calls (sessions, messages,
    streaming sends).
  - Owns lifecycle hooks for:
    - Starting/stopping Bonjour advertising (`bonjour.py`).
    - Starting/stopping the bridge WebSocket client (`bridge_client.py`).
  - Also hosts the small demo endpoints used by the mobile app integration:
    - `GET /api/data`, `PUT /api/data`, `GET /api/hello`.

- `terminal_app.py`
  - The main application façade for terminal usage.
  - Exposes high-level operations: create/delete/list sessions, send messages,
    inspect agents/plugins, apply config overrides.
  - Called by `terminal.py` (UI) and uses `app_core.AgentAppCore` underneath.

- `terminal.py`
  - Implements the prompt_toolkit UI and slash commands.
  - Should remain UI-only; non-trivial logic belongs in `terminal_app.py`.

- `app_core.py`
  - Binds the core SDK (`agent_core`, `agent_app`) into a cohesive app
    abstraction for this package.
  - If you need to change how configs are loaded, agents are instantiated, or
    how the tool loop is called from this app, do it here.

- `bonjour.py`
  - Small wrapper around `zeroconf` to advertise an `_http._tcp` service.
  - Called from FastAPI startup/shutdown via `asyncio.to_thread` to avoid
    blocking the event loop.
  - Do **not** add complex logic here; keep it focused on registration and
    teardown.

- `bridge_client.py`
  - Registered-server adapter for the Elixir bridge service.
  - Speaks the Phoenix control protocol to:
    - Register this server instance.
    - Handle pairing requests and responses.
    - Proxy legacy text requests and versioned HTTP raw-byte transfers to the
      local FastAPI endpoints (`/api/*`, `/sessions/*`, etc.).
  - Treat it as an integration layer; do not add application/business logic
    here (it should live in `server.py` / `app_core.py`).

- `event_rendering.py`
  - Renders streamed events for the terminal client (assistant messages,
    reasoning/tool traces, etc.).
  - Any changes should preserve readability in a plain terminal.

- Session files use the active session root. The default is
  `./.crystal/sessions`; `--sessions-dir` may override it. Tests may create
  temporary session files; do not commit them unless a test explicitly needs
  them.

---

## 3. Running & Integration Expectations

### 3.1. HTTP server

- Standard entrypoint:

  ```bash
  cd application/python
  python -m agent_terminal_app --host 0.0.0.0 --port 9000
  ```

- The React Native demo app talks to this server via:
  - Direct IP/port: `http://<host>:<port>/api/data` and `/sessions` endpoints.
  - Bonjour: discovers `_http._tcp` service advertised by `bonjour.py`.
  - Bridge: uses the selected frontend path; `bridge_client.py` receives
    legacy requests or v2 metadata/body transfers and proxies them to this HTTP
    server.

When modifying endpoints, keep their semantics backward compatible for the
mobile integration unless explicitly updating the mobile app at the same time.

### 3.2. Terminal client

- Standard entrypoints:

  ```bash
  # Console only
  python -m agent_terminal_app --console

  # Server + console in one process
  python -m agent_terminal_app --server --console
  ```

- The terminal shares sessions and events with the HTTP server when run in the
  same process; changes that affect event storage or rendering must preserve
  this contract and be covered by tests in `application/python/tests`.

### 3.3. Bonjour & bridge options

- Bonjour and bridge activation is configured through CLI flags to
  `python -m agent_terminal_app`; advanced bridge transport settings may come
  from the documented `application.bridge` configuration object. The CLI
  passes explicit process-local runtime configuration to the server. Do not
  use ambient environment variables to activate or configure these internally
  hosted integrations.
- The effective contract for mobile clients is:
  - Bonjour service type: `_http._tcp.local.` with `path=/` and a human
    readable service name.
  - Bridge URL pattern: `ws(s)://<bridge-host>:4000/ws/websocket`.

If you change these conventions, coordinate updates with the mobile app and
`bridge-elixir` docs.

---

## 4. Coding Style & Change Guidelines

- Follow the root `AGENTS.md` principles:
  - Keep core logic in `agent_core` / `agent_app` when possible.
  - Treat returned data structures as immutable; avoid defensive copying.
  - Add tests for any new externally visible behavior.

- For this package specifically:
  - **Do not** put complex logic in FastAPI route functions or prompt_toolkit
    callbacks. Factor logic into `app_core.py` or `terminal_app.py` and have
    routes/UI delegate there.
  - Keep modules focused:
    - `server.py` → HTTP + lifecycle wiring.
    - `terminal_app.py` → business logic for terminal workflows.
    - `terminal.py` → I/O and keybindings only.
  - Avoid adding global mutable state; use dependency injection or object
    instances when practical. The existing few globals (e.g. shared data store,
    Bonjour/bridge handles) should remain tightly scoped.
  - Prefer small, explicit helper functions over deep class hierarchies.

- Testing:
  - New behavior in this package should be covered in
    `application/python/tests`.
  - When changing server behavior, add or update tests in
    `test_agent_terminal_app_server.py`.
  - When changing terminal behavior, look at `test_terminal_application.py`
    and related tests.
  - Use FastAPI `TestClient` for HTTP contract behavior such as routing, query
    parsing, response envelopes, serialization, and status codes. Direct route
    calls are useful adapter tests but do not count as HTTP integration.

---

## 5. When Integrating Mobile Features

When extending or changing behavior that affects the mobile app:

- Keep the three connection modes working:
  1. **Direct HTTP** by host/port.
  2. **Bonjour discovery** using `_http._tcp` and the advertised port.
  3. **Bridge service** using `http_request` messages via the Elixir bridge.

- Any new HTTP endpoints intended for mobile should:
  - Use simple JSON request/response formats.
  - Avoid streaming in the first iteration (mobile can call a
    non-streaming send endpoint, then later we can add streaming support if
    needed).

- Document new mobile-related endpoints and flows in
  `application/python/README.md` or a dedicated doc file alongside
  `server_endpoints_parity.md`.

If in doubt about where to put something, prefer:

- Core agent behavior → `core/python/agent_core` / `agent_app`.
- Application wiring, HTTP, terminal, mobile/bridge integration → this
  package.
