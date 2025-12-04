# Plan: Refactor `terminal.py` with clearer application/UI boundaries

## 1. Context and problems

`application/python/agent_terminal_app/terminal.py` currently mixes two distinct concerns:

- **Application logic** built on `AgentApplication` + event store:
  - `create_session`, `add_message`, `send_request`, `list_events`.
  - Session metadata structure, including `metadata["agent_id"]` and `metadata["overrides"]`.
  - Logic for merging stored overrides with explicit overrides before calling `AgentApplication.send_request`.
  - Logic for flattening `core.get_ui_schema()` into a configuration-oriented schema.
- **Terminal UI logic** based on `prompt_toolkit`:
  - `TerminalContext` with `session_id`, `agent_id`, `last_event_id`, etc.
  - Slash commands (`/agent`, `/set`, `/new`, `/help`, `/exit`) and their argument completers.
  - Keyboard shortcuts, event polling, status bar text, and event rendering.

This coupling causes two concrete issues:

1. **Application-level tests depend on terminal UI constructs.**
   - `application/python/tests/test_terminal_application.py` has tests like
     `test_agent_switch_slash_command` and
     `test_set_overrides_and_send_request_uses_them` that:
       - Construct a real `TerminalContext`.
       - Invoke slash command handlers (`_cmd_agent`, `_cmd_set`).
       - Exercise session metadata updates and `send_request` behaviour.
   - These tests are really about application semantics (sessions, agents,
     overrides), but they must go through prompt_toolkit-specific wiring.

2. **Application logic is embedded in terminal helpers.**
   - `_switch_session_agent` and `_update_session_overrides` are
     application-layer operations that:
       - Load sessions.
       - Construct updated `Session` instances with modified metadata.
       - Persist those sessions.
     but they:
       - Take a `TerminalContext` argument.
       - Live alongside pure UI helpers.
       - Write directly to the terminal via `ctx.write`.
   - `_get_session_ui_elements` and `_flatten_ui_schema` are about turning
     `core.get_ui_schema()` into a flat config schema, but they also
     currently sit in the UI module and depend on `TerminalContext`.

The net effect: the boundary between "application layer" and "terminal
frontend layer" is blurry, and tests that should be application-focused
are forced to go through the UI.


## 2. Design principles

- **Application layer (Terminal application):**
  - Owns an `AgentApplication` instance.
  - Knows how to:
    - Create, load, and save sessions.
    - Append messages.
    - Manage and persist agent selection in session metadata.
    - Manage and persist configuration overrides in session metadata.
    - Merge stored overrides with explicit overrides for requests.
    - Expose UI schema elements in a frontend-agnostic format.
    - List events from the event store.
  - Does **not** know about prompt_toolkit, slash commands, key bindings,
    or terminal rendering.

- **Frontend layer (Terminal UI):**
  - Owns the *current UI state* for this terminal instance:
    - Which session the user is currently working with.
    - Last seen event ID for polling.
    - Pending agent-selection choices, etc.
  - Deals with:
    - `prompt_toolkit` (PromptSession, KeyBindings, Completion).
    - Slash command parsing and completions.
    - Keyboard shortcuts.
    - Textual rendering of events and status.
  - Delegates all persistence and business rules to the application layer.

- **State ownership:**
  - The *application* should not own a hidden "current session" pointer;
    that is a UI concern.
  - The *UI* holds the current `session_id` and uses explicit `session_id`
    parameters when calling the application.

- **`agent_id` as a derived concept:**
  - The current agent is a property of the current session (stored in
    `session.metadata["agent_id"]`).
  - The UI should treat `agent_id` as derived from the current session,
    not as its own separate source of truth.


## 3. Introduce `TerminalApplication`

Add a dedicated application-layer class in `terminal.py` (or in a new
module under the same package) that wraps `AgentApplication` and exposes
terminal-specific business operations.

### 3.1 Construction API

```python
class TerminalApplication:
    def __init__(
        self,
        *,
        config_path: str | Path,
        session_root: str | Path,
        agent_app: AgentApplication | None = None,
    ) -> None:
        # If agent_app is None, construct a new
        # AgentApplication(config_path, session_root).
        # Store it on self (e.g. self._app).
```

