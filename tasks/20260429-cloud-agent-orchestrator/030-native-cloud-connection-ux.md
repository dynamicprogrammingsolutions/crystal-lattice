# Native Cloud Connection UX
Polish cloud connection handling so action-backed cloud workflows feel native: links can be opened/imported, cloud connections can be persisted, and action results can add/open cloud sessions automatically.

## Requirements checklist

- [ ] Parse cloud connection links in mobile/frontend.
- [ ] Persist cloud connection records and support reconnecting to existing cloud instances.
- [ ] Extend action result effects with add/update connection, open connection, and open session on connection.
- [ ] Add native UI affordances for cloud-linked readonly sessions.
- [ ] Show cloud status indicators on connection/session surfaces.
- [ ] Preserve the manual copy-link fallback from the MVP.

Parent Task: `tasks/20260429-cloud-agent-orchestrator/000-main.md`
Depends On: `tasks/20260429-cloud-agent-orchestrator/010-remote-docker-orchestrator-mvp.md`
Depends On: `tasks/20260429-cloud-agent-orchestrator/020-linked-readonly-session-ux.md`

## Scope

The underlying operations should still be action-backed and replaceable. Native UI should rely on conventions and metadata, not hardcoded provider internals.

Useful action effect directions:

- `add_connection`
- `update_connection`
- `open_connection`
- `open_session_on_connection`
- `reload_connection_sessions`

## High-Level Behaviors To Test Before Acceptance

- A copied cloud connection link can be pasted/opened and converted into a usable cloud connection.
- Action results can add a cloud connection and navigate to the remote session.
- Reopening a saved cloud connection reconnects through the orchestrator.
- Linked readonly sessions show a clear native affordance to open the cloud session.
- Manual fallback still works when automatic action effects are unavailable.