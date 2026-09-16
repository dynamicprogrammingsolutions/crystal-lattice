# Agent Guidelines

This file is the starting point when you’re asked to change behavior, add a feature, or debug an issue. It summarizes architecture, key directories, dev workflow, and testing/doc principles. For details, read the referenced modules and docs.

---

## Project Overview

The AI Agent Platform is a **modular, functional agent framework** for building conversational apps on top of arbitrary LLM providers.

Main pieces:
- **Core SDK** (`core/python/agent_core`): pure conversation engine + plugin system.
- **Application layer** (`core/python/agent_app`): config loading, session & event stores, tool loop.
- **Terminal + HTTP + mobile integration app** (`application/python/agent_terminal_app`): FastAPI JSON API, prompt_toolkit terminal, and glue for mobile connectivity (direct HTTP, Bonjour/mDNS, and bridge service).
- **Mobile app** (`mobile/crystal-lattice-control-rn`): React Native client (Crystal Lattice Control) that connects to the terminal/HTTP app directly or via the bridge, providing a sessions/messages UI on phones and simulators.
- **Desktop app** (`desktop/crystal-lattice-control-desktop-rn`): React Native macOS desktop client for Crystal Lattice Control.
- **Shared packages** (`packages/`): shared frontend SDKs, React bindings, React Native components, and tool-host packages used by mobile, desktop, and related runtimes.
- **Bridge service** (`bridge-elixir`): Elixir/Phoenix WebSocket bridge that lets mobile/desktop apps talk to local HTTP servers across networks using pairing + proxied HTTP requests.
- **Built-in plugin projects** (`plugins/`): first-party plugin repos used by the current runtime and bundled layout, plus plugin docs and templates.
- **Core-packaged plugins** (`core/python/plugins`): older Python plugins shipped with `agent-core`, kept mainly for tests, compatibility, and a small set of package-local/core features.
- **Examples & tests** (`core/python/examples`, `core/python/tests`, `application/python/tests`, `plugins/*/tests`).

Design principles:
- Immutable core types (`Message`, `Session`); operations return new objects.
- Plugin-based providers/features/tools; core only orchestrates.
- Streaming-first APIs.
- Application-managed sessions, config, and persistence.
- Returned data structures are treated as immutable by convention; **avoid defensive copying** just to guard against potential mutation.

---

## Architecture & Key Directories

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

**Desktop app – `desktop/crystal-lattice-control-desktop-rn`**
- React Native macOS desktop client for Crystal Lattice Control.
- Reuses shared workspace packages from `packages/`.
- See `desktop/crystal-lattice-control-desktop-rn/README.md` for setup and workflow details.

**Shared packages – `packages/`**
- Shared workspace packages used by mobile, desktop, and tool runtimes.
- Main examples:
  - `packages/frontend-sdk`
  - `packages/frontend-sdk-react`
  - `packages/frontend-rn-components`
  - `packages/tool-host-node`
  - `packages/react-native-mac-text-view`
- Check the package-local README before changing shared interfaces or package-specific build/test behavior.

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
- Built-in plugin projects: `plugins/`
  - First-party plugin repos used by the current runtime and bundled layout.
  - Contains Python plugin packages, Node/Bash tool packages, templates, and shared plugin docs.
  - Depending on plugin type, loaders may use `path:`, `node:`, or `bash:` sources.
  - Start with `plugins/AGENTS.md` and `plugins/docs/index.md`.
- Core-packaged plugins: `core/python/plugins` (Python package `plugins.*`)
  - Older plugins that still ship inside `agent-core`.
  - Used mainly for tests, compatibility, and a small set of package-local/core features.
  - Do not place new plugins here without explicit user consent.

