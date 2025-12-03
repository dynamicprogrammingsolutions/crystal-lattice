# Plan: Refactor agent_terminal_app to use per-frontend applications + shared event store

## Goals

- Remove the current `app_core`-style shared wrapper around `AgentApplication`.
- Share **only** the `InMemoryEventStore` instance across frontends.
- Introduce two separate application classes:
  - `ServerApplication` in `server.py`
  - `TerminalApplication` in `terminal.py`
- Each application class:
  - Owns its own `AgentApplication` instance by default.
  - Owns or uses an `InMemoryEventStore` instance.
  - Accepts optional injected `AgentApplication` and `InMemoryEventStore` in `__init__`.
- `__main__` is responsible for wiring a shared `InMemoryEventStore` when both
  server and terminal run in the same process.
- Tests construct `ServerApplication` / `TerminalApplication` directly and
  exercise their methods, both in isolation and with a shared event store.

## High-level architecture after refactor

### Shared components

- The only shared cross-module primitive is **`InMemoryEventStore`**
  (from `agent_app.events`).
- There is **no** shared `AgentApplication` instance or shared helper functions
  like `create_session_core`.

### `ServerApplication` (in `server.py`)

Responsibilities:
- Own a per-server `AgentApplication` (configuration + session root).
- Optionally use an externally provided `InMemoryEventStore` instance.
- Provide server-specific helpers:
  - `create_session(...)`
  - `add_message(...)`
  - `send_request(...)`
  - `list_events(...)`
- Implement all logic for:
  - Session loading/saving.
  - Publishing events into its `InMemoryEventStore`.
  - How requests are executed (foreground, no background threads).

Construction API:

```python
class ServerApplication:
    def __init__(
        self,
        *,
        config_path: str | Path,
        session_root: str | Path,
        agent_app: AgentApplication | None = None,
        event_store: InMemoryEventStore | None = None,
    ) -> None:
        # If agent_app is None, construct a new AgentApplication(config_path, session_root).
        # If event_store is None, construct a new InMemoryEventStore().
        # Store both on self.
```

Methods (sketch):

```python
class ServerApplication:
    def create_session(self, agent_id: str, system_message: str | None) -> Session: ...
    def add_message(
        self,
        session_id: str,
        *,
        role: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> Session: ...
    def send_request(
        self,
        session_id: str,
        *,
        overrides: dict[str, Any] | None = None,
        stream: bool = True,
    ) -> tuple[dict[str, Any] | None, list[dict[str, Any]], str | None]: ...
    def list_events(
        self,
        *,
        since_id: str | None = None,
        request_id: str | None = None,
        session_id: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]: ...
    def get_config_errors(self) -> list[dict[str, Any]]: ...
```

FastAPI wiring:
- `server.py` will create a module-level `ServerApplication` instance
  (e.g. `_server_app = ServerApplication(...)`) using default
  `config_echo_app.json` + `sessions` directory.
- Route functions close over `_server_app`:

```python
@app.post("/sessions")
def create_session_route(...):
    session = _server_app.create_session(agent_id, system_message)
    return {"session": session.to_dict(), "errors": _server_app.get_config_errors()}
```

- `run_api(host, port)` will accept an optional `ServerApplication` instance:

```python
def run_api(
    host: str = "127.0.0.1",
    port: int = 8000,
    app_instance: ServerApplication | None = None,
) -> None:
    # If app_instance is provided, assign it to a module-level variable
    # used by the route functions; otherwise, use the default one.
```

### `TerminalApplication` (in `terminal.py`)

Responsibilities:
- Own a per-terminal `AgentApplication` and optionally a shared
  `InMemoryEventStore`.
- Provide terminal-specific helpers:
  - `create_initial_session(system_message: str | None) -> Session`
  - `append_user_message(session_id: str, text: str) -> Session`
  - `send_request_background(session_id: str) -> asyncio.Task` (or similar)
  - `poll_events(...)` helper using its event store.
- Implement any differences from the server in how requests are run:
  - Use background threads or tasks so that input and shortcuts remain
    responsive while requests are in progress.

Construction API:

```python
class TerminalApplication:
    def __init__(
        self,
        *,
        config_path: str | Path,
        session_root: str | Path,
        agent_app: AgentApplication | None = None,
        event_store: InMemoryEventStore | None = None,
    ) -> None:
        # Same pattern as ServerApplication.
```

Methods (sketch):

```python
class TerminalApplication:
    def create_initial_session(self, system_message: str | None) -> Session: ...
    def append_user_message(self, session_id: str, text: str) -> Session: ...
    def send_request_background(self, session_id: str) -> asyncio.Task[None]: ...
    def poll_events(
        self,
        *,
        since_id: str | None,
        session_id: str | None,
        limit: int,
    ) -> list[dict[str, Any]]: ...
```

Terminal UI wiring:
- The prompt_toolkit loop will hold a `TerminalApplication` instance,
  plus a `TerminalContext` with the current `session_id` and
  `last_event_id`.
- Slash commands and shortcuts will call methods on the
  `TerminalApplication` instance instead of importing helpers from
  `server.py`.
- Event polling uses the `TerminalApplication`'s own `event_store`.

Example construction in `terminal.py`:

```python
def run_terminal(system_message: str | None = None, logger: Logger | None = None) -> None:
    app = TerminalApplication(config_path=DEFAULT_CONFIG, session_root=DEFAULT_SESSIONS)
    asyncio.run(app.run_ui(system_message=system_message, logger=logger))
```

