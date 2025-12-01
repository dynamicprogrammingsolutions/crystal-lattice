# Application Layer MVP Plan

## Goal
- Introduce a minimal **Python Application Layer** that sits above `AgentCore`, owns configuration and session persistence, and exposes a simple dict-based API that future HTTP/WebSocket/JSON‑RPC servers can call.
- Ensure **stateless per-call behavior** for consumers:
  - Every call uses a `session_id` and/or `request_id`.
  - Sessions are always loaded from disk at the start and saved back at the end.
  - No long‑lived in‑memory session map; only in‑flight streaming requests keep ephemeral state.
- Keep the design aligned with **functional core, imperative shell**:
  - `AgentCore` + `Session` remain pure/immutable.
  - Application Layer performs orchestration, I/O, tool loops, plugin registration, and event emission.

## Context (Current Core Architecture)
- `agent_core.core.AgentCore`:
  - Stores plugin wrappers (providers, extensions, features, tools) and internal caches only; **no application/session state**.
  - Provides pure methods: `create_session`, `add_message`, `send_request`, `send_request_stream`, `send_request_stream_async`, `execute_tool_calls`, `export_session`, `import_session`, `get_tool_schemas`, `get_config_schema`, `get_ui_schema`, `discover_and_register`.
  - Uses immutable `Session` and `Message` dataclasses from `agent_core.types`.
  - Handles provider-native history retention in `session.metadata.native_messages` with integrity verification.
- Configuration model (architecture docs):
  - Application loads JSON config, resolves `${env:...}` and `${file:...}`.
  - Core receives a **flat dict per request** (no nested plugin structure required) and does not manage config itself.
- Tool execution:
  - Core exposes `execute_tool_calls(tool_calls, config) -> list["tool" messages]` but **does not own the tool loop**.
  - Application is expected to detect tool calls in assistant messages, call `execute_tool_calls`, append tool results as messages, and then call `send_request` / `send_request_stream` again.

## Scope of This MVP

### In scope

- A Python package for the Application Layer at `core/python/agent_app`.
- A main `AgentApplication` class that:
  - Lives for the life of the application process.
  - Owns a configured `AgentCore` instance.
  - Exposes **separate actions**:
    - `create_session` (explicitly required before any usage).
    - `add_message` (append messages to a session).
    - `send_request` (execute LLM + tool loop, non‑streaming or streaming based on a flag in the request dict).
    - `get_events` (poll events for streaming requests).
  - Never keeps complete sessions in memory across calls (sessions are always reloaded from disk).
- A **configuration module** that:
  - Loads JSON configuration.
  - Resolves `${env:...}` and `${file:...}` placeholders.
  - Provides an `agents` mapping with a provider name per agent.
  - Provides a `plugins` section listing which plugin classes to register (providers, features, tools, extensions).
  - Produces **flat per-request config dicts** for `AgentCore` by merging provider defaults and agent-specific overrides (plugin defaults are deferred).
- A **session persistence layer** that:
  - Persists `Session` objects to disk using `AgentCore.export_session` / `import_session`.
  - Stores each session as one JSON file at `<session_root>/<session_id>.json`.
  - Preserves `session.metadata` (including provider-native history and `agent_id`).
- A **tool execution loop** inside the Application Layer that runs for **both non‑streaming and streaming** requests.
- A **background streaming execution model**:
  - `send_request` with `{"stream": true}` returns immediately with a `request_id`.
  - Streaming work runs in the background using `AgentCore.send_request_stream` and the tool loop.
  - Results are emitted as discrete **events** and retrievable via polling (`get_events`) or pluggable listeners.
- Tests under `core/python/tests/` that simulate how API consumers would interact with this layer.

### Explicitly not included / deferred

These items are **not** part of this MVP plan. They may be implemented later or refined during development:

- HTTP or WebSocket servers (FastAPI/Express) and routing.
- Frontend/UI integration.
- Database-backed session or event storage (filesystem + in‑memory events only).
- Cross-language Application Layer (Python only).
- Configuration‑driven plugin defaults and advanced config validation.
- Multi-tenant or multi-environment session namespacing beyond flat `session_id` → JSON mapping.
- Backpressure, rate limiting, or complex scheduling for background streaming tasks.
- Persistent event logs across process restarts.
- Automatic schema generation for the application API (OpenAPI/JSON Schema).
- Multi-agent orchestration in one call (only single agent per session).

## Proposed Module Structure (Python)

> Exact file names can be adjusted; this is a concrete starting point.

- `core/python/agent_app/`
  - `__init__.py`
    - Expose `AgentApplication` and any public helper functions.
  - `application.py`
    - Implementation of the main `AgentApplication` class.
  - `config.py`
    - Configuration loading, placeholder resolution, plugin registration lists, per-agent config derivation.
  - `sessions.py`
    - Session persistence abstractions (filesystem-backed `SessionStore`).
  - `events.py`
    - Event store abstraction and in‑memory implementation for streaming events.

- Tests
  - `core/python/tests/test_application_layer_basic.py`
  - `core/python/tests/test_application_layer_streaming.py`
  - `core/python/tests/test_application_layer_tools.py`
  - `core/python/tests/test_application_layer_config.py`

## Configuration Module Design (`agent_app.config`)

### 1) Config file shape (on disk)

MVP JSON structure reflecting your requirements:

```jsonc
{
  "core": {
    // Optional core-level settings (e.g. log level)
  },
  "providers": {
    "openrouter": {
      "provider": "openrouter",      // Name understood by AgentCore
      "base_url": "https://...",
      "api_key": "${env:OPENROUTER_API_KEY}",
      "timeout": 30
    }
  },
  "plugins": {
    // Which plugin classes to load and register
    "providers": [
      "plugins.openrouter_provider.OpenRouterProvider"
    ],
    "features": [
      "plugins.system_message_feature.SystemMessageFeature",
      "plugins.request_options_feature.RequestOptionsFeature"
    ],
    "tools": [
      "plugins.file_reader_tool.FileReaderTool",
      "plugins.math_tools.CalculatorTool"
    ],
    "extensions": [
      "plugins.ollama_thinking_extension.OllamaThinkingExtension"
    ]
  },
  "agents": {
    "default": {
      "provider": "openrouter",          // Key into providers{} above
      // Agent-level overrides (flattened keys used by provider + plugins)
      "model": "anthropic/claude-3.5",
      "request_options": {"temperature": 0.3}
    }
  }
}
```

Key ideas:
- `agents[agent_id]["provider"]` selects a provider from `providers`.
- `plugins` lists **which plugin classes** to import and register with `AgentCore`.
- Plugin defaults (e.g. `system_message_feature.system_files`) are **not** handled in this MVP; all effective config used by plugins will come from provider + agent config as flat keys.

### 2) Config loading & placeholder resolution

Functions:

- `load_raw_config(path: str | Path) -> dict`
  - Read JSON from disk without modification.

- `resolve_placeholders(raw: dict, env: Mapping[str, str] = os.environ) -> tuple[dict, list[dict]]`
  - Recursively walk the config and replace:
    - `${env:VAR_NAME}` with `env.get(VAR_NAME, "")`.
    - `${file:path/to/file}` with file contents (or `""` on error).
  - Collect **non-fatal errors** instead of raising:
    - Each error entry could be: `{ "path": "providers.openrouter.api_key", "type": "env_missing", "detail": "OPENROUTER_API_KEY not set" }`.
  - Return `(resolved_config, errors)` so the caller (server/CLI/tests) can decide whether to fail fast or just warn the user.

### 3) Per-agent config derivation

