# Agent Guidelines

This file is the starting point when you’re asked to change behavior, add a feature, or debug an issue. It summarizes architecture, key directories, dev workflow, and testing/doc principles. For details, read the referenced modules and docs.

---

## 1. Project Overview

The AI Agent Platform is a **modular, functional agent framework** for building conversational apps on top of arbitrary LLM providers.

Main pieces:
- **Core SDK** (`core/python/agent_core`): pure conversation engine + plugin system.
- **Application layer** (`core/python/agent_app`): config loading, session & event stores, tool loop.
- **Terminal + HTTP + mobile integration app** (`application/python/agent_terminal_app`): FastAPI JSON API, prompt_toolkit terminal, and glue for mobile connectivity (direct HTTP, Bonjour/mDNS, and bridge service).
- **Mobile app** (`mobile/crystal-lattice-control-rn`): React Native client (Crystal Lattice Control) that connects to the terminal/HTTP app directly or via the bridge, providing a sessions/messages UI on phones and simulators.
- **Bridge service** (`bridge-elixir`): Elixir/Phoenix WebSocket bridge that lets mobile/desktop apps talk to local HTTP servers across networks using pairing + proxied HTTP requests.
- **Built-in plugins** (`core/python/plugins`): providers, extensions, features, tools.
- **Examples & tests** (`core/python/examples`, `core/python/tests`, `application/python/tests`, `plugins/*/tests`).

Design principles:
- Immutable core types (`Message`, `Session`); operations return new objects.
- Plugin-based providers/features/tools; core only orchestrates.
- Streaming-first APIs.
- Application-managed sessions, config, and persistence.
- Returned data structures are treated as immutable by convention; **avoid defensive copying** just to guard against potential mutation.

---

## 2. Architecture & Key Directories

**Core SDK – `core/python/agent_core`**
- `core.py`: `AgentCore` – session/message ops, request/streaming pipeline, tool orchestration, native history.
- `types.py`: immutable data types and plugin Protocols.
- `plugin/`: wrappers for providers, extensions, features, tools; default adapters.
- `utils.py`: `pipeline` and logging helpers.

**Application layer – `core/python/agent_app`**
- `application_future.py`: `AgentApplication` – loads config, discovers plugins, builds per-agent cores, exposes `send_request` (event stream).
- `tool_loop.py`: `ToolLoopRunner` – drives LLM + tool loop on top of `AgentCore`.
- `sessions.py`: `FilesystemSessionStore`.
- `events.py`: `InMemoryEventStore`.

**Terminal & HTTP app – `application/python/agent_terminal_app`**
- `server.py`: FastAPI routes; maps HTTP JSON to `AgentApplication`, exposes both agent/session APIs and small demo endpoints used by the mobile app (e.g. `/api/data`, `/api/hello`).
- `terminal_app.py`: `TerminalApplication` – terminal-facing app API (sessions, delete/modify/list, agents, plugins, overrides).
- `terminal.py`: CLI UI (slash commands, shortcuts); calls `TerminalApplication` only.
- `event_rendering.py`: how streamed events (assistant, reasoning, tools) are printed.
- `bonjour.py` / `bridge_client.py`: integration helpers so the mobile app can connect via direct address, Bonjour discovery, or the bridge service.

See `application/python/agent_terminal_app/AGENTS.md` for directory-specific guidelines when working on the server, terminal, or mobile/bridge integration.

**Mobile app – `mobile/crystal-lattice-control-rn`**
- React Native app (Crystal Lattice Control) that talks to the terminal/HTTP app and bridge.
- Connection methods: manual IP/port, Bonjour/mDNS discovery, and bridge WebSocket.
- Main pieces:
  - `App.tsx`: connection flow; constructs SDK transports (`FetchTransport` / `BridgeTransport`) and a backend (`RestAgentBackend`).
  - `src/ConnectedRoot.tsx`: bottom-tab navigation (Connection / Sessions / Messages).
  - `src/api.ts`: type-only re-export shim (SDK types).
  - `src/components/MessageBubble.tsx`: per-role message renderers (user/system/tool/assistant) including collapsible tool results and reasoning.
  - `src/SessionsScreen.tsx`, `src/SessionChatScreen.tsx`, `src/ConnectionScreen.tsx`: screens for listing sessions, viewing messages, and connection status.

