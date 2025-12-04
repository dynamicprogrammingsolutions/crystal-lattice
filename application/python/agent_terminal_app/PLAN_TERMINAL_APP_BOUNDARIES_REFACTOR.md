**Goals**

- Treat the **stateful terminal “application”** as the main abstraction, specialized for the terminal frontend.
- Remove `TerminalContext` and `session_id` from UI state; the **TerminalApplication** instance itself holds the active session and related state.
- Keep **all application logic** (session lifecycle, overrides, agent switching, event polling) inside `TerminalApplication`.
- Keep **all representation / UX logic** (prompt_toolkit, printing, slash commands) in `terminal.py`.
- Avoid repeated `load_session` calls by keeping a **loaded `Session` object** inside `TerminalApplication`, updating it as operations occur.
- As we discover truly generic behaviour, move it down into `AgentApplication`, not into a generic “frontend-agnostic” terminal app.

---

**1. New module and class structure**

1. **Create a new module** `application/python/agent_terminal_app/terminal_app.py` containing `TerminalApplication`.
2. **Keep `terminal.py` focused on UI wiring**:
   - `PromptSession`, key bindings, event rendering, slash commands, completions.
   - It imports and uses `TerminalApplication` as its only “application” dependency.
3. Optionally **re-export** `TerminalApplication` from `terminal.py` and/or `agent_terminal_app.__init__` for backwards compatibility.

---

**2. Stateful `TerminalApplication` design**

`terminal_app.py`:

```python
class TerminalApplication:
    def __init__(
        self,
        *,
        config_path: str | Path,
        session_root: str | Path,
        agent_app: AgentApplication | None = None,
    ) -> None:
        ...
        self._app: AgentApplication
        self._session: Session | None = None
        self._last_event_id: str | None = None
```

Key aspects:

- `self._app`: the underlying `AgentApplication`.
- `self._session`: the **current active session object**, or `None` before initialization.
- `self._last_event_id`: tracks the last-seen event for polling; avoids passing this around externally.
- No `TerminalContext` or separate `session_id` field; `session_id` is always `self._session.session_id`.

**Invariants and behaviour:**

- There is exactly one “current” session at a time in `TerminalApplication`.
- Public methods that require a session either:
  - Assert `self._session` is present (raise a clear error if not), or
  - Create a session implicitly if the design warrants it (e.g. `ensure_session`).

---

**3. Application-layer methods & avoided `load_session` calls**

All methods currently on `TerminalApplication` in `terminal.py` will move and be **adapted to stateful usage**:

1. **Session lifecycle**

   - `create_initial_session(system_message: str | None, agent_id: str = "default") -> Session`
     - Calls `self._app.create_session(agent_id)`.
     - Appends system message if provided.
     - Saves the session.
     - Publishes `session_created`.
     - Sets `self._session` and resets `self._last_event_id`.
   - `start_new_session(system_message: str | None = None, agent_id: str | None = None) -> Session`
     - Like `create_initial_session`, but callable at any time to replace `self._session`.
     - If `agent_id` is `None`, it may use the current session’s agent as default.

2. **Message handling**

   - `append_user_message(text: str, metadata: dict[str, Any] | None = None) -> Session`
     - Requires `self._session` to be set.
     - Uses **in-memory** `self._session` with `core.add_message(...)`, not `load_session`.
     - Saves via `self._app.save_session`.
     - Publishes `message_appended`.
     - Updates `self._session` to the new `Session`.

   - Optionally a more generic:
     - `add_message(role: str, content: str, metadata: dict | None) -> Session`
       used by `append_user_message` and any future slash commands.

3. **Request execution**

   - `send_request(overrides: dict[str, Any] | None, stream: bool) -> tuple[dict | None, list[dict], str | None]`
     - Requires `self._session`.
     - Reads/merges overrides from `self._session.metadata["overrides"]` and explicit `overrides`.
     - Calls `self._app.send_request(core, self._session, base_config, merged_overrides, stream=stream)`.
     - Publishes events into the event store.
     - When a `final` event is received, reconstructs the final session and:
       - Saves it via `self._app.save_session`.
       - Updates `self._session` to that final session.
     - Returns `(final_session_dict, messages, request_id)` as today.

   - For performance, no `load_session` is used; the `Session` passed into `send_request` is always `self._session`.