- `build_agent_config(resolved_config: dict, agent_id: str) -> dict`
  - Steps:
    1. Fetch `agent = resolved_config["agents"][agent_id]`.
    2. Fetch `provider_name = agent["provider"]`.
    3. Fetch `provider_defaults = resolved_config["providers"][provider_name]`.
    4. Merge into a **flat dict**:
       - Start from `provider_defaults`.
       - Overlay agent-level keys (agent overrides provider defaults).
    5. Ensure a top-level `"provider"` key is present for `AgentCore` selection:
       - Use `provider_defaults["provider"]` if present, else fall back to `provider_name`.
  - Returns the per-agent base config used for all requests in that session.

- `resolve_request_config(base_agent_config: dict, overrides: dict | None) -> dict`
  - Merge per-request overrides into the base agent config.
  - Used when a client wants to change temperature/model/etc. for a single `send_request` call.

### 4) Plugin registration from config

- `load_plugins(plugin_config: dict) -> dict`
  - Import plugin classes from dotted paths listed under `plugin_config["providers"]`, `"features"`, `"tools"`, `"extensions"`.
  - Returns a summary dict:
    - `{ "providers": [ProviderClass, ...], "features": [...], "tools": [...], "extensions": [...] }`.
  - Import errors should be collected and surfaced similarly to placeholder resolution errors (non-fatal, caller decides what to do).

The `AgentApplication` constructor will then:
- Call `load_plugins`.
- For each provider, call `AgentCore.register_provider(provider_cls, extensions=[...])`.
- For each feature and tool, call `AgentCore.register_feature` / `AgentCore.register_tool`.
- Additionally expose helper methods (`register_provider`, `register_feature`, `register_tool`, `register_extension`) that delegate to the underlying `AgentCore` for test convenience or manual overrides.

### 5) Agent registry / lookup in sessions

- When creating a session via the Application Layer, store `session.metadata["agent_id"] = agent_id`.
- On `add_message` and `send_request`, the Application Layer:
  - Loads the `Session` from disk by `session_id`.
  - Reads `agent_id` from `session.metadata`.
  - Builds (or reuses cached) base config for that agent.

This ensures every call is scoped by `session_id`, and agent selection is stable for the session.

## Session Persistence Design (`agent_app.sessions`)

### 1) Abstraction

- `class SessionStore(Protocol)`
  - `def load(self, session_id: str) -> Session | None`
  - `def save(self, session: Session) -> None`
  - `def delete(self, session_id: str) -> None`

- `class FilesystemSessionStore(SessionStore)`
  - Constructor: `__init__(self, root_dir: Path)`.
  - Layout: `<root_dir>/<session_id>.json`.
  - Uses `AgentCore.export_session` / `import_session` for (de)serialization.
  - Writes atomically (temp file + rename) to avoid corruption.

### 2) Behavior

- **Create session**
  - Application calls `AgentCore.create_session()`.
  - Sets `session.metadata["agent_id"] = agent_id`.
  - Saves immediately via `SessionStore.save`.

- **Load session**
  - For any call that takes `session_id`, first call `SessionStore.load(session_id)`.
  - If not found, raise a clear error (no auto-creation; `create_session` is mandatory).

- **Update session**
  - Whenever `AgentCore` returns a new `Session` (end of non-streaming request or streaming phase), the Application overwrites the stored file with `save`.

- **Statelessness guarantee**
  - The `AgentApplication` does **not** keep a process-wide `dict[session_id, Session]`.
  - Between calls, only the serialized JSON files represent session state.
  - The only exception is **in-flight streaming requests**, which may temporarily hold the current `Session` and partial outputs until the request completes.

## Event Model and Streaming (`agent_app.events`)

### 1) Event store abstraction

- `class EventStore(Protocol)`
  - `def publish(self, event: dict) -> None`
  - `def list(self, *, since_id: str | None = None, request_id: str | None = None, session_id: str | None = None, limit: int = 100) -> list[dict]`