See `mobile/crystal-lattice-control-rn/AGENTS.md` for React Native–specific guidelines, styling rules, and notes on message rendering and scrolling behavior.

**Bridge service – `bridge-elixir`**
- Distributed Elixir/Phoenix bridge that:
  - Accepts "server" WebSocket clients (e.g. Python `agent_terminal_app`).
  - Accepts "app" WebSocket clients (e.g. the React Native demo).
  - Manages pairing (6-digit codes) and sessions.
  - Forwards serialized HTTP requests/responses between app and server.

See `bridge-elixir/AGENTS.md` for directory-specific guidelines and deployment notes.

**Cloud orchestrator – `cloud-orchestrator`**
- Elixir/Phoenix service plus runtime/deploy assets for remote cloud agents.

See `cloud-orchestrator/AGENTS.md` for orchestrator-specific test realism rules and related test references.

**Plugins**
- Built-in plugins: `core/python/plugins` (Python package `plugins.*`)
  - Providers: e.g. `openai_provider.py`, `echo_openai_like_provider.py`.
  - Extensions/features/tools: reasoning, request-options, system-message, shell, file reader/writer, math, apply-patch.
- Optional plugin repos: `plugins/` (each is separately installable and/or loadable via `path:`)
  - OpenRouter provider bundle: `plugins/openrouter` (Python package `openrouter_plugins.*`).

**Docs & scripts**
- Root: `ARCHITECTURE.md`, `PROJECT_PLAN.md`, `TYPES_AND_PROTOCOLS.md`, `DEVELOPMENT.md`, `EXAMPLES.md`.
- API docs: `docs/api/core-sdk.md`, `docs/reference/agent_core/*`.
- Plugin guide: `docs/plugins/development.md`.
- Provider plugin guide (canonical): `plugins/docs/provider-plugins.md`.
- Examples generator: `scripts/generate_examples_md.py`.

---

## 3. Development Workflow

**Setup (Python 3.10+)**
- Core + plugins:
  ```bash
  cd core/python
  pip install -e ".[dev]"
  ```
- Terminal app:
  ```bash
  cd application/python
  pip install -e .
  ```

**Tests**
- Major Python test locations:
  - `core/python/tests`
  - `core/python/examples/tests`
  - `application/python/tests`
  - `plugins/openrouter/tests`
  - `plugins/openai_responses/tests`
  - `plugins/reference-openai-compatible-provider/tests`
- Default package-local `pytest` runs are intentionally narrow:
  - `core/python`: excludes `integration`
  - `application/python`: excludes `integration` and `docker`
  - `plugins/openrouter`: excludes `integration`
  - `plugins/openai_responses`: excludes `integration` and `manual_integration`
  - `plugins/reference-openai-compatible-provider`: excludes `integration`
- Fast default verification:
  - `pytest core/python/tests -q`
  - `pytest application/python/tests -q`
  - `pytest plugins/openrouter/tests -q`
  - `pytest plugins/openai_responses/tests -q`
  - `pytest plugins/reference-openai-compatible-provider/tests -q`
- Integration verification:
  - Core non-API integration: `pytest core/python/tests -m 'integration and not api and not slow_integration' -q`
  - Application non-API integration: `pytest application/python/tests -m 'integration and not api and not slow_integration and not docker' -q`
  - Local Ollama verification: `pytest core/python/tests -m 'ollama and not api' -q`
