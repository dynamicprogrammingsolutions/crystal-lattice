# agent_terminal_app server – endpoint parity plan

Goal: expose enough HTTP endpoints so that web or other frontends can do
everything the terminal client can, using the same underlying
`AgentApplication` behaviour.

Endpoints are grouped by priority. Within each group, items are kept
intentionally terse so they are easy to edit.

Legend:

- `EXISTING` – already implemented in `server.py`
- `NEW`      – proposed additions

---

## Essential features (phase 1)

Foundational operations needed for a basic multi-session chat UI that
can send requests and consume streaming events.

- [EXISTING] `POST /sessions`
    - Purpose: create a new session (optionally for a specific `agent_id`
      and with an initial `system_message`).
    - Terminal parity: `TerminalApplication.start_new_session(..., persist=True)`.

- [EXISTING] `POST /sessions/{session_id}/messages`
    - Purpose: append a message to a session (`role`, `content`, optional
      `metadata`).
    - Terminal parity: `TerminalApplication.append_user_message` and
      `TerminalApplication.add_message`.

- [EXISTING] `POST /sessions/{session_id}/send`
    - Purpose: delegate to the application-layer session request coordinator
      with optional `config_overrides`. The HTTP response immediately reports
      `started` or `already_running` with the authoritative `request_id`.
    - Ownership: FastAPI validates and maps HTTP data only. Request admission,
      background execution, event publication, cancellation registration, and
      cleanup are application-layer behavior shared with terminal and plugin
      callers. See
      [Application request execution](../docs/development/request-execution.md).
    - Terminal parity: terminal sends use the same coordinator. Frontends
      observe progress via `/events` and apply incremental events to keep local
      message history in sync. Reload `/sessions/{id}/messages` only for
      initial bootstrap or as a fallback when the client becomes out of sync.

- [EXISTING] `GET /events`
    - Purpose: read events from the shared event store, filtered by
      `since_id`, `session_id`, `request_id`, `limit`.
    - Notes: events are incremental deltas only and never embed full
      session history.
    - Terminal parity: `TerminalApplication.list_events` and
      `TerminalApplication.poll_new_events` (frontends keep
      `since_id` client-side like the terminal keeps `_last_event_id`).

- [NEW] `GET /sessions`
    - Purpose: list existing sessions with lightweight metadata ordered by
      last modification time.
    - Response shape (mirrors `TerminalApplication.list_sessions_metadata`):
      `[{ "session_id": str, "modified": float, "preview": str }, ...]`.
    - Terminal parity: used by `/session` command and session-completion.

- [NEW] `GET /sessions/{session_id}/messages`
    - Purpose: list messages for a session, with optional slice-style
      bounds.
    - Query params (mirroring terminal semantics):
        - `start: Optional[int]` – inclusive, supports negative indices.
        - `end: Optional[int]` – exclusive, supports negative indices.
        - When both are omitted, return the full history.
    - Response shape: `{ "messages": [ {"index": int, "message": <Message.to_dict()>}, ... ] }`.
    - Terminal parity: `TerminalApplication.list_messages_by_range` and
      `/list` command.

- [NEW] `POST /requests/{request_id}/cancel`
    - Purpose: cancel an in-flight request started by `send_request`.
    - Behaviour: delegates to `AgentApplication.cancel_request(request_id)`.
    - Terminal parity: `/cancel` command and `c-x c` shortcut.

---

## Basic features (phase 2)

Quality-of-life operations for manipulating history and working with
multiple agents. Not required for a minimal chat UI, but necessary for
parity with the richer terminal UX.

### Message history editing

- [NEW] `PATCH /sessions/{session_id}/messages/{index}`
    - Purpose: modify the content of a single message at `index`.
    - Body: `{ "content": str }`.
    - Index semantics: Python-style (0-based, negatives allowed).
    - Terminal parity: `TerminalApplication.modify_message` and `/modify`.

- [NEW] `DELETE /sessions/{session_id}/messages`
    - Purpose: delete one or more messages from history.
    - Body (one of):
        - `{ "indices": [int, ...] }` – delete specific indices.
        - `{ "range": { "start": Optional[int], "end": Optional[int] } }` –
          delete a slice (Python semantics).
        - `{ "last": int }` – delete the last N messages.
    - Response: `{ "session": <Session>, "deleted_indices": [int, ...] }`.
    - Terminal parity:
        - `TerminalApplication.delete_messages`
        - `TerminalApplication.delete_messages_by_range`
        - `TerminalApplication.delete_last_messages`
        - `/delete` command.

