# Terminal and HTTP feature development

This document captures the common patterns and background knowledge needed to add features similar to the session-slicing and `/delete` work.

## High-level architecture

- **Core SDK (`core/python/agent_core`)**
  - `AgentCore` implements the provider-agnostic conversation engine.
  - Works with `Session` objects and provider configs.
  - Responsible for slicing/forking sessions and translating between "core" messages and provider-native messages.

- **Application layer (`core/python/agent_app`)**
  - `AgentApplication` wires `AgentCore` to:
    - a session store,
    - an event store,
    - plugin configuration.
  - Exposes high-level operations such as "send a request", "load a session", etc.

- **Terminal + server apps (`application/python/agent_terminal_app`)**
  - `app_core.py` defines a shared `EventStore` implementation and utilities.
  - `server.py` exposes the application over HTTP / websockets.
  - `terminal_app.py` contains `TerminalApplication`, the frontend-agnostic app API.
  - `terminal.py` is the interactive CLI client:
    - handles input parsing, slash commands, and printing output,
    - delegates all business logic to `TerminalApplication`.

The most important rule is: **business logic lives in the application layer (e.g. `TerminalApplication`), not in the CLI.**

Terminal message headers, event rendering, transient progress state, prompt redraw, and
pseudo-terminal verification are mapped in
[Terminal rendering, progress, and UI testing](terminal-ui.md).

## Sessions, configs, and slicing

When implementing features that modify or inspect history, you need to understand:

- **Sessions**
  - A `Session` holds:
    - `session_id`
    - a list of core messages (`session.messages`)
    - `metadata` (including provider-native history and per-session overrides).
  - Sessions are stored on disk via the application layer (e.g. `AgentApplication`).

- **Configs**
  - Each request uses a base config plus optional per-session overrides.
  - `AgentApplication` helpers resolve the effective config for you.
  - For operations like slicing/forking, always resolve the config the same way as a normal request.

- **Slicing / deleting**
  - `AgentCore` provides primitives to:
    - slice sessions over indices,
    - rebuild provider-native history if possible,
    - fall back to a core-only slice when native data is missing.
  - Application code (e.g. `TerminalApplication`) should:
    - normalize indices (including negative indices),
    - translate user intent (ranges, "last N", etc.) into concrete indices,
    - call into the core slice API,
    - persist the new session and emit appropriate events.

If you add a new kind of history manipulation, mirror this pattern: keep low-level index math in the application layer and call into the core via its existing APIs.

## Event store and cross-process communication

The server and terminal processes communicate via an event store:

- Both use the same `EventStore` implementation (see `application/python/agent_terminal_app/app_core.py`).
- Events are simple dictionaries with at least:
  - `type` (string)
  - `session_id`
  - optional payload such as `message`, `indices`, or `error`.
- Typical event types include:
  - `session_created`
  - `message_appended`
  - `messages_deleted`
  - request lifecycle events (e.g. `request_started`, `request_partial`, `request_final`, `request_error`).

When you add a new feature:

- Decide what events should be emitted (if any).
- Emit them from the application layer right after you mutate a session or start/finish a request.
- Update the terminal and/or server rendering code to handle the new event type.
- When an event has terminal rendering semantics, ensure application event
  compaction preserves the fields the renderer needs. In particular,
  `tool_partial` events with `phase == "end"` are final display events rather
  than redundant stream chunks.
- Treat assistant lifecycle `message_index` as semantic display data. It is
  the reserved first message index for the LLM phase and can remain
  provisional if the stream is cancelled before commit.

## Where to put new feature logic

When you add a feature that affects sessions, messages, or requests:

- **`core/python/agent_core`**
  - Only add/change things here if you need new low-level capabilities (e.g. a new slicing mode).
  - Keep the API provider-agnostic and functional.

- **`core/python/agent_app`**
  - Add new high-level operations in `AgentApplication` when they are generally useful across frontends.
  - Use existing helpers for config resolution, session loading/saving, and event emission.

- **`application/python/agent_terminal_app/terminal_app.py`**
  - Add terminal-specific application logic here, in `TerminalApplication`.
  - Examples:
    - interpreting indices and ranges for deletion,
    - publishing `messages_deleted` events after a mutation,
    - convenience helpers used by the CLI and tests.

- **`application/python/agent_terminal_app/terminal.py`**
  - Keep this file focused on UI concerns:
    - parse user input,
    - dispatch to methods on `TerminalApplication`,
    - render events and errors to the terminal.
  - Avoid embedding business rules or session logic here.