- Hosted API verification:
  - Examples / SDK smoke tests: `pytest core/python/examples/tests -m 'integration and api and not slow_integration' -q`
  - Application hosted API: `pytest application/python/tests -m 'integration and api and not slow_integration and not docker' -q`
  - OpenRouter: `pytest plugins/openrouter/tests -m 'integration and api and not slow_integration and openrouter' -q`
  - OpenAI Responses: `pytest plugins/openai_responses/tests -m 'integration and api and not slow_integration and openai' -q`
  - Reference provider Fireworks: `pytest plugins/reference-openai-compatible-provider/tests -m 'integration and api and not slow_integration and fireworks' -q`
  - Reference provider Z.ai: `pytest plugins/reference-openai-compatible-provider/tests -m 'integration and api and not slow_integration and zai' -q`
- Slow integration verification:
  - Run slow suites selectively, usually by package marker or single file rather than all at once.
  - OpenRouter slow hosted suites: `pytest plugins/openrouter/tests -m 'slow_integration and openrouter' -q`
- Provider follow-up for major changes:
  - For major provider, request-pipeline, tool-loop, or default-config changes, explicitly consider follow-up verification in `plugins/openrouter`, `plugins/openai_responses`, and `plugins/reference-openai-compatible-provider`.
- Coverage (core focus):
  ```bash
  pytest core/python/tests -v --cov=core/python/agent_core --cov-report=term-missing
  ```

**Lint / format / typecheck (from repo root)**
- `ruff check core/python/agent_core core/python/tests core/python/examples core/python/plugins`
- `black core/python/agent_core core/python/tests core/python/examples core/python/plugins`
- `pyright`

**Docs**
- `mkdocs serve` / `mkdocs build`
- After changing examples: run the relevant example tests selectively, then `python scripts/generate_examples_md.py`

---

## 4. Where to Change What

**Core behavior (`agent_core`)**
- Change `core/python/agent_core/core.py` when you need new capabilities that all apps share:
  - Session/message operations, streaming behavior, native history, provider selection, tool orchestration.
- Change `types.py` or `plugin/*.py` when you touch public types or plugin-wrapping behavior.
- Tests: `core/python/tests` (+ example tests if examples demonstrate the change).

**Plugins (`core/python/plugins`)**
- Add/modify providers, extensions, features, tools here.
- Use `docs/plugins/development.md` and `core/python/agent_core/types.py` as protocol references.
- Provider-specific authoring guide: `plugins/docs/provider-plugins.md`.
- Tests: plugin-focused tests under `core/python/tests` and, if relevant, example tests.

**Application layer (`agent_app`)**
- Use `core/python/agent_app/application_future.py` and `tool_loop.py` when changing:
  - Config loading/placeholder resolution.
  - Agent ↔ plugin wiring.
  - Request API and tool-loop semantics.
- Session/event storage: `sessions.py`, `events.py`.
- Tests: `core/python/tests/test_application_layer_*.py` and related.

**Terminal & HTTP app (`agent_terminal_app`)**
- HTTP API behavior: `server.py`.
- Terminal behavior and business logic: `terminal_app.py` (history ops, agent switching, plugin toggling, overrides).
- CLI UX and commands: `terminal.py` (keep UI-only; delegate logic to `TerminalApplication`).
- Event printing: `event_rendering.py`.
- Tests: `application/python/tests`.

---

## 5. Plugin Development (Summary)

- Plugins are plain classes with instance methods, using explicit `state: dict`.
- Instances are short-lived per request; avoid persistent mutable attributes.
- Providers/extensions/features share provider state; tools keep separate tool state.

**Provider plugins** (`ProviderPlugin`)
- Implement `init(config)`, `call_api` or `stream_api`, `process_chunk`, `finalize`.
- Rely on default adapters for `to_native_messages`, `from_native_messages`, `initialize_request` when possible.
- Put implementations in `core/python/plugins` and add unit/integration tests.