4. **Events**

   - `poll_new_events(limit: int = 50) -> list[dict[str, Any]]`
     - Uses `self._app.get_event_store().list(...)` with:
       - `since_id=self._last_event_id`,
       - `session_id=self._session.session_id` (if set),
       - `limit`.
     - Updates `self._last_event_id` based on the last event returned.
     - Returns the new events only.
   - `reset_event_cursor() -> None` to allow UI to restart from scratch (e.g. when switching sessions).

5. **Agents and configuration**

   - `current_agent_id() -> str`
     - Reads from `self._session.metadata["agent_id"]` if present; else `"default"`.

   - `available_agents() -> list[str]`
     - Thin wrapper over `self._app.list_agents()`, with normalization / sorting.

   - `switch_agent(target_agent_id: str) -> Session`
     - Requires `self._session`.
     - Validates that `target_agent_id` is in `available_agents`.
     - If equal to `current_agent_id`, it can either be a no-op or raise; the UI decides what to show.
     - Writes updated metadata with new `agent_id`.
     - Saves and updates `self._session`.
     - Resets `self._last_event_id`.

   - `session_ui_elements() -> list[dict[str, Any]]`
     - Reuses and internalizes the `_flatten_ui_schema` logic.
     - Uses `self._session`’s associated core (or loads if necessary once) to call `core.get_ui_schema()` and cache/flatten it.

   - `update_override(key: str, value: Any) -> Session`
     - Mutates only `metadata["overrides"][key]`.
     - Creates a new `Session` value (if we keep immutability semantics) and updates `self._session`.
     - Saves via `self._app.save_session`.

6. **Small generic helpers**

   - `get_agent_app()` (or `.agent_app` property) to expose the wrapped `AgentApplication` to the UI where absolutely necessary (e.g. for the `/ui_schema` debug command).


**Load vs. save behaviour**

- **Never call `load_session` on each operation**; treat `self._session` as the canonical in-memory session for this terminal instance.
- After operations that might touch the session from outside (e.g. after a full request run), refresh `self._session` from the final event, not via `load_session`.
- If a background operation or error might have desynchronized state, we can provide an explicit `reload_session()` helper for the UI to call when needed.

---

**4. Terminal UI functions using stateful `TerminalApplication`**

`terminal.py` will:

1. **Change command function types** to operate on `TerminalApplication` directly:

   ```python
   CommandFn = Callable[[TerminalApplication, str], Awaitable[None] | None]
   SlashCompletionFn = Callable[[TerminalApplication, str], List[Completion]]
   ```

2. **`SlashCommandCompleter`** will hold a `get_app: Callable[[], TerminalApplication]` and hand that into completion functions:

   ```python
   class SlashCommandCompleter(Completer):
       def __init__(self, get_app: Callable[[], TerminalApplication]) -> None:
           self._get_app = get_app
       ...
       app = self._get_app()
       completions = cmd.completer(app, rest) or []
   ```

3. **Status bar and rendering**:

   - `_status_bar_text(app: TerminalApplication) -> str` will use `app.current_agent_id()` and `app.current_session_id` to build the status line.
   - `_render_event(app, event)` will stay mostly the same but be parameterized by the app and a `write` callback (see below).

4. **Printing / logging abstraction**:

   - Instead of `TerminalContext.write`, we’ll pass a `write: Callable[[str], None]` into relevant helpers (or keep it local in `_run_terminal`), so they can print and log without carrying a context object.

   Example:

   ```python
   def _render_event(app: TerminalApplication, event: dict, write: Callable[[str], None]) -> None:
       ...
       write("Assistant: ...")
   ```

5. **Event polling loop**:

   - `_poll_events(app: TerminalApplication, write: Callable[[str], None], poll_interval: float = 0.1)`:
     - Calls `events = app.poll_new_events(limit=50)`.
     - Loops through events and calls `_render_event(app, ev, write)`.
     - Respects a `running` flag owned by the outer UI loop (not by the application), e.g. a local `running: bool` captured in a closure.

6. **Slash commands as pure UI orchestrators**:

   - `/new`:
     - Calls `app.start_new_session(system_message=None, agent_id=app.current_agent_id())`.
     - Calls `app.reset_event_cursor()`.
     - Uses `write` to inform the user of the new session ID.

   - `/agent`:
     - Uses `app.available_agents()` and `app.current_agent_id()` for listing.
     - On selection, calls `app.switch_agent(target_agent_id)`.
     - Uses `write` for messages like “already using …” or “switched to …”.

   - `/set`:
     - Uses `app.session_ui_elements()` to discover valid keys + options.
     - Validates & coerces values from arguments.
     - Calls `app.update_override(key, coerced)`.
     - Uses `write` to display success or error messages.

   - `/ui_schema`, `/help`, `/exit`:
     - Continue to operate on `TerminalApplication` and `write`, but do not need any extra state containers.