## Pattern for a new slash command

For a new command like `/delete`, follow this pattern:

1. **Design the application API**

   - Add a method on `TerminalApplication` that:
     - accepts clear, typed arguments (e.g. `indices: List[int]`, `count: int`),
     - performs validation and normalization,
     - calls into `AgentApplication` / `AgentCore`,
     - saves the updated session,
     - emits any relevant events,
     - returns structured data (e.g. `(session, deleted_indices)`).

2. **Add CLI parsing**

   - In `terminal.py`, register a new command with `@slash_command`.
   - Parse the raw argument string into the structured inputs your application method expects.
   - Map application exceptions to user-friendly error messages.
   - Print a short confirmation on success (e.g. which indices were affected).

3. **Wire up event rendering**

   - If the feature emits new or updated event types:
     - Extend the event rendering logic in `terminal.py` to handle them.
     - Keep rendering functions small and side-effect-free (they should only write to the output writer).

## Testing strategy

Tests live alongside the relevant layers:

- **Core and application layer tests**
  - Location: `core/python/tests` and `core/python/examples/tests`.
  - Run from the repository root:
    - `python -m pip install -e "core/python[dev]"`
    - `pytest core/python/tests -q`
  - When you change core slicing or application logic, add unit tests near existing tests that cover similar behavior.

- **Terminal + server tests**
  - Location: `application/python/tests`.
  - Run from the repository root:
    - `pytest application/python/tests -q`
  - Tests here should:
    - construct `TerminalApplication` and/or the server application,
    - exercise the public methods (e.g. delete APIs, helpers that append messages),
    - assert on sessions and on events read from the shared event store,
    - for CLI commands, call the command functions in `terminal.py` with a fake writer and inspect the output.

When adding a feature, aim to:

- Cover both the application layer API and the CLI behavior.
- Prefer small, focused tests that work directly with public APIs.
- Use existing tests (e.g. `test_terminal_application.py`, `test_agent_terminal_app_shared_events.py`) as templates.

## Coding style and conventions

- Use **functional/immutable style** where reasonable:
  - Avoid mutating shared state in place.
  - Prefer creating new objects (e.g. new `Session` instances) instead of mutating existing ones.
- Keep functions small and composable.
- Avoid one-letter variable names in non-trivial code.
- Keep terminal output short, clear, and predictable; tests often assert against it.
- When in doubt, follow the patterns already used in:
  - `core/python/agent_app/application_future.py`
  - `application/python/agent_terminal_app/terminal_app.py`
  - `application/python/agent_terminal_app/terminal.py`

By following these guidelines and mirroring the existing patterns, you can add new features—such as additional history operations, new slash commands, or custom workflows—without breaking the separation between core logic, application logic, and UI.

## Dynamic commands, action references, and notifications

Dynamic command discovery is generation-scoped:

- `AgentApplication` normalizes `cli_command` and `slash_command` UI elements,
  validates their action bindings and foreground metadata, and reports route
  collisions before execution.
- `TerminalApplication` resolves the current session's slash elements and
  applicable `/action` elements. Application replacement invalidates command
  and direct-result reference state.
- `terminal.py` merges dynamic slash elements with immutable built-ins only
  for help, completion, and dispatch. It never installs plugin handlers into
  the module-global decorator registry.

Action invocation remains `execute_action_with_metadata(...)`. The terminal
façade owns context mapping, element applicability, command references, and
notification revision state; prompt callbacks own
text/select/multiline/secret interaction. Top-level and interactive commands,
direct results, and notifications use the shared action-result renderer.

Direct display `run_action` entries are stored as terminal-local synthetic
action elements without retaining an old `AgentApplication`. Notification
references additionally store scope, notification identity, revision, and
follow-up id. They reread authoritative notification state before invocation.

Ordinary terminal event polling is session-filtered, but application
notification events are global. The terminal therefore maintains a separate
global notification cursor. On startup, application replacement, cursor
recovery, or session switch it:

1. captures the latest global event cursor;
2. hydrates active application and current-session notification snapshots;
3. resumes global polling from the captured cursor;
4. merges observations by scoped identity and revision.

This ordering lets snapshot/event races converge without duplicate rendering.
Inactive-session notification events are intentionally discarded; switching
sessions hydrates the newly active session instead.
