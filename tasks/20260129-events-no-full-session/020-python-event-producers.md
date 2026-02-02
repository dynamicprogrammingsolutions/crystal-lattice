# Update Python event producers (remove `session` payloads)

Parent Task: `tasks/20260129-events-no-full-session/000-main.md`

Depends On:

- `tasks/20260129-events-no-full-session/010-event-contract.md`

Update all Python code that publishes events so events never include `session: session.to_dict()`.

## Status

- [x] Completed

## Current producers that embed full session history

### FastAPI server

File: `application/python/agent_terminal_app/server.py`

- `session_created` publishes `session.to_dict()`: `application/python/agent_terminal_app/server.py:410`
- `message_appended` publishes `session.to_dict()`: `application/python/agent_terminal_app/server.py:742`
- `message_modified` publishes `session.to_dict()`: `application/python/agent_terminal_app/server.py:1025`
- `messages_deleted` publishes `session.to_dict()`: `application/python/agent_terminal_app/server.py:1223`
- `fork` publishes `session.to_dict()` in `session_created`: `application/python/agent_terminal_app/server.py:1663`

### Terminal app

File: `application/python/agent_terminal_app/terminal_app.py`

- `session_created`: `application/python/agent_terminal_app/terminal_app.py:120`
- `message_appended`: `application/python/agent_terminal_app/terminal_app.py:246`
- `messages_deleted`: `application/python/agent_terminal_app/terminal_app.py:422`
- `message_modified`: `application/python/agent_terminal_app/terminal_app.py:600`
- `message_appended` (append to arbitrary session): `application/python/agent_terminal_app/terminal_app.py:789`

## Work checklist

- [x] Remove `session` field from all published events
- [x] Ensure mutation events include enough information for reducers:
  - [x] `message_appended` includes `index` and `message`
  - [x] `messages_deleted` includes `indices`
  - [x] `message_modified` includes `index` and `message` (and keeps `content` for compatibility)
- [x] Ensure `final` and `tool_results` events include positional info (`start_index`)

## Special notes

### `final` / `tool_results` sources are in core

These events are yielded by the application-layer tool loop:

- `final` events: `core/python/agent_app/tool_loop.py:126` and `core/python/agent_app/tool_loop.py:198`
- `tool_results` events: `core/python/agent_app/tool_loop.py:329`

They currently emit `messages` but no indices. To make them reducible without guessing, update these yields to include `start_index`.

Implemented in `core/python/agent_app/tool_loop.py`.

### Avoid leaking sessions via “backcompat” branches

The send background worker has a backcompat branch that checks for a `session` key in stored events:

- `application/python/agent_terminal_app/server.py:584`

After this task, new events should not include `session`. Consider removing that branch or keeping it strictly for old historical events.

The branch remains, but it is now only relevant for historical event store data.