**Documentation & scripts**
- Root: `ARCHITECTURE.md`, `TYPES_AND_PROTOCOLS.md`, `EXAMPLES.md`.
- Development documentation and conventions: `docs/development/index.md`.
- Guidance-maintenance specifications: `maintainer/specifications/`.
- API docs: `docs/api/core-sdk.md`, `docs/reference/agent_core/*`.
- Current plugin docs: `plugins/docs/*`; start with `plugins/docs/index.md`.
- General plugin overview: `plugins/docs/overview.md`.
- Examples generator: `scripts/generate_examples_md.py`.

## Documentation ownership and routing

Start package work with its `README.md`, nearest `AGENTS.md`, and `docs/index.md`
when present. Use the smallest structure that helps the reader.

Put package-user documentation under `<package>/docs/` and current internals,
architecture, testing, and specifications under
`<package>/docs/development/`. Keep root `docs/` for project-wide guidance,
cross-package architecture and behavior, and site entry points.

Specifications define intended targets, requirements track live implementation,
verification, and documentation, and tasks track approval and execution.
Published user and developer documentation describes available behavior.
Branch-only target text is marked `Not implemented` and is not published as
current guidance by default. Update only maintained sources affected by a
behavior change.

Use requests and conversations for outcomes, tasks for approved work,
specifications and requirements for behavior, and code, tests, and
documentation for current behavior. Choose terminology and organization for
each file or record; do not copy labels or structure from an earlier context.
Replace inherited planning or tracking terminology unless it is required or
established by the product, public interface, or relevant domain.

Examples: a task heading named “Deployment workstream” does not become a
specification heading; an inherited “Implementation checkpoint” heading in
user documentation is replaced with the supported capability; an established
public `retry_after` field remains exact.

Change generated documentation through its maintained source or generator;
never edit `docs_site/prepared/` or `docs_site/dist/` directly. If generation is
blocked, preserve the boundaries and report the remaining action. Commands are
maintained in the Crystal Lattice conventions.

Document verified facts; do not reconstruct unfamiliar areas or normalize
unrelated variations.

Before creating, moving, or materially restructuring documentation or
specifications, read both files in full:

- `docs/development/documentation.md`
- `docs/development/crystal-lattice-documentation.md`

A local factual correction does not require unrelated structure guidance when
the page, reader, and maintained source are clear.

When changing this guidance, task guidance, publication rules, or their
validation, also read:

- `maintainer/specifications/documentation-and-specification-standard/index.md`
- `maintainer/specifications/documentation-and-specification-standard/requirements.md`

**Auxiliary directories**
- `evaluations/`: shared evaluation framework and benchmark suites.
- `tasks/`: task handoff files used for planning and delegated follow-up work.
- `test/`: repository-level shared test support and cross-cutting tests.
- `archive/`: historical conversations, plans, notes, and diagnostics; not current guidance.
- `artifacts/`, `build/`, `dist/`, `tmp/`: generated outputs, staging areas, and local scratch space.
- `test_dir/`: ad hoc local scratch/test workspace.

---

## Development Workflow

**Commit guidance**

Create a commit only when the user explicitly requests one in the current conversation. Use a short, clear message—usually two to six words—without type or scope prefixes unless a specific format is requested. Stage only files belonging to the requested work and leave unrelated changes unstaged.

Examples: `Improve error handling`, `Add cache validation`, `Update deployment notes`.

**Setup (Python 3.10+)**
- Core SDK + core-packaged plugins:
  ```bash
  python -m pip install -e "core/python[dev]"
  ```
- Terminal app against the local core checkout:
  ```bash
  python -m pip install -e application/python
  ```
