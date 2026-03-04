# Terminal + VS Code alignment

This plan intentionally aligns the new TS SDK abstractions with:

- The existing Python REST API (`application/python/agent_terminal_app/server.py`)
- The existing in-process terminal logic (`application/python/agent_terminal_app/terminal_app.py`)
- The future goal of an in-process TypeScript `agent_core`/`agent_app` runtime

## 1) Why this matters

You want multiple frontends to swap between “remote REST” and “local in-process” backends:

- **VS Code extension** (Node runtime): initially REST → later in-process TS.
- **Terminal UI** (Python): currently in-process Python → later optional REST.

The common thread is an **adapter interface** that expresses *domain operations*, not transport details.

## 2) Interface alignment points

The TS `AgentBackend` interface in `@crystal-lattice/frontend-sdk` is designed to cover the same operations the terminal uses today:

- Sessions: create/list/switch/fork
- Messages: list/append/modify/delete-range
- Requests: send/resend/cancel
- Events: list/poll incrementally
- Plugins/UI schema: list application actions/ui schema
- Application-level config: schema + values for terminal-owned settings
- Feature completions: get/apply completions for partially typed input

### 2.1 Feature completions parity gap

Python terminal supports feature-driven completions today via:

- `TerminalApplication.get_feature_completions()`
- `AgentCore.apply_feature_completion()` (used by `terminal.py` after accepting a completion)

The HTTP server has a parity spec documented in `application/python/agent_terminal_app/server_endpoints_parity.md`:

- `POST /sessions/{session_id}/completions`

But `application/python/agent_terminal_app/server.py` does not currently implement this route.

Plan:

- Add `POST /sessions/{session_id}/completions` to the Python server so REST-backed frontends can use completions.
- Consider whether `apply_feature_completion` must also be a server endpoint:
  - If feature completion requires server-side filesystem context (common), then the server must either:
    - return a completion descriptor that is already fully applicable client-side, or
    - expose `POST /sessions/{session_id}/apply-completion`.
  - The TS SDK supports both via optional `getFeatureCompletions` / `applyFeatureCompletion` methods.

This is particularly important for a VS Code extension when running against the Python server, because completions are a key UX bridge for workspace-aware features (e.g. `@file:` suggestions).

### 2.2 Application config parity

The terminal has application-owned settings today (for example tool output rendering limits) via:

- `TerminalApplication.get_application_config_schema()`
- `AgentApplication.get_application_config()`

There is parity documentation for HTTP endpoints in `application/python/agent_terminal_app/server_endpoints_parity.md`:

- `GET /config/application/schema`
- `GET /config/application`

The TS backend interface includes optional methods (`getApplicationConfigSchema`, `getApplicationConfig`, `patchApplicationConfig`) so desktop/editor frontends can share these settings without duplicating config semantics.

## 3) How terminal can adopt the same adapter pattern

Terminal is currently hard-wired to the in-process Python `AgentApplication` via `TerminalApplication`.

To allow terminal to switch between in-process and REST without rewriting terminal UI logic:

1) Define a Python-side backend interface analogous to TS `AgentBackend`.
   - Keep names/parameters intentionally similar.

2) Provide two Python implementations:

- `InProcessBackend` backed by `TerminalApplication` (current behavior)
- `HttpBackend` backed by calling the FastAPI server (same process or remote)

3) Refactor `terminal.py` so it depends only on the backend interface.
   - The terminal UI stays representation-only.

Outcome:

- The terminal can be pointed at a remote REST server, or use its local core, using the same slash commands.
- Parity issues surface quickly because both backends drive the same UI.

## 4) Preparing for in-process TypeScript `agent_app`

The TS SDK should make it easy to replace the REST backend with an in-process backend later.

Key design choices that enable this:

- **Domain-oriented methods** (`createSession`, `send`, `listEvents`, etc.) instead of “HTTP get/post”.
- **Feature completions** are part of the backend contract (optional initially), which matches `AgentCore.get_completions` and `apply_feature_completion`.
- **UI schema** is treated as data (plugin-driven), so a TS `AgentCore.get_ui_schema(config)` port can feed the same UI logic.

Recommended future packaging split:

- `@crystal-lattice/frontend-sdk` (this plan): domain interfaces + controllers
- `@crystal-lattice/agent-runtime-*` (future): implements `AgentBackend` using in-process TS `agent_app`
  - `agent-runtime-node` for VS Code/Node
  - optionally `agent-runtime-browser` if a browser runtime is feasible

This keeps the frontend SDK stable even as the runtime implementations evolve.