- `class InMemoryEventStore(EventStore)` (MVP)
  - Stores events in an in-memory list with monotonically increasing `event_id`.
  - Does **not** persist events across restarts.
  - May prune events after a request finishes or when exceeding a max size.

### 2) Event shapes

Events are plain dicts that always include at least:

- `"event_id"`: unique identifier within the process.
- `"request_id"`: ID of the logical request (one `send_request` call).
- `"session_id"`: session this event belongs to.
- `"type"`: e.g. `"partial"`, `"final"`, `"tool_calls"`, `"tool_results"`, `"session_updated"`, `"error"`.

Examples:

- Partial LLM output:

```jsonc
{
  "event_id": "e1",
  "type": "partial",
  "session_id": "s1",
  "request_id": "r1",
  "message": {"role": "assistant", "content": "Hello", "metadata": {}}
}
```

- Final LLM messages for a request:

```jsonc
{
  "event_id": "e2",
  "type": "final",
  "session_id": "s1",
  "request_id": "r1",
  "messages": [ {"role": "assistant", "content": "Hello!", "metadata": {}} ],
  "session": { /* serialized Session.to_dict() */ }
}
```

- Tool calls and results:

```jsonc
{
  "event_id": "e3",
  "type": "tool_calls",
  "session_id": "s1",
  "request_id": "r1",
  "tool_calls": [ /* normalized OpenAI-style tool call dicts */ ]
}

{
  "event_id": "e4",
  "type": "tool_results",
  "session_id": "s1",
  "request_id": "r1",
  "messages": [ /* tool messages added to session */ ]
}
```

Servers built on top of the Application Layer can:
- Use **long-polling** (`get_events` with `since_id`),
- Attach to a WebSocket and push events downstream, or
- Stream events over a single HTTP response (SSE, chunked encoding).

## Application Class Design (`agent_app.application`)

### 1) Construction

```python
class AgentApplication:
    def __init__(
        self,
        config_path: str | Path,
        session_root: str | Path,
        core_factory: Callable[[], AgentCore] = AgentCore,
        *,
        event_store: EventStore | None = None,
    ) -> None:
        ...
```

Responsibilities:
- Load raw config and call `resolve_placeholders`, surfacing any non-fatal errors to the caller.
- Build per-agent base configs via `build_agent_config`.
- Load plugin classes from `config["plugins"]` and register them on a single `AgentCore` instance.
- Initialize `FilesystemSessionStore` at `session_root`.
- Initialize an `EventStore` (in-memory by default) for streaming events.
- Expose helper registration methods for tests:
  - `register_provider`, `register_feature`, `register_tool`, `register_extension` → delegate to underlying `AgentCore`.

### 2) Public API: create_session (dict-based)

```python
def create_session(self, payload: dict) -> dict:
    """Create a new session for a given agent and persist it.

    Expected payload keys:
      - "agent_id": str
    Returns:
      - {"session": Session.to_dict(), "errors": [...]}  # errors from config resolution/imports, if any
    """
```

- Steps:
  1. Read `agent_id` from `payload`.
  2. Validate that `agent_id` exists in config.
  3. Use `core.create_session()` to create a `Session`.
  4. Set `session.metadata["agent_id"] = agent_id`.
  5. Persist via `SessionStore.save`.
  6. Return the serialized session dict (and any accumulated config/plugin errors, if we choose to surface them here).

### 3) Public API: add_message (dict-based)

```python
def add_message(self, payload: dict) -> dict:
    """Append a message to an existing session and persist it.

    Expected payload keys:
      - "session_id": str
      - "message": {"role": str, "content": str, "metadata"?: dict}

    Returns:
      - {"session": Session.to_dict()}
    """
```

- Steps:
  1. Load the session from disk by `session_id`.
  2. Call `core.add_message` with the provided message.
  3. Persist the new session via `SessionStore.save`.
  4. Return serialized session.

No automatic `send_request` happens here; the consumer must explicitly call `send_request` after adding messages.

