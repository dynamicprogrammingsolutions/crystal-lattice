# C: ETag / Versioning For Session UI Schema (Pull-Based)

Parent Task: `tasks/20260306-session-ui-reload/000-main.md`

Description:
Introduce a pull-based cache validation strategy for `/sessions/{session_id}/ui-schema` so clients can cheaply detect changes even if they miss events (offline, backgrounded, event polling disabled).

Scope / requirements:
- Optional future direction.
- Avoid high-frequency polling; prefer conditional requests (`If-None-Match`) or a cheap "version" endpoint.
- Preserve current response shape for backwards compatibility.

Possible approaches:
1. HTTP `ETag` for `/sessions/{session_id}/ui-schema`
   - ETag derived from `(agent_id, enabled_plugins, overrides, server version)`.
   - SDK sends `If-None-Match`; server replies `304` when unchanged.
2. Separate version endpoint
   - `GET /sessions/{session_id}/ui-schema/version` returning `{version: string}`.
   - SDK compares and fetches full schema only on change.

Acceptance criteria:
- Clients can revalidate cached UI schema with low overhead.
- Works even when no events are delivered.
