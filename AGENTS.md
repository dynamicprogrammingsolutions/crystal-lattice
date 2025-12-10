# AI Agent Platform – Contributor Guide

This file is the starting point when you’re asked to change behavior, add a feature, or debug an issue. It summarizes architecture, key directories, dev workflow, and testing/doc principles. For details, read the referenced modules and docs.

---

## 1. Project Overview

The AI Agent Platform is a **modular, functional agent framework** for building conversational apps on top of arbitrary LLM providers.

Main pieces:
- **Core SDK** (`core/python/agent_core`): pure conversation engine + plugin system.
- **Application layer** (`core/python/agent_app`): config loading, session & event stores, tool loop.
- **Terminal + HTTP app** (`application/python/agent_terminal_app`): FastAPI JSON API and prompt_toolkit terminal.
- **Built-in plugins** (`core/python/plugins`): providers, extensions, features, tools.
- **Examples & tests** (`core/python/examples`, `core/python/tests`, `application/python/tests`).

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
- `server.py`: FastAPI routes; maps HTTP JSON to `AgentApplication`.
- `terminal_app.py`: `TerminalApplication` – terminal-facing app API (sessions, delete/modify/list, agents, plugins, overrides).
- `terminal.py`: CLI UI (slash commands, shortcuts); calls `TerminalApplication` only.
- `event_rendering.py`: how streamed events (assistant, reasoning, tools) are printed.

**Plugins – `core/python/plugins`**
- Providers: e.g. `openai_provider.py`, `openrouter_provider.py`.
- Extensions/features: e.g. reasoning, request-options, system-message.
- Tools: e.g. shell, file reader/writer, math, apply-patch.

**Docs & scripts**
- Root: `ARCHITECTURE.md`, `PROJECT_PLAN.md`, `TYPES_AND_PROTOCOLS.md`, `DEVELOPMENT.md`, `EXAMPLES.md`.
- API docs: `docs/api/core-sdk.md`, `docs/reference/agent_core/*`.
- Plugin guide: `docs/plugins/development.md`.
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
- Core + plugins:
  ```bash
  pytest core/python/tests -q
  ```
- Marked suites:
  - OpenRouter: `pytest core/python/tests -m openrouter -q`
  - All integration: `pytest core/python/tests -m integration -q`
  - Ollama-only: `pytest core/python/tests -m ollama -q`
- Examples: `pytest core/python/examples/tests -qs`
- Terminal app: `pytest application/python/tests -q`
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
- After changing examples: `pytest core/python/examples/tests -qs && python scripts/generate_examples_md.py`

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
- Use **integration tests** for multi-layer flows or real providers; mark them (`integration`, `openrouter`, `ollama`).
- Use **example / end-to-end tests** for high-level flows (`core/python/examples/tests`, `application/python/tests`).

**Design/testing style**
- Keep code functional/immutable; avoid in-place mutation of shared data.
- Do not add shallow copies (e.g. `dict(...)`, `list(...)`) purely to "protect" returned structures; callers are expected to treat them as immutable.
- Assert on data structures (sessions, messages, events), not logs.
- For history-modifying features (`slice_session`, `modify_message`, `/delete`, `/modify`), cover both core and app/terminal behavior.

**When to update docs**
- Changing core APIs, plugin protocols, or application behavior:
  - Update: `TYPES_AND_PROTOCOLS.md`, `docs/api/core-sdk.md`, relevant `docs/reference/agent_core/*`, `DEVELOPMENT.md`, `application/python/README.md` as appropriate.
- Changing examples or adding new ones:
  - Update example code + tests, then regenerate `EXAMPLES.md`.

Treat tests, type hints, and documentation updates as part of “done” for any substantive change.