### 4) Public API: send_request (non-streaming and streaming)

```python
def send_request(self, payload: dict) -> dict:
    """Send a request using the current session state.

    Expected payload keys:
      - "session_id": str
      - "config_overrides"?: dict   # per-call config overrides
      - "stream"?: bool             # default False; True for streaming

    Non-streaming (stream=False):
      - Runs tool loop to completion and returns final messages.
    Streaming (stream=True):
      - Starts background streaming + tool loop and returns immediately
        with a request_id; results are available via get_events.
    """
```

#### 4a) Non-streaming path (`stream` is False or absent)

Steps:
1. Load session from disk and derive `agent_id` and base agent config.
2. Merge any `config_overrides` into the base config.
3. Enter tool loop with `AgentCore.send_request`:
   - Call `session, final_messages = core.send_request(session, config)`.
   - Inspect `final_messages` for tool calls (OpenAI-style) via a helper.
   - If no tool calls, break.
   - Normalize tool calls and call `core.execute_tool_calls(tool_calls, config)`.
   - Emit a `tool_calls` and `tool_results` event (optional but consistent with streaming).
   - Append tool result messages to the session via `core.add_message`.
   - Repeat until no tool calls or hitting a `max_tool_loops` limit.
4. Persist final session via `SessionStore.save`.
5. Return a dict like:

```jsonc
{
  "session": { /* Session.to_dict() */ },
  "messages": final_messages  // last assistant messages from final LLM call
}
```

#### 4b) Streaming path (`stream` is True)

High-level behavior:
- `send_request` starts a background task and returns immediately with a `request_id`.
- The background task:
  - Uses `AgentCore.send_request_stream` for each LLM phase.
  - Runs the **same tool loop** as the non-streaming path, but interleaves events:
    - Partial events for LLM output.
    - Tool call/result events.
    - Final events after each LLM phase.
- All intermediate and final outputs are **published as events** with `session_id` and `request_id`.

Steps in the background task for one `send_request` call:
1. Load session, derive agent config as above.
2. Create a fresh `request_id` and publish an initial `{"type": "request_started", ...}` event.
3. Define a helper `stream_llm_phase(session, config) -> (session, final_messages)`:
   - Call `core.send_request_stream(session, config)`.
   - For each `"partial"` chunk from core:
     - Publish a `{"type": "partial", "message": chunk["message"], ...}` event.
   - On the core `"final"` chunk:
     - Extract `new_session` and `final_core_messages`.
     - Persist `new_session` to disk.
     - Publish a `{"type": "final", "messages": final_core_messages, "session": new_session.to_dict(), ...}` event.
     - Return `new_session, final_core_messages`.
4. Call `stream_llm_phase` once.
5. Inspect the returned `final_messages` for tool calls.
6. While there are tool calls (and under `max_tool_loops`):
   - Publish a `tool_calls` event.
   - Compute tool results via `core.execute_tool_calls`.
   - Append each tool message to the session via `core.add_message`.
   - Persist updated session and publish a `tool_results` event.
   - Call `stream_llm_phase` again for the follow-up LLM call.
7. When no more tool calls, publish a `{"type": "request_completed", ...}` event.

Return value of `send_request` for streaming path:

```jsonc
{
  "session_id": "s1",
  "request_id": "r1",
  "stream": true,
  "status": "started"
}
```

The consumer then polls `get_events` (or another transport-specific mechanism) to receive partials, tool progress, and finals.

### 5) Public API: get_events (polling)

```python
def get_events(self, payload: dict) -> dict:
    """List events for polling-based consumers.

    Expected payload keys (all optional):
      - "since_id"?: str
      - "request_id"?: str
      - "session_id"?: str
      - "limit"?: int

    Returns:
      - {"events": [ ... ]}
    """
```

- Simply delegates to `event_store.list(...)` and packages the result.
- Supports polling-based transports (REST + polling), while also being usable behind WebSockets/SSE.

