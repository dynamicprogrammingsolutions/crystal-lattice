# Session Metadata UI Schema Invalidation Events

Emit and consume explicit events when session metadata or UI-schema-affecting state changes, so clients can keep UI schema/settings fresh without refreshing them on every message reload.

## Requirements checklist

- [ ] Identify all session metadata/update paths that can affect UI schema, settings, actions, or message footer rendering.
- [ ] Emit a clear session-scoped event when metadata/overrides/UI-affecting state changes.
- [ ] Include enough event payload for clients to know which cached controllers to invalidate.
- [ ] Preserve existing checkpoint/cursor behavior for message/event polling.
- [ ] Add application/server tests for event emission.
- [ ] Cover the cloud plugin with integration tests, because it can update session metadata in background/server-side flows.

Parent Task: tasks/20260610-mobile-message-refresh-performance/000-main.md

Depends On: tasks/20260610-mobile-message-refresh-performance/010-bridge-concurrent-proxied-requests.md

## Background

The broad UI schema/settings refresh during message reload was added for a real reason: session metadata can change on the server in the background, not only due to frontend-visible actions. The frontend needs to learn about those changes.

The preferred fix is event-based invalidation, not blindly removing refreshes.

Existing infrastructure:

- `application/python/agent_terminal_app/server.py`
  - `/events` already supports polling by `session_id` and cursor.
- `packages/frontend-sdk/src/events/pollingEventSource.ts`
  - Mobile/SDK already poll events and can react to session-scoped event types.
- `core/python/agent_app/application_future.py`
  - `_apply_lifecycle_result` can patch `session_metadata` and `session_overrides`.
  - `save_session` persists sessions.
  - `publish_event` and `record_checkpoint` publish events and advance cursors when needed.
- `application/python/agent_terminal_app/terminal_app.py`
  - Many terminal-facing operations already publish events and record checkpoints after session changes.

## Event Design Notes

Use explicit event names rather than overloading generic checkpoint events. Candidate event types:

- `session_metadata_updated`
- `session_overrides_updated`
- `session_ui_schema_invalidated`

The event payload should include:

- `session_id`
- changed metadata keys if cheap/known
- whether overrides changed
- invalidation hints, for example `ui_schema`, `application_ui_schema`, `settings`, `message_footer`
- timestamp

Avoid embedding the full session or large metadata payload in the invalidation event.

## Cloud Plugin Coverage

The cloud plugin must be covered by integration tests. The test should exercise a realistic public flow where the cloud plugin or cloud-agent-related application behavior updates session metadata or UI-affecting state, then verify that the relevant invalidation event is visible through `/events`.

Likely places to inspect:

- `plugins/cloud-agent-app`
- `application/python/tests/test_cloud_agent_runtime.py`
- `application/python/tests/test_cloud_orchestrator_source_bundle.py`
- frontend SDK integration tests under `packages/frontend-sdk/src/integration/__tests__/cloud-orchestrator*.test.ts`

Keep the integration test realistic. Do not add test-only shortcuts that bypass the normal server/plugin/event path.