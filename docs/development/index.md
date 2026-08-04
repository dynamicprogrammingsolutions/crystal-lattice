# Development specifications

This section contains cross-package behavior that must remain consistent across
the Python runtime, transports, SDKs, plugins, and frontends.

- [Notifications](specifications/notifications/index.md)
- [Action displays](specifications/action-display/index.md)
- [Application runtime reload](specifications/application-runtime-reload/index.md)
- [Sessions actions](specifications/sessions-actions/index.md)

These specifications own portable behavior. Package development documentation
describes how the current implementation satisfies them without redefining the
contracts.