## Testing Strategy

All tests live under `core/python/tests` and use dummy plugins already present in the test suite (`DummyProvider`, `DummyFeature`, `DummyCalculator`, etc.) plus temporary directories for session files.

### 1) Basic non-streaming flows (`test_application_layer_basic.py`)

- `test_create_session_persists_to_disk`
  - Temp directory for `session_root`.
  - Minimal config with 1 provider and 1 agent.
  - Manually register `DummyProvider` via Application helper or config.
  - Call `create_session({"agent_id": "default"})`.
  - Assert JSON file exists and contains correct `agent_id` metadata.

- `test_add_message_updates_session_and_persists`
  - Create a session, then call `add_message` once.
  - Assert the session JSON reflects the new message via `AgentCore.import_session`.

- `test_send_request_non_streaming_updates_session`
  - Set up `DummyProvider` only.
  - Create a session, add a user message, then call `send_request({"session_id": ..., "stream": false})`.
  - Assert returned `messages` contain the assistant echo.
  - Assert the persisted session contains both user and assistant messages.

- `test_sessions_are_reusable_across_application_instances`
  - Use `app1` to create a session and perform one `send_request`.
  - Construct `app2` with the same config + session root.
  - Use `app2` to add a message and run another `send_request`.
  - Assert that behavior is correct and independent of `app1`'s in-memory state.

### 2) Config behavior (`test_application_layer_config.py`)

- `test_build_agent_config_merges_provider_and_agent`
  - Simple config with one provider and one agent override.
  - Assert that `build_agent_config` returns a flat dict with expected keys and that agent values override provider defaults.

- `test_resolve_placeholders_collects_errors`
  - Config referencing a missing env var and a missing file.
  - Assert resolved config has empty strings for these values.
  - Assert returned errors list contains descriptive entries; application does not crash.

- `test_agent_id_stored_in_session_metadata`
  - After `create_session`, assert `session["metadata"]["agent_id"] == agent_id`.

### 3) Tool loop behavior (`test_application_layer_tools.py`)

- Use a dummy provider that emits OpenAI-style tool calls in assistant metadata, plus `DummyCalculator` as a tool.

- `test_send_request_non_streaming_executes_tool_calls`
  - Scenario where first LLM response requests a tool call.
  - Assert Application:
    - Publishes `tool_calls` and `tool_results` events (using in-memory EventStore).
    - Appends tool messages to the session.
    - Performs a follow-up LLM call that uses the tool result.
    - Persisted session contains both tool and assistant messages.

- `test_send_request_streaming_executes_tool_calls`
  - Same scenario, but with `{"stream": true}`.
  - Call `send_request`, get `request_id`.
  - Poll `get_events` until a `request_completed` event.
  - Assert that events include partials, tool calls/results, and final messages.

- `test_tool_loop_max_depth`
  - Use a provider that intentionally always returns a tool call (or loop after a certain number).
  - Assert that the Application stops after `max_tool_loops` and publishes an `error` or `request_completed` with a clear reason.

### 4) Streaming behavior (`test_application_layer_streaming.py`)

- `test_send_request_streaming_emits_partials_and_final`
  - With `DummyProvider` and streaming enabled.
  - Start a streaming request, then poll `get_events` until completion.
  - Assert multiple `partial` events and a final event are present.
  - Assert final persisted session matches the last `final` event.

- `test_streaming_is_stateless_between_calls`
  - Run a streaming request, allow it to complete, and discard Application instance.
  - Create a new Application instance and start another streaming request on the same session.
  - Assert behavior is correct based solely on session JSON on disk.

---

This updated plan incorporates your decisions: explicit `create_session`/`add_message`/`send_request` actions, config-driven plugin lists with manual registration, non-fatal placeholder resolution, flat JSON session files, dict-based APIs, and a background streaming model with event polling that works for both LLM responses and tool calls.