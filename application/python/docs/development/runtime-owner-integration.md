# Runtime owner integration

`agent_terminal_app` constructs and retains one application owner for terminal,
HTTP, combined server/console, bridge, Bonjour, and shutdown paths.

Maintainer entry points:

- `application/python/agent_terminal_app/__main__.py`
- `application/python/agent_terminal_app/server.py`
- `application/python/agent_terminal_app/terminal_app.py`
- `application/python/agent_terminal_app/bridge_client.py`

Routes acquire owner operations rather than retaining a replaceable
`AgentApplication`. While reload is pending, new application operations receive
the `application_reload_pending` response.

Notification events use the shared event store. Application notifications are
polled without a session filter; session notifications use ordinary
session-filtered polling and session metadata for reconnect.

The runtime composition root creates one durable
`ApplicationNotificationStore` and injects it into every replacement
`AgentApplication`. `AgentApplication` owns the public notification contract.
`ApplicationControl` is limited to reload coordination, and the owner creates
reload requested/completed/failed notifications through the current
application.

The configured SQLite path is read when the owning runtime starts. Inner
application reloads reuse the already-open store; changing the path requires
reconstructing the owning runtime rather than switching or migrating databases
during reload.

Stage A exposes authoritative notification state and server dismissal through:

```text
GET  /application/notifications
POST /application/notifications/{notification_id}/dismiss
GET  /sessions/{session_id}/notifications
POST /sessions/{session_id}/notifications/{notification_id}/dismiss
```

List routes return active records unless `include_terminal=true`. Dismiss
accepts optional `expected_revision` and `reason`; stale revisions and invalid
lifecycle transitions return HTTP 409 with the current notification.

Server and terminal shutdown close the owner, which closes the active
application and its MCP/runtime resources, then close the runtime-owned
notification store.

Primary integration tests:

- `application/python/tests/test_application_reload_owner.py`
- `application/python/tests/test_notification_demo_plugins_http.py`
- `application/python/tests/test_cli_e2e.py`