**Extensions & features**
- Extensions (`ProviderExtensionPlugin`): hot-path streaming enrichments + finalize.
- Features (`FeaturePlugin`): cold-path per-turn behavior, operate in `init` / `initialize_request` / `finalize`.

**Tools** (`ToolPlugin`)
- Implement `init`, `get_tool_schemas`, `execute_tool`, `format_tool_result` (and optionally `stream_tool`, `to_display_format`).
- Register via `AgentCore.register_tool`; use `get_tool_schemas`, `iter_tool_messages`, `execute_tool_calls` in apps.

---

## 6. Testing & Documentation Principles

**When to add tests**
- Any new public behavior or API surface.
- Any bugfix (add a regression test that fails before the fix).
- Any change in `agent_core`, `agent_app`, `agent_terminal_app`, or built-in plugins visible to users.

**What to test**
- Prefer **unit tests** first (pure functions, protocol implementations, small helpers).
- Use **integration tests** for multi-layer flows or provider-backed behavior; mark them with `integration`.
- Add `api` for hosted real-provider tests that require credentials and may incur cost.
- Add `slow_integration` for broad, high-latency, or expensive integration suites that should be run selectively.
- Keep provider selectors such as `openrouter`, `openai`, `ollama`, `gemini`, `fireworks`, `zai`, plus `docker` and `manual_integration`, so specific integration slices stay easy to target.
- Treat `not integration` as the practical quick filter for local verification; some intentionally fast local Ollama coverage may still remain in that path if it is not marked `integration`.
- Use **example / end-to-end tests** for high-level flows (`core/python/examples/tests`, `application/python/tests`).

**Test realism**
- Integration/e2e tests must exercise realistic public user/deployment flows. Do not make a test pass by adding test-only shortcuts, direct internal endpoints, special overrides, or alternate paths that hide an important product defect.
- If a realistic test exposes a real issue, keep the test realistic and fix the product code. If the fix is out of scope, report the failing test and exposed issue clearly instead of weakening the test.
- When a requested or required test is gated by markers, flags, or environment variables, run it with the appropriate marker/flag/env enabled instead of accepting a skipped result as success. The main Python suites in `core/python/tests`, `core/python/examples/tests`, `application/python/tests`, `plugins/openrouter/tests`, `plugins/openai_responses/tests`, and `plugins/reference-openai-compatible-provider/tests` bootstrap the repo-root `.env` via suite `conftest.py` without overwriting already-exported env vars, but do not assume every other suite in the repo does. Report a skipped gated test as "not run" unless you explicitly enabled the gate and verified the skip is intentional for the current task.

**Design/testing style**
- Keep code functional/immutable; avoid in-place mutation of shared data.
- Do not add shallow copies (e.g. `dict(...)`, `list(...)`) purely to "protect" returned structures; callers are expected to treat them as immutable.
- Assert on data structures (sessions, messages, events), not logs.
- For history-modifying features (`slice_session`, `modify_message`, `/delete`, `/modify`), cover both core and app/terminal behavior.

**Plugin + test fixture placement**
- Do not add new `core/python/tests` that depend on repo-root `plugins/` (use `core/python/tests/fixtures` instead).
- Test-only plugins/fixtures live under `core/python/tests` (prefer `core/python/tests/fixtures`).
- Simple/manual plugins that ship with the core package live under `core/python/plugins`.
- Production plugins live under repo-root `plugins/`, and their tests live alongside them.

**When to update docs**
- Changing core APIs, plugin protocols, or application behavior:
  - Update: `TYPES_AND_PROTOCOLS.md`, `docs/api/core-sdk.md`, relevant `docs/reference/agent_core/*`, `DEVELOPMENT.md`, `application/python/README.md` as appropriate.
- Changing examples or adding new ones:
  - Update example code + tests, then regenerate `EXAMPLES.md`.

Treat tests, type hints, and documentation updates as part of “done” for any substantive change.