7. **User message input**:

   - `_handle_user_message(app, text, write)`:
     - Calls `app.append_user_message(text)`.
     - Starts a background task that calls `app.send_request(overrides=None, stream=True)` via `asyncio.to_thread` to keep the UI responsive.

8. **Key bindings and main loop**:

   - `_build_key_bindings(app, write)` attaches shortcuts that call slash command handlers with `app` and UI state.
   - `_run_terminal(app, system_message, logger)`:
     - Calls `app.create_initial_session(system_message, agent_id="default")`.
     - Maintains a local `running` flag and passes it into `_poll_events` or as a closure variable.
   - `run_terminal(...)`:
     - Constructs a `TerminalApplication` (or uses injected one), then runs `_run_terminal`.

No `TerminalContext` dataclass is needed anymore; UI state is either:

- In `TerminalApplication` for application data (session, last_event_id).
- In local variables/closures in `terminal.py` for pure UI-concerns like `running` and `pending_agent_choices`.

---

**5. Shared logic and possible moves into `AgentApplication`**

As part of this refactor, identify logic that is both:

- Not terminal-specific, and
- Useful for other frontends.

Examples that might be good candidates:

- Override merging logic (stored vs explicit) used by both server and terminal.
- UI schema flattening if other frontends need a similar normalized representation.

Plan:

1. Implement them first as private helpers on `TerminalApplication` (`_merge_overrides`, `_flatten_ui_schema`).
2. Once stabilized and shared with server or other app layers, lift into `AgentApplication` (or a small utility module) with an explicit API, e.g.:

   - `AgentApplication.merge_overrides(session: Session, overrides: dict | None) -> dict | None`
   - `AgentApplication.get_config_ui_elements(session: Session) -> list[dict]`

This keeps `TerminalApplication` flexible but doesn’t force it to be multi-frontend from day one.

---

**6. Tests and migration**

1. **Update `test_terminal_application.py` to the new API:**

   - Replace uses of `TerminalContext` with direct `TerminalApplication` calls.
   - Adapt tests for:
     - `create_initial_session` / `start_new_session`.
     - `append_user_message`.
     - `send_request` (confirm overrides behaviour via metadata + send_request patching).
     - `available_agents` / `current_agent_id` / `switch_agent`.
     - `session_ui_elements` / `update_override`.
     - `poll_new_events` (if needed).

2. **Completion tests:**

   - Update `SlashCommandCompleter` tests to use a stub `TerminalApplication` or a minimal mock object with the required methods (`available_agents`, `session_ui_elements`, etc.), passed in via the new API (e.g. `SlashCommandCompleter(lambda: fake_app)`).

3. **Backwards compatibility:**

   - Optionally:
     - Keep a thin `TerminalContext` shim (deprecated) during migration that wraps `TerminalApplication` for any external code relying on it.
     - Or just expose `TerminalApplication` from `terminal.py` and adjust local examples/tests to use the new pattern.

4. **Server-side consideration (optional):**

   - For consistency, consider a later pass that introduces a `ServerApplication` class with its own state model and shared helper methods with `TerminalApplication`, possibly reusing any new `AgentApplication` helpers.

---

**7. Implementation order**

1. Introduce `terminal_app.py` with the stateful `TerminalApplication` and its methods, but keep existing `terminal.py` intact initially.
2. Incrementally migrate `terminal.py`:
   - Update `CommandFn` / `SlashCommandCompleter` signatures to use `TerminalApplication`.
   - Replace `TerminalContext` usage with `TerminalApplication` + local UI state.
   - Remove `TerminalContext` once no references remain.
3. Update `__main__.py` to import `TerminalApplication` from `terminal_app.py` and pass it into `run_terminal`.
4. Update tests in `test_terminal_application.py` to use the new API.
5. Remove any now-dead code in `terminal.py` and, if desired, add a brief docstring in `terminal_app.py` explaining that this class is terminal-specific and not intended as a generic frontend adapter.