### `__main__.py` orchestration

Responsibilities:
- Parse CLI flags: `--console`, `--server`, `--host`, `--port`, `--log-file`.
- Depending on the combination of flags, construct the appropriate
  application instances:

Modes:
1. **Server only** (default when no flags given):
   - Create a `ServerApplication` with its own `InMemoryEventStore`.
   - Call `run_api(host, port, app_instance=server_app)`.

2. **Console only** (`--console`):
   - Create a `TerminalApplication` with its own `InMemoryEventStore`.
   - Call `terminal_app.run_ui(...)`.

3. **Server + console** (`--server --console`):
   - Create a **shared** `InMemoryEventStore` instance:

     ```python
     shared_events = InMemoryEventStore()
     server_app = ServerApplication(
         config_path=DEFAULT_CONFIG,
         session_root=DEFAULT_SESSIONS,
         event_store=shared_events,
     )
     terminal_app = TerminalApplication(
         config_path=DEFAULT_CONFIG,
         session_root=DEFAULT_SESSIONS,
         event_store=shared_events,
     )
     ```

   - Start the server in a background thread, passing `server_app`:

     ```python
     threading.Thread(
         target=run_api,
         kwargs={"host": host, "port": port, "app_instance": server_app},
         daemon=True,
     ).start()
     ```

   - Then run the terminal UI in the foreground using `terminal_app`.

This ensures that **only the event store** is shared between server and
terminal in the combined mode; each has its own `AgentApplication`.

## Refactor steps

1. **Remove `app_core` usage**
   - Delete or deprecate `app_core.py` in favour of the new
     `InMemoryEventStore`-only sharing pattern.
   - If transitional helpers are still needed (e.g. to centralise default
     config paths), restrict them to configuration values, not behaviour.

2. **Implement `ServerApplication` in `server.py`**
   - Extract the current module-level application logic (creation of
     `AgentApplication`, session loading/saving, event publishing) into
     the new class.
   - Replace existing helper functions (`_create_session_impl`,
     `_add_message_impl`, `_send_request_impl`) with methods of
     `ServerApplication`.
   - Keep the FastAPI route functions thin wrappers around a single
     module-level `ServerApplication` instance, but ensure `run_api` can
     accept an override instance for tests and for `__main__`.

3. **Implement `TerminalApplication` in `terminal.py`**
   - Extract the console-specific logic (initial session creation,
     appending user messages, background request sending, and event
     polling) into methods on `TerminalApplication`.
   - The prompt_toolkit loop will own a `TerminalApplication` and a
     `TerminalContext`; all business logic goes through the application
     object.
   - Ensure that `TerminalApplication.__init__` accepts optional
     `agent_app` and `event_store` instances, defaulting to freshly
     constructed ones.

4. **Update `__main__.py` to orchestrate instances**
   - Replace direct calls to `run_api` and `run_terminal` with logic
     that constructs `ServerApplication` / `TerminalApplication` and
     passes them in.
   - In the combined mode, construct a single `InMemoryEventStore` and
     pass it into both constructors.
   - Leave logging behaviour (`--log-file`) unchanged but ensure logs
     can still be associated with either server or console.

5. **Update tests for the new architecture**

   - **Server tests**:
     - Instantiate `ServerApplication` directly with:

       ```python
       app = ServerApplication(
           config_path=config_echo_app.json,
           session_root=tmp_path / "sessions",
           event_store=InMemoryEventStore(),
       )
       ```

     - Call `app.create_session`, `app.add_message`, `app.send_request`
       and assert echo-style behaviour and that events recorded by
       `app.list_events` have the expected types.

   - **Terminal tests (optional but desirable)**:
     - Instantiate `TerminalApplication` directly with its own
       `InMemoryEventStore`.
     - Call its methods to create sessions, append messages, and trigger
       background requests, then inspect its `event_store` for the
       expected events.

   - **Shared event store test**:
     - Create `shared_events = InMemoryEventStore()`.
     - Instantiate both applications with that shared store:

       ```python
       server_app = ServerApplication(..., event_store=shared_events)
       terminal_app = TerminalApplication(..., event_store=shared_events)
       ```

     - Use `server_app` to create a session and run a request.
     - Use `terminal_app` to poll events and assert that it sees the
       same events (by `session_id`) that the server produced.

6. **Cleanup and compatibility**
   - Ensure `agent_terminal_app.__init__` still exports a module-level
     `app` (FastAPI instance) and `run_api` / `run_terminal` for
     backward compatibility, now implemented in terms of the new
     classes.
   - Remove any leftover references to the old `app_core` helper
     functions.
   - Optionally add a short comment in `server.py` and `terminal.py`
     documenting that the only intended shared primitive across
     frontends is the `InMemoryEventStore`.

## Risks and mitigations

- **Risk**: Tight coupling between FastAPI route functions and a
  singleton `ServerApplication`.
  - *Mitigation*: Keep a clear `run_api(..., app_instance=...)` API so
    tests and `__main__` can inject their own application object.

- **Risk**: Event order or semantics diverge between server and terminal
  implementations.
  - *Mitigation*: Keep the basic event types (`session_created`,
    `message_appended`, `request_started`, `partial`, `final`,
    `request_completed`) consistent, but allow each frontend to choose
    when to publish them.

- **Risk**: Tests may accidentally rely on module-level globals.
  - *Mitigation*: Tests should primarily construct their own
    `ServerApplication` / `TerminalApplication` instances and avoid
    using module-level singletons, except in explicit integration-style
    tests.