### Session forking

- [NEW] `POST /sessions/{session_id}/fork`
    - Purpose: create a new session by forking history up to a given
      message index.
    - Body: `{ "index": int }` (Python-style index; default `-1` to fork
      full history).
    - Response: `{ "session": <new Session>, "source_session_id": str }`.
    - Terminal parity: `TerminalApplication.fork_session` and `/fork`.

### Agent management

- [NEW] `GET /agents`
    - Purpose: list all configured agent ids.
    - Response: `{ "agents": [str, ...] }`.
    - Terminal parity: `TerminalApplication.available_agents` and
      `/agent` completion.

- [NEW] `GET /sessions/{session_id}/agent`
    - Purpose: get the current agent id for a session.
    - Response: `{ "agent_id": str }`.
    - Terminal parity: `TerminalApplication.current_agent_id`.

- [NEW] `PATCH /sessions/{session_id}/agent`
    - Purpose: switch the agent for a given session.
    - Body: `{ "agent_id": str }`.
    - Behaviour: delegates to `AgentApplication.update_agent` and
      persists the updated session.
    - Terminal parity: `TerminalApplication.switch_agent` and `/agent`.

---

## Advanced features (phase 3)

Endpoints that expose deeper configurability, plugin management, and
UI-schema details. These are mostly useful for rich IDE / web UIs or
admin tools.

### Plugin management

- [NEW] `GET /sessions/{session_id}/plugins`
    - Purpose: list plugins with enabled/active state for a session.
    - Response shape mirrors `TerminalApplication.list_plugins_for_session`:
      each entry includes `id`, `kind`, `name` (if any), `enabled`,
      `active`, and other plugin metadata.

- [NEW] `PUT /sessions/{session_id}/plugins`
    - Purpose: set the explicit list of enabled plugin ids for a session.
    - Body: `{ "enabled": [str, ...] }`.
    - Behaviour: delegates to `TerminalApplication.set_session_plugins`.

- [NEW] `DELETE /sessions/{session_id}/plugins`
    - Purpose: clear session-specific plugin overrides and fall back to
      agent defaults / implicit behaviour.
    - Behaviour: delegates to `TerminalApplication.clear_session_plugins`.

### Per-session configuration (/set parity)

- [NEW] `GET /sessions/{session_id}/config/schema`
    - Purpose: expose config keys contributed by plugins for this
      session's agent.
    - Source: `core.get_config_schema()` for the session's core/base
      config.
    - Terminal parity: used by `/help config`.

- [NEW] `GET /sessions/{session_id}/overrides`
    - Purpose: read per-session config overrides stored in
      `session.metadata["overrides"]`.

- [NEW] `PATCH /sessions/{session_id}/overrides`
    - Purpose: upsert one or more override keys for this session.
    - Body examples:
        - `{ "key": str, "value": Any }` – single-key helper (maps to
          `TerminalApplication.update_override`).
        - or `{ "values": {"k": v, ...} }` – bulk update.

### Application-level configuration

- [NEW] `GET /config/application/schema`
    - Purpose: expose static schema for application-level options used by
      the terminal / UI (e.g. tool output limits).
    - Source: `TerminalApplication.get_application_config_schema()`.

- [NEW] `GET /config/application`
    - Purpose: expose current values for `config["application"]`.
    - Source: `AgentApplication.get_application_config()`.

### UI schema helpers

- [NEW] `GET /sessions/{session_id}/ui-schema`
    - Purpose: expose the full flattened UI schema for this session's
      agent and plugin set, as returned by `AgentCore.get_ui_schema(config)`.
    - Usage:
        - Filter `ui_type == "config"` (or omitted) for configuration
          inputs.
        - Filter `ui_type == "message_footer"` for per-message footer
          fields.
        - Filter `ui_type == "status_bar"` for status bar fields.

### Feature-driven completions

- [NEW] `POST /sessions/{session_id}/completions`
    - Purpose: request feature-driven completions for a partially-typed
      input line (e.g. file-context suggestions for `@file:`).
    - Body: `{ "text": str }`.
    - Response: `{ "completions": [ {"replacement": str, "start": int, ...}, ... ] }`.
    - Source: `TerminalApplication.get_feature_completions()`.