- Built-in or optional plugin packages you are actively changing:
  ```bash
  python -m pip install -e "plugins/<plugin-name>[dev]"
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
  - OpenAI Responses non-API integration: `pytest plugins/openai_responses/tests -m 'integration and not api and not slow_integration and not manual_integration' -q`
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
- Shared workspace package verification:
  - Fast/default package tests:
    - `npm --workspace @crystal-lattice/frontend-sdk test`
    - `npm --workspace @crystal-lattice/frontend-sdk-react test`
    - `npm --workspace @crystal-lattice/frontend-rn-components test`
  - `packages/frontend-sdk` excludes `src/integration/**` from its default Vitest run; use explicit `integration:*` scripts for backend, hosted-provider, bridge, cloud, or AWS e2e coverage.
  - Frontend SDK integration commands are documented in `packages/frontend-sdk/src/integration/__tests__/README.md`; run hosted API, Docker, cloud, and AWS-backed suites selectively rather than all at once.
  - `packages/react-native-mac-text-view` and `packages/tool-host-node` currently do not define package-local automated test scripts.
- Coverage (core focus):
  ```bash
  pytest core/python/tests -v --cov=core/python/agent_core --cov-report=term-missing
  ```

**Lint / format / typecheck (from repo root)**
- `ruff check core/python/agent_core core/python/tests core/python/examples core/python/plugins`
- `black core/python/agent_core core/python/tests core/python/examples core/python/plugins`
- `pyright`

---

## Where to Change What

**Core behavior (`agent_core`)**
- Change `core/python/agent_core/core.py` when you need new capabilities that all apps share:
  - Session/message operations, streaming behavior, native history, provider selection, tool orchestration.
- Change `types.py` or `plugin/*.py` when you touch public types or plugin-wrapping behavior.
- Tests: `core/python/tests` (+ example tests if examples demonstrate the change).

**Built-in And First-party Plugin Projects (`plugins/`)**
- Add/modify providers, provider extensions, features, tools, application plugins, and related tool packages here.
- Start with `plugins/AGENTS.md` and `plugins/docs/index.md`.
- Use `plugins/docs/provider-plugins.md`, `plugins/docs/provider-extensions.md`, `plugins/docs/feature-plugins.md`, `plugins/docs/tool-plugins.md`, and `plugins/docs/application-plugins.md` as the current authoring docs.
- Tests live alongside each plugin project under `plugins/<plugin>/tests`.

**Core-packaged plugins (`core/python/plugins`)**
- This is the older in-package plugin directory for `agent-core`.
- Use it mainly for tests, compatibility, and a small set of package-local/core features that truly belong in the core package.
- Do not place new plugins here without explicit user consent.
- Tests remain primarily under `core/python/tests`.

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

## Plugin Development (Summary)

- Plugins are plain classes with instance methods, using explicit `state: dict`.
- Instances are short-lived per request; avoid persistent mutable attributes.
- Providers/extensions/features share provider state; tools keep separate tool state.
- For new first-party plugin work, prefer repo-root `plugins/` unless there is a clear reason the code must stay in the core package.

**Provider plugins** (`ProviderPlugin`)
- Implement the hooks your provider actually needs.
- Default adapters can supply `to_native_messages`, `from_native_messages`, `initialize_request`, `finalize`, and `stream_api` when they are omitted.
- Put new first-party implementations in repo-root `plugins/` and add unit/integration tests alongside the plugin project.

**Extensions & features**
- Extensions (`ProviderExtensionPlugin`): hot-path streaming enrichments + finalize.
- Features (`FeaturePlugin`): cold-path per-turn behavior, operate in `init` / `initialize_request` / `finalize`.
- See `plugins/docs/provider-extensions.md`, `plugins/docs/feature-plugins.md`, and `plugins/docs/actions.md` for the current hook surface.

**Application plugins** (`ApplicationPlugin`)
- Application-layer plugins live above `AgentCore` and can expose actions and UI schema with access to sessions, persistence, and multi-session workflows.
- Protocol: `core/python/agent_app/app_plugins.py`
- Docs: `plugins/docs/application-plugins.md`

**Tools** (`ToolPlugin`)
- Implement the hooks you need such as `init`, `get_tool_schemas`, `execute_tool`, and `format_tool_result`; optional hooks include preparation, streaming, async, and display helpers.
- Register via `AgentCore.register_tool`; use `get_tool_schemas`, `iter_tool_messages`, `execute_tool_calls` in apps.
- Tool-packaged plugins can be Python, Node, or Bash depending on the loader.
- Docs: `plugins/docs/tool-plugins.md`, `plugins/docs/node-tool-plugins.md`, `plugins/docs/bash-tool-plugins.md`, and `plugins/docs/tool-interop.md`.

---

## Testing Principles

**When to add tests**
- Any new public behavior or API surface.
- Any bugfix (add a regression test that fails before the fix).
- Any change in `agent_core`, `agent_app`, `agent_terminal_app`, built-in plugin projects, or core-packaged plugins visible to users.

**What to test**
- Use the least expensive test that proves the requirement without bypassing
  the important boundary. Unit and component tests suit pure functions,
  protocol implementations, local state, and rendering behavior.
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
- Describe coverage by the boundary it actually crosses. Direct route-function calls are not HTTP integration tests, mocked frontend tests are not backend integration tests, and deterministic simulator harnesses are native UI tests rather than network/server end-to-end tests.
- Count a test run as successful only when the requested tests are collected and the command exits successfully. Collection failures, teardown errors, open handles, or background-timer errors after passing assertions still make the run incomplete or failed.
- When behavior crosses server, transport, and UI boundaries, include at least one integration test that uses the public backend/HTTP API and production frontend adapter.
- Treat shared test harnesses as production test infrastructure: keep them type-checkable, verify an existing consumer when they change, and do not count tests that fail before collection.

**Design/testing style**
- Keep code functional/immutable; avoid in-place mutation of shared data.
- Do not add shallow copies (e.g. `dict(...)`, `list(...)`) purely to "protect" returned structures; callers are expected to treat them as immutable.
- Assert on data structures (sessions, messages, events), not logs.
- For history-modifying features (`slice_session`, `modify_message`, `/delete`, `/modify`), cover both core and app/terminal behavior.
- Put stable test identifiers or accessibility labels on production entity rows, action triggers, and dialog controls. Do not create harness-only copies of production UI solely to make native tests selectable.
- Exercise shared helpers through at least one real consumer; do not replace the helper with a duplicate implementation in the consumer's test mock.
- In React Native unit/component tests, mock native host-component packages at their public package boundary while preserving the props, events, and imperative ref methods used by consumers.

**Plugin + test fixture placement**
- Keep package-specific tests and fixtures in the owning package's test directory.
- Put cross-cutting tests and fixtures used by multiple packages or runtimes under `test/`; put shared fixture files under `test/fixture/`.
- Do not add new `core/python/tests` that depend on repo-root `plugins/` (use `core/python/tests/fixtures` instead).
- Test-only plugins/fixtures live under `core/python/tests` (prefer `core/python/tests/fixtures`).
- Core-packaged plugins that still ship with `agent-core` live under `core/python/plugins`.
- First-party built-in plugin projects live under repo-root `plugins/`, and their tests live alongside them.
- Do not add new plugin projects under `core/python/plugins` without explicit user consent.

Treat applicable tests, type hints, and documentation updates as part of
“done” for substantive changes.

## Long-running work and waiting

- Start safe, authorized commands expected to take longer than 10 minutes in
  the background, and keep a process ID, log, or other status mechanism.
- Continue independent in-scope work while background commands run. Use
  waiting intervals only when completion blocks the remaining work.
- Monitor at intervals of up to 10 minutes. Limit waiting-only work to two
  hours or 12 wait calls.
- Read the current time at the start of commands whose behavior depends on it.

For example, start a long-running command and continue other work:

```bash
nohup <command> > /tmp/<task-name>.log 2>&1 < /dev/null &
pid=$!
```

Check it later:

```bash
date -u
kill -0 "$pid" && tail -n 50 /tmp/<task-name>.log
```

For a scheduled wait, calculate from the current time read by that command:

```bash
now=$(date -u +%s)
(( now < target_epoch )) &&
  sleep $(( target_epoch - now < 600 ? target_epoch - now : 600 ))
```