`_DEFAULT_CONFIG_PATH` and `_DEFAULT_SESSION_ROOT` in `terminal.py`
continue to provide defaults for `config_path` and `session_root`.

### 3.2 Methods

The following methods encapsulate the current module-level application
helpers and embedded logic:

- **`create_session(agent_id: str, system_message: str | None) -> Session`**
  - Moves logic from the current free `create_session` function.
  - Uses `self._app.create_session(agent_id)`.
  - Optionally adds a system message via `core.add_message`.
  - Saves the resulting session.
  - Publishes a `"session_created"` event via `self._app.get_event_store()`.

- **`add_message(session_id: str, *, role: str, content: str, metadata: dict[str, Any] | None) -> Session`**
  - Moves logic from the current free `add_message` function.
  - Loads the session, normalizes `role`, calls `core.add_message`,
    persists the session, and publishes `"message_appended"`.

- **`send_request(session_id: str, *, overrides: dict[str, Any] | None, stream: bool) -> tuple[dict[str, Any] | None, list[dict[str, Any]], str | None]`**
  - Moves logic from the current free `send_request` function.
  - Behaviour is preserved:
    - Load session.
    - Read stored overrides from `session.metadata["overrides"]`.
    - Merge stored overrides with explicit `overrides` (explicit wins).
    - Iterate `self._app.send_request(core, session, base_config, effective_overrides, stream=stream)`.
    - Publish each event to the event store, track final session + messages
      + request ID, and save the final session reconstructed from dict.

- **`list_events(*, since_id: str | None, session_id: str | None, limit: int) -> list[dict[str, Any]]`**
  - Wrap `self._app.get_event_store().list(...)` with the same semantics
    as the current `list_events` helper.

- **`get_session_ui_elements(session_id: str) -> list[dict[str, Any]]`**
  - Move `_get_session_ui_elements` and `_flatten_ui_schema` logic into
    the class.
  - Implementation sketch:

    ```python
    def get_session_ui_elements(self, session_id: str) -> list[dict[str, Any]]:
        loaded = self._app.load_session(session_id)
        if loaded is None:
            return []
        core, _cfg, _session = loaded
        try:
            ui_schema = core.get_ui_schema()
        except Exception:
            return []
        return self._flatten_ui_schema(ui_schema)
    ```

  - `_flatten_ui_schema` becomes a private helper:
    - Filters to `ui_type == "config"` (or unset).
    - Normalizes options to a list of string values.
    - De-duplicates by key.

- **`switch_session_agent(session_id: str, agent_id: str) -> Session`**
  - Moves the session/metadata mutation from `_switch_session_agent` into
    a pure application method:
    - Load the session.
    - Build new metadata with `{"agent_id": agent_id}` merged in.
    - Create a new `Session` instance with the same messages but updated
      metadata.
    - Save the session.
    - Return the updated `Session`.

- **`update_session_overrides(session_id: str, key: str, value: Any) -> Session`**
  - Moves the logic from `_update_session_overrides` into the class:
    - Load the session.
    - Normalize `metadata` and `overrides` to dicts.
    - Compute a new `overrides` dict with the updated key.
    - Construct new metadata and a new `Session` with the same messages.
    - Save and return the new `Session`.
  - Does **not** print; printing remains a UI responsibility.

- **`list_agents() -> list[str]`**
  - Simple wrapper for `self._app.list_agents()` with normalization (e.g.
    strings only, deduplicated and sorted).

- **`get_session_agent_id(session_id: str) -> str`**
  - Convenience helper to retrieve the agent identifier for a session:

    ```python
    def get_session_agent_id(self, session_id: str) -> str:
        loaded = self._app.load_session(session_id)
        if loaded is None:
            return "default"
        _core, _cfg, session = loaded
        metadata = session.metadata or {}
        agent = metadata.get("agent_id")
        return agent if isinstance(agent, str) and agent else "default"
    ```

  - Used by the UI to display the current agent and check whether an
    agent switch actually changes anything.


## 4. Simplify `TerminalContext` and keep `session_id` in the UI

`TerminalContext` stays as a UI-layer state container but becomes
lighter and more clearly scoped:

```python
@dataclass
class TerminalContext:
    app: TerminalApplication
    session_id: str
    last_event_id: str | None = None
    running: bool = True
    logger: Logger | None = None
    pending_agent_choices: list[str] | None = None

    def write(self, text: str) -> None:
        print(text, flush=True)
        if self.logger is not None:
            self.logger.info(text)
```

Key points:

- **`session_id` remains in the UI context.**
  - `TerminalApplication` stays stateless with respect to "which
    session"; methods always take `session_id` explicitly.
  - The UI is responsible for updating `ctx.session_id` when the user
    starts or switches sessions.

- **`agent_id` is removed as primary state.**
  - The current agent is derived from the session via
    `TerminalApplication.get_session_agent_id(ctx.session_id)`.
  - If needed, an `agent_id` cache on `TerminalContext` can be kept as a
    pure UI optimization, but the source of truth lives in the
    application layer.


## 5. Updating UI helpers to use `TerminalApplication`

With `TerminalApplication` in place and `TerminalContext` simplified,
UI helpers are updated to delegate all business logic to the
application.

### 5.1 Status bar and event polling

- **Status bar text**

  ```python
  def _status_bar_text(ctx: TerminalContext) -> str:
      agent = ctx.app.get_session_agent_id(ctx.session_id)
      return f"Agent: {agent}  Session: {ctx.session_id}"
  ```

- **Event polling**

  `_poll_events` no longer calls `ctx.app.get_event_store()` directly:

  ```python
  async def _poll_events(ctx: TerminalContext, poll_interval: float = 0.1) -> None:
      while ctx.running:
          events = ctx.app.list_events(
              since_id=ctx.last_event_id,
              session_id=ctx.session_id,
              limit=50,
          )
          if events:
              last = events[-1].get("event_id")
              if isinstance(last, str):
                  ctx.last_event_id = last
              for ev in events:
                  _render_event(ctx, ev)
          await asyncio.sleep(poll_interval)
  ```

### 5.2 Slash commands and shortcuts

- **`/agent` command**
  - Uses `ctx.app.list_agents()` for available agents.
  - Uses `ctx.app.get_session_agent_id(ctx.session_id)` to determine the
    currently active agent.
  - When switching, calls
    `ctx.app.switch_session_agent(ctx.session_id, target)` and then:
    - Updates any UI-level cache if present.
    - Resets `ctx.last_event_id` and writes informative messages.

- **`/set` command**
  - Uses `ctx.app.get_session_ui_elements(ctx.session_id)` instead of
    `_get_session_ui_elements(ctx)`.
  - Performs parsing and coercion of the value (including boolean
    handling for checkbox types).
  - On success, calls
    `ctx.app.update_session_overrides(ctx.session_id, key, coerced)` and
    prints the success message.
  - On failure, prints appropriate errors but does not touch the
    application state directly.

- **`/new` command and shortcuts**
  - Calls `app.create_session(agent_id=..., system_message=None)`.
  - Updates `ctx.session_id` to the new session ID.
  - Resets `ctx.last_event_id`.
  - The active agent is then derived via
    `app.get_session_agent_id(ctx.session_id)` when needed.

### 5.3 User message handling

`_handle_user_message` becomes a thin UI wrapper:

```python
async def _handle_user_message(ctx: TerminalContext, text: str) -> None:
    app = ctx.app

    try:
        app.add_message(ctx.session_id, role="user", content=text, metadata=None)
    except KeyError:
        ctx.write("[error] session not found; starting a new one")
        session = app.create_session(agent_id="default", system_message=None)
        ctx.session_id = session.session_id
        ctx.last_event_id = None
        app.add_message(ctx.session_id, role="user", content=text, metadata=None)

    async def _run_request() -> None:
        def _worker() -> None:
            try:
                app.send_request(ctx.session_id, overrides=None, stream=True)
            except Exception:
                pass

        await asyncio.to_thread(_worker)

    asyncio.create_task(_run_request())
```

The UI no longer manipulates sessions or overrides directly; it only
coordinates user input and background request execution.


## 6. Terminal startup and `run_terminal`

`_run_terminal` and `run_terminal` are updated to construct and use a
`TerminalApplication`:

