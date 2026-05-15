# MCP Runtime App Plugin

Application-level observability plugin for MCP runtimes.

This plugin exposes session actions for:

- showing MCP runtime status
- clearing stored MCP runtimes
- forcing reconnect on the next request by clearing runtimes

It is intentionally application-scoped rather than tool-scoped so that the UI
can inspect runtime state independent of any one wrapper plugin.

## License

This directory is available under the [Apache License 2.0](../../LICENSE).
