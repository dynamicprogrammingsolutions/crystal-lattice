# Application Layer MVP Plan

## Goal
- Introduce a minimal **Python Application Layer** that sits above `AgentCore`, owns configuration and session persistence, and exposes a simple class-based API that future HTTP/WebSocket servers can call.
- Ensure **stateless per-call behavior** at the application level: no in-memory session storage; all conversations are loaded from and saved to disk on each call. The only in-memory state across moments is within an ongoing streaming request.
- Keep the design aligned with **functional core, imperative shell**: `AgentCore` and `Session` remain pure/immutable; the Application Layer performs orchestration, I/O, and tool loops.

## Context (Current Core Architecture)
- `agent_core.core.AgentCore`:
  - Stores plugin wrappers (providers, extensions, features, tools) and internal caches only; **no application/session state**.
  - Provides pure methods: `create_session`, `add_message`, `send_request`, `send_request_stream`, `send_request_stream_async`, `execute_tool_calls`, `export_session`, `import_session`, `get_tool_schemas`, `get_config_schema`, `get_ui_schema`, `discover_and_register`.
  - Uses immutable `Session` and `Message` dataclasses from `agent_core.types`.
  - Handles provider-native history retention in `session.metadata.native_messages` with integrity verification.
- Configuration model (architecture docs):
  - Application loads JSON config, resolves `${env:...}` and `${file:...}`, and merges provider defaults with agent-specific overrides.
  - Core receives a **flat dict per request** (no nested plugin structure required) and does not manage config itself.
- Tool execution:
  - Core exposes `execute_tool_calls(tool_calls, config) -> list["tool" messages]` but **does not own the tool loop**.
  - Application is expected to detect tool calls in assistant messages, call `execute_tool_calls`, append tool results as messages, and then call `send_request` / `send_request_stream` again.

## Scope of This MVP
- **In scope**
  - A Python package for the Application Layer (exact package name can be finalized later, e.g. `agent_app`).
  - A main `Application` class that:
    - Lives for the lifetime of the process.
    - Owns a configured `AgentCore` instance.
    - Exposes high-level methods to run agent "turns" using session IDs and agent IDs.
    - Never keeps session state in memory across calls (loads from disk at the start of a call, writes back at the end).
  - A simple **configuration module** that:
    - Loads JSON configuration.
    - Resolves `${env:...}` and `${file:...}` placeholders.
    - Provides an `agents` mapping with a provider name per agent.
    - Produces **flat per-request config dicts** for `AgentCore` by merging provider defaults, plugin defaults, and agent-specific overrides.
  - A **session persistence layer** that:
    - Persists `Session` objects to disk using `AgentCore.export_session` / `import_session`.
    - Stores a mapping from `session_id` to serialized `Session` (e.g. one JSON file per session).
    - Preserves `session.metadata` (including provider-native history and agent identifier).
  - A minimal **tool execution loop** inside the Application Layer for non-streaming requests.
  - A thin **streaming wrapper** over `send_request_stream` that respects the stateless-per-call requirement while allowing an in-memory streaming iterator for the duration of the request.
  - Tests under `core/python/tests/` that simulate real API usage patterns without introducing an HTTP server.

- **Out of scope for this MVP**
  - HTTP or WebSocket servers (FastAPI/Express).
  - Frontend integration.
  - Database-backed session stores (filesystem only for now).
  - Cross-language Application Layer (Python only).

## Proposed Module Structure (Python)
> Exact package and file names can be adjusted; this is a concrete starting point.

- `core/python/agent_app/`
  - `__init__.py`
    - Expose `AgentApplication` (or similar) and public types.
  - `application.py`
    - Implementation of the main `AgentApplication` class.
  - `config.py`
    - Configuration loading, resolution, and per-agent config derivation.
  - `sessions.py`
    - Session persistence abstractions (filesystem-backed `SessionStore`).
  - `types.py`
    - Light-weight request/response types for application-level operations (if needed; can be plain dicts initially).

- Tests
  - `core/python/tests/test_application_layer_basic.py`
  - `core/python/tests/test_application_layer_streaming.py`
  - `core/python/tests/test_application_layer_tools.py`
  - `core/python/tests/test_application_layer_config.py`

## Configuration Module Design

### 1) Config file shape (on disk)

MVP JSON structure, consistent with ARCHITECTURE.md and your notes:

