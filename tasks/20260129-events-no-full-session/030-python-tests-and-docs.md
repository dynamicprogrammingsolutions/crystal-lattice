# Update Python tests and documentation for new event schema

Parent Task: `tasks/20260129-events-no-full-session/000-main.md`

Depends On:

- `tasks/20260129-events-no-full-session/020-python-event-producers.md`

After changing the event payloads, update tests and docs that assume events contain full session payloads.

## Status

- [x] Completed

## Tests likely affected

Search targets:

- `application/python/tests/` (many tests assert event kinds and sometimes payload fields)
- Any tests that reference `event["session"]` or expect a full session after mutation.

Quick grep suggestions:

- `rg "\"session\"\s*:" application/python/tests -n`
- `rg "message_modified|messages_deleted|session_created|message_appended" application/python/tests -n`

## Docs likely affected

- `application/python/agent_terminal_app/server_endpoints_parity.md`
- Any internal docs describing event payloads.

## Work checklist

- [x] Update tests to validate the new minimal fields (`index`, `indices`, `start_index`)
- [x] Remove assertions that require `event.session.messages`
- [x] Add/adjust tests verifying that events do *not* include a `session` key
- [x] Update docs to reflect that clients must bootstrap by fetching session messages after `session_created`

## Notes

- Added/updated size-budget regression tests to catch accidental re-introduction of full session payloads:
  - `application/python/tests/test_event_payload_size_budget.py`
  - `application/python/tests/test_terminal_event_rendering_ollama_tools.py` (Ollama-only)
- Updated doc: `application/python/agent_terminal_app/server_endpoints_parity.md`