```python
async def _run_terminal(
    app: TerminalApplication,
    system_message: str | None = None,
    logger: Logger | None = None,
) -> None:
    session = app.create_session(
        agent_id="default",
        system_message=system_message
        or "You are a helpful coding assistant. Respond concisely.",
    )
    ctx = TerminalContext(app=app, session_id=session.session_id, logger=logger)
    # ... build PromptSession, key bindings, event task, main loop ...


def run_terminal(
    system_message: str | None = None,
    logger: Logger | None = None,
    app_instance: TerminalApplication | None = None,
) -> None:  # pragma: no cover
    if app_instance is None:
        app_instance = TerminalApplication(
            config_path=_DEFAULT_CONFIG_PATH,
            session_root=_DEFAULT_SESSION_ROOT,
        )

    asyncio.run(_run_terminal(app_instance, system_message=system_message, logger=logger))
```

`agent_terminal_app.__init__` can optionally export `TerminalApplication`
for advanced usage and tests.


## 7. Testing strategy after the refactor

### 7.1 Application-focused tests (no `TerminalContext`)

Introduce or update tests to exercise `TerminalApplication` directly,
without any terminal UI constructs:

- **Echo flow:**
  - Instantiate `TerminalApplication` using `config_echo_app.json` and a
    temporary session root.
  - Call `create_session`, `add_message`, and `send_request`.
  - Reload the final session from `AgentApplication` and assert that the
    message history is intact.
  - Use `list_events` to assert presence of `"session_created"`,
    `"message_appended"`, and `"request_started"`/`"final"` events.

- **Agent switching:**
  - Create a session via `TerminalApplication`.
  - Call `switch_session_agent(session_id, target_agent)`.
  - Reload the session via `AgentApplication.load_session` and assert
    that `metadata["agent_id"]` matches.

- **Overrides behaviour:**
  - Monkeypatch `AgentCore.get_ui_schema` to expose a `reasoning_effort`
    select.
  - Create a session via `TerminalApplication`.
  - Call `update_session_overrides(session_id, "reasoning_effort", "high")`.
  - Monkeypatch `AgentApplication.send_request` to capture the
    `overrides` argument.
  - Call `send_request(session_id, overrides=None, stream=True)` and
    assert `{"reasoning_effort": "high"}` is passed through.

These tests validate application semantics without needing
`TerminalContext`, slash commands, or prompt_toolkit.

### 7.2 UI-focused tests (`TerminalContext` + commands/completions)

Retain and narrow tests in `test_terminal_application.py` to focus on
UI behaviour:

- **Slash command completion tests** remain, but use a lightweight
  context:
  - `ctx.app` can be a fake `TerminalApplication` (or stub object)
    exposing only the methods needed for completions (`list_agents`,
    `get_session_ui_elements`).
  - Tests assert which completions are suggested for given inputs.

- **Command wiring tests** (optional, small number):
  - Verify `/agent`:
    - Delegates to `TerminalApplication.switch_session_agent`.
    - Writes appropriate messages to the UI.
  - Verify `/set`:
    - Delegates to `TerminalApplication.update_session_overrides` on
      valid input.
    - Prints user-facing error messages on invalid input.

Deep persistence and override-merging behaviour is covered by
`TerminalApplication` tests, so UI tests can stay shallow.


## 8. Relationship to `PLAN_SHARED_EVENT_STORE_REFACTOR.md`

This plan complements `PLAN_SHARED_EVENT_STORE_REFACTOR.md`:

- That document defines the overall architecture with per-frontend
  application classes (`ServerApplication` and `TerminalApplication`)
  and a shared `InMemoryEventStore`.
- This document focuses specifically on:
  - Keeping `TerminalApplication` stateless with respect to
    "current session".
  - Keeping `session_id` and other UI concerns in `TerminalContext`.
  - Treating `agent_id` as derived from the current session via
    `get_session_agent_id`.
  - Moving all session mutation and override logic out of UI helpers and
    into `TerminalApplication`.

Together, these plans give a clear end state:

- Application layer: `ServerApplication` + `TerminalApplication`, each
  owning an `AgentApplication` and defining all session/event logic.
- Frontend layer: FastAPI routes and terminal UI code that are thin
  wrappers around the application layer, with no embedded business
  rules.