```jsonc
{
  "core": {
    // Optional core-level settings (e.g. plugin discovery later)
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
    // Optional global defaults per plugin (feature/extension/tool)
    "system_message_feature": {
      "system_files": ["${file:./AGENTS.md}"]
    },
    "request_options_feature": {
      "request_options": {"temperature": 0.3}
    }
  },
  "agents": {
    "default": {
      "provider": "openrouter",      // Provider name; used to pick provider config
      // Agent-level overrides (flattened keys used by provider + plugins)
      "model": "openrouter/anthropic/claude-3.5",
      "temperature": 0.2,
      "system_message_feature.enabled": true,
      "request_options_feature.max_tokens": 4096
    }
  }
}
```

Key ideas:
- **Agents list with provider name**: `agents[agent_id]["provider"]` selects a provider from `providers`.
- **Provider and plugin config as top-level keys** in the *resolved* per-request dict:
  - Disk config is structured for readability.
  - The configuration module resolves and flattens the nested structure into a flat dict for each agent, where provider and plugin-related keys all sit at the top level (matching core expectations).

### 2) Config loading & resolution API

Module: `agent_app.config`

- `load_raw_config(path: str | Path) -> dict`
  - Read JSON file from disk.
  - No environment or file resolution yet.

- `resolve_placeholders(raw: dict, env: Mapping[str, str] = os.environ) -> dict`
  - Recursively walk the config and replace:
    - `${env:VAR_NAME}` with `env[VAR_NAME]` (or fail/leave empty – see open questions).
    - `${file:path/to/file}` with the contents of the file (text).

- `build_agent_config(raw_config: dict, agent_id: str) -> dict`
  - Steps:
    1. Look up `agent = raw_config["agents"][agent_id]`.
    2. Look up `provider_name = agent["provider"]`.
    3. Get `provider_defaults = raw_config["providers"][provider_name]`.
    4. Optionally gather plugin defaults from `raw_config["plugins"]`.
    5. Merge into a **flat dict**:
       - Start from `provider_defaults` (minus nested identifiers like `name` if present).
       - Overlay plugin defaults (flattened key space, e.g. `system_message_feature.system_files`).
       - Overlay `agent` overrides.
    6. Ensure **`provider` key** is present and correctly names the provider for `AgentCore`.
  - Return value is the per-agent base config used for all requests for that agent.

- `resolve_request_config(base_agent_config: dict, overrides: dict | None) -> dict`
  - Merge request-specific overrides into the resolved agent config.
  - Used when a UI/API wants to change temperature, model, etc. for a single call.

### 3) Agent registry / lookup in sessions

- When creating a session via the Application Layer, the chosen `agent_id` is stored into `session.metadata["agent_id"]`.
- On subsequent calls, the Application Layer:
  - Loads the `Session` from disk.
  - Reads `agent_id` from `session.metadata`.
  - Builds or reuses the resolved base config for that agent.

This means each application call only needs the `session_id` (plus new messages); the Application can infer which agent to use from persisted session metadata.

## Session Persistence Design

### 1) Abstraction

Module: `agent_app.sessions`

- `class SessionStore(Protocol)`
  - `def load(self, session_id: str) -> Session | None`
  - `def save(self, session: Session) -> None`
  - `def delete(self, session_id: str) -> None`

- `class FilesystemSessionStore(SessionStore)`
  - Constructor: `__init__(self, root_dir: Path)`.
  - Layout: one file per session, e.g. `<root_dir>/<session_id>.json`.
  - Uses `AgentCore.export_session` / `import_session` for serialization/deserialization.
  - Writes atomically (e.g. write to temp file then rename) to avoid corruption on crash.

### 2) Behavior

- **Create session**:
  - Application calls `AgentCore.create_session()`.
  - Sets `session.metadata["agent_id"] = agent_id`.
  - Saves to disk immediately via `SessionStore.save`.

- **Load session**:
  - For each public Application call that takes a `session_id`, the first step is `SessionStore.load(session_id)`.
  - If not found, raise a clear error (or optionally auto-create, see open questions).

- **Update session**:
  - Every time `AgentCore` returns a new `Session` (non-streaming or streaming final event), the Application Layer overwrites the stored file via `save`.

- **Statelessness guarantee**:
  - Application instances hold **no mapping** of `session_id` → `Session` in memory.
  - All state between calls is persisted via the filesystem, except for ephemeral state during an active streaming iterator.

## Application Class Design

Module: `agent_app.application`

### 1) Construction

```python
class AgentApplication:
    def __init__(
        self,
        config_path: str | Path,
        session_root: str | Path,
        core_factory: Callable[[], AgentCore] = AgentCore,
        *,
        auto_discover_plugins: bool = False,
        plugin_modules: Sequence[str] | None = None,
    ) -> None:
        ...
```

