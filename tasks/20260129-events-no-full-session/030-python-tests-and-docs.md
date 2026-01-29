# Update Python tests and documentation for new event schema

Parent Task: `tasks/20260129-events-no-full-session/000-main.md`

Depends On:

- `tasks/20260129-events-no-full-session/020-python-event-producers.md`

After changing the event payloads, update tests and docs that assume events contain full session payloads.

## Status

- [ ] Not started

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

- [ ] Update tests to validate the new minimal fields (`index`, `indices`, `start_index`)
- [ ] Remove assertions that require `event.session.messages`
- [ ] Add/adjust tests verifying that events do *not* include a `session` key
- [ ] Update docs to reflect that clients must bootstrap by fetching session messages after `session_created`
