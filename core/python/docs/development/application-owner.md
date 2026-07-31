# Application owner implementation

This page maps the current Python implementation to the root runtime-reload
specification. It does not redefine reload behavior.

`agent_app.application_owner` owns the stable process-lifetime boundary around
the replaceable `AgentApplication`.

Maintainer entry points:

- `core/python/agent_app/application_owner.py`
- `core/python/agent_app/application_future.py`
- `core/python/agent_app/events.py`
- `core/python/tests/test_application_owner.py`

The owner implements operation admission, active-operation retention,
candidate construction, swap/rollback, application-notification state, and
old-application closure. `AgentApplication.close()` owns cleanup of
application plugins, async resources, runtime stores, tools, and MCP servers.

When changing this code, verify `RLD-*` requirements and preserve the
distinction between the stable owner and replaceable application.