Responsibilities:
- Load & resolve configuration from `config_path` once at startup.
- Instantiate a single `AgentCore` via `core_factory` and register providers/features/tools.
  - For MVP tests, we can manually register test plugins.
  - For later, optionally use `AgentCore.discover_and_register(plugin_modules)` if `auto_discover_plugins` is enabled.
- Create a `FilesystemSessionStore` rooted at `session_root`.
- Precompute and cache **per-agent base configs** (flattened dicts) derived from the loaded config.

### 2) Public API (non-streaming)

#### `create_session`

```python
def create_session(self, agent_id: str) -> Session:
    """Create a new session for a given agent and persist it."""
```

- Steps:
  1. Get base config for `agent_id` (validate agent exists).
  2. Use `self._core.create_session()` to create a `Session`.
  3. Attach `agent_id` into `session.metadata["agent_id"]`.
  4. Persist to disk via `SessionStore.save`.
  5. Return the new `Session` (for immediate use by caller/tests).

#### `run_turn`

```python
@dataclass
class TurnRequest:
    session_id: str
    # New messages to append for this turn
    messages: list[dict]  # {"role": str, "content": str, "metadata"?: dict}
    overrides: dict | None = None  # Per-call config overrides

@dataclass
class TurnResult:
    session: Session
    final_messages: list[dict]  # assistant/tool messages added this turn


def run_turn(self, request: TurnRequest) -> TurnResult:
    """Run a full non-streaming turn, including tool loop."""
```

- Steps:
  1. Load `Session` from disk using `request.session_id`.
  2. Read `agent_id` from `session.metadata` and fetch base config.
  3. Merge `overrides` into config via `resolve_request_config`.
  4. For each new message in `request.messages`, call `AgentCore.add_message` to get an updated `Session`.
  5. Enter a **tool loop**:
     - Call `AgentCore.send_request(session, config)`.
     - Inspect the returned `final_messages` for tool calls (using a helper that understands the OpenAI-style structure in `metadata`).
     - If there are no tool calls, break.
     - Normalize tool calls and call `AgentCore.execute_tool_calls(tool_calls, config)`.
     - For each returned "tool" message, append to session via `add_message`.
     - Repeat until no tool calls or a `max_tool_loops` limit is reached.
  6. After loop termination, persist the final `Session` to disk.
  7. Return `TurnResult(session=final_session, final_messages=messages_from_last_llm_call)`.

This mirrors the tool execution responsibilities described in `ARCHITECTURE.md` while keeping all state transitions explicit and testable.

### 3) Public API (streaming)

#### `run_turn_stream`

```python
@dataclass
class StreamTurnRequest:
    session_id: str
    messages: list[dict]
    overrides: dict | None = None

# Event format is intentionally similar to core stream events
StreamEvent = dict  # {"type": "partial"|"final"|"tool_progress", ...}


def run_turn_stream(
    self, request: StreamTurnRequest
) -> Iterator[StreamEvent]:
    """Run a streaming turn for a session.

    - Adds messages, then delegates to AgentCore.send_request_stream.
    - Yields partial events as they arrive.
    - On final event, persists the new Session and yields a final event
      with `session` and `messages`.
    - Tool-loop integration for streaming can be incremental (see notes).
    """
```

- Initial MVP behavior:
  - Load and update the session as in `run_turn` (steps 1–4 above).
  - Call `send_request_stream(session, config)` on the core.
  - For each `"partial"` chunk, yield an application-level partial event.
  - On the core `"final"` chunk:
    - Get the `new_session` from the chunk.
    - Persist `new_session` to disk.
    - Yield an application-level final event with `session` and `messages`.
  - The iterator is the **only place** where in-memory state about this turn lives; once the iterator terminates, only the on-disk session remains.

- Tool loop interaction (MVP):
  - For the first iteration, we can support tools only for **non-streaming** calls to keep complexity low.
  - We can then extend `run_turn_stream` to:
    - Yield final events for each LLM phase.
    - Detect tool calls at the end of each phase.
    - Emit `"tool_progress"` events while executing tools.
    - Start a new streaming request from the updated session and continue yielding events.
  - This extension can be a follow-up task once the non-streaming tool loop is validated.

## Testing Strategy

All tests live under `core/python/tests` and use dummy plugins already present in the test suite (e.g., `DummyProvider`, `DummyFeature`, `DummyCalculator`) plus temporary directories for session files.

