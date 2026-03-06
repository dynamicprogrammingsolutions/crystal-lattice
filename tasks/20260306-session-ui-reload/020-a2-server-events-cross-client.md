# A2: Server Events For Cross-Client Session UI Reload

Parent Task: `tasks/20260306-session-ui-reload/000-main.md`

Depends On:
- `tasks/20260306-session-ui-reload/010-a1-sdk-local-invalidation.md`

Description:
Add server-published events indicating that session settings/plugins changed, and have the JS SDK treat those events as cache-invalidation triggers so other clients (mobile/desktop) reload session-specific UI without user action.

Scope / requirements:
- Optional after A1.
- Keep events lightweight; do not embed full session payloads.
- Ensure this works even when changes are initiated outside the current client.

Relevant code:
- Server endpoints:
  - `application/python/agent_terminal_app/server.py`:
    - `PATCH /sessions/{session_id}/overrides`
    - `DELETE /sessions/{session_id}/overrides/{key}`
    - `PUT /sessions/{session_id}/plugins`
    - `DELETE /sessions/{session_id}/plugins`
    - (optional) `PATCH /sessions/{session_id}/agent`
- Event polling:
  - `packages/frontend-sdk/src/events/pollingEventSource.ts`
  - `packages/frontend-sdk/src/types/events.ts`

Proposed implementation:
- Publish events after successful mutations, e.g.:
  - `session_overrides_updated`
  - `session_plugins_updated`
  - `session_agent_updated`
- Add these to the SDK event union type.
- When `PollingEventSource` receives such events, emit the same invalidation signal used in A1.

Acceptance criteria:
- If desktop changes session plugins/settings, mobile reloads the session UI schema without reopening the session (and vice versa), as long as the session is polling `/events`.
