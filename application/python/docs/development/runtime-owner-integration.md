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

Server and terminal shutdown close the owner, which closes the active
application and its MCP/runtime resources.

Primary integration tests:

- `application/python/tests/test_application_reload_owner.py`
- `application/python/tests/test_notification_demo_plugins_http.py`
- `application/python/tests/test_cli_e2e.py`