### 1) Basic non-streaming flows (`test_application_layer_basic.py`)
- `test_create_session_persists_to_disk`
  - Use a temp directory for `session_root`.
  - Construct `AgentApplication` with a small config and manually registered `DummyProvider`.
  - Call `create_session(agent_id="default")`.
  - Assert that a corresponding JSON file exists.

- `test_run_turn_updates_session_and_persists`
  - Create a session, then call `run_turn` with a single user message.
  - Assert that:
    - The returned session has one more message than before.
    - The session file on disk reflects the new message (via `AgentCore.import_session`).

- `test_session_can_be_reused_across_application_instances`
  - Create a session and run one turn with `app1`.
  - Construct a new `AgentApplication` instance pointing at the same config and session root.
  - Use `app2` to run another turn on the same `session_id`.
  - Assert appended messages and that there is no in-memory coupling between instances.

### 2) Config behavior (`test_application_layer_config.py`)
- `test_agent_config_merges_provider_and_agent`
  - Config file with one provider and one agent with overrides.
  - Assert that `build_agent_config` produces a flat dict with expected keys and overrides.

- `test_env_and_file_placeholders_are_resolved`
  - Temp file + temp env var.
  - Ensure `${env:...}` and `${file:...}` placeholders are resolved correctly.

- `test_agent_id_stored_in_session_metadata`
  - After `create_session`, assert `session.metadata["agent_id"] == agent_id`.

### 3) Tool loop behavior (`test_application_layer_tools.py`)
- Use a dummy provider that emits OpenAI-style tool calls in assistant message metadata, plus `DummyCalculator` as a tool.

- `test_run_turn_executes_tool_calls_and_appends_tool_messages`
  - run a turn where the model requests a tool call.
  - Assert that:
    - Application calls `execute_tool_calls` and appends a tool message.
    - A second request is made and returns a final assistant message that references the tool result.
    - The persisted session on disk contains both tool and assistant messages.

- `test_tool_loop_max_depth`
  - Ensure we enforce a reasonable maximum number of tool loops to prevent infinite cycles.

### 4) Streaming behavior (`test_application_layer_streaming.py`)
- `test_run_turn_stream_yields_partials_and_final`
  - Use `DummyProvider` with streaming enabled (as in existing tests).
  - Assert that `run_turn_stream` yields multiple `"partial"` events and a final event.
  - Verify that after iteration, the session file on disk reflects the final session state.

- `test_streaming_is_stateless_between_calls`
  - Run two separate streaming turns and ensure that between them only disk state is used (e.g., create a new Application instance between turns).

## Open Questions / Design Decisions to Confirm

1. **Package name and location**
   - Should the Application Layer live under `core/python/agent_app` (library-style), or should we align with the future `applications/` directory from ARCHITECTURE.md and put a reusable library module there?

2. **Exact config structure for plugin settings**
   - The plan assumes a structured `plugins` section plus flattened agent configs.
   - Alternative: for MVP, keep everything inside `agents[agent_id]` (i.e., only `providers` + `agents` sections) and treat all keys in the agent as final flat config.
   - Which direction should we take for the first iteration?

3. **How strict should placeholder resolution be?**
   - On missing `${env:VAR}` or `${file:path}`:
     - Fail fast with a clear error?
     - Or allow empty strings / leave the placeholder unresolved?

4. **Session auto-creation vs. explicit creation**
   - Should `run_turn` auto-create a new session if `session_id` is unknown?
   - Or should callers always call `create_session` first and treat unknown `session_id` as an error?

5. **Tool loop behavior for streaming**
   - For MVP, is it acceptable to support tools only in non-streaming flows, and add streaming+tools as a follow-up?
   - Or do we want an integrated streaming+tool loop from the start (more complex but more capable)?

6. **Config-driven plugin registration**
   - Should the Application Layer automatically call `AgentCore.discover_and_register` based on config (e.g. a `core.plugin_modules` list), or should plugin registration be left entirely to the host application and tests for now?

7. **Session storage root and naming**
   - Is a simple `root_dir/<session_id>.json` layout acceptable for now?
   - Do we need namespacing by agent or environment in the path (e.g. `root_dir/<agent_id>/<session_id>.json`)?

8. **Public API types**
   - Do we want lightweight dataclasses like `TurnRequest`/`TurnResult`, or keep the Application API purely dict-based to more closely mirror an eventual HTTP JSON API?

Once these questions are clarified, the next step would be to tighten this plan into concrete interfaces (signatures + minimal docstrings), then implement the Application Layer and tests iteratively.