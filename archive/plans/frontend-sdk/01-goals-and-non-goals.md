# Goals and non-goals

## Goals

### G1. Multi-frontend code reuse

Extract the non-UI logic currently embedded in `mobile/crystal-lattice-control-rn/` into a shared SDK so new frontends can be created with minimal duplication:

- Desktop RN macOS app in a separate directory
- VS Code extension (Node runtime)
- Future web/desktop UIs
- (Eventually) align with terminal UX concepts where possible

### G2. Unified backend interface (adapters)

Define a single high-level backend interface (“Agent backend”) that can be implemented by:

- **REST backend**: calls the existing Python HTTP API (`application/python/agent_terminal_app/server.py`).
- **Bridge backend**: tunnels HTTP calls over Phoenix WebSocket via `bridge-elixir` (same HTTP semantics).
- **In-process backend (future)**: calls a future TypeScript port of `agent_core` + `agent_app` directly.

Frontends should depend on the high-level backend interface, not on HTTP routes.

### G3. Headless controllers / view models

Create reusable controllers that encapsulate complex workflows currently implemented inside screens:

- Chat lifecycle: load/append/send/resend/cancel, incremental events polling, streaming aggregation.
- Session list lifecycle: refresh/staleness, create session, derived title/subtitle/meta from UI schema.
- Plugin actions: load/categorize UI schema + execute actions with param mapping and dialog values.
- Connection records persistence: store recent/saved connections and rehydrate.

These controllers expose a small observable state and imperative actions, so UIs can be replaced without rewriting the logic.

### G4. Protocol-forward compatibility

Keep types flexible and forward-compatible with the existing backend and the future TS in-process backend:

- Preserve unknown fields from events and UI schema elements.
- Prefer “capabilities” discovery for optional features.
- Avoid baking in React Native specifics (e.g. `Alert`, `AsyncStorage`, `Clipboard`).

### G5. Prepare for editor/desktop runtimes

Some frontends (VS Code extension) will run “on the user’s machine” and can access the user’s workspace filesystem. The plan should make it easy to:

- Use the REST backend today (talking to Python app)
- Swap to a future in-process TS backend with a host-provided filesystem/tool environment

## Non-goals (initially)

- Rewriting the Python server API.
  - We will *add* endpoints only when required for parity (e.g. feature completions), but avoid breaking changes.
- Designing a full cross-platform navigation framework.
- Implementing the TS port of `agent_core`/`agent_app` now.
- Unifying every visual detail across mobile/desktop (desktop can diverge).
